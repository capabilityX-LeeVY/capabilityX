WebexVDITxAudio usage

Purpose
- Convert text to speech and play it to a virtual mic device (VB-Audio Virtual Cable).

Install
- pip install pyttsx3 sounddevice soundfile
- Install VB-Audio Virtual Cable: https://vb-audio.com/Cable/

Ubuntu Setup
- sudo apt-get install espeak-ng portaudio19-dev libsndfile1
- pip install pyttsx3 sounddevice soundfile
- Create a virtual mic (PulseAudio/PipeWire):
	- pactl load-module module-null-sink sink_name=virtual_mic sink_properties=device.description=VirtualMic
	- pactl load-module module-loopback source=virtual_mic.monitor
	- Set your app microphone to "VirtualMic Monitor".

Ubuntu Tips
- Use --list-devices to find the output device name/index.
- Unload modules when done:
	- pactl unload-module module-loopback
	- pactl unload-module module-null-sink

Run
- python WebexVDITxAudio.py "Hello from pyttsx3" --device "VB-Audio Virtual Cable"

Command Examples
- python WebexVDITxAudio.py
- python WebexVDITxAudio.py "Short test"
- python WebexVDITxAudio.py "Hello" --device-index 7 --channels 1
- python WebexVDITxAudio.py --list-devices

Notes
- Set your target app's microphone input to "CABLE Output".
- The script plays to the cable playback device ("CABLE Input").
