import requests
import subprocess
import os
import time
import argparse
import sys
import urllib.request
import json
import tempfile
from datetime import datetime
import py7zr
import socket
from WebexVDIBuildMsgCard import WebexVDIBuildMsgCard, WebexVDIBuildFailureCard
from WebexVDIRsAICheckFailureAlert import collect_mentions, parse_table_row
from WebexVDISendAdaptiveCard import send_adaptive_card

BEAR_TOKEN = "NWE0ZjBhZjEtNDUxZS00ZDNkLThhOGItMjcwNjUwMjFlNWZkMDI2NTY0MmQtY2Nl_PF84_1eb65fdf-9643-417f-9974-ad72cae0e10f"
ROOM_ID = "7d6b04f0-ff44-11f0-a678-4559f92c6a95"  # or hardcode the room ID string

def resolve_hvd_info_path(vdi_env=None):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    use_horizon = str(vdi_env or "").strip().lower() == "horizon"
    hvd_info_name = "hvd_info-horizon.txt" if use_horizon else "hvd_info.txt"
    candidate = os.path.normpath(os.path.join(script_dir, "..", hvd_info_name))
    if os.path.isfile(candidate):
        return candidate

    if sys.platform.startswith("win"):
        windows_path = rf"C:\dev\auto_vdi\{hvd_info_name}"
        return windows_path if os.path.isfile(windows_path) else None

    linux_path = f"/devOps/auto_vdi/{hvd_info_name}"
    return linux_path if os.path.isfile(linux_path) else None

def read_eftbranch(info_path):
    if not info_path or not os.path.isfile(info_path):
        return None
    try:
        with open(info_path, 'r', encoding='utf-8') as info_file:
            for line in info_file:
                stripped = line.strip()
                if not stripped or stripped.startswith('#'):
                    continue
                if stripped.lower().startswith('eftbranch:'):
                    return stripped.split(':', 1)[1].strip() or None
    except Exception as exc:
        print(f"Failed to read eftbranch from {info_path}: {exc}")
    return None

def format_webex_app_version(versionnumber, eftbranch):
    #label = f"Webex App version: {versionnumber}"
    label = f"{versionnumber}"    
    if versionnumber and eftbranch and eftbranch in str(versionnumber):
        return f"🅱️ **{label}**"
    return f"Ⓜ️ **{label}**"

def parse_args():
    parser = argparse.ArgumentParser(description="Pocess Run Test scripts Argument")
    parser.add_argument('-s', '--test_server', required=True, help="Test server,e.g 10.74.145.104:8080")
    parser.add_argument('-v', '--versionnumber', required=False, help="versionnumber,e.g 3.0.16319.0")
    parser.add_argument('-pv', '--pluginversionnumber', required=False, help="plugin versionnumber,e.g 3.0.16319.0")    
    parser.add_argument('-tc', '--testcase', required=True, help="testcase, eg.g vbg_static")
    parser.add_argument('-o', '--report', required=True, help="File name of test report,e.g output.xml")
    parser.add_argument('--vdi-env', required=False, default='-', help="VDI environment, e.g. Citrix or Horizon")
    parser.add_argument('--deployTeamsWindows', required=False, default='yes', help="If install Teams Windows")
    parser.add_argument(
        '--reportAnalyzerInsecure',
        action='store_true',
        help="Disable SSL verification when running the report analyzer",
    )
    args = parser.parse_args()

    return args

def execTask(url):
    print('send request,', url, ',waitting result...')
    try:
        res = requests.get(url, timeout=(10, None))
    except requests.exceptions.ConnectTimeout as exc:
        print(f"connect timeout while requesting: {url} ({exc})")
        return -1
    task_res = res.json()
    print('request status code:', res.status_code)
    print('return_code:', task_res['return_code'])
    print('duration:', task_res['duration'])
    return task_res['return_code']

def build_base_url(test_server):
    if not test_server:
        return ""

    server = test_server.strip().rstrip("/")
    if server.startswith("http://") or server.startswith("https://"):
        return server
    return f"http://{server}"

def build_url(base_url, path):
    if not base_url:
        return ""
    if not path.startswith("/"):
        path = f"/{path}"
    return f"{base_url}{path}"

def send_tc_info(url, tc_info):
    print('send request,', url, ',posting tc info...')
    try:
        res = requests.post(url, json={"tc_info": tc_info}, timeout=(10, None))
    except requests.exceptions.ConnectTimeout as exc:
        print(f"connect timeout while requesting: {url} ({exc})")
        return False
    print('request status code:', res.status_code)
    if res.status_code != 200:
        print('tc info post failed:', res.text)
        return False
    return True

def get_local_ip():
    # Use UDP socket to discover the outbound interface IP without sending data.
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.connect(("8.8.8.8", 80))
        ip = sock.getsockname()[0]
        sock.close()
        return ip
    except OSError:
        try:
            return socket.gethostbyname(socket.gethostname())
        except OSError:
            return "127.0.0.1"

def post_tc_info(base_url):
    tc_info = f"{get_local_ip()}:5000"
    send_tc_info(build_url(base_url, "/tc_info"), tc_info)

def getReportTask(url,reportpath):
    print ('send request,',url,',waitting result...')
    res = requests.get(url,timeout=None)
    print ('request status code:',res.status_code)
    print ('report file:',reportpath)
    with open(reportpath, 'w', encoding='utf-8') as content_file:
        content_file.write(res.text)

def downloadLogsTask(url, archive_path):
    print('send request,', url, ',waitting result...')
    with requests.get(url, stream=True, timeout=None) as res:
        print('request status code:', res.status_code)
        if res.status_code != 200:
            print('download failed:', res.text)
            return False
        with open(archive_path, 'wb') as content_file:
            for chunk in res.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    content_file.write(chunk)
    print('logs file:', archive_path)
    return True

def sendMessageToTeams(message):

    roomId = "7d6b04f0-ff44-11f0-a678-4559f92c6a95"
    sparkapi = 'https://webexapis.com/v1/messages'
    headers = {
            'Content-Type': 'application/json;charset=UTF-8',
            'Authorization': f'''Bearer {BEAR_TOKEN}'''
            }
    data = {"roomId": roomId, "text": "", "markdown": "%s" % (message)}
    try:
        req = requests.post(sparkapi, data=json.dumps(data), headers = headers)
        if req.status_code == 200:
            print(f"Notify message bot succeeded. with room ID: ({roomId})")
            # Return message ID for thread support
            response_data = req.json()
            return response_data.get('id')
        else:
            print(f"Notify message bot failed, status code : {req.status_code} - {req.text} with room ID: {roomId}")
            return None
    except Exception as e:
        print(f"Notify message bot failed: {e}")
        return None

def log_warn(message):
    timestamp = time.strftime("%Y-%m-%d-%H%M%S")
    print(f"[{timestamp}] WARNING: {message}")

def sendFileToTeams(file_path, room_id=ROOM_ID):
    sparkapi = 'https://webexapis.com/v1/messages'
    headers = {
        'Authorization': f'''Bearer {BEAR_TOKEN}'''
    }

    if not os.path.isfile(file_path):
        print(f"File not found: {file_path}")
        return None

    file_size = os.path.getsize(file_path)
    if file_size <= 0:
        print(f"File is empty: {file_path}")
        return None

    archive_name = os.path.basename(file_path)
    if archive_name == "CiscoSpark-Logs.7z":
        archive_text = "CiscoSpark logs archive"
    elif archive_name == "CiscoWebexVDI-Logs.7z":
        archive_text = "VDI Plugin logs archive"
    else:
        archive_text = "Logs archive"

    data = {
        "roomId": room_id,
        "text": archive_text
    }

    try:
        with open(file_path, 'rb') as f:
            files = [
                (
                    'files',
                    (os.path.basename(file_path), f, 'application/x-7z-compressed')
                )
            ]
            req = requests.post(sparkapi, data=data, files=files, headers=headers, timeout=60)
        if req.status_code == 200:
            print(f"File upload succeeded. room ID: ({room_id})")
            message_id = req.json().get('id')
            try:
                os.remove(file_path)
                print(f"Deleted local file: {file_path}")
            except Exception as e:
                print(f"Failed to delete local file: {file_path} - {e}")
            return message_id
        else:
            print(f"File upload failed, status code : {req.status_code} - {req.text} with room ID: {room_id}")
            return None
    except Exception as e:
        print(f"File upload failed: {e}")
        return None


def send_status_card(status, timestamp, platform, vdi_env, webex_app_version, vdi_plugin_version, test_suite):
    card = WebexVDIBuildMsgCard(
        title=status,
        timestamp=timestamp,
        platform=platform,
        vdi_env=vdi_env or "-",
        webex_app_version=webex_app_version or "-",
        vdi_plugin_version=vdi_plugin_version or "-",
        test_suite=test_suite or "-",
    )
    fallback_text = f"Running Status: {status}"
    return send_adaptive_card(card, ROOM_ID, BEAR_TOKEN, fallback_text)

def vdi_compress_webexvdi_logs(output_dir=None, vdi_env=None):
    if sys.platform.startswith("win"):
        logs = os.path.join(os.environ["LOCALAPPDATA"], "CiscoWebexVDI")
    else:
        logs = "/var/log/CiscoWebexVDI"
    print(f"Using VDI logs path: {logs}")
    if not os.path.isdir(logs):
        raise FileNotFoundError(logs)

    if output_dir is None:
        use_horizon = str(vdi_env or "").strip().lower() == "horizon"
        if sys.platform.startswith("win"):
            output_dir = r"C:\dev\auto_vdi\TC_Horizon" if use_horizon else r"C:\dev\auto_vdi\TC_Citrix"
        else:
            output_dir = "/devOps/auto_vdi/TC_Horizon" if use_horizon else "/devOps/auto_vdi/TC_Citrix"
    os.makedirs(output_dir, exist_ok=True)

    out = os.path.join(
        output_dir,
        f"CiscoWebexVDI-Logs.7z",
    )

    with py7zr.SevenZipFile(out, "w") as archive:
        archive.writeall(logs, arcname="Logs")

    try:
        archive_size = os.path.getsize(out)
        print(f"Created VDI logs archive: {out} ({archive_size} bytes)")
    except OSError as exc:
        print(f"Created VDI logs archive: {out} (size unavailable: {exc})")

    return out


def _download_fallback_report_md(fallback_report_url):
    if not fallback_report_url:
        return None

    print(f"Trying fallback markdown download: {fallback_report_url}")
    try:
        with requests.get(fallback_report_url, stream=True, timeout=(10, None)) as res:
            print('fallback request status code:', res.status_code)
            if res.status_code != 200:
                print('fallback markdown download failed:', res.text)
                return None

            with tempfile.NamedTemporaryFile(delete=False, suffix=".md") as temp_file:
                temp_md_path = temp_file.name
            with open(temp_md_path, 'wb') as content_file:
                for chunk in res.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        content_file.write(chunk)

        print(f"Fallback markdown downloaded to: {temp_md_path}")
        return temp_md_path
    except Exception as exc:
        print(f"Fallback markdown download error: {exc}")
        return None


def send_ai_failure_report(report_path, insecure=False, fallback_report_url=None):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    analyzer_path = os.path.join(script_dir, "WebexVDIRsReportAnalyzer.py")
    builder_path = os.path.join(script_dir, "WebexVDIRsAICheckFailureAlert.py")
    if not os.path.isfile(analyzer_path):
        print(f"AI report analyzer not found: {analyzer_path}")
        return False
    if not os.path.isfile(builder_path):
        print(f"AI failure alert builder not found: {builder_path}")
        return False
    if not os.path.isfile(report_path):
        print(f"Report output file not found: {report_path}")
        return False

    temp_list_path = None
    temp_msg_path = None
    fallback_md_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as temp_file:
            temp_list_path = temp_file.name
        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as temp_file:
            temp_msg_path = temp_file.name

        cmd = [
            sys.executable,
            analyzer_path,
            "--output-file",
            report_path,
            "--print-failures",
            "--result-file",
            temp_list_path,
            "--cleanup",
        ]
        if insecure:
            cmd.append("--insecure")
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if result.returncode != 0:
            combined_output = result.stderr or result.stdout
            if not insecure and combined_output and "CERTIFICATE_VERIFY_FAILED" in combined_output:
                cmd.append("--insecure")
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                )
            if result.returncode != 0:
                print("AI report analyzer failed from output.txt URL; trying /wrstestreport fallback...")
                fallback_md_path = _download_fallback_report_md(fallback_report_url)
                if not fallback_md_path:
                    print("AI report analyzer failed:")
                    print(result.stderr or result.stdout)
                    return False, ""

                fallback_cmd = [
                    sys.executable,
                    analyzer_path,
                    "--report-file",
                    fallback_md_path,
                    "--print-failures",
                    "--result-file",
                    temp_list_path,
                ]
                fallback_result = subprocess.run(
                    fallback_cmd,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                )
                if fallback_result.returncode != 0:
                    print("AI report analyzer failed with /wrstestreport fallback:")
                    print(fallback_result.stderr or fallback_result.stdout)
                    return False, ""

        build_cmd = [
            sys.executable,
            builder_path,
            "--analyzer-output",
            temp_list_path,
            "--out-file",
            temp_msg_path,
        ]
        build_result = subprocess.run(
            build_cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if build_result.returncode != 0:
            print("AI failure alert builder failed:")
            print(build_result.stderr or build_result.stdout)
            return False, ""

        with open(temp_list_path, "r", encoding="utf-8", errors="replace") as handle:
            failure_list_text = handle.read().strip()
        if not failure_list_text:
            print("AI failure alert builder returned empty output.")
            return False, failure_list_text

        timestamp = time.strftime("%Y-%m-%d-%H%M%S")
        card = WebexVDIBuildFailureCard(
            title="AI Check Failure List",
            timestamp=timestamp,
            platform="-",
            webex_app_version="-",
            vdi_plugin_version="-",
            test_suite="-",
            failures=failure_list_text,
        )
        fallback_text = "AI Check Failure List"
        send_adaptive_card(card, ROOM_ID, BEAR_TOKEN, fallback_text)

        mention_tokens = []
        mention_seen = set()
        first_failed_case = None
        for line in failure_list_text.splitlines():
            stripped = line.strip()
            if stripped.lower().startswith("first failed test case"):
                parts = line.split(":", 1)
                if len(parts) == 2:
                    first_failed_case = parts[1].strip()
            row = parse_table_row(line)
            if not row:
                continue
            _, case_name, reason = row
            mention_text = collect_mentions("", case_name, reason)
            if not mention_text:
                continue
            for token in mention_text.split():
                if token.startswith("<@personEmail:") and token.endswith(">"):
                    if token not in mention_seen:
                        mention_seen.add(token)
                        mention_tokens.append(token)

        if first_failed_case:
            mention_text = collect_mentions("", first_failed_case, "")
            if mention_text:
                for token in mention_text.split():
                    if token.startswith("<@personEmail:") and token.endswith(">"):
                        if token not in mention_seen:
                            mention_seen.add(token)
                            mention_tokens.append(token)

        if mention_tokens:
            attention_message = f"{' '.join(mention_tokens)} **Pls pay attension.**"
            sendMessageToTeams(attention_message)
        return True, failure_list_text
    finally:
        for temp_path in (temp_list_path, temp_msg_path, fallback_md_path):
            if temp_path and os.path.isfile(temp_path):
                try:
                    os.remove(temp_path)
                except OSError as exc:
                    print(f"Failed to delete temp file: {temp_path} ({exc})")


def ai_failure_case_present(failure_list_text, case_substring):
    if not failure_list_text:
        return False
    return case_substring.lower() in failure_list_text.lower()


if __name__ == '__main__':
    args = parse_args()
    test_server = args.test_server
    versionnumber = args.versionnumber
    testcase = args.testcase
    report = args.report
    pluginversionnumber = args.pluginversionnumber
    vdi_env = args.vdi_env
    platform = "Windows" if sys.platform.startswith("win") else "Linux"
    base_url = build_base_url(test_server)
    hvd_info_path = resolve_hvd_info_path(vdi_env)
    eftbranch = read_eftbranch(hvd_info_path)
    webex_version_label = format_webex_app_version(versionnumber, eftbranch)

    # Send starting message to Webex App room
    timestamp = time.strftime("%Y-%m-%d-%H%M%S")
    send_status_card(
        "Starting",
        timestamp,
        platform,
        vdi_env,
        webex_version_label,
        pluginversionnumber,
        testcase,
    )

    # Download&Install Teams Windows
    if (args.deployTeamsWindows == 'yes'):
        deploy_returncode = execTask(build_url(base_url, f"/deployTeamsWindows/{versionnumber}"))
        if(deploy_returncode == 0):
            time.sleep(5)
            post_tc_info(base_url)
            # run test
            test_returncode = execTask(build_url(base_url, f"/Runtest/{testcase}"))
            # kill process
            execTask(build_url(base_url, "/Kill"))
            # Delete App Data and Disconnect Session
            execTask(build_url(base_url, "/disconnect"))
            if (test_returncode == 0):
                print ('Running E2E case succeed...')
                timestamp = time.strftime("%Y-%m-%d-%H%M%S")
                send_status_card(
                    "Test run succeed",
                    timestamp,
                    platform,
                    vdi_env,
                    webex_version_label,
                    pluginversionnumber,
                    testcase,
                )
                getReportTask(build_url(base_url, f"/gettestresult/{report}"), report)
                _, failure_list_text = send_ai_failure_report(
                    report,
                    args.reportAnalyzerInsecure,
                    build_url(base_url, "/wrstestreport"),
                )
                if downloadLogsTask(build_url(base_url, "/downloadlogs"), 'CiscoSpark-Logs.7z'):
                    if not sendFileToTeams('CiscoSpark-Logs.7z'):
                        log_warn("Failed to upload CiscoSpark logs archive to Webex.")
                vdi_compress_webexvdi_logs(vdi_env=vdi_env)
                if not sendFileToTeams('CiscoWebexVDI-Logs.7z'):
                    log_warn("Failed to upload CiscoWebexVDI logs archive to Webex.")
                if ai_failure_case_present(failure_list_text, "vdi_healthchecker"):
                    sendMessageToTeams("<@personEmail:qd@webex.bot> bug:[vdi] virtual channel problem")
                sys.exit(0)
            else:
                # get report
                getReportTask(build_url(base_url, f"/gettestresult/{report}"), report)
                print ('Running E2E case fail...')
                timestamp = time.strftime("%Y-%m-%d-%H%M%S")
                send_status_card(
                    "Test run failed",
                    timestamp,
                    platform,
                    vdi_env,
                    webex_version_label,
                    pluginversionnumber,
                    testcase,
                )
                sys.exit(1)
        else:
            # kill process
            execTask(build_url(base_url, "/Kill"))
            # Delete App Data and Disconnect Session
            execTask(build_url(base_url, "/disconnect"))
            #deploy fail
            print ('deploy fail without running E2E test case...')
            timestamp = time.strftime("%Y-%m-%d-%H%M%S")
            send_status_card(
                "Deployment failed, test not run",
                timestamp,
                platform,
                vdi_env,
                webex_version_label,
                pluginversionnumber,
                testcase,
            )
            sys.exit(1)
    else:
        time.sleep(5)
        post_tc_info(base_url)
        test_returncode = execTask(build_url(base_url, f"/Runtest/{testcase}"))
        # kill process
        execTask(build_url(base_url, "/Kill"))
        # Delete App Data and Disconnect Session
        execTask(build_url(base_url, "/disconnect"))
        if (test_returncode == 0):
            print ('Running E2E case succeed...')
            timestamp = time.strftime("%Y-%m-%d-%H%M%S")
            send_status_card(
                "Test run succeed",
                timestamp,
                platform,
                vdi_env,
                webex_version_label,
                pluginversionnumber,
                testcase,
            )
            getReportTask(build_url(base_url, f"/gettestresult/{report}"), report)
            _, failure_list_text = send_ai_failure_report(
                report,
                args.reportAnalyzerInsecure,
                build_url(base_url, "/wrstestreport"),
            )
            if downloadLogsTask(build_url(base_url, "/downloadlogs"), 'CiscoSpark-Logs.7z'):
                if not sendFileToTeams('CiscoSpark-Logs.7z'):
                    log_warn("Failed to upload CiscoSpark logs archive to Webex.")
            vdi_compress_webexvdi_logs(vdi_env=vdi_env)
            if not sendFileToTeams('CiscoWebexVDI-Logs.7z'):
                log_warn("Failed to upload CiscoWebexVDI logs archive to Webex.")
            if ai_failure_case_present(failure_list_text, "vdi_healthchecker"):
                sendMessageToTeams("<@personEmail:qd@webex.bot> bug:[vdi] virtual channel problem")
            sys.exit(0)
        else:
            # get report
            getReportTask(build_url(base_url, f"/gettestresult/{report}"), report)
            print ('Running E2E case fail...')
            timestamp = time.strftime("%Y-%m-%d-%H%M%S")
            send_status_card(
                "Test run failed",
                timestamp,
                platform,
                vdi_env,
                webex_version_label,
                pluginversionnumber,
                testcase,
            )
            sys.exit(1)