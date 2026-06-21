
from tools.webexApp import appHandler
from common.utils.logger import LOGGER_INFO, LOGGER_ERROR
from config.paths import TEST_SUITE_PATH, TEST_CASES_PATH
from pathlib import Path
import requests
import pyautogui
from PIL import ImageGrab
import io
import win32clipboard
import time
import subprocess
import platform
import shutil
from concurrent.futures import ThreadPoolExecutor


def vdi_get_screenshot(tc_ip: str = None):
    url = 'http://' + tc_ip + '/screenshot'
    try:
        res = requests.get(url, timeout=30)
        res.raise_for_status()
    except requests.RequestException as exc:
        LOGGER_ERROR(f"VDI screenshot request failed: {exc}", "RED")
        return

    os_info = None
    try:
        os_info = res.json()
    except ValueError:
        LOGGER_INFO("VDI screenshot response is not JSON", "YELLOW")

    if isinstance(os_info, dict):
        os_name = os_info.get("os")
        if os_name:
            LOGGER_INFO(f"VDI screenshot peer OS: {os_name}", "CYAN")

    horizon_suffix = ""
    try:
        if platform.system().lower() == "windows":
            tasklist = subprocess.run(
                ["tasklist", "/FI", "IMAGENAME eq VMBlastS.exe"],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
            )
            if "vmblasts.exe" in tasklist.stdout.lower():
                horizon_suffix = "?horizon=1&send_ss=1"
    except Exception as exc:
        LOGGER_INFO(f"Failed to detect Horizon process: {exc}", "YELLOW")
    if not horizon_suffix:
        horizon_suffix = "?send_ss=1"

    download_url = "http://" + tc_ip + "/screenshot" + horizon_suffix
    output_dir = Path(r"C:\dev\auto_vdi")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "vdi_screenshot.png"
    if output_path.exists():
        try:
            output_path.unlink()
            LOGGER_INFO(f"Removed old screenshot: {output_path}", "YELLOW")
        except OSError as exc:
            LOGGER_ERROR(f"Failed to remove old screenshot: {exc}", "RED")
            return
    try:
        download_res = requests.get(download_url, stream=True, timeout=60)
        download_res.raise_for_status()
        with open(output_path, "wb") as f:
            for chunk in download_res.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
    except requests.RequestException as exc:
        LOGGER_ERROR(f"VDI screenshot download failed: {exc}", "RED")
        return
    LOGGER_INFO(f"VDI screenshot saved to: {output_path}", "GREEN")


def vdi_open_screenshot():
    screenshot_path = Path(r"C:\dev\auto_vdi") / "vdi_screenshot.png"
    if not screenshot_path.exists():
        LOGGER_ERROR(f"Screenshot not found: {screenshot_path}", "RED")
        return
    try:
        subprocess.run([
            "taskkill",
            "/IM",
            "mspaint.exe",
            "/F"
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for _ in range(10):
            check = subprocess.run(
                ["tasklist", "/FI", "IMAGENAME eq mspaint.exe"],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True
            )
            if "mspaint.exe" not in check.stdout.lower():
                break
            time.sleep(0.3)
        subprocess.Popen(["mspaint", str(screenshot_path)])
        time.sleep(1)
        try:
            windows = pyautogui.getWindowsWithTitle("Paint")
            if windows:
                windows[0].activate()
            else:
                LOGGER_INFO("Paint window not found to activate", "YELLOW")
        except Exception as exc:
            LOGGER_INFO(f"Unable to activate Paint window: {exc}", "YELLOW")
        LOGGER_INFO(f"Opened screenshot: {screenshot_path}", "GREEN")
    except OSError as exc:
        LOGGER_ERROR(f"Failed to open screenshot: {exc}", "RED")

def vdi_get_ringback_detection(tc_ip: str, ringback_on: float = 1.88, ringback_off: float = 2.88, duration_seconds: float = 25.0):
    url = "http://" + tc_ip + "/detectTone"
    params = {
        "ringback_on": str(ringback_on),
        "ringback_off": str(ringback_off),
        "duration_seconds": str(duration_seconds),
    }
    try:
        res = requests.get(url, params=params, timeout=90)
        res.raise_for_status()
    except requests.RequestException as exc:
        LOGGER_ERROR(f"VDI ringback detection request failed: {exc}", "RED")
        return None

    try:
        data = res.json()
    except ValueError:
        LOGGER_ERROR("VDI ringback detection response is not JSON", "RED")
        return None

    detections = data.get("ringback_detections")
    if detections is None:
        LOGGER_ERROR(f"VDI ringback detection missing count: {data}", "RED")
        return None

    LOGGER_INFO(f"VDI ringback detections: {detections}", "GREEN")
    return detections

def vdi_get_audio_detection(tc_ip: str):
    url = "http://" + tc_ip + "/detectAudio"
    try:
        res = requests.get(url, timeout=90)
        res.raise_for_status()
    except requests.RequestException as exc:
        LOGGER_ERROR(f"VDI audio detection request failed: {exc}", "RED")
        return None

    try:
        data = res.json()
    except ValueError:
        LOGGER_ERROR("VDI audio detection response is not JSON", "RED")
        return None

    audio_present = data.get("audio_present")
    if audio_present is None:
        LOGGER_ERROR(f"VDI audio detection missing audio_present: {data}", "RED")
        return None

    LOGGER_INFO(f"VDI audio present: {audio_present}", "GREEN")
    return audio_present

def vdi_send_audio(tc_ip: str, text: str | None = None, device_index: int | None = None, channels: int | None = None):
    url = "http://" + tc_ip + "/sendAudio"
    params = {}
    if text:
        params["text"] = text
    if device_index is not None:
        params["device_index"] = str(device_index)
    if channels is not None:
        params["channels"] = str(channels)

    try:
        res = requests.get(url, params=params, timeout=90)
        res.raise_for_status()
    except requests.RequestException as exc:
        LOGGER_ERROR(f"VDI send audio request failed: {exc}", "RED")
        return None

    try:
        data = res.json()
    except ValueError:
        LOGGER_ERROR("VDI send audio response is not JSON", "RED")
        return None

    return_code = data.get("return_code")
    if return_code is None:
        LOGGER_ERROR(f"VDI send audio missing return_code: {data}", "RED")
        return None

    if return_code == 0:
        LOGGER_INFO("VDI send audio succeeded", "GREEN")
    else:
        LOGGER_ERROR(f"VDI send audio failed: {data}", "RED")
    return data

def vdi_reaction_screenshot(tc_ip: str, reaction_sc: str, delay: float = 1.0):
    # shortcut format: "ctrl+shift+s"
    keys = [k.strip().lower() for k in reaction_sc.split("+") if k.strip()]
    time.sleep(delay)  # give user time to focus target window
    pyautogui.hotkey(*keys)

    time.sleep(0.5)
    vdi_get_screenshot(tc_ip)

def copy_image_to_clipboard(img):
    output = io.BytesIO()
    img.convert("RGB").save(output, "BMP")
    data = output.getvalue()[14:]  # strip BMP header
    output.close()

    win32clipboard.OpenClipboard()
    try:
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
    finally:
        win32clipboard.CloseClipboard()


def vdi_peer_start_screen_share(peer_ip: str = None):
    url = "http://" + peer_ip + "/sharescreen"
    try:
        res = requests.get(url, timeout=90)
        res.raise_for_status()
    except requests.RequestException as exc:
        LOGGER_ERROR(f"VDI peer start screen share request failed: {exc}", "RED")
        return None

    try:
        data = res.json()
    except ValueError:
        LOGGER_INFO("VDI peer start screen share response is not JSON", "YELLOW")
        return {"status_code": res.status_code, "text": res.text}

    LOGGER_INFO(f"VDI peer start screen share succeeded: {peer_ip}", "GREEN")
    return data


def vdi_peer_stop_share(peer_ip: str = None):
    url = "http://" + peer_ip + "/stopshare"
    try:
        res = requests.get(url, timeout=90)
        res.raise_for_status()
    except requests.RequestException as exc:
        LOGGER_ERROR(f"VDI peer stop share request failed: {exc}", "RED")
        return None

    try:
        data = res.json()
    except ValueError:
        LOGGER_INFO("VDI peer stop share response is not JSON", "YELLOW")
        return {"status_code": res.status_code, "text": res.text}

    LOGGER_INFO(f"VDI peer stop share succeeded: {peer_ip}", "GREEN")
    return data


def vdi_get_peer_audio_detection(peer_ip: str = None):
    url = "http://" + peer_ip + "/detectAudio"
    try:
        res = requests.get(url, timeout=90)
        res.raise_for_status()
    except requests.RequestException as exc:
        LOGGER_ERROR(f"VDI peer audio detection request failed: {exc}", "RED")
        return None

    try:
        data = res.json()
    except ValueError:
        LOGGER_ERROR("VDI peer audio detection response is not JSON", "RED")
        return None

    audio_present = data.get("audio_present")
    if audio_present is None:
        LOGGER_ERROR(f"VDI peer audio detection missing audio_present: {data}", "RED")
        return None

    LOGGER_INFO(f"VDI peer audio present: {audio_present}", "GREEN")
    return audio_present


def vdi_bothway_audio_detection(tc_ip: str, peer_ip: str, text: str | None = None, device_index: int | None = None, channels: int | None = None, bothway: str = "yes", direction: str | None = None):
    def _audio_detected(value):
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.strip().lower() == "true"
        return bool(value)

    bothway_lower = bothway.lower() if isinstance(bothway, str) else str(bothway).lower()
    
    if bothway_lower == "yes":
        # Run detect/send in parallel for each direction.
        with ThreadPoolExecutor(max_workers=2) as executor:
            peer_detect_future = executor.submit(vdi_get_peer_audio_detection, peer_ip)
            tc_send_future = executor.submit(vdi_send_audio, tc_ip, text=text, device_index=device_index, channels=channels)
            peer_audio_present = peer_detect_future.result()
            tc_send_result = tc_send_future.result()

        with ThreadPoolExecutor(max_workers=2) as executor:
            tc_detect_future = executor.submit(vdi_get_audio_detection, tc_ip)
            peer_send_future = executor.submit(vdi_send_audio, peer_ip, text=text, device_index=device_index, channels=channels)
            tc_audio_present = tc_detect_future.result()
            peer_send_result = peer_send_future.result()

        bothway_ok = (
            _audio_detected(peer_audio_present)
            and _audio_detected(tc_audio_present)
            and tc_send_result is not None
            and peer_send_result is not None
        )

        if bothway_ok:
            LOGGER_INFO("VDI bothway audio detection succeeded", "GREEN")
        else:
            LOGGER_ERROR(
                f"VDI bothway audio detection failed: "
                f"peer_audio_present={peer_audio_present}, tc_audio_present={tc_audio_present}, "
                f"tc_send_ok={tc_send_result is not None}, peer_send_ok={peer_send_result is not None}",
                "RED",
            )

        return bothway_ok
    else:
        # One direction only
        direction_lower = direction.lower() if isinstance(direction, str) else str(direction).lower() if direction else ""
        
        if direction_lower == "tc2peer":
            # tc sends audio, peer detects audio
            with ThreadPoolExecutor(max_workers=2) as executor:
                peer_detect_future = executor.submit(vdi_get_peer_audio_detection, peer_ip)
                tc_send_future = executor.submit(vdi_send_audio, tc_ip, text=text, device_index=device_index, channels=channels)
                peer_audio_present = peer_detect_future.result()
                tc_send_result = tc_send_future.result()
            
            result = _audio_detected(peer_audio_present) and tc_send_result is not None
            if result:
                LOGGER_INFO("VDI tc2peer audio detection succeeded", "GREEN")
            else:
                LOGGER_ERROR(
                    f"VDI tc2peer audio detection failed: "
                    f"peer_audio_present={peer_audio_present}, tc_send_ok={tc_send_result is not None}",
                    "RED",
                )
            return result
        elif direction_lower == "peer2tc":
            # peer sends audio, tc detects audio
            with ThreadPoolExecutor(max_workers=2) as executor:
                tc_detect_future = executor.submit(vdi_get_audio_detection, tc_ip)
                peer_send_future = executor.submit(vdi_send_audio, peer_ip, text=text, device_index=device_index, channels=channels)
                tc_audio_present = tc_detect_future.result()
                peer_send_result = peer_send_future.result()
            
            result = _audio_detected(tc_audio_present) and peer_send_result is not None
            if result:
                LOGGER_INFO("VDI peer2tc audio detection succeeded", "GREEN")
            else:
                LOGGER_ERROR(
                    f"VDI peer2tc audio detection failed: "
                    f"tc_audio_present={tc_audio_present}, peer_send_ok={peer_send_result is not None}",
                    "RED",
                )
            return result
        else:
            LOGGER_ERROR(f"Invalid direction: {direction}. Expected 'tc2peer' or 'peer2tc'", "RED")
            return False


def vdi_play_test_audio():
    audio_path = Path(r"c:\test-share-audio.mp3")
    if not audio_path.exists():
        LOGGER_ERROR(f"Test audio file not found: {audio_path}", "RED")
        return None

    vlc_path = shutil.which("vlc")
    if not vlc_path:
        fallback_vlc = Path(r"C:\Program Files\VideoLAN\VLC\vlc.exe")
        if fallback_vlc.exists():
            vlc_path = str(fallback_vlc)
    if not vlc_path:
        LOGGER_ERROR("VLC executable not found in PATH.", "RED")
        return None

    try:
        proc = subprocess.Popen(
            [vlc_path, "--play-and-exit", str(audio_path)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except OSError as exc:
        LOGGER_ERROR(f"Failed to start VLC playback: {exc}", "RED")
        return None

    time.sleep(1.0)
    if proc.poll() is not None:
        LOGGER_ERROR("VLC exited before playback could start.", "RED")
        return None

    LOGGER_INFO(f"VLC started test audio playback: {audio_path}", "GREEN")
    return proc.pid