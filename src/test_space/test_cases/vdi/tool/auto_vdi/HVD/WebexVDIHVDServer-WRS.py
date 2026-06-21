from flask import Flask
from flask import make_response
from flask import Response
from flask import send_file
# from flask_script import Manager
from flask import jsonify
from flask import request
from bs4 import BeautifulSoup
import subprocess
import time
import requests
import os
# import urllib
import urllib.request
import shutil

app = Flask(__name__)
# manager = Manager(app)
nfsServer='http://dlwebex.jabberqa.cisco.com/masterbuild/windows_qt6/'
nfsServer1='http://dlwebex.jabberqa.cisco.com/eftbuild/windows_qt6/'
DEFAULT_DOWNLOAD_TIMEOUT = 60
DEFAULT_MAX_DOWNLOAD_SECONDS = 600
LAST_RUNTEST_START_EPOCH = None

def download_with_progress(url, local_path, timeout=DEFAULT_DOWNLOAD_TIMEOUT, max_seconds=DEFAULT_MAX_DOWNLOAD_SECONDS):
    start_time = time.time()
    downloaded = 0
    last_report_time = start_time
    last_report_bytes = 0

    request = urllib.request.Request(url)
    with urllib.request.urlopen(request, timeout=timeout) as response:
        total = response.getheader("Content-Length")
        total_size = int(total) if total and total.isdigit() else None
        with open(local_path, 'wb') as target_file:
            while True:
                if time.time() - start_time > max_seconds:
                    raise TimeoutError(f"Download exceeded {max_seconds} seconds")
                chunk = response.read(1024 * 64)
                if not chunk:
                    break
                target_file.write(chunk)
                downloaded += len(chunk)

                now = time.time()
                if now - last_report_time >= 1.0:
                    interval = now - last_report_time
                    interval_bytes = downloaded - last_report_bytes
                    speed_kbps = (interval_bytes / 1024.0) / interval if interval > 0 else 0.0
                    if total_size:
                        percent = (downloaded / total_size) * 100.0
                        msg = f"Download: {percent:6.2f}% ({downloaded}/{total_size} bytes) at {speed_kbps:7.2f} KB/s"
                    else:
                        msg = f"Download: {downloaded} bytes at {speed_kbps:7.2f} KB/s"
                    print(msg, end='\r', flush=True)
                    last_report_time = now
                    last_report_bytes = downloaded

    total_time = max(time.time() - start_time, 0.001)
    avg_speed_kbps = (downloaded / 1024.0) / total_time
    if total_size:
        print(f"Download complete: {downloaded}/{total_size} bytes in {total_time:.2f}s, avg {avg_speed_kbps:.2f} KB/s")
    else:
        print(f"Download complete: {downloaded} bytes in {total_time:.2f}s, avg {avg_speed_kbps:.2f} KB/s")
    return 0

@app.route('/')
def index():
    return '<p><h1>Welcome to Teams Automation Agent.</h1></p><p>Support Command:<p>deployTeamsWindows/</p><p>runtest</p>'

@app.route('/disconnect')
def disconnect():
	start_time = time.time()
	AppData_dir = os.getenv('LOCALAPPDATA')
	Spark_dir = os.path.join(AppData_dir,'CiscoSpark')
	if os.path.exists(Spark_dir):
		print("removing cisco spark local app data file...")    
		shutil.rmtree(Spark_dir, ignore_errors=True)
	
	print ('Disconnect')
	disconcmd=['tsdiscon']
	returncode = runCommand(disconcmd)
	return generateResponse(start_time,returncode)

@app.route('/gettestresult/<filename>')
def getTestResult(filename):
    xmlfile=os.path.join(os.getcwd(),filename)
    print ('getTestResult:',xmlfile)
    with open(xmlfile, 'r') as content_file:
        content = content_file.read()
    return Response(content , mimetype='text/xml')

@app.route('/downloadlogs')
def downloadLogs():
    from flask import send_file
    logs_file = os.path.join(os.getcwd(), 'CiscoSpark-Logs.7z')
    print('downloadLogs:', logs_file)
    if not os.path.exists(logs_file):
        return jsonify({'error': 'CiscoSpark-Logs.7z not found'}), 404
    return send_file(
        logs_file,
        as_attachment=True,
        download_name='CiscoSpark-Logs.7z',
        mimetype='application/x-7z-compressed'
    )

@app.route('/wrstestreport')
def wrsTestReport():
    def _find_latest_md(search_root):
        latest_file = None
        latest_mtime = -1.0
        for root, _, files in os.walk(search_root):
            for name in files:
                lower_name = name.lower()
                if not (lower_name.endswith('.md') and lower_name.startswith('navigation-report-')):
                    continue
                full_path = os.path.join(root, name)
                try:
                    mtime = os.path.getmtime(full_path)
                except OSError:
                    continue
                if mtime > latest_mtime:
                    latest_mtime = mtime
                    latest_file = full_path
        return latest_file

    wrs_output_root = r"C:\dev\wrs-output"
    latest_file = None

    if os.path.isdir(wrs_output_root) and LAST_RUNTEST_START_EPOCH is not None:
        closest_report_dir = None
        closest_diff = None
        for machine_dir in os.listdir(wrs_output_root):
            machine_path = os.path.join(wrs_output_root, machine_dir)
            if not os.path.isdir(machine_path):
                continue

            for run_dir in os.listdir(machine_path):
                run_path = os.path.join(machine_path, run_dir)
                if not os.path.isdir(run_path):
                    continue
                try:
                    folder_time = time.mktime(time.strptime(run_dir, "%Y%m%d-%H%M%S"))
                except ValueError:
                    continue

                diff = abs(folder_time - LAST_RUNTEST_START_EPOCH)
                report_dir = os.path.join(run_path, 'report')
                if not os.path.isdir(report_dir):
                    continue

                if closest_diff is None or diff < closest_diff:
                    closest_diff = diff
                    closest_report_dir = report_dir

        if closest_report_dir:
            latest_file = _find_latest_md(closest_report_dir)

    if not latest_file:
        base_dirs = [
            wrs_output_root,
            os.path.join(os.getcwd(), "wrs-output"),
            os.getcwd(),
        ]
        for base_dir in base_dirs:
            if not os.path.isdir(base_dir):
                continue
            latest_file = _find_latest_md(base_dir)
            if latest_file:
                break

    if not latest_file:
        return jsonify({'error': 'No markdown report file found'}), 404

    print('wrstestreport:', latest_file)
    return send_file(
        latest_file,
        as_attachment=True,
        download_name=os.path.basename(latest_file),
        mimetype='text/markdown'
    )

@app.route('/uploadCallingInfo', methods=['POST'])
def upload_calling_info():
    out_path = r"C:\dev\auto_vdi\calling_info.txt"
    try:
        content = request.get_data(as_text=True)
        if not content:
            return jsonify({'error': 'empty body'}), 400
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"[INFO] calling_info.txt saved to {out_path}")
        return jsonify({'status': 'ok'})
    except OSError as exc:
        return jsonify({'error': f'failed to save calling_info: {exc}'}), 500

@app.route('/tc_info', methods=['POST'])
def tc_info():
    data = request.get_json(silent=True) or {}
    tc_info_value = data.get('tc_info')
    if not tc_info_value:
        return jsonify({'error': 'tc_info is required'}), 400
    out_path = r"C:\dev\auto_vdi\tc_info.txt"
    try:
        with open(out_path, 'w', encoding='utf-8') as content_file:
            content_file.write(f"tc_ip: {tc_info_value}")
    except OSError as exc:
        return jsonify({'error': f'failed to write tc_info: {exc}'}), 500
    return jsonify({'status': 'ok'})

@app.route('/deployTeamsWindows/<versionnumber>')
def deployTeamsWindows(versionnumber):
    start_time = time.time()
    #download latest Teams windows
    name = 'Webex.msi'
#    downloadUrl = nfsServer+"windows/"+"x64/"+ versionnumber+'/'+name
#    downloadUrl = nfsServer + versionnumber + '-' + name    
#    local_path = os.path.join(name)
#    print ('Downloading file from: {0} to {1}'.format(downloadUrl, local_path))
#    urllib.request.urlretrieve(downloadUrl, local_path)
#    print ('Download Done')

    downloadUrl1 = nfsServer + versionnumber + '-' + name
    downloadUrl2 = nfsServer1 + versionnumber + '-' + name
    local_path = os.path.join(name)
    print(f'Downloading file from: {downloadUrl1} to {local_path}')
    try:
        download_with_progress(downloadUrl1, local_path)
        print('Download Done (primary URL)')
    except Exception as e:
        print(f'Failed to download from primary URL: {e}')
        print(f'Trying secondary URL: {downloadUrl2}')
        try:
            download_with_progress(downloadUrl2, local_path)
            print('Download Done (secondary URL)')
        except Exception as e2:
            print(f'Failed to download from secondary URL: {e2}')
            return jsonify({'error': 'Failed to download MSI from both URLs.'}), 500

    time.sleep(2)
    #Uninstall Teams windows
    print ('Uninstalling Teams Windows')
    cmd=["wmic", "product", "where", "name='Webex'", "call", "uninstall"]
    returncode = runCommand(cmd)
    print ('Uninstallation Done')

    time.sleep(2)
    #Install Teams windows
    print ('Installing Teams Windows')
    cmd=['msiexec']
    cmd+=['/i']
    cmd+=[local_path]
    cmd+=['/qr']
    cmd+=['ALLUSERS=1']
    cmd+=['ENABLEVDI=1']
    cmd+=['AUTOUPGRADEENABLED=1']
    cmd+=['AUTOUPGRADEVDIPLUGINENABLED=0']
    returncode = runCommand(cmd)
    print ('Installation Done')
    _sync_control_datasets(versionnumber)
    return generateResponse(start_time,returncode)

@app.route('/Runtest/<testcase>')
def Runtest(testcase):
    global LAST_RUNTEST_START_EPOCH
    start_time = time.time()
    LAST_RUNTEST_START_EPOCH = start_time
    filepath = os.getcwd()
    print ('Running TeamsVDIWRSTest',filepath)
    os.chdir(filepath)
    cmd=["WebexVDIWRSTest.bat", testcase]
    returncode = runCommand(cmd)
    print ('Run Test Done')
    return generateResponse(start_time, returncode)

@app.route('/Kill')
def Killproc():
	start_time = time.time()
	filepath = os.getcwd()
	print ('Kill CiscoCollabHost.exe')
	cmd=['KillWebexAppProc.bat']
	returncode = runCommand(cmd)
	print ('Kill Done')
	return generateResponse(start_time, returncode)

def runCommand(cmd):
    print ('runCommand: {0}'.format(cmd))
    returncode = 0
    
    try:
        subprocess.check_call(cmd)
    except subprocess.CalledProcessError as e:
        returncode = e.returncode

    return returncode
	
def generateResponse(start_time,returncode):
    duration = time.time() - start_time
    seconds = int(duration)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    print (hours,minutes,seconds)
    response = jsonify({'return_code':returncode, 'duration':"{0}:{1}:{2}".format(int(hours),int(minutes),seconds)})
    response.status_code=200
    return response

def _get_version_prefix(versionnumber):
    parts = str(versionnumber).split('.')
    if len(parts) >= 2:
        return f"{parts[0]}.{parts[1]}.0"
    return ""

def _strip_app_version_line(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as handle:
            lines = handle.readlines()
    except OSError as exc:
        print(f"Failed to read {file_path}: {exc}")
        return

    new_lines = []
    removed = False
    for line in lines:
        if not removed and '"app_version"' in line:
            removed = True
            continue
        new_lines.append(line)

    if removed:
        try:
            with open(file_path, 'w', encoding='utf-8', newline='') as handle:
                handle.writelines(new_lines)
            print(f"Removed app_version line from {file_path}")
        except OSError as exc:
            print(f"Failed to write {file_path}: {exc}")

def _sync_control_datasets(versionnumber):
    version_prefix = _get_version_prefix(versionnumber)
    if not version_prefix:
        print(f"Invalid versionnumber for datasets: {versionnumber}")
        return

    datasets_root = r"C:\dev\webex-regress-shield\src\test_space\datasets"
    source_dir = os.path.join(datasets_root, version_prefix)
    source_file = os.path.join(source_dir, "control_datasets.json")
    target_file = os.path.join(datasets_root, "control_datasets.json")

    if not os.path.isdir(source_dir):
        print(f"Dataset folder not found: {source_dir}")
        return
    if not os.path.isfile(source_file):
        print(f"Dataset file not found: {source_file}")
        return

    try:
        shutil.copyfile(source_file, target_file)
        print(f"Copied dataset control file to {target_file}")
    except OSError as exc:
        print(f"Failed to copy dataset control file: {exc}")
        return

    _strip_app_version_line(target_file)

if __name__ == '__main__':
#    manager.run()
    app.run(host="0.0.0.0", port=8080)


