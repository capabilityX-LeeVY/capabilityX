import subprocess
import os
import time
import argparse
import sys
import urllib.request
import urllib.error
import socket
import re

nfsServer_linux = 'http://shanghai-nfs.cisco.com/teams/TVDI/'
nfsServer_windows = 'https://spark-nfs.cisco.com/builds/spark/vdi/'
artifactory_windows_base = 'https://engci-maven-master.cisco.com/artifactory/webex-vdi-builds-generic/webex-vdi/'
artifactory_token_env = 'WEBEX_VDI_ARTIFACTORY_TOKEN'
fallback_dir = "/devOps/auto_vdi/GA_Builds"

def download_with_progress(url, local_path, request=None, timeout=60, max_seconds=600):
    start_time = time.time()
    downloaded = 0
    last_report_time = start_time
    last_report_bytes = 0

    if request is None:
        request = urllib.request.Request(url)

    with urllib.request.urlopen(request, timeout=timeout) as response:
        total = response.getheader("Content-Length")
        total_size = int(total) if total and total.isdigit() else None
        with open(local_path, 'wb') as target_file:
            while True:
                if time.time() - start_time > max_seconds:
                    raise socket.timeout(f"Download exceeded {max_seconds} seconds")
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

def parse_args():
    parser = argparse.ArgumentParser(description="Pocess Run Test scripts Argument")
    parser.add_argument('-v', '--versionnumber', required=True, help="versionnumber,e.g 3.0.16319.0")
    parser.add_argument('--max-download-seconds', type=int, default=600, help="Max download time in seconds (default: 600)")
    args = parser.parse_args()

    return args


def deployVdiPlugin(versionnumber, max_download_seconds=600):
    versionnumber = versionnumber.strip()
    if not re.fullmatch(r"[0-9]+(\.[0-9]+)*", versionnumber):
        print(f"Invalid version format: {versionnumber}")
        return 1
    request_timeout = 60
    if sys.platform.startswith("win"):
        # download latest VDI plugin (Windows)
        name = 'WebexVDIPlugin.msi'
        downloadUrl = nfsServer_windows + "windows/" + "x64/" + versionnumber + '/' + name
        local_path = os.path.join(name)
        print('Downloading VDI plugin from: {0} to {1}'.format(downloadUrl, local_path))
        try:
            download_with_progress(downloadUrl, local_path, timeout=request_timeout, max_seconds=max_download_seconds)
        except (urllib.error.HTTPError, urllib.error.URLError, socket.timeout) as exc:
            print('Download failed: {0}'.format(exc))
            token = os.getenv(artifactory_token_env)
            if not token:
                print(f"Missing token env var: {artifactory_token_env}")
                return 1
            fallback_url = artifactory_windows_base + "windows/" + "x64/" + versionnumber + '/' + name
            print('Downloading VDI plugin from fallback: {0} to {1}'.format(fallback_url, local_path))
            request = urllib.request.Request(fallback_url)
            request.add_header("Authorization", f"Bearer {token}")
            try:
                download_with_progress(fallback_url, local_path, request=request, timeout=request_timeout, max_seconds=max_download_seconds)
            except (urllib.error.HTTPError, urllib.error.URLError, socket.timeout) as fallback_exc:
                print('Fallback download failed: {0}'.format(fallback_exc))
                return 1
        print('Download Done...')

        time.sleep(2)
        # Install VDI plugin
        print('Installing VDI Plugin...')
        cmd = ['msiexec', '/i', local_path, '/qb']
        returncode = runCommand(cmd)
        print('Installation Done...')
        return returncode
    else:
        # download latest VDI plugin (Linux)
        name = "cisco-webex-vdi_" + versionnumber + "_amd64.deb"
        downloadUrl = nfsServer_linux + "linux/" + "ubuntu1804_x64/" + versionnumber + '/' + name
        local_path = os.path.join(name)
        install_needed = False
        if os.path.isfile(local_path):
            print(f"Using existing deb: {local_path}")
        else:
            remove_existing_deb_files(os.getcwd())
            print('Downloading VDI plugin from: {0} to {1}'.format(downloadUrl, local_path))
            try:
                download_with_progress(downloadUrl, local_path, timeout=request_timeout, max_seconds=max_download_seconds)
                print('Download Done')
                install_needed = True
            except (urllib.error.HTTPError, urllib.error.URLError, socket.timeout) as exc:
                print('Download failed: {0}'.format(exc))
                fallback_path = os.path.join(fallback_dir, name)
                if os.path.isfile(fallback_path):
                    print(f"Using local deb from: {fallback_path}")
                    local_path = fallback_path
                    install_needed = True
                else:
                    print(f"Local deb not found: {fallback_path}")
                    return 1

        if not install_needed:
            return 0

        time.sleep(2)
        # Uninstall VDI plugin
        print('Uninstalling VDI Plugin')
        uninstall_package('cisco-webex-vdi')
        print('Uninstallation Done')

        time.sleep(2)
        # Install VDI plugin
        print('Installing VDI Plugin')
        returncode = install_deb_package(local_path)
        print('Installation Done')
        return returncode

def remove_existing_deb_files(target_dir):
    if not os.path.isdir(target_dir):
        return

    removed_any = False
    for entry in os.listdir(target_dir):
        if not entry.endswith(".deb"):
            continue
        file_path = os.path.join(target_dir, entry)
        if not os.path.isfile(file_path):
            continue
        try:
            os.remove(file_path)
            removed_any = True
            print(f"Removed old deb: {file_path}")
        except OSError as exc:
            print(f"Failed to remove deb: {file_path} ({exc})")

    if not removed_any:
        print("No existing deb files to remove")

def install_deb_package(deb_path):
    """
    Install a .deb package using dpkg.
    """
    if not os.path.isfile(deb_path):
        print(f"File not found: {deb_path}")
        return 1


    password = "Kyehwa300426!"
    cmd = f'echo "{password}" | sudo -S dpkg -i {deb_path}' 
    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            shell=True
        )
        print(result.stdout)
        if result.returncode != 0:
            print("dpkg install failed")
            print(result.stderr)
            return 1
        reload_cmd = f'echo "{password}" | sudo -S systemctl daemon-reload'
        reload_result = subprocess.run(
            reload_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            shell=True
        )
        print(reload_result.stdout)
        if reload_result.returncode != 0:
            print("systemctl daemon-reload failed")
            print(reload_result.stderr)
            return 1
        restart_cmd = f'echo "{password}" | sudo -S systemctl restart teamsvdi.service'
        restart_result = subprocess.run(
            restart_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            shell=True
        )
        print(restart_result.stdout)
        if restart_result.returncode != 0:
            print("systemctl restart teamsvdi.service failed")
            print(restart_result.stderr)
            return 1
        status_cmd = f'echo "{password}" | sudo -S systemctl is-active teamsvdi.service'
        status_output = ""
        status_result = None
        for attempt in range(3):
            status_result = subprocess.run(
                status_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                shell=True
            )
            status_output = status_result.stdout.strip()
            print(status_output)
            if status_result.returncode == 0 and status_output == "active":
                break
            time.sleep(1)
        if status_result is None or status_result.returncode != 0 or status_output != "active":
            print("systemctl is-active teamsvdi.service failed")
            if status_result and status_result.stderr:
                print(status_result.stderr)
            return 1
        return 0
    except Exception as e:
        print(f"Error installing package: {e}")
        return 1

def uninstall_package(package_name):
    """
    Uninstall a package by name using dpkg.
    """
    password = "Kyehwa300426!"
    cmd = f'echo "{password}" | sudo -S dpkg -P {package_name}'
    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            shell=True
        )
        print(result.stdout)
        if result.returncode != 0:
            print(result.stderr)
            return 1
        return 0
    except Exception as e:
        print(f"Error uninstalling package: {e}")
        return 1

def runCommand(cmd):
    print('runCommand: {0}'.format(cmd))
    returncode = 0

    try:
        subprocess.check_call(cmd)
    except subprocess.CalledProcessError as e:
        returncode = e.returncode
        print('Command failed with exit code:', returncode)

    return returncode


if __name__ == '__main__':
    args = parse_args()
    versionnumber = args.versionnumber

    # Download&Install VDI plugin
    deploy_returncode = deployVdiPlugin(versionnumber, max_download_seconds=args.max_download_seconds)
    if(deploy_returncode != 0):
        print ('Installing VDI plugin fail without running E2E test case')
        sys.exit(1)
