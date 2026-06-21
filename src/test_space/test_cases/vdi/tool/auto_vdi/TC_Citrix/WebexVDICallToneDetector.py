"""Ringback/call-progress tone detector.

Examples:
    python WebexVDICallToneDetector.py
    python WebexVDICallToneDetector.py --ringback-single --ringback-on 0.9 --ringback-off 4.8
    python WebexVDICallToneDetector.py --duration-seconds 60
    python WebexVDICallToneDetector.py --no-duration
    python WebexVDICallToneDetector.py --list-loopback
    python WebexVDICallToneDetector.py --backend sounddevice
    python WebexVDICallToneDetector.py --backend soundcard --list-speakers
    python WebexVDICallToneDetector.py --backend soundcard --speaker "Realtek"
    python WebexVDICallToneDetector.py --ringback-single --cadence-debug ringback --meter --meter-mode tones
    python WebexVDICallToneDetector.py --deps
"""

import argparse
import inspect
import math
import queue
import sys
import time

import numpy as np
try:
    import sounddevice as sd
    _SOUNDDEVICE_ERROR = None
except Exception as exc:
    sd = None
    _SOUNDDEVICE_ERROR = exc
try:
    import soundcard as sc
except ImportError:
    sc = None

DEFAULT_BACKEND = "soundcard" if sys.platform != "win32" else "sounddevice"

# US call progress tones (default). Adjust if your region differs.
TONE_DEFS = {
    "ringback": {
        "freqs_hz": (440.0, 480.0),
        "cadence": (0.9, 4.8),
        "cycles_required": 1,
        "cadence_on_min_only": True,
    },
    "busy": {
        "freqs_hz": (480.0, 620.0),
        "cadence": (0.5, 0.5),
        "cycles_required": 3,
    },
    "fast_busy": {
        "freqs_hz": (480.0, 620.0),
        "cadence": (0.25, 0.25),
        "cycles_required": 4,
    },
    "dial": {
        "freqs_hz": (350.0, 440.0),
        "cadence": None,
        "hold_sec": 1.0,
    },
}

SAMPLE_RATE = 8000
FRAME_MS = 40  # 25 fps
FRAME_SIZE = int(SAMPLE_RATE * FRAME_MS / 1000)

# Energy thresholds (tune if needed)
MIN_TONE_DB = -35.0
MIN_MATCH_FRAMES = int(0.2 / (FRAME_MS / 1000))  # 200ms stability
TONE_POWER_RATIO = 0.05
CADENCE_TOLERANCE_RATIO = 0.4
CADENCE_TOLERANCE_MIN_SEC = 0.3

_audio_q = queue.Queue()


def _goertzel_power(samples: np.ndarray, freq_hz: float, sample_rate: int) -> float:
    # Goertzel algorithm for a single frequency bin
    n = len(samples)
    k = int(0.5 + (n * freq_hz) / sample_rate)
    w = (2.0 * math.pi * k) / n
    cosine = math.cos(w)
    sine = math.sin(w)
    coeff = 2.0 * cosine
    q0 = 0.0
    q1 = 0.0
    q2 = 0.0
    for x in samples:
        q0 = coeff * q1 - q2 + x
        q2 = q1
        q1 = q0
    real = q1 - q2 * cosine
    imag = q2 * sine
    return real * real + imag * imag


def _rms_db(samples: np.ndarray) -> float:
    rms = np.sqrt(np.mean(samples * samples) + 1e-12)
    return 20.0 * math.log10(rms + 1e-12)


def _audio_callback(indata, frames, time_info, status):
    if status:
        print(status, file=sys.stderr)
    _audio_q.put(indata.copy())


def _is_tone_present(samples: np.ndarray, freqs_hz, total_power, level_db) -> bool:
    if level_db < MIN_TONE_DB:
        return False
    for freq in freqs_hz:
        p = _goertzel_power(samples, freq, SAMPLE_RATE)
        if (p / total_power) <= TONE_POWER_RATIO:
            return False
    return True


def _process_samples(
    samples,
    unique_freqs,
    tone_state,
    sample_rate,
    meter_state=None,
    cadence_debug=None,
    detect_state=None,
):
    level_db = _rms_db(samples)
    total = np.sum(samples * samples) + 1e-12
    freq_power = {freq: _goertzel_power(samples, freq, sample_rate) for freq in unique_freqs}

    now = time.time()
    if meter_state is not None:
        if now - meter_state["last_print"] >= meter_state["interval_sec"]:
            if meter_state.get("mode") == "tones":
                parts = [f"Level: {level_db:.1f} dB"]
                for name, cfg in TONE_DEFS.items():
                    ratios = []
                    for freq in cfg["freqs_hz"]:
                        ratios.append(freq_power[freq] / total)
                    ratio_str = ",".join(f"{r:.3f}" for r in ratios)
                    parts.append(f"{name}:{ratio_str}")
                print(" | ".join(parts))
            else:
                print(f"Level: {level_db:.1f} dB")
            meter_state["last_print"] = now
    for name, cfg in TONE_DEFS.items():
        state = tone_state[name]
        if level_db < MIN_TONE_DB:
            match = False
        else:
            if cfg.get("single_freq_ok"):
                match = any((freq_power[f] / total) > TONE_POWER_RATIO for f in cfg["freqs_hz"])
            else:
                match = all((freq_power[f] / total) > TONE_POWER_RATIO for f in cfg["freqs_hz"])

        if match:
            state["match_frames"] += 1
        else:
            state["match_frames"] = 0

        stable_on = state["match_frames"] >= MIN_MATCH_FRAMES
        cadence = cfg.get("cadence")
        if cadence:
            if stable_on:
                if state["last_state"] != "on":
                    if cadence_debug == name and state["off_start"]:
                        off_dur = now - state["off_start"]
                        print(f"{name} off_dur={off_dur:.2f}s")
                    state["on_start"] = now
                    state["last_state"] = "on"
                    state["off_start"] = None
            else:
                if state["last_state"] != "off":
                    if cadence_debug == name and state["on_start"]:
                        on_dur = now - state["on_start"]
                        print(f"{name} on_dur={on_dur:.2f}s")
                    state["off_start"] = now
                    state["last_state"] = "off"

            if state["on_start"] and state["off_start"]:
                on_dur = state["off_start"] - state["on_start"]
                tol = max(CADENCE_TOLERANCE_MIN_SEC, cadence[0] * CADENCE_TOLERANCE_RATIO)
                if cfg.get("cadence_on_min_only"):
                    on_ok = on_dur >= cadence[0] - tol
                else:
                    on_ok = abs(on_dur - cadence[0]) <= tol
                if on_ok:
                    off_dur = now - state["off_start"]
                    tol_off = max(CADENCE_TOLERANCE_MIN_SEC, cadence[1] * CADENCE_TOLERANCE_RATIO)
                    if off_dur >= cadence[1] - tol_off:
                        state["cycles"] += 1
                        state["on_start"] = None
                        state["off_start"] = None
                        state["last_state"] = "off"
                        if cadence_debug == name:
                            print(f"{name} off_dur={off_dur:.2f}s")

            if state["cycles"] >= cfg.get("cycles_required", 2):
                if now - state["last_detect_time"] >= 1.0:
                    if detect_state is None or not detect_state.get("summary_only", False):
                        print(f"{name} detected")
                    if detect_state is not None and name == "ringback":
                        detect_state["ringback_count"] += 1
                    state["last_detect_time"] = now
                state["cycles"] = 0
        else:
            hold_sec = cfg.get("hold_sec", 1.0)
            if stable_on:
                if state["on_start"] is None:
                    state["on_start"] = now
                if now - state["on_start"] >= hold_sec:
                    if now - state["last_detect_time"] >= 1.0:
                        print(f"{name} detected")
                        state["last_detect_time"] = now
                    state["on_start"] = now
            else:
                state["on_start"] = None


def _list_input_devices():
    devices = sd.query_devices()
    hostapis = sd.query_hostapis()
    for idx, dev in enumerate(devices):
        if dev.get("max_input_channels", 0) <= 0:
            continue
        hostapi = hostapis[dev["hostapi"]]["name"]
        print(f"[{idx}] {dev['name']} (hostapi={hostapi}, in_ch={dev['max_input_channels']})")


def _print_deps():
    print("Required modules:")
    print("  numpy")
    print("  sounddevice")
    print("  Microsoft Visual Studio Build Tools - Windows C/C++ build toolchain")
    print("  MSVC v143 C++ build tools (x64/x86)")
    print("  Windows 10/11 SDK")
    print("  (Windows only) Needed for building numpy from source")
    print("Optional modules:")
    print("  soundcard (for loopback fallback)")
    print("\nInstall commands:")
    print("  pip install numpy sounddevice")
    print("  pip install soundcard")


def _print_examples():
    print("Examples:")
    print("  python WebexVDICallToneDetector.py")
    print("  python WebexVDICallToneDetector.py --ringback-single --ringback-on 0.9 --ringback-off 4.8")
    print("  python WebexVDICallToneDetector.py --duration-seconds 60")
    print("  python WebexVDICallToneDetector.py --no-duration")
    print("  python WebexVDICallToneDetector.py --list-loopback")
    print("  python WebexVDICallToneDetector.py --backend sounddevice")
    print("  python WebexVDICallToneDetector.py --backend soundcard --list-speakers")
    print("  python WebexVDICallToneDetector.py --backend soundcard --speaker \"Realtek\"")
    print("  python WebexVDICallToneDetector.py --ringback-single --cadence-debug ringback --meter --meter-mode tones")
    print("  python WebexVDICallToneDetector.py --deps")


def _require_sounddevice():
    if sd is None:
        raise RuntimeError(
            "sounddevice is not available. Install PortAudio and sounddevice. "
            "See --deps for details."
        ) from _SOUNDDEVICE_ERROR
    return sd


def _pick_wasapi_loopback_device():
    devices = sd.query_devices()
    hostapis = sd.query_hostapis()
    for idx, dev in enumerate(devices):
        if dev.get("max_input_channels", 0) <= 0:
            continue
        hostapi = hostapis[dev["hostapi"]]["name"]
        name = dev.get("name", "")
        if "WASAPI" in hostapi and "loopback" in name.lower():
            return idx
    return None


def _get_wasapi_loopback_devices():
    devices = sd.query_devices()
    hostapis = sd.query_hostapis()
    loopbacks = []
    for idx, dev in enumerate(devices):
        hostapi = hostapis[dev["hostapi"]]["name"]
        name = dev.get("name", "")
        if "WASAPI" in hostapi and dev.get("max_output_channels", 0) > 0:
            loopbacks.append((idx, dev))
    return loopbacks


def _list_loopback_devices():
    loopbacks = _get_wasapi_loopback_devices()
    if not loopbacks:
        print("No WASAPI loopback devices found.")
        return
    for idx, dev in loopbacks:
        hostapi = sd.query_hostapis()[dev["hostapi"]]["name"]
        print(f"[{idx}] {dev['name']} (hostapi={hostapi}, in_ch={dev['max_input_channels']})")


def _is_wasapi_device(device_index: int) -> bool:
    if device_index is None:
        return False
    dev = sd.query_devices(device_index)
    hostapi = sd.query_hostapis()[dev["hostapi"]]["name"]
    return "WASAPI" in hostapi


def _get_wasapi_loopback_settings():
    if not hasattr(sd, "WasapiSettings"):
        return None
    try:
        sig = inspect.signature(sd.WasapiSettings)
    except (TypeError, ValueError):
        return None
    if "loopback" in sig.parameters:
        return sd.WasapiSettings(loopback=True)
    return None


def _get_loopback_mics():
    mics = sc.all_microphones(include_loopback=True)
    loopbacks = []
    for mic in mics:
        if getattr(mic, "isloopback", False) or "loopback" in mic.name.lower():
            loopbacks.append(mic)
    return loopbacks


def _list_speakers():
    if sc is None:
        print("soundcard is not installed. Use: pip install soundcard")
        return
    loopbacks = _get_loopback_mics()
    if not loopbacks:
        print("No loopback microphones found (soundcard).")
        return
    for mic in loopbacks:
        print(mic.name)


def _pick_loopback_mic(name_substr: str | None):
    if sc is None:
        raise RuntimeError("soundcard is not installed. Use: pip install soundcard")
    loopbacks = _get_loopback_mics()
    if not loopbacks:
        raise RuntimeError("No loopback microphones found (soundcard).")
    if name_substr:
        name_substr = name_substr.lower()
        for mic in loopbacks:
            if name_substr in mic.name.lower():
                return mic
        raise RuntimeError(f"No loopback mic matched '{name_substr}'.")

    speaker = sc.default_speaker()
    if speaker:
        for mic in loopbacks:
            if speaker.name.lower() in mic.name.lower():
                return mic

    if sys.platform != "win32":
        for mic in loopbacks:
            if "monitor" in mic.name.lower():
                return mic
    return loopbacks[0]


def _run_soundcard(
    tone_state,
    unique_freqs,
    speaker_filter: str | None,
    meter_state=None,
    cadence_debug=None,
    detect_state=None,
    end_time=None,
):
    mic = _pick_loopback_mic(speaker_filter)
    sample_rate = int(getattr(mic, "default_samplerate", SAMPLE_RATE))
    print(f"Soundcard loopback: {mic.name} (sample_rate={sample_rate})")
    with mic.recorder(samplerate=sample_rate, channels=1) as rec:
        while True:
            data = rec.record(numframes=FRAME_SIZE)
            samples = data[:, 0].astype(np.float32)
            _process_samples(
                samples,
                unique_freqs,
                tone_state,
                sample_rate,
                meter_state,
                cadence_debug,
                detect_state,
            )
            if end_time is not None and time.time() >= end_time:
                break


def _get_capture_channels(device_info, loopback_active: bool) -> int:
    if loopback_active and device_info.get("max_output_channels", 0) > 0:
        return min(2, int(device_info["max_output_channels"]))
    return int(device_info.get("max_input_channels", 0))


def _scan_loopback_devices(seconds_per_device: float) -> int | None:
    loopbacks = _get_wasapi_loopback_devices()
    if not loopbacks:
        print("No WASAPI loopback devices found.")
        return None

    print("Scanning WASAPI loopback devices...")
    for idx, dev in loopbacks:
        print(f"Testing [{idx}] {dev['name']} for {seconds_per_device:.1f}s")
        q = queue.Queue()

        def _cb(indata, frames, time_info, status):
            if status:
                print(status, file=sys.stderr)
            q.put(indata.copy())

        match_frames = 0
        total_frames = 0
        start = time.time()
        with sd.InputStream(
            channels=1,
            samplerate=SAMPLE_RATE,
            blocksize=FRAME_SIZE,
            device=idx,
            extra_settings=sd.WasapiSettings(loopback=True),
            callback=_cb,
        ):
            while time.time() - start < seconds_per_device:
                data = q.get()
                samples = data[:, 0].astype(np.float32)
                level_db = _rms_db(samples)
                total_power = np.sum(samples * samples) + 1e-12
                if _is_tone_present(samples, TONE_DEFS["ringback"]["freqs_hz"], total_power, level_db):
                    match_frames += 1
                total_frames += 1

        if total_frames > 0:
            ratio = match_frames / total_frames
        else:
            ratio = 0.0
        print(f"  ringback match ratio: {ratio:.2f}")

        ans = input("Use this device? [y/N/q]: ").strip().lower()
        if ans == "y":
            return idx
        if ans == "q":
            return None

    print("No device selected.")
    return None


def main():
    parser = argparse.ArgumentParser(description="Detect call progress tones in real time.")
    parser.add_argument(
        "--backend",
        choices=["sounddevice", "soundcard"],
        default=DEFAULT_BACKEND,
        help="Audio backend to use.",
    )
    parser.add_argument("--list-devices", action="store_true", help="List input devices and exit.")
    parser.add_argument("--list-loopback", action="store_true", help="List WASAPI loopback devices and exit.")
    parser.add_argument("--list-speakers", action="store_true", help="List speakers (soundcard backend only).")
    parser.add_argument("--deps", action="store_true", help="Show required/optional modules and exit.")
    parser.add_argument("--examples", action="store_true", help="Show command examples and exit.")
    parser.add_argument("--device", type=int, default=None, help="Input device index to use.")
    parser.add_argument("--speaker", type=str, default=None, help="Speaker name filter (soundcard backend).")
    parser.add_argument(
        "--scan-loopback",
        action="store_true",
        help="Scan WASAPI loopback devices one by one and select interactively.",
    )
    parser.add_argument(
        "--scan-seconds",
        type=float,
        default=3.0,
        help="Seconds to test each loopback device during scan.",
    )
    parser.add_argument("--meter", action="store_true", help="Print live input level every second.")
    parser.add_argument(
        "--meter-mode",
        choices=["level", "tones"],
        default="level",
        help="Meter output mode.",
    )
    parser.add_argument(
        "--meter-interval",
        type=float,
        default=1.0,
        help="Seconds between meter prints.",
    )
    parser.add_argument(
        "--ringback-single",
        action="store_true",
        help="Allow single-frequency ringback detection (e.g., 440 Hz only).",
    )
    parser.add_argument("--ringback-on", type=float, default=None, help="Ringback on duration (seconds).")
    parser.add_argument("--ringback-off", type=float, default=None, help="Ringback off duration (seconds).")
    parser.add_argument(
        "--ringback-cycles",
        type=int,
        default=None,
        help="Number of ringback cycles required for detection.",
    )
    parser.add_argument(
        "--cadence-debug",
        type=str,
        default=None,
        help="Print observed on/off durations for a tone (e.g., ringback).",
    )
    parser.add_argument(
        "--duration-seconds",
        type=float,
        default=20.0,
        help="Total run duration in seconds; prints ringback count at end.",
    )
    parser.add_argument(
        "--no-duration",
        action="store_true",
        help="Run indefinitely and print detections as they occur.",
    )
    args = parser.parse_args()

    if args.list_devices:
        _require_sounddevice()
        _list_input_devices()
        return
    if args.list_loopback:
        _require_sounddevice()
        _list_loopback_devices()
        return
    if args.list_speakers:
        _list_speakers()
        return
    if args.deps:
        _print_deps()
        return
    if args.examples:
        _print_examples()
        return

    print("Starting tone detection (default device)...")
    print(f"Sample rate: {SAMPLE_RATE} Hz, frame: {FRAME_MS} ms")
    for name, cfg in TONE_DEFS.items():
        freqs = cfg["freqs_hz"]
        cadence = cfg.get("cadence")
        if cadence:
            print(f"Tone: {name}, freqs: {freqs}, cadence: {cadence[0]}s on / {cadence[1]}s off")
        else:
            print(f"Tone: {name}, freqs: {freqs}, continuous")

    tone_state = {}
    for name in TONE_DEFS.keys():
        tone_state[name] = {
            "on_start": None,
            "off_start": None,
            "last_state": "off",
            "match_frames": 0,
            "cycles": 0,
            "last_detect_time": 0.0,
        }

    if args.ringback_single:
        TONE_DEFS["ringback"]["single_freq_ok"] = True
    if args.ringback_on is not None or args.ringback_off is not None:
        on = args.ringback_on if args.ringback_on is not None else TONE_DEFS["ringback"]["cadence"][0]
        off = args.ringback_off if args.ringback_off is not None else TONE_DEFS["ringback"]["cadence"][1]
        TONE_DEFS["ringback"]["cadence"] = (on, off)
    if args.ringback_cycles is not None:
        TONE_DEFS["ringback"]["cycles_required"] = max(1, args.ringback_cycles)

    unique_freqs = sorted({f for cfg in TONE_DEFS.values() for f in cfg["freqs_hz"]})
    meter_state = None
    if args.meter:
        meter_state = {
            "last_print": 0.0,
            "interval_sec": args.meter_interval,
            "mode": args.meter_mode,
        }
    if args.no_duration:
        duration_seconds = None
    else:
        duration_seconds = args.duration_seconds

    detect_state = {
        "ringback_count": 0,
        "summary_only": duration_seconds is not None,
    }
    end_time = None
    if duration_seconds is not None:
        end_time = time.time() + duration_seconds

    if args.backend == "soundcard":
        _run_soundcard(
            tone_state,
            unique_freqs,
            args.speaker,
            meter_state,
            args.cadence_debug,
            detect_state,
            end_time,
        )
        if detect_state["summary_only"]:
            print(f"Ringback detections: {detect_state['ringback_count']}")
        return

    _require_sounddevice()
    try:
        input_device = None
        if args.scan_loopback:
            input_device = _scan_loopback_devices(args.scan_seconds)
        else:
            input_device = args.device

        if input_device is None:
            input_device = _pick_wasapi_loopback_device()
        if input_device is None:
            input_device = sd.default.device[1]
        if input_device is None:
            input_device = sd.default.device[0]
        if input_device is None:
            device_info = sd.query_devices(kind="input")
        else:
            device_info = sd.query_devices(input_device)
        loopback_active = _is_wasapi_device(input_device)
        print(
            "Input device: "
            f"{device_info['name']} (in_ch={device_info['max_input_channels']}, "
            f"out_ch={device_info['max_output_channels']}, loopback={loopback_active})"
        )
        loopback_settings = _get_wasapi_loopback_settings() if loopback_active else None
        if loopback_active and loopback_settings is None:
            raise RuntimeError(
                "WASAPI loopback is not supported by this sounddevice version. "
                "Upgrade with: pip install -U sounddevice"
            )
        if loopback_active:
            print("WASAPI loopback mode enabled")

        capture_channels = _get_capture_channels(device_info, loopback_active)
        if capture_channels <= 0:
            raise RuntimeError(
                "Selected device has no usable capture channels. "
                "Pick a WASAPI output device for loopback or an input device with channels."
            )

        with sd.InputStream(
            channels=capture_channels,
            samplerate=SAMPLE_RATE,
            blocksize=FRAME_SIZE,
            device=input_device,
            extra_settings=loopback_settings,
            callback=_audio_callback,
        ):
            while True:
                data = _audio_q.get()
                samples = data[:, 0].astype(np.float32)
                _process_samples(
                    samples,
                    unique_freqs,
                    tone_state,
                    SAMPLE_RATE,
                    meter_state,
                    args.cadence_debug,
                    detect_state,
                )
                if end_time is not None and time.time() >= end_time:
                    break
    except (RuntimeError, sd.PortAudioError) as exc:
        print(f"sounddevice failed: {exc}")
        if sc is None:
            raise
        print("Falling back to soundcard backend.")
        _run_soundcard(
            tone_state,
            unique_freqs,
            args.speaker,
            meter_state,
            args.cadence_debug,
            detect_state,
            end_time,
        )

    if detect_state["summary_only"]:
        print(f"Ringback detections: {detect_state['ringback_count']}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Stopped.")


def run_detector_soundcard(
    sample_rate,
    freqs,
    threshold,
    on_min_s,
    off_min_s,
    window_ms,
    speaker_name=None,
    calibrate_seconds=0,
    auto_apply=False,
    vu_meter=False,
    rms_positive_streak=0,
    rms_positive_duration_s=0.0,
    total_run_s=0.0,
):
    try:
        import soundcard as sc
    except ImportError:
        raise RuntimeError("Missing dependency: soundcard. Install with: pip install soundcard")

    speaker = None
    if speaker_name:
        for sp in sc.all_speakers():
            if speaker_name.lower() in sp.name.lower():
                speaker = sp
                break
        if speaker is None:
            raise RuntimeError(f"Speaker not found: {speaker_name}")
    else:
        speaker = sc.default_speaker()

    if speaker is None:
        raise RuntimeError("No default speaker found.")

    print(f"Using speaker: {speaker.name}")

    mic = sc.get_microphone(speaker.name, include_loopback=True)
    if mic is None:
        raise RuntimeError(f"Loopback microphone not available for speaker: {speaker.name}")
    print(f"Using loopback microphone: {mic.name}")

    def chunk_provider(window_samples_local):
        with mic.recorder(samplerate=sample_rate, channels=1) as rec:
            data = rec.record(numframes=window_samples_local)
        return data

    if calibrate_seconds > 0:
        result = _run_calibration(chunk_provider, sample_rate, calibrate_seconds, window_ms)
        if auto_apply and result:
            print("Applying calibration results.")
            freqs = result["freqs"]
            on_min_s = result["on_min"]
            off_min_s = result["off_min"]
        else:
            return

    if calibrate_seconds == 0 or (auto_apply and result):
        _run_detector_loop(
            chunk_provider,
            sample_rate,
            freqs,
            threshold,
            on_min_s,
            off_min_s,
            window_ms,
            vu_meter=vu_meter,
            rms_positive_streak=rms_positive_streak,
            rms_positive_duration_s=rms_positive_duration_s,
            total_run_s=total_run_s,
        )


def legacy_main():
    parser = argparse.ArgumentParser(description="Detect ringback tone via WASAPI loopback")
    parser.add_argument("--list-devices", action="store_true", help="List audio devices and exit")
    parser.add_argument("--list-speakers", action="store_true", help="List soundcard speakers and loopback availability")
    parser.add_argument("--print-comm-speaker", action="store_true", help="Print Windows default communications speaker and exit")
    parser.add_argument("--deps", action="store_true", help="Print required Python modules and exit")
    parser.add_argument("--device", type=int, default=None, help="Audio device index for loopback capture")
    parser.add_argument("--backend", choices=["sounddevice", "soundcard"], default="soundcard", help="Capture backend")
    parser.add_argument("--speaker-name", default="Speakers (Realtek(R) Audio)", help="Speaker name filter for soundcard backend")
    parser.add_argument("--use-comm-speaker", action="store_true", help="Use Windows default communications speaker (soundcard backend)")
    parser.add_argument("--no-comm-speaker", dest="use_comm_speaker", action="store_false", help="Do not prefer communications speaker (soundcard backend)")
    parser.set_defaults(use_comm_speaker=True)
    parser.add_argument("--sample-rate", type=int, default=8000, help="Sample rate (default: 8000)")
    parser.add_argument("--channels", type=int, default=None, help="Number of channels for loopback capture")
    parser.add_argument("--freqs", type=float, nargs="+", default=[450.0], help="Target frequencies in Hz")
    parser.add_argument("--threshold", type=float, default=1.0e12, help="Detection power threshold")
    parser.add_argument("--on-min", type=float, default=0.9, help="Minimum ON time to count (seconds)")
    parser.add_argument("--off-min", type=float, default=3.5, help="Minimum OFF time to count (seconds)")
    parser.add_argument("--window-ms", type=int, default=200, help="Analysis window size in ms")
    parser.add_argument("--calibrate-seconds", type=int, default=0, help="Calibrate from live audio and exit")
    parser.add_argument("--auto-apply", action="store_true", help="Apply calibration results and continue detection")
    parser.add_argument("--vu", action="store_true", help="Print live RMS and tone power")
    parser.add_argument("--rms-positive-streak", type=int, default=0, help="Count RMS>0 streaks of N windows (0 disables)")
    parser.add_argument("--rms-positive-duration", type=float, default=0.0, help="Count RMS>0 streaks for duration in seconds (0 disables)")
    parser.add_argument("--run-seconds", type=float, default=0.0, help="Stop after N seconds and print summary (0 runs until Ctrl+C)")
    args = parser.parse_args()

    if args.list_devices:
        list_devices()
        return
    if args.list_speakers:
        list_soundcard_speakers()
        return
    if args.print_comm_speaker:
        name = get_default_communications_speaker_name()
        if name:
            print(f"Default communications speaker: {name}")
        else:
            fallback = get_default_speaker_name()
            if fallback:
                print("Unable to detect default communications speaker.")
                print(f"Default speaker: {fallback}")
            else:
                print("Unable to detect default communications speaker. Install with: pip install pycaw comtypes")
        return
    if args.deps:
        print("Required modules: numpy, sounddevice, soundcard")
        print("Recommended modules: pycaw, comtypes (for communications speaker)")
        print("Install with: pip install numpy sounddevice soundcard")
        print("Install optional with: pip install pycaw comtypes")
        return

    if args.backend == "soundcard":
        if args.use_comm_speaker:
            comm_name = get_default_communications_speaker_name()
            if comm_name:
                args.speaker_name = comm_name
                print(f"Using communications speaker: {comm_name}")
            else:
                args.speaker_name = None
                print("Unable to detect communications speaker. Falling back to default speaker.")
        run_detector_soundcard(
            sample_rate=args.sample_rate,
            freqs=args.freqs,
            threshold=args.threshold,
            on_min_s=args.on_min,
            off_min_s=args.off_min,
            window_ms=args.window_ms,
            speaker_name=args.speaker_name,
            calibrate_seconds=args.calibrate_seconds,
            auto_apply=args.auto_apply,
            vu_meter=args.vu,
            rms_positive_streak=args.rms_positive_streak,
            rms_positive_duration_s=args.rms_positive_duration,
            total_run_s=args.run_seconds,
        )
    else:
        run_detector_sounddevice(
            device_index=args.device,
            sample_rate=args.sample_rate,
            freqs=args.freqs,
            threshold=args.threshold,
            on_min_s=args.on_min,
            off_min_s=args.off_min,
            window_ms=args.window_ms,
            channels=args.channels,
            calibrate_seconds=args.calibrate_seconds,
            auto_apply=args.auto_apply,
            vu_meter=args.vu,
            rms_positive_streak=args.rms_positive_streak,
            rms_positive_duration_s=args.rms_positive_duration,
            total_run_s=args.run_seconds,
        )


