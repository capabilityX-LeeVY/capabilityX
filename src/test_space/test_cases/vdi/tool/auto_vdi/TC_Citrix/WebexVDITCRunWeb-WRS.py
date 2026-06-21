from flask import Flask, jsonify, request, send_file, Response
import subprocess
import os
import time
import sys
import shutil
import re

IS_WINDOWS = sys.platform.startswith("win")

if IS_WINDOWS:
    from PIL import Image
    import io
    import win32clipboard
    import win32gui
    import win32ui
    import ctypes

app = Flask(__name__)
if IS_WINDOWS:
    user32 = ctypes.windll.user32

HVD_INFO_PATH = "C:\\dev\\auto_vdi\\hvd_info.txt" if IS_WINDOWS else "/devOps/auto_vdi/hvd_info.txt"
HVD_INFO_HORIZON_PATH = "C:\\dev\\auto_vdi\\hvd_info-horizon.txt" if IS_WINDOWS else "/devOps/auto_vdi/hvd_info-horizon.txt"
N4_GA_VERSION_PATH = "C:\\dev\\auto_vdi\\n-4_GA_version.txt" if IS_WINDOWS else "/devOps/auto_vdi/n-4_GA_version.txt"

MAX_SCREENSHOT_BYTES = 1_300_000  # 1.3 MB


def _save_screenshot_under_limit(img, output_path, max_bytes=MAX_SCREENSHOT_BYTES):
    """Save a PIL Image to output_path, scaling down iteratively to stay under max_bytes."""
    import io as _io
    from PIL import Image as _Image
    scale = 1.0
    while True:
        candidate = img if scale >= 1.0 else img.resize(
            (max(1, int(img.width * scale)), max(1, int(img.height * scale))),
            _Image.LANCZOS,
        )
        buf = _io.BytesIO()
        candidate.save(buf, "PNG", compress_level=9)
        if buf.tell() <= max_bytes or scale <= 0.1:
            with open(output_path, "wb") as fh:
                fh.write(buf.getvalue())
            return
        scale = max(0.1, scale - 0.1)


def capture_window_to_clipboard(window_title):
    if not IS_WINDOWS:
        raise RuntimeError("Screenshot capture is only supported on Windows")

    hwnd = win32gui.FindWindow(None, window_title)
    if not hwnd:
        raise RuntimeError(f"Window not found: {window_title}")

    left, top, right, bottom = win32gui.GetWindowRect(hwnd)
    width, height = right - left, bottom - top

    hwnd_dc = win32gui.GetWindowDC(hwnd)
    mfc_dc = win32ui.CreateDCFromHandle(hwnd_dc)
    save_dc = mfc_dc.CreateCompatibleDC()

    bitmap = win32ui.CreateBitmap()
    bitmap.CreateCompatibleBitmap(mfc_dc, width, height)
    save_dc.SelectObject(bitmap)

    # 2 = PW_RENDERFULLCONTENT (best effort)
    result = user32.PrintWindow(hwnd, save_dc.GetSafeHdc(), 2)
    if result != 1:
        raise RuntimeError("PrintWindow failed")

    bmpinfo = bitmap.GetInfo()
    bmpstr = bitmap.GetBitmapBits(True)
    img = Image.frombuffer(
        "RGB",
        (bmpinfo["bmWidth"], bmpinfo["bmHeight"]),
        bmpstr, "raw", "BGRX", 0, 1
    )

    # Put in clipboard as DIB
    output = io.BytesIO()
    img.convert("RGB").save(output, "BMP")
    data = output.getvalue()[14:]
    output.close()

    win32clipboard.OpenClipboard()
    try:
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
    finally:
        win32clipboard.CloseClipboard()

    # cleanup
    win32gui.DeleteObject(bitmap.GetHandle())
    save_dc.DeleteDC()
    mfc_dc.DeleteDC()
    win32gui.ReleaseDC(hwnd, hwnd_dc)


def capture_window_to_file_windows(window_title, output_path=None):
    if not IS_WINDOWS:
        raise RuntimeError("Screenshot capture is only supported on Windows")

    hwnd = win32gui.FindWindow(None, window_title)
    if not hwnd:
        raise RuntimeError(f"Window not found: {window_title}")

    temp_dir = os.getenv("TEMP") or os.getenv("TMP") or os.getcwd()
    if output_path is None:
        output_path = os.path.join(temp_dir, "vdi_screenshot.png")

    left, top, right, bottom = win32gui.GetWindowRect(hwnd)
    width, height = right - left, bottom - top

    hwnd_dc = win32gui.GetWindowDC(hwnd)
    mfc_dc = win32ui.CreateDCFromHandle(hwnd_dc)
    save_dc = mfc_dc.CreateCompatibleDC()

    bitmap = win32ui.CreateBitmap()
    bitmap.CreateCompatibleBitmap(mfc_dc, width, height)
    save_dc.SelectObject(bitmap)

    # 2 = PW_RENDERFULLCONTENT (best effort)
    result = user32.PrintWindow(hwnd, save_dc.GetSafeHdc(), 2)
    if result != 1:
        raise RuntimeError("PrintWindow failed")

    bmpinfo = bitmap.GetInfo()
    bmpstr = bitmap.GetBitmapBits(True)
    img = Image.frombuffer(
        "RGB",
        (bmpinfo["bmWidth"], bmpinfo["bmHeight"]),
        bmpstr, "raw", "BGRX", 0, 1
    )
    _save_screenshot_under_limit(img, output_path)

    # cleanup
    win32gui.DeleteObject(bitmap.GetHandle())
    save_dc.DeleteDC()
    mfc_dc.DeleteDC()
    win32gui.ReleaseDC(hwnd, hwnd_dc)

    return output_path


def capture_window_to_file_linux(window_title, output_path=None):
    if shutil.which("gnome-screenshot") is None:
        raise RuntimeError("Missing gnome-screenshot on Linux")

    if output_path is None:
        output_path = "/tmp/vdi_screenshot.png"

    if window_title:
        if shutil.which("wmctrl") is None:
            raise RuntimeError("wmctrl is required to activate a window by title")
        activate = subprocess.run(
            ["wmctrl", "-xa", window_title],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if activate.returncode != 0:
            raise RuntimeError(f"wmctrl failed to activate window: {activate.stderr}")

    result = subprocess.run(
        ["gnome-screenshot", "-w", "-f", output_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"gnome-screenshot failed: {result.stderr}")

    if os.path.getsize(output_path) > MAX_SCREENSHOT_BYTES:
        try:
            from PIL import Image as _Image
            _save_screenshot_under_limit(_Image.open(output_path), output_path)
        except Exception as exc:
            print(f"Screenshot size reduction failed: {exc}")

    return output_path
    

def generateResponse(start_time,returncode):
    duration = time.time() - start_time
    seconds = int(duration)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    print (hours,minutes,seconds)
    response = jsonify({'return_code':returncode, 'duration':"{0}:{1}:{2}".format(int(hours),int(minutes),seconds)})
    response.status_code=200
    return response 

def runCommand(cmd):
    print ('runCommand: {0}'.format(cmd))
    returncode = 0
    
    try:
        subprocess.check_call(cmd)
    except subprocess.CalledProcessError as e:
        returncode = e.returncode

    return returncode


def _normalize_branch_value(value):
    if value is None:
        return ""
    return value.strip().strip("/\\")

def _select_hvd_info_path(horizon_flag):
    if horizon_flag is None:
        return HVD_INFO_PATH
    return HVD_INFO_HORIZON_PATH if str(horizon_flag).strip().lower() in {"1", "true", "yes", "y"} else HVD_INFO_PATH

def _get_hvd_info_value(key, hvd_info_path=HVD_INFO_PATH):
    if not os.path.isfile(hvd_info_path):
        return ""
    try:
        with open(hvd_info_path, "r", encoding="utf-8", newline="") as handle:
            for line in handle:
                if ":" not in line:
                    continue
                name, value = line.split(":", 1)
                if name.strip().lower() == key.lower():
                    return value.strip()
    except OSError as exc:
        print(f"Failed to read {hvd_info_path}: {exc}")
    return ""


def _update_hvd_info_eftbranch(branch_value, hvd_info_path):
    if not os.path.isfile(hvd_info_path):
        raise FileNotFoundError(f"Missing file: {hvd_info_path}")

    with open(hvd_info_path, "r", encoding="utf-8", newline="") as handle:
        lines = handle.readlines()

    new_lines = []
    updated = False
    for line in lines:
        if re.match(r"^\s*eftbranch\s*:", line, re.IGNORECASE):
            new_lines.append(f"eftbranch: {branch_value}\n")
            updated = True
        else:
            new_lines.append(line)

    if not updated:
        if new_lines and not new_lines[-1].endswith("\n"):
            new_lines[-1] = new_lines[-1] + "\n"
        new_lines.append(f"eftbranch: {branch_value}\n")

    with open(hvd_info_path, "w", encoding="utf-8", newline="") as handle:
        handle.writelines(new_lines)


def _validate_hvd_info_content(content):
    required_keys = [
        "sf_url",
        "username",
        "pwd",
        "domain",
        "vm_group",
        "hvd_ip",
        "eftbranch",
    ]
    values = {}
    for line in content.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip().lower()
        if not key:
            continue
        values[key] = value.strip()

    missing = [key for key in required_keys if not values.get(key)]
    if missing:
        return None, f"Missing or empty keys: {', '.join(missing)}"
    return values, None


@app.route('/')
def index():
    return (
        '<h1>Welcome to Teams Automation Agent.</h1>'
        '<p>Supported commands:</p>'
        '<ul>'
        '<li>runtestL</li>'
        '<li>runtestL?eftbranch=1</li>'
        '<li>runtestL-H</li>'
        '<li>runtestN</li>'
        '<li>runtestN?eftbranch=1</li>'
        '<li>setEftbranch?branch=46.3</li>'
        '<li>setEftbranch?branch=46.3&horizon=1</li>'
        '<li>getEftbranch</li>'
        '<li>getEftbranch?horizon=1</li>'
        '<li>getN-4Ver</li>'
        '<li>uploadHvdInfo (POST form-data: file=hvd_info.txt or hvd_info-horizon.txt)</li>'
        '<li>uploadN-4Ver (POST form-data: file=n-4_GA_version.txt)</li>'
        '<li>uploadHvdInfoForm</li>'
        '<li>uploadN-4VerForm</li>'
        '<li>screenshot</li>'
        '<li>screenshot?title=WINDOW_TITLE</li>'
        '<li>screenshot?send_ss=1&title=WINDOW_TITLE</li>'
        '<li>screenshot?horizon=1</li>'
        '<li>screenshot?horizon=1&send_ss=1</li>'
        '<li>screenshot?horizon=1&send_ss=1&title=WINDOW_TITLE</li>'
        '<li>send_ss=1 returns PNG image</li>'
        '<li>detectTone?ringback_on=0.9&ringback_off=4.8&duration_seconds=40</li>'
        '<li>detectAudio?duration_seconds=30&classify=1&model_path=PATH&class_labels=voice,music</li>'
        '<li>sendAudio</li>'
        '<li>sendAudio?text=Hello%20from%20API</li>'
        '<li>sendAudio?text=Hello&device_index=7&channels=1</li>'
        '</ul>'
    )
    
@app.route("/runtestL")
def RuntestL():
    start_time = time.time()
    filepath = os.getcwd()
    print ('Running WebexVDI Automation Test - Lastest main build',filepath)
    os.chdir(filepath)
    eft_branch = request.args.get("eftbranch")
    if eft_branch:
        cmd = ['TC-TestRunner-EFTbranch.bat'] if IS_WINDOWS else ['bash', 'TC-TestRunner-EFTbranch.sh']
    else:
        cmd = ['TC-TestRunner-LatestV.bat'] if IS_WINDOWS else ['bash', 'TC-TestRunner-LatestV.sh']
    returncode = runCommand(cmd)
    print ('Run Test Done')
    return generateResponse(start_time,returncode)

@app.route("/runtestL-H")
def RuntestL_H():
    start_time = time.time()
    filepath = os.getcwd()
    print('Running WebexVDI Automation Test - Horizon latest build', filepath)
    os.chdir(filepath)
    cmd = ['TC-TestRunner-Horizon-LatestV.bat'] if IS_WINDOWS else ['bash', 'TC-TestRunner-Horizon-LatestV.sh']
    returncode = runCommand(cmd)
    print('Run Test Done')
    return generateResponse(start_time, returncode)
    
@app.route("/runtestN")
def RuntestN():
    start_time = time.time()
    filepath = os.getcwd()
    print ('Running WebexVDI Automation Test - N-4 build',filepath)
    os.chdir(filepath)
    eft_branch = request.args.get("eftbranch")
    if eft_branch:
        cmd = ['TC-TestRunner-EFTbranch-N-4.bat'] if IS_WINDOWS else ['bash', 'TC-TestRunner-EFTbranch-N-4.sh']
    else:
        cmd = ['TC-TestRunner-N-4.bat'] if IS_WINDOWS else ['bash', 'TC-TestRunner-N-4.sh']
    returncode = runCommand(cmd)
    print ('Run Test Done')
    return generateResponse(start_time,returncode)


@app.route("/setEftbranch")
def setEftbranch():
    branch = _normalize_branch_value(request.args.get("branch"))
    if not branch:
        return jsonify({"error": "Missing branch parameter"}), 400

    hvd_info_path = _select_hvd_info_path(request.args.get("horizon"))

    try:
        _update_hvd_info_eftbranch(branch, hvd_info_path)
    except FileNotFoundError as exc:
        return jsonify({"error": str(exc)}), 404
    except OSError as exc:
        return jsonify({"error": f"Failed to update {hvd_info_path}: {exc}"}), 500

    return jsonify({"eftbranch": branch, "status": "updated"}), 200


@app.route("/getEftbranch")
def getEftbranch():
    hvd_info_path = _select_hvd_info_path(request.args.get("horizon"))
    if not os.path.isfile(hvd_info_path):
        return jsonify({"error": f"Missing file: {hvd_info_path}"}), 404

    try:
        with open(hvd_info_path, "r", encoding="utf-8", newline="") as handle:
            for line in handle:
                if re.match(r"^\s*eftbranch\s*:", line, re.IGNORECASE):
                    value = line.split(":", 1)[1]
                    branch = _normalize_branch_value(value)
                    return jsonify({"eftbranch": branch}), 200
    except OSError as exc:
        return jsonify({"error": f"Failed to read {hvd_info_path}: {exc}"}), 500

    return jsonify({"eftbranch": ""}), 200


@app.route("/getN-4Ver")
def get_n4_ver():
    if not os.path.isfile(N4_GA_VERSION_PATH):
        return f"Missing file: {N4_GA_VERSION_PATH}", 404

    try:
        with open(N4_GA_VERSION_PATH, "r", encoding="utf-8", newline="") as handle:
            lines = [line.strip() for line in handle if line.strip()]
    except OSError as exc:
        return f"Failed to read {N4_GA_VERSION_PATH}: {exc}", 500

    return Response("\n".join(lines), mimetype="text/plain"), 200


@app.route("/uploadHvdInfo", methods=["POST"])
def uploadHvdInfo():
    upload = request.files.get("file")
    if upload is None:
        return jsonify({"error": "Missing file upload"}), 400

    filename = os.path.basename(upload.filename or "")
    allowed_names = {"hvd_info.txt", "hvd_info-horizon.txt"}
    if filename.lower() not in allowed_names:
        return jsonify({"error": "Invalid file name; expected hvd_info.txt or hvd_info-horizon.txt"}), 400

    try:
        content = upload.read().decode("utf-8")
    except UnicodeDecodeError:
        return jsonify({"error": "Invalid file encoding; expected utf-8"}), 400

    _, error = _validate_hvd_info_content(content)
    if error:
        return jsonify({"error": error}), 400

    target_path = HVD_INFO_HORIZON_PATH if filename.lower() == "hvd_info-horizon.txt" else HVD_INFO_PATH
    try:
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        with open(target_path, "w", encoding="utf-8", newline="") as handle:
            handle.write(content if content.endswith("\n") else content + "\n")
    except OSError as exc:
        return jsonify({"error": f"Failed to write {target_path}: {exc}"}), 500

    return jsonify({"status": "uploaded", "path": target_path}), 200


@app.route("/uploadN-4Ver", methods=["POST"])
def upload_n4_ver():
    upload = request.files.get("file")
    if upload is None:
        return jsonify({"error": "Missing file upload"}), 400

    filename = os.path.basename(upload.filename or "")
    if filename.lower() != "n-4_ga_version.txt":
        return jsonify({"error": "Invalid file name; expected n-4_GA_version.txt"}), 400

    try:
        content = upload.read().decode("utf-8")
    except UnicodeDecodeError:
        return jsonify({"error": "Invalid file encoding; expected utf-8"}), 400

    if not content.strip():
        return jsonify({"error": "File is empty"}), 400

    versions = [item for item in content.replace("\r", "\n").split() if item]
    if not versions:
        return jsonify({"error": "File is empty"}), 400
    normalized = "\n".join(versions) + "\n"

    try:
        os.makedirs(os.path.dirname(N4_GA_VERSION_PATH), exist_ok=True)
        with open(N4_GA_VERSION_PATH, "w", encoding="utf-8", newline="") as handle:
            handle.write(normalized)
    except OSError as exc:
        return jsonify({"error": f"Failed to write {N4_GA_VERSION_PATH}: {exc}"}), 500

    return jsonify({"status": "uploaded", "path": N4_GA_VERSION_PATH}), 200


@app.route("/uploadHvdInfoForm")
def uploadHvdInfoForm():
    return (
        "<h1>Upload hvd_info.txt or hvd_info-horizon.txt</h1>"
        "<form action='/uploadHvdInfo' method='post' enctype='multipart/form-data'>"
        "<input type='file' name='file' accept='.txt' required>"
        "<button type='submit'>Upload</button>"
        "</form>"
        "<p>File name must be <strong>hvd_info.txt</strong> or <strong>hvd_info-horizon.txt</strong>.</p>"
    )


@app.route("/uploadN-4VerForm")
def uploadN4VerForm():
    return (
        "<h1>Upload n-4_GA_version.txt</h1>"
        "<form action='/uploadN-4Ver' method='post' enctype='multipart/form-data'>"
        "<input type='file' name='file' accept='.txt' required>"
        "<button type='submit'>Upload</button>"
        "</form>"
        "<p>File name must be <strong>n-4_GA_version.txt</strong>.</p>"
    )
    
@app.route('/screenshot')
def screenshot():
    start_time = time.time()
    if IS_WINDOWS:
        horizon_flag = request.args.get("horizon")
        hvd_info_path = _select_hvd_info_path(horizon_flag)
        vm_group = _get_hvd_info_value("vm_group", hvd_info_path)
        if str(horizon_flag).strip().lower() in {"1", "true", "yes", "y"}:
            default_title = vm_group or "Desktop"
        else:
            default_title = f"{vm_group} - Desktop Viewer" if vm_group else "Desktop Viewer"
    else:
        default_title = "Wfica.Wfica"
    window_title = request.args.get("title") or default_title
    try:
        if not request.args:
            os_name = "windows" if IS_WINDOWS else "linux"
            response = jsonify({"os": os_name})
            response.status_code = 200
            return response

        if IS_WINDOWS:
            if request.args.get("send_ss") is not None:
                screenshot_path = capture_window_to_file_windows(window_title)
                if not os.path.isfile(screenshot_path):
                    print("Screenshot file not found for download")
                    return generateResponse(start_time, 1)
                return send_file(screenshot_path, mimetype="image/png", as_attachment=True)

            capture_window_to_clipboard(window_title)
            print("Screenshot copied to clipboard.")
            return generateResponse(start_time, 0)

        print(f"Screenshot window title: {window_title}.")
        screenshot_path = capture_window_to_file_linux(window_title)
        print(f"Screenshot saved to {screenshot_path}.")

        if request.args.get("send_ss") is not None:
            if not os.path.isfile(screenshot_path):
                print("Screenshot file not found for download")
                return generateResponse(start_time, 1)
            return send_file(screenshot_path, mimetype="image/png", as_attachment=True)

        return generateResponse(start_time, 0)
    except Exception as exc:
        print(f"Screenshot failed: {exc}")
        return generateResponse(start_time, 1)


@app.route('/detectTone')
def detect_tone_route():
    start_time = time.time()
    script_dir = os.path.dirname(os.path.abspath(__file__))
    script_path = os.path.join(script_dir, "WebexVDICallToneDetector.py")
    if not os.path.isfile(script_path):
        return jsonify({"error": f"Missing script: {script_path}"}), 404

    ringback_on = request.args.get("ringback_on", "0.9").strip()
    ringback_off = request.args.get("ringback_off", "4.8").strip()
    duration_seconds = request.args.get("duration_seconds", "40").strip()
    try:
        float(ringback_on)
        float(ringback_off)
        float(duration_seconds)
    except ValueError:
        return jsonify({"error": "Invalid ringback_on/ringback_off/duration_seconds"}), 400

    cmd = [
        sys.executable,
        script_path,
        "--ringback-single",
        "--ringback-on",
        ringback_on,
        "--ringback-off",
        ringback_off,
        "--duration-seconds",
        duration_seconds,
    ]

    result = subprocess.run(
        cmd,
        cwd=script_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    output = f"{result.stdout}\n{result.stderr}"
    match = re.search(r"Ringback detections:\s*(\d+)", output)
    if match:
        ringback_detections = int(match.group(1))
        response = jsonify({
            "ringback_detections": ringback_detections,
            "return_code": result.returncode,
        })
        print(f"Ringback detections (API): {ringback_detections}")
        response.status_code = 200
        return response

    response = jsonify({
        "error": "Unable to parse ringback detections",
        "return_code": result.returncode,
        "output": output.strip(),
    })
    response.status_code = 500
    return response


@app.route('/sendAudio')
def send_audio_route():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    script_path = os.path.join(script_dir, "WebexVDITxAudio.py")
    if not os.path.isfile(script_path):
        return jsonify({"error": f"Missing script: {script_path}"}), 404

    text = request.args.get("text", "").strip()
    device_index = request.args.get("device_index", "").strip()
    channels = request.args.get("channels", "").strip()

    cmd = [sys.executable, script_path]
    if text:
        cmd.append(text)
    if device_index:
        cmd.extend(["--device-index", device_index])
    if channels:
        cmd.extend(["--channels", channels])

    result = subprocess.run(
        cmd,
        cwd=script_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    response = {
        "return_code": result.returncode,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
    }
    status_code = 200 if result.returncode == 0 else 500
    return jsonify(response), status_code


@app.route('/detectAudio')
def detect_audio_route():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    script_path = os.path.join(script_dir, "WebexVDIAudioPresenceDetector.py")
    if not os.path.isfile(script_path):
        return jsonify({"error": f"Missing script: {script_path}"}), 404

    duration_seconds = request.args.get("duration_seconds", "30").strip()
    classify = request.args.get("classify", "0").strip()
    model_path = request.args.get("model_path", "").strip()
    class_labels = request.args.get("class_labels", "").strip()

    try:
        float(duration_seconds)
    except ValueError:
        return jsonify({"error": "Invalid duration_seconds"}), 400

    cmd = [
        sys.executable,
        script_path,
        "--duration-seconds",
        duration_seconds,
    ]

    if classify in {"1", "true", "yes", "y"}:
        if not model_path:
            return jsonify({"error": "model_path is required when classify=1"}), 400
        cmd.extend(["--classify", "--classifier-model", model_path])
        if class_labels:
            cmd.extend(["--class-labels", class_labels])

    result = subprocess.run(
        cmd,
        cwd=script_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    output = f"{result.stdout}\n{result.stderr}"

    present_match = re.search(r"Audio present:\s*(true|false)", output)
    class_match = re.search(r"Audio class:\s*(.+)", output)
    if present_match:
        response = {
            "audio_present": present_match.group(1) == "true",
            "return_code": result.returncode,
        }
        if class_match:
            response["audio_class"] = class_match.group(1).strip()
        print(f"Audio present (API): {response['audio_present']}")
        return jsonify(response), 200

    return jsonify({
        "error": "Unable to parse audio presence",
        "return_code": result.returncode,
        "output": output.strip(),
    }), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0')