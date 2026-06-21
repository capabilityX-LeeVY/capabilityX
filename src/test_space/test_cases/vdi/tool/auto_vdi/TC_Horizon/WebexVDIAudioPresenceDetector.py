"""Audio presence detector (music/voice vs blank/noise).

Examples:
    python WebexVDIAudioPresenceDetector.py
    python WebexVDIAudioPresenceDetector.py --duration-seconds 60
    python WebexVDIAudioPresenceDetector.py --no-duration --meter
    python WebexVDIAudioPresenceDetector.py --backend sounddevice
    python WebexVDIAudioPresenceDetector.py --backend soundcard --list-speakers
    python WebexVDIAudioPresenceDetector.py --backend soundcard --speaker "monitor"
    python WebexVDIAudioPresenceDetector.py --deps
    python WebexVDIAudioPresenceDetector.py --classify --classifier-model model.joblib
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

SAMPLE_RATE = 16000
FRAME_MS = 50
FRAME_SIZE = int(SAMPLE_RATE * FRAME_MS / 1000)

MIN_AUDIO_DB = -45.0 if sys.platform == "win32" else -60.0
FLATNESS_MAX = 0.7
BAND_RATIO_MIN = 0.15

_audio_q = queue.Queue()


def _rms_db(samples: np.ndarray) -> float:
    rms = np.sqrt(np.mean(samples * samples) + 1e-12)
    return 20.0 * math.log10(rms + 1e-12)


def _spectral_flatness(samples: np.ndarray) -> float:
    window = np.hanning(len(samples))
    spectrum = np.fft.rfft(samples * window)
    power = (np.abs(spectrum) ** 2) + 1e-12
    geometric = np.exp(np.mean(np.log(power)))
    arithmetic = np.mean(power)
    return float(geometric / arithmetic)


def _band_energy_ratio(samples: np.ndarray, sample_rate: int, low_hz: float = 150.0, high_hz: float = 4000.0) -> float:
    window = np.hanning(len(samples))
    spectrum = np.fft.rfft(samples * window)
    power = (np.abs(spectrum) ** 2) + 1e-12
    freqs = np.fft.rfftfreq(len(samples), d=1.0 / sample_rate)
    band = (freqs >= low_hz) & (freqs <= high_hz)
    band_energy = float(np.sum(power[band]))
    total_energy = float(np.sum(power))
    return band_energy / total_energy


def _audio_callback(indata, frames, time_info, status):
    if status:
        print(status, file=sys.stderr)
    _audio_q.put(indata.copy())


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
    print("  numpy - DSP math and FFT")
    print("  sounddevice - audio capture via PortAudio")
    print("  Microsoft Visual Studio Build Tools - Windows C/C++ build toolchain")
    print("  MSVC v143 C++ build tools (x64/x86)")
    print("  Windows 10/11 SDK")
    print("  (Windows only) Needed for building numpy from source")
    print("Optional modules:")
    print("  soundcard - loopback capture fallback")
    print("  librosa - audio feature extraction")
    print("  scikit-learn - ML classifier")
    print("  joblib - model load/save")
    print("\nInstall commands:")
    print("  pip install numpy sounddevice")
    print("  pip install soundcard")
    print("  pip install librosa scikit-learn joblib")


def _print_examples():
    print("Examples:")
    print("  python WebexVDIAudioPresenceDetector.py")
    print("  python WebexVDIAudioPresenceDetector.py --duration-seconds 60")
    print("  python WebexVDIAudioPresenceDetector.py --no-duration --meter")
    print("  python WebexVDIAudioPresenceDetector.py --no-duration --meter-ui")
    print("  python WebexVDIAudioPresenceDetector.py --backend sounddevice")
    print("  python WebexVDIAudioPresenceDetector.py --backend soundcard --list-speakers")
    print("  python WebexVDIAudioPresenceDetector.py --backend soundcard --speaker \"monitor\"")
    print("  python WebexVDIAudioPresenceDetector.py --deps")
    print("  python WebexVDIAudioPresenceDetector.py --classify --classifier-model model.joblib --class-labels voice,music")


def _require_sounddevice():
    if sd is None:
        raise RuntimeError(
            "sounddevice is not available. Install PortAudio and sounddevice. "
            "See --deps for details."
        ) from _SOUNDDEVICE_ERROR
    return sd


def _print_helper():
    print("Helper commands:")
    print("  python WebexVDIAudioPresenceDetector.py")
    print("  python WebexVDIAudioPresenceDetector.py --meter")
    print("  python WebexVDIAudioPresenceDetector.py --meter-ui")
    print("  python WebexVDIAudioPresenceDetector.py --duration-seconds 30")
    print("  python WebexVDIAudioPresenceDetector.py --no-duration --meter")
    print("  python WebexVDIAudioPresenceDetector.py --no-duration --meter-ui")
    print("  python WebexVDIAudioPresenceDetector.py --backend sounddevice")
    print("  python WebexVDIAudioPresenceDetector.py --backend soundcard --list-speakers")
    print("  python WebexVDIAudioPresenceDetector.py --backend soundcard --speaker \"monitor\"")
    print("  python WebexVDIAudioPresenceDetector.py --classify --classifier-model model.joblib --class-labels voice,music")
    print("  python WebexVDIAudioPresenceDetector.py --deps")
    print("  python dataset_setup.py --out-dir dataset --auto-install-ffmpeg")
    print("  python train_audio_classifier.py --data-dir dataset --model-out model.joblib")
    print("  python WebexVDIAudioPresenceDetector.py --classify --classifier-model model.joblib")


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


def _get_wasapi_loopback_devices():
    devices = sd.query_devices()
    hostapis = sd.query_hostapis()
    loopbacks = []
    for idx, dev in enumerate(devices):
        hostapi = hostapis[dev["hostapi"]]["name"]
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


def _get_capture_channels(device_info, loopback_active: bool) -> int:
    if loopback_active and device_info.get("max_output_channels", 0) > 0:
        return min(2, int(device_info["max_output_channels"]))
    return int(device_info.get("max_input_channels", 0))


def _process_frame(samples, sample_rate, meter_state, meter_ui_state, thresholds):
    level_db = _rms_db(samples)
    flatness = _spectral_flatness(samples)
    band_ratio = _band_energy_ratio(samples, sample_rate)

    if meter_state is not None:
        now = time.time()
        if now - meter_state["last_print"] >= meter_state["interval_sec"]:
            print(f"Level: {level_db:.1f} dB | flatness: {flatness:.2f} | band_ratio: {band_ratio:.2f}")
            meter_state["last_print"] = now

    if meter_ui_state is not None:
        now = time.time()
        if now - meter_ui_state["last_print"] >= meter_ui_state["interval_sec"]:
            min_db = meter_ui_state["min_db"]
            max_db = meter_ui_state["max_db"]
            width = meter_ui_state["width"]
            clamped = max(min_db, min(max_db, level_db))
            norm = (clamped - min_db) / (max_db - min_db)
            filled = int(round(norm * width))
            bar = "|" * filled + "-" * (width - filled)
            msg = (
                f"[{bar}] {level_db:6.1f} dB | flatness {flatness:.2f} | band {band_ratio:.2f}"
            )
            print(f"\r\x1b[32m{msg}\x1b[0m", end="", flush=True)
            meter_ui_state["last_print"] = now

    min_db, flatness_max, band_min = thresholds
    audio_present = (level_db > min_db) and (flatness < flatness_max or band_ratio > band_min)
    return audio_present


def _load_classifier(model_path: str):
    try:
        import joblib
    except ImportError as exc:
        raise RuntimeError("Missing dependency: joblib. Install with: pip install joblib") from exc
    return joblib.load(model_path)


def _extract_features(samples: np.ndarray, sample_rate: int) -> np.ndarray:
    try:
        import librosa
    except ImportError as exc:
        raise RuntimeError("Missing dependency: librosa. Install with: pip install librosa") from exc

    if len(samples) == 0:
        return np.zeros(1, dtype=np.float32)

    y = samples.astype(np.float32)
    mfcc = librosa.feature.mfcc(y=y, sr=sample_rate, n_mfcc=13)
    centroid = librosa.feature.spectral_centroid(y=y, sr=sample_rate)
    bandwidth = librosa.feature.spectral_bandwidth(y=y, sr=sample_rate)
    rolloff = librosa.feature.spectral_rolloff(y=y, sr=sample_rate)
    zcr = librosa.feature.zero_crossing_rate(y=y)
    rms = librosa.feature.rms(y=y)
    flatness = librosa.feature.spectral_flatness(y=y)

    feats = [
        mfcc.mean(axis=1), mfcc.std(axis=1),
        centroid.mean(axis=1), centroid.std(axis=1),
        bandwidth.mean(axis=1), bandwidth.std(axis=1),
        rolloff.mean(axis=1), rolloff.std(axis=1),
        zcr.mean(axis=1), zcr.std(axis=1),
        rms.mean(axis=1), rms.std(axis=1),
        flatness.mean(axis=1), flatness.std(axis=1),
    ]
    return np.concatenate(feats, axis=0)


def _finalize_classification(classify_state, sample_rate: int):
    if classify_state is None or not classify_state.get("enabled"):
        return None

    buffer = classify_state.get("buffer")
    if not buffer:
        classify_state["label"] = "unknown"
        return classify_state

    samples = np.concatenate(buffer, axis=0)
    if len(samples) < classify_state["target_samples"]:
        classify_state["label"] = "unknown"
        return classify_state

    features = _extract_features(samples, sample_rate)
    model = classify_state["model"]
    labels = classify_state["labels"]

    if hasattr(model, "predict_proba"):
        probs = model.predict_proba([features])[0]
        idx = int(np.argmax(probs))
        classify_state["label"] = labels[idx] if labels else str(model.classes_[idx])
        classify_state["score"] = float(probs[idx])
    else:
        pred = model.predict([features])[0]
        classify_state["label"] = str(pred)
        classify_state["score"] = None
    return classify_state


def _run_soundcard(duration_seconds, meter_state, meter_ui_state, thresholds, speaker_filter: str | None, classify_state=None):
    mic = _pick_loopback_mic(speaker_filter)
    sample_rate = int(getattr(mic, "default_samplerate", SAMPLE_RATE))
    print(f"Soundcard loopback: {mic.name} (sample_rate={sample_rate})")
    end_time = None if duration_seconds is None else time.time() + duration_seconds

    total_frames = 0
    audio_frames = 0
    with mic.recorder(samplerate=sample_rate, channels=1) as rec:
        while True:
            data = rec.record(numframes=FRAME_SIZE)
            samples = data[:, 0].astype(np.float32)
            audio_present = _process_frame(samples, sample_rate, meter_state, meter_ui_state, thresholds)
            if audio_present and classify_state is not None:
                if len(classify_state["buffer"]) < classify_state["buffer_frames_max"]:
                    classify_state["buffer"].append(samples)
            if audio_present:
                audio_frames += 1
            total_frames += 1
            if end_time is not None and time.time() >= end_time:
                break

    return audio_frames, total_frames, sample_rate


def _run_sounddevice(duration_seconds, meter_state, meter_ui_state, thresholds, device_index: int | None, classify_state=None):
    input_device = device_index
    if input_device is None:
        loopbacks = _get_wasapi_loopback_devices()
        if loopbacks:
            input_device = loopbacks[0][0]
    if input_device is None:
        input_device = sd.default.device[1]
    if input_device is None:
        input_device = sd.default.device[0]

    if input_device is None:
        device_info = sd.query_devices(kind="input")
    else:
        device_info = sd.query_devices(input_device)

    loopback_active = _is_wasapi_device(input_device)
    loopback_settings = _get_wasapi_loopback_settings() if loopback_active else None
    if loopback_active and loopback_settings is None:
        raise RuntimeError(
            "WASAPI loopback is not supported by this sounddevice version. "
            "Upgrade with: pip install -U sounddevice"
        )

    capture_channels = _get_capture_channels(device_info, loopback_active)
    if capture_channels <= 0:
        raise RuntimeError(
            "Selected device has no usable capture channels. "
            "Pick a WASAPI output device for loopback or an input device with channels."
        )

    print(
        "Input device: "
        f"{device_info['name']} (in_ch={device_info['max_input_channels']}, "
        f"out_ch={device_info['max_output_channels']}, loopback={loopback_active})"
    )
    if loopback_active:
        print("WASAPI loopback mode enabled")

    end_time = None if duration_seconds is None else time.time() + duration_seconds

    total_frames = 0
    audio_frames = 0
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
            audio_present = _process_frame(samples, SAMPLE_RATE, meter_state, meter_ui_state, thresholds)
            if audio_present and classify_state is not None:
                if len(classify_state["buffer"]) < classify_state["buffer_frames_max"]:
                    classify_state["buffer"].append(samples)
            if audio_present:
                audio_frames += 1
            total_frames += 1
            if end_time is not None and time.time() >= end_time:
                break

    return audio_frames, total_frames, SAMPLE_RATE


def main():
    parser = argparse.ArgumentParser(description="Detect presence of real audio vs blank/noise.")
    parser.add_argument(
        "--backend",
        choices=["sounddevice", "soundcard"],
        default=DEFAULT_BACKEND,
        help="Audio backend to use.",
    )
    parser.add_argument("--list-devices", action="store_true", help="List input devices and exit.")
    parser.add_argument("--list-loopback", action="store_true", help="List WASAPI loopback devices and exit.")
    parser.add_argument("--list-speakers", action="store_true", help="List loopback mics (soundcard backend).")
    parser.add_argument("--deps", action="store_true", help="Show required/optional modules and exit.")
    parser.add_argument("--examples", action="store_true", help="Show command examples and exit.")
    parser.add_argument("--helper", action="store_true", help="Show helper commands and exit.")
    parser.add_argument("--device", type=int, default=None, help="Input device index to use (sounddevice).")
    parser.add_argument("--speaker", type=str, default=None, help="Loopback mic name filter (soundcard).")
    parser.add_argument("--duration-seconds", type=float, default=30.0, help="Run duration in seconds.")
    parser.add_argument("--no-duration", action="store_true", help="Run indefinitely.")
    parser.add_argument("--meter", action="store_true", help="Print level/feature meter.")
    parser.add_argument("--meter-ui", action="store_true", help="Show an updating one-line meter bar UI.")
    parser.add_argument("--meter-interval", type=float, default=1.0, help="Seconds between meter prints.")
    parser.add_argument("--min-db", type=float, default=MIN_AUDIO_DB, help="Minimum RMS dB for audio.")
    parser.add_argument("--flatness-max", type=float, default=FLATNESS_MAX, help="Max spectral flatness for audio.")
    parser.add_argument("--band-ratio-min", type=float, default=BAND_RATIO_MIN, help="Min band energy ratio for audio.")
    parser.add_argument(
        "--min-audio-ratio",
        type=float,
        default=0.05,
        help="Fraction of frames that must contain audio.",
    )
    parser.add_argument("--classify", action="store_true", help="Classify audio as voice/music using ML.")
    parser.add_argument("--classifier-model", type=str, default=None, help="Path to joblib sklearn model.")
    parser.add_argument("--classify-seconds", type=float, default=2.0, help="Seconds of audio to classify.")
    parser.add_argument("--class-labels", type=str, default=None, help="Comma-separated labels for model outputs.")
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
    if args.helper:
        _print_helper()
        return

    duration_seconds = None if args.no_duration else args.duration_seconds
    meter_state = None
    meter_ui_state = None
    if args.meter:
        meter_state = {"last_print": 0.0, "interval_sec": args.meter_interval}
    if args.meter_ui:
        meter_ui_state = {
            "last_print": 0.0,
            "interval_sec": args.meter_interval,
            "min_db": -80.0,
            "max_db": 0.0,
            "width": 30,
        }

    thresholds = (args.min_db, args.flatness_max, args.band_ratio_min)

    classify_state = None
    if args.classify:
        if not args.classifier_model:
            raise RuntimeError("--classifier-model is required when --classify is set")
        model = _load_classifier(args.classifier_model)
        labels = None
        if args.class_labels:
            labels = [item.strip() for item in args.class_labels.split(",") if item.strip()]
        classify_state = {
            "enabled": True,
            "model": model,
            "labels": labels,
            "buffer": [],
            "target_samples": int(args.classify_seconds * SAMPLE_RATE),
            "buffer_frames_max": int((args.classify_seconds * 1000.0) / FRAME_MS) + 2,
            "label": None,
            "score": None,
        }

    if args.backend == "soundcard":
        audio_frames, total_frames, used_sample_rate = _run_soundcard(
            duration_seconds,
            meter_state,
            meter_ui_state,
            thresholds,
            args.speaker,
            classify_state,
        )
    else:
        _require_sounddevice()
        try:
            audio_frames, total_frames, used_sample_rate = _run_sounddevice(
                duration_seconds,
                meter_state,
                meter_ui_state,
                thresholds,
                args.device,
                classify_state,
            )
        except (RuntimeError, sd.PortAudioError) as exc:
            print(f"sounddevice failed: {exc}")
            if sc is None:
                raise
            print("Falling back to soundcard backend.")
            audio_frames, total_frames, used_sample_rate = _run_soundcard(
                duration_seconds,
                meter_state,
                meter_ui_state,
                thresholds,
                args.speaker,
                classify_state,
            )

    if meter_ui_state is not None:
        print()

    ratio = (audio_frames / total_frames) if total_frames > 0 else 0.0
    audio_present = ratio >= args.min_audio_ratio
    print(f"Audio present: {str(audio_present).lower()}")
    print(f"Audio frames: {audio_frames}/{total_frames} (ratio={ratio:.2f})")

    if classify_state is not None:
        _finalize_classification(classify_state, used_sample_rate)
        label = classify_state.get("label")
        score = classify_state.get("score")
        if score is None:
            print(f"Audio class: {label}")
        else:
            print(f"Audio class: {label} (score={score:.2f})")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Stopped.")
