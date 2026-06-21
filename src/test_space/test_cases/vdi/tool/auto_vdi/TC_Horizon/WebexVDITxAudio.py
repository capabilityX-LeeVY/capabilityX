import argparse
import os
import time
import tempfile

import pyttsx3
import numpy as np
import sounddevice as sd
import soundfile as sf


def synthesize_to_wav(text: str, rate: int, volume: float) -> str:
    engine = pyttsx3.init()
    engine.setProperty("rate", rate)
    engine.setProperty("volume", volume)

    fd, path = tempfile.mkstemp(suffix=".wav")
    os.close(fd)

    engine.save_to_file(text, path)
    engine.runAndWait()

    # Wait for the file to be fully written by the TTS engine.
    deadline = time.time() + 5.0
    while time.time() < deadline:
        if os.path.exists(path) and os.path.getsize(path) > 0:
            return path
        time.sleep(0.05)

    raise RuntimeError("TTS output file was not created in time.")


def _coerce_channels(data, channels: int):
    if data.ndim == 1:
        if channels == 1:
            return data
        return np.tile(data[:, None], (1, channels))

    current = data.shape[1]
    if current == channels:
        return data
    if current > channels:
        return data[:, :channels]
    # Pad extra channels by repeating the last channel.
    pad = np.tile(data[:, -1:], (1, channels - current))
    return np.concatenate([data, pad], axis=1)


def _find_vb_audio_output_device():
    for idx, info in enumerate(sd.query_devices()):
        if info.get("max_output_channels", 0) <= 0:
            continue
        name = info["name"].lower()
        if "vb-audio" in name or "virtual cable" in name or "cable input" in name:
            return idx, info
    return None


def _select_output_device(device_name: str | None, device_index: int | None):
    if device_index is not None:
        info = sd.query_devices(device_index, "output")
        if info.get("max_output_channels", 0) <= 0:
            raise RuntimeError(f"Device index {device_index} is not an output device")
        return device_index, info

    if not device_name:
        vb_match = _find_vb_audio_output_device()
        if vb_match:
            return vb_match
        return None, sd.query_devices(sd.default.device[1], "output")

    matches = []
    for idx, info in enumerate(sd.query_devices()):
        if device_name.lower() in info["name"].lower() and info["max_output_channels"] > 0:
            matches.append((idx, info))

    if not matches:
        raise RuntimeError(f"Output device not found: {device_name}")

    if len(matches) == 1:
        return matches[0]

    for idx, info in matches:
        if info["name"].lower() == device_name.lower():
            return idx, info

    options = ", ".join(f"{idx}:{info['name']}" for idx, info in matches)
    raise RuntimeError(
        f"Multiple output devices match '{device_name}'. Use --device-index. Options: {options}"
    )


def _pick_output_channels(device_info, override: int | None) -> int:
    if override:
        return override
    if not device_info:
        return 2
    default_channels = int(device_info.get("default_output_channels", 0) or 0)
    if default_channels > 0:
        return default_channels
    max_channels = int(device_info.get("max_output_channels", 0) or 0)
    if max_channels >= 2:
        return 2
    if max_channels == 1:
        return 1
    return 2


def play_wav_to_device(
    path: str,
    device_name: str | None,
    device_index: int | None,
    channels_override: int | None,
) -> None:
    data, samplerate = sf.read(path, dtype="float32")

    device, device_info = _select_output_device(device_name, device_index)
    channels = _pick_output_channels(device_info, channels_override)
    data = _coerce_channels(data, channels)

    sd.play(data, samplerate=samplerate, device=device)
    sd.wait()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert text to speech and play it to a virtual mic device.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Purpose\n"
            "- Convert text to speech and play it to a virtual mic device "
            "(VB-Audio Virtual Cable).\n\n"
            "Install\n"
            "- pip install pyttsx3 sounddevice soundfile\n"
            "- Install VB-Audio Virtual Cable: https://vb-audio.com/Cable/\n\n"
            "Ubuntu Setup\n"
            "- sudo apt-get install espeak-ng portaudio19-dev libsndfile1\n"
            "- pip install pyttsx3 sounddevice soundfile\n"
            "- Create a virtual mic (PulseAudio/PipeWire):\n"
            "  - pactl load-module module-null-sink sink_name=virtual_mic "
            "sink_properties=device.description=VirtualMic\n"
            "  - pactl load-module module-loopback source=virtual_mic.monitor\n"
            "  - Set your app microphone to \"VirtualMic Monitor\".\n\n"
            "Ubuntu Tips\n"
            "- Use --list-devices to find the output device name/index.\n"
            "- Unload modules when done: pactl unload-module module-loopback; "
            "pactl unload-module module-null-sink\n\n"
            "Run\n"
            "- python WebexVDITxAudio.py \"Hello from pyttsx3\" "
            "--device \"VB-Audio Virtual Cable\"\n\n"
            "Command Examples\n"
            "- python WebexVDITxAudio.py\n"
            "- python WebexVDITxAudio.py \"Short test\"\n"
            "- python WebexVDITxAudio.py \"Hello\" --device-index 7 --channels 1\n"
            "- python WebexVDITxAudio.py --list-devices\n\n"
            "Notes\n"
            "- If no device is specified, the script picks the first VB-Audio virtual cable output.\n"
            "- Set your target app's microphone input to \"CABLE Output\".\n"
            "- The script plays to the cable playback device \"CABLE Input\".\n"
        ),
    )
    parser.add_argument("text", nargs="*", help="Text to speak")
    parser.add_argument(
        "--device",
        default=None,
        help="Output device name (partial match).",
    )
    parser.add_argument(
        "--device-index",
        type=int,
        default=None,
        help="Output device index from --list-devices.",
    )
    parser.add_argument(
        "--channels",
        type=int,
        choices=[1, 2],
        default=1,
        help="Force output channels (1 or 2).",
    )
    parser.add_argument(
        "--list-devices",
        action="store_true",
        help="List available audio devices and exit.",
    )
    parser.add_argument("--rate", type=int, default=180, help="Speech rate")
    parser.add_argument("--volume", type=float, default=1.0, help="Volume 0.0-1.0")

    args = parser.parse_args()
    if args.list_devices:
        for idx, info in enumerate(sd.query_devices()):
            io = []
            if info.get("max_input_channels", 0) > 0:
                io.append("in")
            if info.get("max_output_channels", 0) > 0:
                io.append("out")
            io_label = "/".join(io) if io else "n/a"
            print(f"{idx}: {info['name']} ({io_label})")
        return
    if args.device_index is not None and args.device is not None:
        raise SystemExit("Use only one of --device or --device-index.")
    # When no device is specified, prefer the first VB-Audio virtual cable device.
    if not args.text:
        text = "Hello! This is VDI Automation Tool!!! We are testing audio-sending!"
    else:
        text = " ".join(args.text)

    wav_path = synthesize_to_wav(text, args.rate, args.volume)
    try:
        play_wav_to_device(wav_path, args.device, args.device_index, args.channels)
    finally:
        if os.path.exists(wav_path):
            os.remove(wav_path)


if __name__ == "__main__":
    main()
