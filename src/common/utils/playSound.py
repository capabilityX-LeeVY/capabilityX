
import os
import subprocess

def play_sound_with_subprocess(file_name):
    subprocess.run(["afplay", f"/System/Library/Sounds/{file_name}"])

def play_sound(file_name):
    os.system(f"afplay /System/Library/Sounds/{file_name}")

if __name__ == "__main__":

    # Basso.aiff	Frog.aiff	Hero.aiff	Pop.aiff	Submarine.aiff
    # Blow.aiff	Funk.aiff	Morse.aiff	Purr.aiff	Tink.aiff
    # Bottle.aiff	Glass.aiff	Ping.aiff	Sosumi.aiff

    play_sound_with_subprocess("Glass.aiff")