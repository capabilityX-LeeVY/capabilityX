# Make sure those python modules are installed on Windows: pyinstaller pywin32 (python -m pip install pyinstaller pywin32)
# Can generate installer with command: pyinstaller -F --console installwebex.py

import os
import locale
import plistlib
try:
    import urllib.request as urllib
except ImportError:
    import urllib2 as urllib
import sys
import subprocess
import time
import re
import ssl
import threading
import itertools
import tqdm
from base64 import b64encode
if sys.platform.startswith('win'):
    import psutil
    import ctypes
    import winreg
    from win32api import GetFileVersionInfo, LOWORD, HIWORD
    user32 = ctypes.windll.user32

try:
    import requests
    from requests.auth import HTTPBasicAuth
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", 'requests'])
finally:
    import requests
    from requests.auth import HTTPBasicAuth
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from common.utils.logger import LOGGER_INFO, LOGGER_DEBUG, LOGGER_WARNING, LOGGER_ERROR
from common.handler.settingsHandler import DynamicConfig
from common.handler import fileHandler
from config.paths import SETTINGS_PATH, APP_VERSION_PATH
from config.config import WAIT_WINDOW_ACTION_TIME, WAIT_SHORT_TIME

"""
1. -v is required. -v should be full verison, eg:42.4.0.21560, or -v latest, to install latest master build
2. if current running version is the latest one, keep it!
3. script will download build to ~/Downloads on mac or %Downloads% on windows
4. after download, script will uninstall older webex(windows only)
5. after uninstall, it will install downloaded webex client
run command in terminal: python3 installwebex.py -v 42.5.0.xxxx (default is latest)
any issue you hit please contact with meixiang@cisco.com
"""

LOCAL_APP_PATH = ''
_cleanup_all_performed = False  # Runtime flag: cleanup_all_versions only runs once per process
SSL_CONTEXT = ssl.create_default_context()
SSL_CONTEXT.check_hostname = False
SSL_CONTEXT.verify_mode = ssl.CERT_NONE

# Internal server authentication credentials
INTERNAL_SERVER_USERNAME = 'admin'
INTERNAL_SERVER_PASSWORD = 'Happy123!@#'

PLATFORM_WIN = 'windows'
PLATFORM_MAC = 'mac'
PLATFORM_UBUNTU_1804 = 'ubuntu1804'
PLATFORM_UBUNTU_2004 = 'ubuntu2004'
PLATFORM_CENTOS = 'centos'

def get_windows_webex_exe_path():
    per_user_path = os.path.join(os.path.expanduser('~'), 
                                 'AppData\\Local\\Programs\\Cisco Spark\\CiscoCollabHost.exe')
    if os.path.exists(per_user_path):
        return per_user_path
    
    per_system_path = os.path.join('C:\\Program Files', 'Cisco Spark', 'CiscoCollabHost.exe')
    if os.path.exists(per_system_path):
        return per_system_path
    
    return per_user_path


def get_windows_webex_dll_path():
    per_user_dll = os.path.join(os.path.expanduser('~'), 
                                'AppData\\Local\\Programs\\Cisco Spark\\dependencies\\spark-windows-desktop-ui.dll')
    if os.path.exists(per_user_dll):
        return per_user_dll
    
    per_system_dll = os.path.join('C:\\Program Files', 'Cisco Spark', 
                                  'dependencies', 'spark-windows-desktop-ui.dll')
    if os.path.exists(per_system_dll):
        return per_system_dll
    
    return per_user_dll


def get_linux_distro():
    try:
        with open('/etc/os-release') as f:
            info = {}
            for line in f:
                if '=' in line:
                    k, v = line.strip().split('=', 1)
                    info[k] = v.strip('"')
            
            name = info.get('NAME', '').lower()
            version_id = info.get('VERSION_ID', '')
            
            if 'ubuntu' in name:
                return "Ubuntu {version_id}".format(version_id=version_id)
            elif 'centos' in name:
                return "CentOS {version_id}".format(version_id=version_id)
            elif 'debian' in name:
                return "Debian {version_id}".format(version_id=version_id)
            elif 'fedora' in name:
                return "Fedora {version_id}".format(version_id=version_id)
            else:
                return info.get('PRETTY_NAME', 'Unknown Linux distribution')
    except FileNotFoundError:
        return "Unknown (cannot find /etc/os-release)"

# print(get_linux_distro())

def current_platform():
    platform = sys.platform
    if 'darwin' in platform:
        return PLATFORM_MAC
    elif 'win' in platform:
        return PLATFORM_WIN
    
    linux_distro = get_linux_distro()
    if linux_distro.startswith('Ubuntu 2'):
        return PLATFORM_UBUNTU_2004
    elif linux_distro.startswith('Ubuntu 1'):
        return PLATFORM_UBUNTU_1804
    elif linux_distro.startswith('CentOS') or linux_distro.startswith('Debian') or linux_distro.startswith('Fedora'):
        return PLATFORM_CENTOS

    return 'unsupported'


def get_chip_info(platform):
    """
       get chip info for macOS
    """
    if platform == PLATFORM_MAC:
        cmd = r'sysctl -n machdep.cpu.brand_string'
        for line in os.popen(cmd):
            if "Apple M" in line:
                # LOGGER_INFO(f'Mac chip is {line.split("\n")[0]}')
                return "apple"
            else:
                # LOGGER_INFO(f'Mac chip is {line.split("\n")[0]}')
                return "intel"
    else:
        return "notmac"


def app_name(platform, version, qtversion, arch, is_http2, chip_info):
    """
    get app name based on platform info
    """
    if platform == PLATFORM_MAC:
        mac_arch = 'arm64' if chip_info == 'apple' else 'x64'
        if is_http2:
            return 'Webex-{arch}-{version}.dmg'.format(arch=mac_arch, version=version)
        else:
            return 'Webex-nonhttp2-{arch}-{version}.dmg'.format(arch=mac_arch, version=version)
    elif platform == PLATFORM_WIN:
        if qtversion == '5':
            return 'Webex-qt5-{arch}-{version}.msi'.format(arch=arch, version=version)
        else:
            return 'Webex-{arch}-{version}.msi'.format(arch=arch, version=version)
    elif platform == PLATFORM_UBUNTU_1804 or platform == PLATFORM_UBUNTU_2004:
        return 'Webex-{version}.deb'.format(version=version)
    elif platform == PLATFORM_CENTOS:
        return 'Webex-{version}.rpm'.format(version=version)
    else:
        return ''


def get_local_downloads_folder(path=''):
    """
    default download path is defined here for different platform
    """
    if path:
        return path
    return os.path.join(os.path.expanduser('~'), 'Downloads')


def add_internal_auth(request, url):
    """
    Add Basic Auth header for internal servers (dlwebex.jabberqa.cisco.com or sym.jabberqa.cisco.com)
    """
    if 'dlwebex.jabberqa.cisco.com' in url or 'sym.jabberqa.cisco.com' in url:
        import base64
        credentials = f'{INTERNAL_SERVER_USERNAME}:{INTERNAL_SERVER_PASSWORD}'
        b64_credentials = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')
        request.add_header('Authorization', f'Basic {b64_credentials}')


def getUrl_multiTry(url, cdn_token=''):
    """
        check url response to make sure url is valid
    """
    maxTryNum = 10
    file = None
    for tries in range(maxTryNum):
        try:
            req = urllib.Request(url)
            add_headers(req, cdn_token)
            file = urllib.urlopen(req, context=SSL_CONTEXT)
            break
        except:
            if tries < (maxTryNum - 1):
                continue
            else:
                LOGGER_ERROR(f'''Has tried {maxTryNum} times to access url {url}, all failed!''')
                return 0, None
    if file:
        return 1, file
    return 0, file


def delete_invalid_local_file(local_file):
    """
    check & delete 0 kb file generated by previous error job
    """
    LOGGER_INFO(f'Check {local_file}')
    if os.path.isfile(local_file):
        if os.path.getsize(local_file) == 0:
            LOGGER_WARNING('0 KB install file found...deleting...')
            os.remove(local_file)
            LOGGER_ERROR('invalid file finished')


def ensure_tqdm_available():
    """
    Ensure tqdm is available for progress bar display
    """
    try:
        import tqdm
        return True
    except ImportError:
        try:
            LOGGER_INFO("Installing tqdm for progress bar support...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "tqdm"], 
                                stdout=subprocess.DEVNULL, 
                                stderr=subprocess.DEVNULL)
            import tqdm
            LOGGER_INFO("tqdm installed successfully")
            return True
        except Exception as e:
            LOGGER_WARNING(f"Could not install tqdm: {e}")
            return False

def download_with_curl(url, download_to, cdn_token='', max_retries=3, resume=True):
    """
    Download using curl with tqdm progress bar and resume support
    """
    try:
        # Check and install tqdm if needed
        has_tqdm = ensure_tqdm_available()
        
        cmd = ['curl']
        
        # Use silent mode and show progress to stderr for parsing
        cmd.extend(['--silent', '--show-error'])
        cmd.extend(['--write-out', '%{size_download}\\n%{size_total}\\n'])
        
        # Add resume support
        if resume and os.path.exists(download_to):
            cmd.extend(['-C', '-'])  # Continue from where it left off
            LOGGER_INFO(f"Resuming download with curl from {os.path.getsize(download_to)} bytes")
        
        # Add retry support
        cmd.extend(['--retry', str(max_retries)])
        cmd.extend(['--retry-delay', '2'])
        cmd.extend(['--retry-max-time', '300'])  # 5 minutes max retry time
        
        # Add SSL and connection options
        cmd.extend(['--location'])  # Follow redirects
        cmd.extend(['--fail'])      # Fail fast on HTTP errors
        
        # Add Basic Auth for internal server
        if 'dlwebex.jabberqa.cisco.com' in url or 'sym.jabberqa.cisco.com' in url:
            cmd.extend(['-u', f'{INTERNAL_SERVER_USERNAME}:{INTERNAL_SERVER_PASSWORD}'])
        # Add headers if CDN token provided
        elif cdn_token:
            headers = get_headers(cdn_token)
            for key, value in headers.items():
                cmd.extend(['-H', f'{key}: {value}'])
        
        # Add URL and output
        cmd.extend(['-o', download_to, url])
        
        LOGGER_INFO(f"Downloading with curl (tqdm progress)...")
        LOGGER_DEBUG(f"Curl command: {' '.join(cmd[:-1])} [URL]")
        
        # Get total file size first
        total_size = 0
        try:
            # Get content length
            size_cmd = ['curl', '-sI', url]
            if cdn_token:
                headers = get_headers(cdn_token)
                for key, value in headers.items():
                    size_cmd.extend(['-H', f'{key}: {value}'])
            
            result = subprocess.run(size_cmd, capture_output=True, text=True)
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if line.lower().startswith('content-length:'):
                        total_size = int(line.split(':')[1].strip())
                        break
        except Exception as e:
            LOGGER_DEBUG(f"Could not get file size: {e}")
        
        # Initialize progress bar
        if has_tqdm:
            from tqdm import tqdm
            initial_size = os.path.getsize(download_to) if (resume and os.path.exists(download_to)) else 0
            progress_bar = tqdm(
                total=total_size if total_size > 0 else None,
                initial=initial_size,
                unit='B',
                unit_scale=True,
                unit_divisor=1024,
                desc="Downloading"
            )
        
        # Run curl with real-time progress monitoring
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Monitor file size for progress
        last_size = initial_size if resume and os.path.exists(download_to) else 0
        
        while process.poll() is None:
            if os.path.exists(download_to):
                current_size = os.path.getsize(download_to)
                if current_size > last_size and has_tqdm:
                    progress_bar.update(current_size - last_size)
                    last_size = current_size
            time.sleep(0.1)  # Update every 100ms
        
        # Final update
        if os.path.exists(download_to) and has_tqdm:
            final_size = os.path.getsize(download_to)
            if final_size > last_size:
                progress_bar.update(final_size - last_size)
        
        if has_tqdm:
            progress_bar.close()
        
        # Check result
        return_code = process.returncode
        if return_code == 0:
            LOGGER_INFO("✅ Download completed successfully with curl", color='GREEN')
            return True
        else:
            LOGGER_WARNING(f"❌ Curl download failed with exit code: {return_code}")
            return False
            
    except FileNotFoundError:
        LOGGER_WARNING("❌ curl command not found")
        return False
    except Exception as e:
        LOGGER_WARNING(f"❌ Error running curl: {e}")
        return False

def download_file(url, download_to, cdn_token='', max_retries=3, resume=True):
    """
    Simplified download function: Try curl first, fallback to Python implementation
    
    Strategy:
    1. curl (Windows 11 built-in, should always work)
    2. Python urllib implementation (fallback)
    
    Args:
        url: Download URL
        download_to: Local file path
        cdn_token: CDN authentication token
        max_retries: Maximum retry attempts
        resume: Enable resume download from interruption
    
    Returns:
        bool: True if download successful, False otherwise
    """
    LOGGER_INFO(f'Starting download to: {download_to}')
    
    # Check file size first (for Webex specific validation)
    try:
        req = urllib.Request(url)
        req.get_method = lambda: 'HEAD'
        add_headers(req, cdn_token)
        add_internal_auth(req, url)
        with urllib.urlopen(req, context=SSL_CONTEXT) as response:
            total_size = int(response.headers.get('content-length', 0))
            if total_size > 0:
                filesize_MB = total_size / 1024 / 1024
                LOGGER_DEBUG(f'File size: {filesize_MB:.2f} MB')
                
                # Webex specific size check
                if "-Webex" in url and filesize_MB < 150:
                    LOGGER_ERROR("Installation package size is incorrect, please specify another version")
                    return False
    except Exception as e:
        LOGGER_WARNING(f"Could not determine file size: {e}")
    
    # Strategy 1: Try curl first (Windows 11 built-in)
    LOGGER_DEBUG("Trying curl download...")
    if download_with_curl(url, download_to, cdn_token, max_retries, resume):
        return True
    
    LOGGER_WARNING("Curl download failed, falling back to Python implementation")
    
    # Strategy 2: Fallback to Python implementation
    LOGGER_INFO("Using Python urllib implementation")
    return download_file_python(url, download_to, cdn_token, max_retries, resume)


def download_file_python(url, download_to, cdn_token='', max_retries=3, resume=True):
    """
    Python urllib implementation with resume support, retry mechanism and progress bar
    
    Args:
        url: Download URL
        download_to: Local file path
        cdn_token: CDN authentication token
        max_retries: Maximum retry attempts
        resume: Enable resume download from interruption
    
    Returns:
        bool: True if download successful, False otherwise
    """
    import sys
    
    # Check and install tqdm if needed
    has_tqdm = ensure_tqdm_available()
    if has_tqdm:
        from tqdm import tqdm

    # Check if file partially exists and resume is enabled
    resume_pos = 0
    if resume and os.path.exists(download_to):
        resume_pos = os.path.getsize(download_to)
        LOGGER_INFO(f"Resuming Python download from {resume_pos} bytes")

    # Get total file size first
    try:
        req = urllib.Request(url)
        req.get_method = lambda: 'HEAD'
        add_headers(req, cdn_token)
        add_internal_auth(req, url)
        with urllib.urlopen(req, context=SSL_CONTEXT) as response:
            total_size = int(response.headers.get('content-length', 0))
            if total_size == 0:
                LOGGER_ERROR("Could not determine file size")
                return False
    except Exception as e:
        LOGGER_ERROR(f"Failed to get file info: {e}")
        return False

    # Check if file is already complete
    if resume_pos >= total_size:
        LOGGER_INFO("File already complete, skipping download")
        return True

    LOGGER_INFO(f'Using Python urllib for download')
    
    for attempt in range(max_retries + 1):
        try:
            # Setup request with resume support
            req = urllib.Request(url)
            add_headers(req, cdn_token)
            add_internal_auth(req, url)  # Add Basic Auth for internal servers
            
            if resume_pos > 0:
                req.add_header('Range', f'bytes={resume_pos}-')
                LOGGER_DEBUG(f"Requesting bytes from {resume_pos}")

            start_time = time.time()
            response = urllib.urlopen(req, context=SSL_CONTEXT)
            
            # Check if server supports resume
            if resume_pos > 0 and response.getcode() not in [206, 200]:
                LOGGER_WARNING("Server doesn't support resume, starting from beginning")
                resume_pos = 0
                req = urllib.Request(url)
                add_headers(req, cdn_token)
                add_internal_auth(req, url)  # Add Basic Auth for internal servers
                response = urllib.urlopen(req, context=SSL_CONTEXT)

            # Open file for writing (append mode if resuming)
            file_mode = 'ab' if resume_pos > 0 else 'wb'
            
            # Setup progress tracking
            chunk_size = 8192  # 8KB chunks for better responsiveness
            downloaded = resume_pos
            
            # Initialize progress bar
            if has_tqdm:
                progress_bar = tqdm(
                    total=total_size,
                    initial=resume_pos,
                    unit='B',
                    unit_scale=True,
                    unit_divisor=1024,
                    desc="Downloading"
                )
            else:
                last_progress = 0

            with open(download_to, file_mode) as out_file:
                while True:
                    try:
                        chunk = response.read(chunk_size)
                        if not chunk:
                            break
                        
                        out_file.write(chunk)
                        downloaded += len(chunk)
                        
                        # Update progress
                        if has_tqdm:
                            progress_bar.update(len(chunk))
                        else:
                            # Basic progress display (every 5%)
                            progress = (downloaded / total_size) * 100
                            if progress - last_progress >= 5:
                                LOGGER_INFO(f'Download progress: {progress:.1f}% ({downloaded}/{total_size} bytes)')
                                last_progress = progress
                                
                    except Exception as e:
                        LOGGER_WARNING(f"Download interruption: {e}")
                        break

            if has_tqdm:
                progress_bar.close()

            # Check if download completed successfully
            end_time = time.time()
            if downloaded >= total_size:
                LOGGER_INFO(f'Python download completed successfully in {end_time - start_time:.2f} seconds', color='GREEN')
                return True
            else:
                LOGGER_WARNING(f'Download incomplete: {downloaded}/{total_size} bytes')
                if attempt < max_retries:
                    LOGGER_INFO(f'Retrying download (attempt {attempt + 2}/{max_retries + 1})...')
                    resume_pos = downloaded
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue
                else:
                    LOGGER_ERROR(f'Python download failed after {max_retries + 1} attempts')
                    return False

        except Exception as e:
            LOGGER_ERROR(f'Python download error (attempt {attempt + 1}): {e}')
            if attempt < max_retries:
                LOGGER_INFO(f'Retrying in {2 ** attempt} seconds...')
                time.sleep(2 ** attempt)
                continue
            else:
                LOGGER_ERROR(f'Python download failed permanently after {max_retries + 1} attempts')
                return False

    return False


def prepare_test_build(platform):
    """
        kill process then to install new build
    """
    if platform == PLATFORM_WIN:
        kill_process_cmd = r'taskkill /im "CiscoCollabHost.exe" /f >nul 2>&1'
        try:
            LOGGER_DEBUG(f"[killing Webex App processes to prepare for new build] {kill_process_cmd}")
            subprocess.check_call(kill_process_cmd, shell=True)
            LOGGER_DEBUG("Successfully killed CiscoCollabHost.exe process for new build")
        except subprocess.CalledProcessError as e:
            LOGGER_DEBUG(f"CiscoCollabHost.exe process not found or already closed for new build (exit code: {e.returncode})")
        except Exception as e:
            LOGGER_DEBUG(f"Error killing process for new build: {e}")
    else:
        kill_process(platform)


def get_uninstall_string():
    uninstall_string = ''
    current_user_reg = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
    uninstall_key = winreg.OpenKey(current_user_reg, r'SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall')
    for i in range(1024):
        try:
            subkey = winreg.EnumKey(uninstall_key, i)
            if subkey == 'CiscoWebex':
                ciscowebex_key = winreg.OpenKey(uninstall_key, subkey)
                uninstall_string = winreg.QueryValueEx(ciscowebex_key, "UninstallString")[0]
                break
        except EnvironmentError:
            break
    return uninstall_string


def has_program(program):
    cmd = "where" if sys.platform.startswith('win') else "which"
    result = False
    try: 
        rc = subprocess.call([cmd, program], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        # logging.info('has_program rc: %d' % rc)
        if rc == 0:
            result = True
    except:
        LOGGER_INFO(f"No program {program}")

    LOGGER_DEBUG(f'is program {program} existed: {result!r}')

    return result


def run_powershell_command(cmd):
    completed = subprocess.run(["powershell", "-Command", cmd], capture_output=True)
    return completed


def uninstall_app_with_powershell(app):
    cmd = '$MyApp = Get-WmiObject -Class Win32_Product | Where-Object{$_.Name -eq "%s"}; $MyApp.Uninstall()' % app
    run_powershell_command(cmd)


def _run_with_spinner(cmd, description="Uninstalling Webex", shell=True, timeout=300):
    """
    Run a subprocess command while showing an animated spinner with elapsed time.
    Raises subprocess.CalledProcessError if the command returns a non-zero exit code.
    """
    spinner_frames = ['|', '/', '-', '\\']
    done_event = threading.Event()
    returncode_holder = [0]

    def _worker():
        proc = subprocess.run(cmd, shell=shell, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        returncode_holder[0] = proc.returncode
        done_event.set()

    worker = threading.Thread(target=_worker, daemon=True)
    worker.start()

    start = time.time()
    for frame in itertools.cycle(spinner_frames):
        elapsed = int(time.time() - start)
        sys.stderr.write(f'\r  [INFO]  {frame} {description}... {elapsed}s elapsed')
        sys.stderr.flush()
        if done_event.wait(timeout=0.2):
            break
        if elapsed >= timeout:
            sys.stderr.write(f'\r  [INFO]  ! {description} timed out after {timeout}s\n')
            sys.stderr.flush()
            break

    sys.stderr.write(f'\r  [INFO]  {description} completed in {int(time.time() - start)}s.     \n')
    sys.stderr.flush()
    worker.join(timeout=5)

    if returncode_holder[0] != 0:
        raise subprocess.CalledProcessError(returncode_holder[0], cmd)


def win_uninstall_app():
    """
        uninstall app for windows platform if eft build or lower version is requested
    """
    kill_process_cmd = r'taskkill /im "CiscoCollabHost.exe" /f'
    try:
        subprocess.check_call(kill_process_cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except:
        pass

    uninstall_string = get_uninstall_string()
    if uninstall_string:
        cmd = uninstall_string
        LOGGER_DEBUG(f"uninstall cmd: {cmd}")
        _run_with_spinner(cmd, description="Uninstalling Webex (silent installer)")
    elif has_program('wmic'):
        cmd = r'wmic product where name="Webex" call uninstall'
        LOGGER_DEBUG(f"uninstall cmd: {cmd}")
        _run_with_spinner(cmd, description="Uninstalling Webex (wmic)")
    elif has_program('powershell'):
        cmd = 'powershell -Command "$MyApp = Get-WmiObject -Class Win32_Product | Where-Object{$_.Name -eq \'Webex\'}; if ($MyApp) { $MyApp.Uninstall() } else { Write-Host \'Webex not found\' }"'
        LOGGER_DEBUG(f"uninstall cmd: {cmd}")
        _run_with_spinner(cmd, description="Uninstalling Webex (powershell)")
    else:
        LOGGER_ERROR("failed to uninstall Webex")

def delete_downloaded_file(local_file):
    """
        delete downloaded installation file
    """
    if os.path.isfile(local_file):
        os.remove(local_file)
        LOGGER_INFO(f'deleted downloaded installation file: {local_file}')


def cleanup_older_versions(download_folder, current_version, platform, qtversion, arch, http2, chip_info):
    """
    Clean up older version installation packages in the download folder.
    Keep only the current version and remove all older versions.
    
    Args:
        download_folder (str): Path to the download folder
        current_version (str): Current version to keep (e.g., "45.10.0.32939")
        platform, qtversion, arch, http2, chip_info: Platform parameters for filename matching
    """
    try:
        import glob
        import re
        
        # Get the file pattern based on platform
        if platform == PLATFORM_WIN:
            if qtversion == '5':
                pattern = 'Webex-qt5-{arch}-*.msi'.format(arch=arch)
                version_regex = r'Webex-qt5-{arch}-(.+?)\.msi'.format(arch=re.escape(arch))
            else:
                pattern = 'Webex-{arch}-*.msi'.format(arch=arch)
                version_regex = r'Webex-{arch}-(.+?)\.msi'.format(arch=re.escape(arch))
        elif platform == PLATFORM_MAC:
            mac_arch = 'arm64' if chip_info == 'apple' else 'x64'
            if http2:
                pattern = 'Webex-{arch}-*.dmg'.format(arch=mac_arch)
                version_regex = r'Webex-{arch}-(.+?)\.dmg'.format(arch=re.escape(mac_arch))
            else:
                pattern = 'Webex-nonhttp2-{arch}-*.dmg'.format(arch=mac_arch)
                version_regex = r'Webex-nonhttp2-{arch}-(.+?)\.dmg'.format(arch=re.escape(mac_arch))
        else:
            # For Linux platforms, implement if needed
            return
        
        # Find all matching files in download folder
        search_pattern = os.path.join(download_folder, pattern)
        found_files = glob.glob(search_pattern)
        
        if not found_files:
            LOGGER_INFO("No existing Webex installation packages found for cleanup")
            return
        
        # Extract versions and compare
        files_to_delete = []
        for file_path in found_files:
            filename = os.path.basename(file_path)
            match = re.search(version_regex, filename)
            if match:
                file_version = match.group(1)
                try:
                    # Check if this is a special version (contains non-numeric characters after version)
                    # e.g., "45.10.0.32927_fr_issue_vbg" - these should be preserved
                    has_special_suffix = re.search(r'[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+[^0-9.]', file_version)
                    if has_special_suffix:
                        LOGGER_INFO(f"Preserving special version: {filename}")
                        continue
                    
                    # Clean version string - extract only numeric version part
                    # e.g., "45.10.0.32927" -> "45.10.0.32927"
                    clean_version = re.sub(r'[^0-9.].*$', '', file_version)
                    clean_current = re.sub(r'[^0-9.].*$', '', current_version)
                    
                    # Skip if version strings are empty after cleaning
                    if not clean_version or not clean_current:
                        LOGGER_WARNING(f"Skipping file with invalid version format: {filename}")
                        continue
                    
                    # Compare versions - delete if older than current
                    if versiontuple(clean_version) < versiontuple(clean_current):
                        files_to_delete.append((file_path, file_version))
                        # Also delete associated .size.txt file if exists
                        size_file = file_path + ".size.txt"
                        if os.path.exists(size_file):
                            files_to_delete.append((size_file, file_version))
                except ValueError as e:
                    # Skip files with invalid version format
                    LOGGER_WARNING(f"Skipping file with invalid version format: {filename} - {str(e)}")
                    continue
        
        # Delete older versions
        if files_to_delete:
            LOGGER_DEBUG(f"Cleaning up {len(files_to_delete)} older version files...")
            for file_path, file_version in files_to_delete:
                try:
                    os.remove(file_path)
                    LOGGER_INFO(f"Deleted older version file: {os.path.basename(file_path)} (v{file_version})")
                except Exception as e:
                    LOGGER_WARNING(f"Failed to delete {file_path}: {str(e)}")
        else:
            LOGGER_INFO("No older version files found for cleanup")
            
    except Exception as e:
        LOGGER_WARNING(f"Error during cleanup of older versions: {str(e)}")


def cleanup_all_versions(download_folder, platform, qtversion, arch, http2, chip_info):
    """
    Clean up all version installation packages in the download folder.
    Remove all Webex installation packages regardless of version.
    
    Args:
        download_folder (str): Path to the download folder
        platform, qtversion, arch, http2, chip_info: Platform parameters for filename matching
    """
    try:
        import glob
        
        # Get the file pattern based on platform
        if platform == PLATFORM_WIN:
            if qtversion == '5':
                pattern = 'Webex-qt5-{arch}-*.msi'.format(arch=arch)
            else:
                pattern = 'Webex-{arch}-*.msi'.format(arch=arch)
        elif platform == PLATFORM_MAC:
            mac_arch = 'arm64' if chip_info == 'apple' else 'x64'
            if http2:
                pattern = 'Webex-{arch}-*.dmg'.format(arch=mac_arch)
            else:
                pattern = 'Webex-nonhttp2-{arch}-*.dmg'.format(arch=mac_arch)
        else:
            # For Linux platforms, implement if needed
            return
        
        # Find all matching files in download folder
        search_pattern = os.path.join(download_folder, pattern)
        found_files = glob.glob(search_pattern)
        
        if not found_files:
            LOGGER_INFO("No Webex installation packages found for cleanup")
            return
        
        # Delete all files
        files_to_delete = []
        for file_path in found_files:
            files_to_delete.append(file_path)
            # Also add associated .size.txt file if exists
            size_file = file_path + ".size.txt"
            if os.path.exists(size_file):
                files_to_delete.append(size_file)
        
        if files_to_delete:
            LOGGER_DEBUG(f"Cleaning up all {len(files_to_delete)} installation package files...")
            for file_path in files_to_delete:
                try:
                    os.remove(file_path)
                    LOGGER_INFO(f"Deleted installation file: {os.path.basename(file_path)}")
                except Exception as e:
                    LOGGER_WARNING(f"Failed to delete {file_path}: {str(e)}")
        else:
            LOGGER_INFO("No installation package files found for cleanup")
            
    except Exception as e:
        LOGGER_WARNING(f"Error during cleanup of all versions: {str(e)}")


def install_app(platform):
    """
        install webex app based on platform
    """
    if platform == 'mac':
        LOGGER_INFO("installing Webex...")
        # attach webex app
        cmd = 'hdiutil attach  {build} -nobrowse | grep Volumes'.format(
            build=LOCAL_APP_PATH)
        try:
            Volumesinfo = subprocess.check_output(cmd, shell=True)
            Webexapp_path = Volumesinfo.decode(
                "utf-8").split("\t")[-1].split("\n")[0]
        except:
            LOGGER_ERROR(
                "Webex installation package corrupted, please download again")
            exit(1)

        # delete previous app
        try:
            subprocess.check_call('rm -rf /Applications/Webex.app', shell=True)
        except subprocess.CalledProcessError:
            LOGGER_INFO(f'Please enter your password and press the Enter key to continue.')
            subprocess.check_call('sudo rm -rf /Applications/Webex.app', shell=True)

        # copy webex app to applications
        cpcmd = r'cp -R "{apath}/Webex.app" /Applications'.format(
            apath=Webexapp_path)
        subprocess.check_call(cpcmd, shell=True)
        # eject disk
        ejectcmd = r'hdiutil unmount "{path}"'.format(path=Webexapp_path)
        subprocess.check_call(ejectcmd, shell=True)
    elif platform == PLATFORM_WIN:
        cmd = 'msiexec /i "{build}" /qr'.format(build=LOCAL_APP_PATH)
        # LOGGER_INFO(cmd)
        subprocess.check_call(cmd, shell=True)
    elif platform == PLATFORM_UBUNTU_1804 or platform == PLATFORM_UBUNTU_2004:
        LOGGER_INFO("Please enter your password and press the Enter key to continue.")
        subprocess.check_call('sudo apt install "{build}"'.format(build=LOCAL_APP_PATH), shell=True)
    elif platform == PLATFORM_CENTOS:
        LOGGER_INFO("Please enter your password and press the Enter key to continue.")
        subprocess.check_call('sudo dnf install "{build}"'.format(build=LOCAL_APP_PATH), shell=True)


def launch_app(platform, language="en_US"):
    """
        launch webex app
    """
    if platform == PLATFORM_MAC:
        # cmd = 'open -a webex.app '
        cmd = 'open -a "Webex.app" --args --lang={lang}'.format(lang=language)
        LOGGER_INFO("please wait, launching webex app")
        subprocess.run(cmd, check=True,shell=True,timeout=15)
        time.sleep(5)
    elif platform == PLATFORM_WIN:
        exe_path = get_windows_webex_exe_path()
        system_language, _ = locale.getdefaultlocale()
        if language == 'en_US':
            language = system_language
        cmd = f'"{exe_path}" /Language={language}'
        LOGGER_INFO(f"[launching webex app] {cmd}")
        subprocess.check_call(cmd, shell=True)
    elif platform == PLATFORM_UBUNTU_2004 or platform == PLATFORM_UBUNTU_1804 or platform == PLATFORM_CENTOS:
        cmd = '/opt/Webex/bin/CiscoCollabHost'
        LOGGER_INFO("please wait, launching webex app")
        subprocess.check_call(cmd, shell=True)

def launch_app_to_top(platform):
    """
        launch webex app
    """
    if platform == 'mac':
        # cmd = 'open -a webex.app '
        cmd = 'open -a "Webex.app"'
        LOGGER_INFO("please wait, launching webex app")
        subprocess.check_call(cmd, shell=True)
    elif platform == 'windows':
        exe_path = get_windows_webex_exe_path()
        subprocess.Popen(exe_path, shell=True, creationflags=subprocess.CREATE_NEW_CONSOLE)

def get_process(platform):
    """
        get webex process info, return related pid
    """
    # LOGGER_INFO("finding webex processes")
    res = []
    if platform == PLATFORM_WIN:
        for p in psutil.process_iter(attrs=['name', 'username']):
            if p.info['name'] == 'CiscoCollabHost.exe':
                res.append(p)
    elif platform == PLATFORM_MAC:
        cmd = 'ps ax | grep "{}" | grep -v grep'.format('Webex')
        for p in os.popen(cmd):
            if 'Webex Teams' in p or 'Webex.app' in p:
                res.append(p.split()[0])
    elif platform == PLATFORM_UBUNTU_2004 or platform == PLATFORM_UBUNTU_1804 or platform == PLATFORM_CENTOS:
        cmd = 'ps ax | grep "{}" | grep -v grep'.format('CiscoCollabHost')
        for p in os.popen(cmd):
            res.append(p.split()[0])
    # LOGGER_INFO(res)
    # logging.info(res)
    return res

def get_pids():
    """
        returns a list of process IDs for the main processes
    """
    all_pids = set()
    main_processes = get_process(current_platform())
    for proc in main_processes:
        try:
            all_pids.add(proc.pid)
            children = proc.children(recursive=True)
            for child in children:
                all_pids.add(child.pid)
        except Exception:
            continue
    return list(all_pids)

def kill_process(platform):
    """
        kill all webex processes
    """
    if platform == PLATFORM_WIN:
        proc = get_process(platform)
        if len(proc) != 0:
            # LOGGER_INFO('Try to kill existing {}'.format('CiscoCollabHost.exe'))
            for pid in proc:
                try:
                    pid.kill()
                    time.sleep(2)
                except:
                    # LOGGER_INFO('Process {} killed'.format('CiscoCollabHost.exe'))
                    break
            LOGGER_INFO('Webex App is killed')
            time.sleep(1)
        else:
            LOGGER_WARNING('Webex App is not running')
    elif platform == PLATFORM_MAC:
        proc = get_process(platform)
        if len(proc) != 0:
            # LOGGER_INFO('Try to kill existing {}'.format('Webex'))
            for pid in proc:
                try:
                    cmd = r'kill -9 ' + pid
                    # logging.info(cmd)
                    subprocess.check_call(cmd, shell=True)
                    time.sleep(2)
                except:
                    # LOGGER_INFO('Process {} killed'.format('Webex'))
                    break
            LOGGER_INFO('Webex App is killed')
            time.sleep(1)
        else:
            LOGGER_WARNING('Webex App is not running')
    else:
        try:
            cmd = r'killall -9 CiscoCollabHost'
            # logging.info(cmd)
            subprocess.check_call(cmd, shell=True)
        except:
            # logging.info('failed to kill webex')
            pass


def versiontuple(v):
    return tuple(map(int, (v.split("."))))


def get_branch(version):
    version_numbers = version.split('.')
    return '.'.join([version_numbers[0], version_numbers[1]])


class ShanghaiBuildsSource:
    SOURCE_URL = r'https://dlwebex.jabberqa.cisco.com/'

    def __init__(self, qtversion, arch, http2):
        self.qtversion = qtversion
        self.arch = arch
        self.http2 = http2
        # Create session with basic auth for internal server
        self.session = requests.Session()
        self.session.auth = HTTPBasicAuth(INTERNAL_SERVER_USERNAME, INTERNAL_SERVER_PASSWORD)
        # Disable SSL verification for internal server to avoid certificate issues on Windows
        self.session.verify = False

    def get_mainbranch_builds_url(self, platform, chip_info):
        mainbranch_builds_url = ''
        if platform == PLATFORM_WIN:
            if self.qtversion == '5':
                mainbranch_builds_url = ShanghaiBuildsSource.SOURCE_URL + 'masterbuild/windows/'
            elif self.arch == 'arm64':
                mainbranch_builds_url = ShanghaiBuildsSource.SOURCE_URL + 'masterbuild/windows_arm64/'
            elif self.qtversion == '6.8':
                mainbranch_builds_url = ShanghaiBuildsSource.SOURCE_URL + 'masterbuild/windows_qt6_8/'
            else:
                mainbranch_builds_url = ShanghaiBuildsSource.SOURCE_URL + 'masterbuild/windows_qt6/'
        elif platform == PLATFORM_MAC:
            if chip_info == "apple":
                if self.http2:
                    mainbranch_builds_url = ShanghaiBuildsSource.SOURCE_URL + 'masterbuild/osx_arm64_http2/'
                else:
                    mainbranch_builds_url = ShanghaiBuildsSource.SOURCE_URL + 'masterbuild/osx_arm64/'
            else:
                if self.http2:
                    mainbranch_builds_url = ShanghaiBuildsSource.SOURCE_URL + 'masterbuild/osx_http2/'
                else:
                    mainbranch_builds_url = ShanghaiBuildsSource.SOURCE_URL + 'masterbuild/mac/'
        elif platform == PLATFORM_UBUNTU_2004:
            mainbranch_builds_url = ShanghaiBuildsSource.SOURCE_URL + 'masterbuild/ubuntu2004/'
        elif platform == PLATFORM_UBUNTU_1804:
            mainbranch_builds_url = ShanghaiBuildsSource.SOURCE_URL + 'masterbuild/ubuntu1804/'
        elif platform == PLATFORM_CENTOS:
            mainbranch_builds_url = ShanghaiBuildsSource.SOURCE_URL + 'masterbuild/centos8/'
        else:
            LOGGER_ERROR('unsupported platform')
        return mainbranch_builds_url

    def get_latest_master_version(self, platform, chip_info):
        """
        get master latest version based on platform from url server
        """
        mainbranch_builds_url = self.get_mainbranch_builds_url(platform, chip_info)
        if not mainbranch_builds_url:
            return ''

        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Use session with basic auth for internal server
                response = self.session.get(mainbranch_builds_url, timeout=10)
                if response.status_code != 200:
                    LOGGER_ERROR(f'Failed to get the latest master builds list: HTTP {response.status_code}')
                    return ''
                break
            except Exception as e:
                if attempt < max_retries - 1:
                    LOGGER_INFO(f'Retry {attempt + 1}/{max_retries} for {mainbranch_builds_url}: {e}')
                    time.sleep(3)
                else:
                    LOGGER_ERROR(f'Failed to open URL after {max_retries} retries: {e}')
                    return ''

        version = ''
        for line in response.text.splitlines():
            try:
                line = str(line)
            except:
                pass
            # <tr><td valign="top"><img src="/icons/unknown.gif" alt="[   ]"></td><td><a href="42.12.0.24167-Webex.msi">42.12.0.24167-Webex.msi</a></td><td align="right">2022-11-02 20:46  </td><td align="right">184M</td><td>&nbsp;</td></tr>
            match_obj = re.search(r'>\d+\.\d+\.\d+\.\d+', line)
            if match_obj:
                if (version == '') or (versiontuple(version) < versiontuple(match_obj.group()[1:])):
                    version = match_obj.group()[1:]
        return version

    def get_eft_builds_url(self, platform, chip_info):
        eft_builds_url = ''
        if platform == PLATFORM_WIN:
            if self.qtversion == '5':
                eft_builds_url = ShanghaiBuildsSource.SOURCE_URL + 'eftbuild/windows/'
            elif self.qtversion == '6.8':
                eft_builds_url = ShanghaiBuildsSource.SOURCE_URL + 'eftbuild/windows_qt6_8/'
            elif self.arch == 'arm64':
                eft_builds_url = ShanghaiBuildsSource.SOURCE_URL + 'eftbuild/windows_arm64/'
            else:
                eft_builds_url = ShanghaiBuildsSource.SOURCE_URL + 'eftbuild/windows_qt6/'
        elif platform == PLATFORM_MAC:
            if chip_info == "apple":
                if self.http2:
                    eft_builds_url = ShanghaiBuildsSource.SOURCE_URL + 'eftbuild/osx_arm64_http2/'
                else:
                    eft_builds_url = ShanghaiBuildsSource.SOURCE_URL + 'eftbuild/osx_arm64/'
            else:
                if self.http2:
                    eft_builds_url = ShanghaiBuildsSource.SOURCE_URL + 'eftbuild/osx_http2/'
                else:
                    eft_builds_url = ShanghaiBuildsSource.SOURCE_URL + 'eftbuild/mac/'
        elif platform == PLATFORM_UBUNTU_2004:
            eft_builds_url = ShanghaiBuildsSource.SOURCE_URL + 'eftbuild/ubuntu2004/'
        elif platform == PLATFORM_UBUNTU_1804:
            eft_builds_url = ShanghaiBuildsSource.SOURCE_URL + 'eftbuild/ubuntu1804/'
        elif platform == PLATFORM_CENTOS:
            eft_builds_url = ShanghaiBuildsSource.SOURCE_URL + 'eftbuild/centos8/'
        else:
            LOGGER_ERROR('unsupported platform')
        return eft_builds_url

    def get_latest_eft_version(self, platform, chip_info):
        """
        get branch latest version based on platform from url server
        """
        eft_builds_url = self.get_eft_builds_url(platform, chip_info)
        LOGGER_INFO(f"eft branch builds url: {eft_builds_url}")

        if not eft_builds_url:
            return ''

        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Use session with basic auth for internal server
                response = self.session.get(eft_builds_url, timeout=10)
                if response.status_code != 200:
                    LOGGER_ERROR(f'Failed to get the latest eft builds list: HTTP {response.status_code}')
                    return ''
                break
            except Exception as e:
                if attempt < max_retries - 1:
                    LOGGER_INFO(f'Retry {attempt + 1}/{max_retries} for {eft_builds_url}: {e}')
                    time.sleep(3)
                else:
                    LOGGER_ERROR(f'Failed to open URL after {max_retries} retries: {e}')
                    return ''

        version = ''
        for line in response.text.splitlines():
            try:
                line = str(line)
            except:
                pass
            # <tr><td valign="top"><img src="/icons/unknown.gif" alt="[   ]"></td><td><a href="42.12.0.24167-Webex.msi">42.12.0.24167-Webex.msi</a></td><td align="right">2022-11-02 20:46  </td><td align="right">184M</td><td>&nbsp;</td></tr>
            match_obj = re.search(r'>\d+\.\d+\.\d+\.\d+', line)
            if match_obj:
                found_version = match_obj.group()[1:]
                # Filter: only consider versions with third component = 0 (X.Y.0.Z)
                version_parts = found_version.split('.')
                if len(version_parts) == 4 and version_parts[2] == '0':
                    if (version == '') or (versiontuple(version) < versiontuple(found_version)):
                        version = found_version
        return version

    def get_content_length_with_auth(self, url):
        """
        Get content length with authentication using session
        """
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.session.head(url, timeout=10)
                if response.status_code == 200:
                    size = int(response.headers.get('content-length', 0))
                    return size
                return 0
            except Exception as e:
                if attempt < max_retries - 1:
                    LOGGER_INFO(f'Retry {attempt + 1}/{max_retries} for HEAD {url}: {e}')
                    time.sleep(3)
                else:
                    if "404" not in str(e):
                        LOGGER_ERROR(f'Failed to get content length after {max_retries} retries: {e}')
                    return 0

    def get_download_url(self, platform, chip_info, version):
        """
        get branch name based on version
        """
        mainbranch_builds_url = self.get_mainbranch_builds_url(platform, chip_info)
        eft_builds_url = self.get_eft_builds_url(platform, chip_info)
        master_build_download_url = ''
        eft_build_download_url = ''
        if platform == PLATFORM_WIN:
            master_build_download_url = mainbranch_builds_url + version + "-Webex.msi"
            eft_build_download_url = eft_builds_url + version + "-Webex.msi"
        elif platform == PLATFORM_MAC:
            master_build_download_url = mainbranch_builds_url + version + "-Webex.dmg"
            eft_build_download_url = eft_builds_url + version + "-Webex.dmg"
        elif platform == PLATFORM_UBUNTU_2004 or platform == PLATFORM_UBUNTU_1804:
            master_build_download_url = mainbranch_builds_url + version + "-Webex.deb"
            eft_build_download_url = eft_builds_url + version + "-Webex.deb"
        elif platform == PLATFORM_CENTOS:
            master_build_download_url = mainbranch_builds_url + version + "-Webex.rpm"
            eft_build_download_url = eft_builds_url + version + "-Webex.rpm"

        LOGGER_DEBUG(f'[main build download url]: {master_build_download_url}')
        LOGGER_DEBUG(f'[eft build download url]: {eft_build_download_url}')
        if self.get_content_length_with_auth(master_build_download_url) > 0:
            return master_build_download_url
        elif self.get_content_length_with_auth(eft_build_download_url) > 0:
            return eft_build_download_url
        else:
            return ""


def get_headers(cdn_token):
    user_agent = '"Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.109 Safari/537.36"'
    headers = {'User-Agent': user_agent}
    if cdn_token:
        headers['Authorization'] = 'Basic ' + b64encode(("prtserver.gen:" + cdn_token).encode('utf-8')).decode('utf-8')
    return headers

def add_headers(request, cdn_token):
    for key, value in get_headers(cdn_token).items():
        request.add_header(key, value)


class GalwayBuildsSource:
    SOURCE_URL = r'https://engci-maven-master.cisco.com/artifactory/webex-client-builds-cdn/webex-apps/'

    def __init__(self, qtversion, arch, cdn_token, http2):
        self.qtversion = qtversion
        self.arch = arch
        self.cdn_token = cdn_token
        self.http2 = http2

    def get_latest_versions_for_all_branches(self, url):
        latest_versions = []
        req = urllib.Request(url)
        add_headers(req, self.cdn_token)
        try:
            page = urllib.urlopen(req, context=SSL_CONTEXT)
        except Exception as e:
            LOGGER_ERROR(f'Failed to open URL: {e}')
            return latest_versions

        if page.getcode() != 200:
            LOGGER_ERROR(f'{url} seems to be invalid')
        else:
            versions = {}
            for line in page.readlines():
                try:
                    line = line.decode('utf-8')
                except:
                    pass
                match_obj = re.search(r'\d+\.\d+\.\d+\.\d+', line)
                if match_obj and '9999.0.0.1' not in match_obj.string:
                    version = match_obj.group()
                    # branch version number, e.g. 41.2
                    branch = get_branch(version)
                    new_version_fund = False
                    if branch in versions:
                        if version > versions[branch]:
                            new_version_fund = True
                    else:
                        new_version_fund = True

                    # if new_version_fund and (get_content_length(url + version + '/' + webex_app_name) > 0):
                    if new_version_fund:
                        versions[branch] = version

            for key, value in versions.items():
                latest_versions.append(value)

            latest_versions.sort(key=versiontuple, reverse=True)

        return latest_versions

    def get_builds_url(self, platform, chip_info):
        builds_url = ''
        if platform == PLATFORM_WIN:
            if self.arch == 'arm64':
                builds_url = GalwayBuildsSource.SOURCE_URL + 'windows/arm64/'
            else:
                builds_url = GalwayBuildsSource.SOURCE_URL + 'windows/x64/'
        elif platform == PLATFORM_MAC:
            if chip_info == "apple":
                builds_url = GalwayBuildsSource.SOURCE_URL + 'macos/arm64/'
            else:
                builds_url = GalwayBuildsSource.SOURCE_URL + 'macos/x86_64/'
        elif platform == PLATFORM_UBUNTU_2004:
            builds_url = GalwayBuildsSource.SOURCE_URL + 'ubuntu2004/amd64/'
        elif platform == PLATFORM_UBUNTU_1804:
            builds_url = GalwayBuildsSource.SOURCE_URL + 'ubuntu1804/amd64/'
        elif platform == PLATFORM_CENTOS:
            builds_url = GalwayBuildsSource.SOURCE_URL + 'centos8/amd64/'
        else:
            LOGGER_ERROR('unsupported platform')
        return builds_url

    def get_latest_version(self, index, platform, chip_info):
        builds_url = self.get_builds_url(platform, chip_info)
        latest_versions = self.get_latest_versions_for_all_branches(
            builds_url)
        if len(latest_versions) > index:
            return latest_versions[index]

    def get_latest_master_version(self, platform, chip_info):
        return self.get_latest_version(0, platform, chip_info)

    def get_latest_eft_version(self, platform, chip_info):
        return self.get_latest_version(1, platform, chip_info)

    def get_download_url(self, platform, chip_info, version):
        """
        get branch name based on version
        """
        download_url = ''
        builds_url = self.get_builds_url(platform, chip_info)
        if platform == PLATFORM_WIN:
            if self.qtversion == '6':
                download_url = builds_url + version + "/Webex.msi"
            else:
                download_url = builds_url + version + "/qt5/Webex.msi"
                if versiontuple(version) < versiontuple("45.2.0.0"):
                    if not uri_exists(download_url, self.cdn_token):
                        download_url = builds_url + version + "/Webex.msi"
        elif platform == PLATFORM_MAC:
            if self.http2:
                download_url = builds_url + version + "/Webex.dmg"
            else:
                download_url = builds_url + version + "/cpprest/Webex.dmg"
                if versiontuple(version) < versiontuple("45.2.0.0"):
                    if not uri_exists(download_url, self.cdn_token):
                        download_url = builds_url + version + "/Webex.dmg"
        elif platform == PLATFORM_UBUNTU_2004 or platform == PLATFORM_UBUNTU_1804:
            download_url = builds_url + version + "/Webex.deb"
        elif platform == PLATFORM_CENTOS:
            download_url = builds_url + version + "/Webex.rpm"

        if get_content_length(download_url, self.cdn_token) > 0:
            return download_url
        else:
            LOGGER_INFO(f'content length is 0 for url: {download_url}')
            return ""

class SymBuildsSource:
    SOURCE_URL = r'http://sym.jabberqa.cisco.com/'

    def __init__(self, qtversion, arch, http2):
        self.qtversion = qtversion
        self.arch = arch
        self.http2 = http2

    def get_mainbranch_builds_url(self, platform, chip_info):
        mainbranch_builds_url = ''
        if platform == PLATFORM_WIN:
            if self.qtversion == '5':
                mainbranch_builds_url = SymBuildsSource.SOURCE_URL + 'masterbuild/windows/'
            elif self.arch == 'arm64':
                mainbranch_builds_url = SymBuildsSource.SOURCE_URL + 'masterbuild/windows_arm64/'
            else:
                mainbranch_builds_url = SymBuildsSource.SOURCE_URL + 'masterbuild/windows_qt6/'
        elif platform == PLATFORM_MAC:
            if chip_info == "apple":
                if self.http2:
                    mainbranch_builds_url = SymBuildsSource.SOURCE_URL + 'masterbuild/osx_arm64_http2/'
                else:
                    mainbranch_builds_url = SymBuildsSource.SOURCE_URL + 'masterbuild/osx_arm64/'
            else:
                if self.http2:
                    mainbranch_builds_url = SymBuildsSource.SOURCE_URL + 'masterbuild/osx_http2/'
                else:
                    mainbranch_builds_url = SymBuildsSource.SOURCE_URL + 'masterbuild/mac/'
        elif platform == PLATFORM_UBUNTU_2004:
            mainbranch_builds_url = SymBuildsSource.SOURCE_URL + 'masterbuild/ubuntu2004/'
        elif platform == PLATFORM_UBUNTU_1804:
            mainbranch_builds_url = SymBuildsSource.SOURCE_URL + 'masterbuild/ubuntu1804/'
        elif platform == PLATFORM_CENTOS:
            mainbranch_builds_url = SymBuildsSource.SOURCE_URL + 'masterbuild/centos8/'
        else:
            LOGGER_ERROR('unsupported platform')
        return mainbranch_builds_url

    def get_latest_master_version(self, platform, chip_info):
        """
        get master latest version based on platform from url server
        """
        mainbranch_builds_url = self.get_mainbranch_builds_url(platform, chip_info)
        LOGGER_INFO(f"main branch builds url: {mainbranch_builds_url}")
        if not mainbranch_builds_url:
            return ''

        try:
            response = urllib.urlopen(mainbranch_builds_url)
        except Exception as e:
            LOGGER_ERROR(f'Failed to open URL: {e}')
            return ''
        if response.getcode() != 200:
            LOGGER_ERROR('failed to get the latest eft builds list')
            return ''

        version = ''
        for line in response.readlines():
            try:
                line = line.decode('utf-8')
            except:
                pass
            # <tr><td valign="top"><img src="/icons/unknown.gif" alt="[   ]"></td><td><a href="42.12.0.24167-Webex.msi">42.12.0.24167-Webex.msi</a></td><td align="right">2022-11-02 20:46  </td><td align="right">184M</td><td>&nbsp;</td></tr>
            match_obj = re.search(r'>\d+\.\d+\.\d+\.\d+', line)
            if match_obj:
                if (version == '') or (versiontuple(version) < versiontuple(match_obj.group()[1:])):
                    version = match_obj.group()[1:]
        return version

    def get_eft_builds_url(self, platform, chip_info):
        eft_builds_url = ''
        if platform == PLATFORM_WIN:
            if self.qtversion == '5':
                eft_builds_url = SymBuildsSource.SOURCE_URL + 'eftbuild/windows/'
            elif self.arch == 'arm64':
                eft_builds_url = SymBuildsSource.SOURCE_URL + 'eftbuild/windows_arm64/'
            else:
                eft_builds_url = SymBuildsSource.SOURCE_URL + 'eftbuild/windows_qt6/'
        elif platform == PLATFORM_MAC:
            if chip_info == "apple":
                if self.http2:
                    eft_builds_url = SymBuildsSource.SOURCE_URL + 'eftbuild/osx_arm64_http2/'
                else:
                    eft_builds_url = SymBuildsSource.SOURCE_URL + 'eftbuild/osx_arm64/'
            else:
                if self.http2:
                    eft_builds_url = SymBuildsSource.SOURCE_URL + 'eftbuild/osx_http2/'
                else:
                    eft_builds_url = SymBuildsSource.SOURCE_URL + 'eftbuild/mac/'
        elif platform == PLATFORM_UBUNTU_2004:
            eft_builds_url = SymBuildsSource.SOURCE_URL + 'eftbuild/ubuntu2004/'
        elif platform == PLATFORM_UBUNTU_1804:
            eft_builds_url = SymBuildsSource.SOURCE_URL + 'eftbuild/ubuntu1804/'
        elif platform == PLATFORM_CENTOS:
            eft_builds_url = SymBuildsSource.SOURCE_URL + 'eftbuild/centos8/'
        else:
            LOGGER_ERROR('unsupported platform')
        return eft_builds_url

    def get_latest_eft_version(self, platform, chip_info):
        """
        get branch latest version based on platform from url server
        """
        eft_builds_url = self.get_eft_builds_url(platform, chip_info)
        LOGGER_INFO(f"eft branch builds url: {eft_builds_url}")

        if not eft_builds_url:
            return ''

        try:
            response = urllib.urlopen(eft_builds_url)
        except Exception as e:
            LOGGER_ERROR(f'Failed to open URL: {e}')
            return ''

        if response.getcode() != 200:
            LOGGER_ERROR('failed to get the latest eft builds list')
            return ''

        version = ''
        for line in response.readlines():
            try:
                line = line.decode('utf-8')
            except:
                pass
            # <tr><td valign="top"><img src="/icons/unknown.gif" alt="[   ]"></td><td><a href="42.12.0.24167-Webex.msi">42.12.0.24167-Webex.msi</a></td><td align="right">2022-11-02 20:46  </td><td align="right">184M</td><td>&nbsp;</td></tr>
            match_obj = re.search(r'>\d+\.\d+\.\d+\.\d+', line)
            if match_obj:
                if (version == '') or (versiontuple(version) < versiontuple(match_obj.group()[1:])):
                    version = match_obj.group()[1:]
        return version

    def get_download_url(self, platform, chip_info, version):
        """
        get branch name based on version
        """
        mainbranch_builds_url = self.get_mainbranch_builds_url(platform, chip_info)
        eft_builds_url = self.get_eft_builds_url(platform, chip_info)
        master_build_download_url = ''
        eft_build_download_url = ''
        if platform == PLATFORM_WIN:
            master_build_download_url = mainbranch_builds_url + version + "-Webex.msi"
            eft_build_download_url = eft_builds_url + version + "-Webex.msi"
        elif platform == PLATFORM_MAC:
            master_build_download_url = mainbranch_builds_url + version + "-Webex.dmg"
            eft_build_download_url = eft_builds_url + version + "-Webex.dmg"
        elif platform == PLATFORM_UBUNTU_2004 or platform == PLATFORM_UBUNTU_1804:
            master_build_download_url = mainbranch_builds_url + version + "-Webex.deb"
            eft_build_download_url = eft_builds_url + version + "-Webex.deb"
        elif platform == PLATFORM_CENTOS:
            master_build_download_url = mainbranch_builds_url + version + "-Webex.rpm"
            eft_build_download_url = eft_builds_url + version + "-Webex.rpm"

        LOGGER_INFO(f'master build download url: {master_build_download_url}')
        LOGGER_INFO(f'eft build download url: {eft_build_download_url}')
        if get_content_length(master_build_download_url) > 0:
            return master_build_download_url
        elif get_content_length(eft_build_download_url) > 0:
            return eft_build_download_url
        else:
            return ""


def get_headers(cdn_token):
    user_agent = '"Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.109 Safari/537.36"'
    headers = {'User-Agent': user_agent}
    if cdn_token:
        headers['Authorization'] = 'Basic ' + b64encode(("prtserver.gen:" + cdn_token).encode('utf-8')).decode('utf-8')
    return headers

def add_headers(request, cdn_token):
    for key, value in get_headers(cdn_token).items():
        request.add_header(key, value)


def get_content_length(url, cdn_token=''):
    try:
        req = urllib.Request(url)
        req.get_method = lambda: 'HEAD'
        add_headers(req, cdn_token)
        response = urllib.urlopen(req, context=SSL_CONTEXT)
        size = int(response.headers.get('content-length', 0))
        # logging.info("content length: %dMB, content url: %s", size / 1024 / 1024, url)
        return size
    except Exception as e:
        if "404" not in str(e):
            LOGGER_ERROR(f'Failed to open URL: {e}')
        return 0


def uri_exists(uri, cdn_token):
    try:
        req = urllib.Request(uri)
        req.get_method = lambda: 'HEAD'
        add_headers(req, cdn_token)
        response = urllib.urlopen(req, context=SSL_CONTEXT)
        exists = response.getcode() == 200
        if exists:
            LOGGER_INFO(f'uri exists: {uri}')
        else:
            LOGGER_INFO(f'uri does not exist: {uri}')
        return exists
    except Exception as e:
        LOGGER_INFO(f'uri does not exist: {uri}')
        LOGGER_ERROR(f'{e}')
        return False


def get_mac_autoupgrade_path(chip_info):
    path = os.path.join(os.path.expanduser(
        '~'), 'Library/Application Support/Cisco Spark')
    if chip_info == "apple":
        auto_upgrade_path = os.path.join(path, 'Webexteams_upgrades_arm')
    else:
        auto_upgrade_path = os.path.join(path, 'Webexteams_upgrades')
    return auto_upgrade_path


def get_linux_autoupgrade_path():
    path = os.path.join(os.path.expanduser(
        '~'), '.local/share/WebexLauncher')
    return path


def get_mac_autoupgrade_version(chip_info):
    webex_curver = "0"
    auto_upgrade_path = get_mac_autoupgrade_path(chip_info)
    if os.path.exists(auto_upgrade_path):
        files = os.listdir(auto_upgrade_path)
        for line in files:
            match_obj = re.search(r'\d+\.\d+\.\d+\.\d+', line)
            if match_obj:
                if (webex_curver == '0') or (versiontuple(webex_curver) < versiontuple(match_obj.group())):
                    webex_curver = match_obj.group()
    return webex_curver


def get_linux_autoupgrade_version():
    webex_curver = "0"
    auto_upgrade_path = get_linux_autoupgrade_path()
    if os.path.exists(auto_upgrade_path):
        files = os.listdir(auto_upgrade_path)
        for line in files:
            match_obj = re.search(r'\d+\.\d+\.\d+\.\d+', line)
            if match_obj:
                if (webex_curver == '0') or (versiontuple(webex_curver) < versiontuple(match_obj.group())):
                    webex_curver = match_obj.group()
    return webex_curver

def get_win_autoupgrade_version():
    path = os.path.join(os.path.expanduser(
        '~'), 'AppData\\Local\\CiscoSparkLauncher')
    webex_curver = "0"
    if os.path.exists(path):
        try:
            files = os.listdir(path)
        except:
            return webex_curver
        for line in files:
            match_obj = re.search(r'\d+\.\d+\.\d+\.\d+', line)
            if match_obj:
                if (webex_curver == '0') or (versiontuple(webex_curver) < versiontuple(match_obj.group())):
                    webex_curver = match_obj.group()
    return webex_curver


def get_win_version_number(filename):

    info = GetFileVersionInfo(filename, "\\")
    ms = info['FileVersionMS']
    ls = info['FileVersionLS']
    return HIWORD(ms), LOWORD(ms), HIWORD(ls), LOWORD(ls)


def get_webex_localversion(platform, chip_info):
    """
        get installed webex app version on local machine
    """
    upgrade_version = '0'
    webex_curver = "0"
    if platform == PLATFORM_WIN:
        dll_file = get_windows_webex_dll_path()
        if os.path.exists(dll_file):
            webex_curver = ".".join([str(i)
                                    for i in get_win_version_number(dll_file)])
            upgrade_version = get_win_autoupgrade_version()
        else:
            webex_curver = "0"
    elif platform == PLATFORM_MAC:
        cmd = r'/usr/libexec/PlistBuddy -c "print CFBundleShortVersionString" /Applications/Webex.app/Contents/Info.plist'
        for line in os.popen(cmd):
            if "File Doesn't Exist" in line:
                webex_curver = "0"
                return webex_curver
            else:
                webex_curver = line.rstrip('\n')
                upgrade_version = get_mac_autoupgrade_version(chip_info)
    elif platform == PLATFORM_UBUNTU_1804 or platform == PLATFORM_UBUNTU_2004 or platform == PLATFORM_CENTOS:
        cmd = r"awk -F= '/^Version=/ {print $2}' /usr/share/applications/webex.desktop"
        for line in os.popen(cmd):
            if not line:
                webex_curver = "0"
                return webex_curver
            else:
                webex_curver = line
                upgrade_version = get_linux_autoupgrade_version()

    if upgrade_version != "0":
        if int(webex_curver.split('.')[0]) < int(upgrade_version.split('.')[0]):
            webex_curver = upgrade_version
        elif int(webex_curver.split('.')[0]) == int(upgrade_version.split('.')[0]):
            if int(webex_curver.replace(".", "")) < int(upgrade_version.replace(".", "")):
                webex_curver = upgrade_version
    if webex_curver == "0":
        LOGGER_WARNING("Webex app was not installed")
    else:
        LOGGER_INFO(f'the current Webex version is {webex_curver}')

    return webex_curver


def get_file_size(file):
    return 0 if not os.path.isfile(file) else os.path.getsize(file)


def read_file_size_from_txt_file(txt_file):
    if not os.path.isfile(txt_file):
        return 0
    with open(txt_file, 'r') as f:
        lines = f.readlines()
        if len(lines) > 0:
            return int(lines[0].strip())
    return 0


def write_file_size_to_txt_file(txt_file, size):
    with open(txt_file, 'w') as f:
        f.write(str(size))


def prepare_webex_downgrades(platform, chip_info):
    """
         prepare for downgrade
    """
    if platform == PLATFORM_WIN:
        win_uninstall_app()
    elif platform == PLATFORM_MAC:
        path = get_mac_autoupgrade_path(chip_info)
        if os.path.exists(path):
            cmd = "rm -rf " + '"' + path + '"'
            LOGGER_INFO(f'removing auto upgrade folder: {path}')
            subprocess.check_call(cmd, shell=True)
            LOGGER_INFO("removed auto upgrade folder")
    elif platform == PLATFORM_UBUNTU_1804 or platform == PLATFORM_UBUNTU_2004 or platform == PLATFORM_CENTOS:
        path = get_linux_autoupgrade_path()
        if os.path.exists(path):
            cmd = "rm -rf " + '"' + path + '"'
            LOGGER_INFO(f'removing auto upgrade folder: {path}')
            subprocess.check_call(cmd, shell=True)
            LOGGER_INFO("removed auto upgrade folder")

def isActiveProcessSame(platform):
    """
    Check if the currently active application is in the Webex process list.
    """
    webex_processes = get_process(platform)
    if platform == PLATFORM_WIN:
        import win32process
        import win32gui
        hwnd = win32gui.GetForegroundWindow()
        _, active_pid = win32process.GetWindowThreadProcessId(hwnd)
        for p in webex_processes:
            if p.pid == active_pid:
                return True
    elif platform == PLATFORM_MAC:
        active_window_process = os.popen("osascript -e 'tell application \"System Events\" to get unix id of first application process whose frontmost is true'").read().strip()
        for p in webex_processes:
            if active_window_process in p:
                return True
    return False

def findWindowByPid(pid: int):
    hwnds = []
    def enumWindowCallback(hwnd_param, lParam):
        nonlocal hwnds
        window_pid = ctypes.c_ulong()
        user32.GetWindowThreadProcessId(hwnd_param, ctypes.byref(window_pid))
        if window_pid.value == pid:
            LOGGER_DEBUG(f"Found hwnd: {window_pid.value}, hwnd: {hwnd_param}, pid: {pid}")
            hwnds.append(hwnd_param)
    ENUM_WINDOWS_CALLBACK = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
    callback = ENUM_WINDOWS_CALLBACK(enumWindowCallback)
    user32.EnumWindows(callback, 0)
    return hwnds

def makeAppToFrontmost():
    """
        Ensure Webex app is frontmost if it's not already.
    """
    platform = current_platform()
    webex_processes = get_process(platform)
    if webex_processes:
        for p in webex_processes:
            pid = p.pid
            if platform == PLATFORM_MAC:
                if webex_processes:
                    os.system(f"osascript -e 'tell application \"System Events\" to set frontmost of (first process whose unix id is {pid}) to true'")
            elif platform == PLATFORM_WIN:
                hwnds = findWindowByPid(pid)
                for hwnd in hwnds:
                    user32.SetForegroundWindow(hwnd)
                    # user32.BringWindowToTop(hwnd)
def uninstallWebex():
    platform = current_platform()
    settings = DynamicConfig(SETTINGS_PATH)
    install_option = settings.get('installOptions')
    
    LOGGER_INFO(f"Uninstalling Webex...")
    if platform == PLATFORM_WIN:
        try:
            win_uninstall_app()
        except subprocess.CalledProcessError:
            LOGGER_INFO("Webex uninstall returned non-zero exit code (app may not be installed). Continuing...")
    elif platform == PLATFORM_MAC:
        kill_process(platform)
        LOGGER_INFO(f"Removing /Applications/Webex.app")

        try:
            subprocess.check_call('rm -rf /Applications/Webex.app', shell=True)
        except subprocess.CalledProcessError:
            LOGGER_INFO("Please enter your password and press the Enter key to continue.")
            subprocess.check_call('sudo rm -rf /Applications/Webex.app', shell=True)

        resetDB = install_option['notResetDB']
        if resetDB == False:
            db_path = os.path.join(os.path.expanduser(
                '~'), 'Library/Application Support/Cisco Spark')
            LOGGER_INFO("removing Webex database and upgrade packages")
            subprocess.check_call('rm -rf "' + db_path + '"', shell=True)

    elif platform == PLATFORM_UBUNTU_1804 or platform == PLATFORM_UBUNTU_2004 or platform == PLATFORM_CENTOS:
        kill_process(platform)

        LOGGER_INFO("removing /opt/Webex")

        LOGGER_INFO("Please enter your password and press the Enter key to continue.")
        if platform == PLATFORM_CENTOS:
            subprocess.check_call('sudo dnf remove webex', shell=True)
        else:
            subprocess.check_call('sudo apt remove webex', shell=True)

        # logging.info("removing Webex database")
        # db_path = os.path.join(os.path.expanduser(
        #     '~'), '.local/share/Webex')
        # subprocess.check_call('rm -rf "' + db_path + '"', shell=True)

        # logging.info("removing Webex upgrade packages")
        # upgrade_path = os.path.join(os.path.expanduser(
        #     '~'), '.local/share/WebexLauncher/')
        # subprocess.check_call('rm -rf "' + upgrade_path + '"', shell=True)

    LOGGER_INFO(f"Webex app uninstalled.")
def installWebex(GT = False):
    """
    Kill current Webex app process, uninstall it.
    Download the Webex app, install and launch it.
    """
    global LOCAL_APP_PATH, _cleanup_all_performed
    settings = DynamicConfig(SETTINGS_PATH)
    install_option = settings.get('installOptions')
    
    # Get cleanupAllVersions setting
    # LOGGER_INFO(f"[install_option] install_option: {install_option}")
    cleanup_all_versions_enabled = settings.get('cleanupAllVersions')
    LOGGER_DEBUG(f"[Cleanup setting] cleanupAllVersions: {cleanup_all_versions_enabled}")
    
    if install_option:
        version = install_option['version']
        path = install_option['path']
        uninstall = install_option['uninstall']
        source = install_option['source']
        qtversion = install_option['qtversion']
        arch = install_option['arch']
        cdntoken = install_option['cdntoken']
        http2 = install_option['http2']
        downloadonly = install_option['downloadonly']
        language = settings.get('language')
        LOGGER_DEBUG(f'====================language: {language}')

    platform = current_platform()
    chip_info = get_chip_info(platform)
    LOGGER_DEBUG(f'Starting install_webex with version:{version}')

    if uninstall and not GT:
        uninstallWebex()

    # get local download folder
    download_to_folder = get_local_downloads_folder(path)
    webex_curver = get_webex_localversion(platform, chip_info)

    if source == 'galway':
        builds_source = GalwayBuildsSource(qtversion = qtversion, arch=arch, cdn_token=cdntoken, http2=http2)
    elif source == 'sym':
        builds_source = SymBuildsSource(qtversion = qtversion, arch=arch, http2=http2)
    else:
        builds_source = ShanghaiBuildsSource(qtversion = qtversion, arch=arch, http2=http2)

    if version == 'latest':
        version = builds_source.get_latest_master_version(
            platform, chip_info)
    elif version == 'eft':
        version = builds_source.get_latest_eft_version(
            platform, chip_info)
        LOGGER_INFO(f"[eft version] {version}")

    if not version:
        LOGGER_INFO("version is empty")
        sys.exit(0)

    # if platform != PLATFORM_WIN and version == webex_curver:
    #     logging.info(
    #         "Your request version is same as current webex version: {}".format(webex_curver))
    #     webexstatus = get_process(platform)
    #     if len(webexstatus) == 0:
    #         launch_app(platform)
    #     sys.exit(0)

    url = builds_source.get_download_url(platform, chip_info, version)
    LOGGER_INFO(f"[Start download url] {url}")
    if url == "":
        LOGGER_ERROR("Your request version is not found in server")
        sys.exit(0)
    # download new build installation package
    download_to_folder = get_local_downloads_folder(path)
    LOCAL_APP_PATH = os.path.join(download_to_folder, app_name(platform, version, qtversion, arch, http2, chip_info))
    size_txt_file = LOCAL_APP_PATH + ".size.txt"
    delete_after_installation = False  # Changed: Keep installation packages by default

    # Clean up versions before downloading/checking current version
    # When cleanupAllVersions is enabled, only perform full cleanup once per process.
    # Subsequent calls (e.g. in batch mode) fall back to cleaning up older versions only,
    # so the just-downloaded package is reused instead of re-downloaded.
    if cleanup_all_versions_enabled and not _cleanup_all_performed:
        LOGGER_DEBUG("Cleaning up all version installation packages...")
        cleanup_all_versions(download_to_folder, platform, qtversion, arch, http2, chip_info)
        _cleanup_all_performed = True
        LOGGER_DEBUG("[cleanupAllVersions] Full cleanup done, subsequent installs will only clean older versions")
    else:
        LOGGER_DEBUG("Cleaning up older version installation packages...")
        cleanup_older_versions(download_to_folder, version, platform, qtversion, arch, http2, chip_info)

    if get_file_size(LOCAL_APP_PATH) > 0 and get_file_size(LOCAL_APP_PATH) == read_file_size_from_txt_file(size_txt_file):
        LOGGER_WARNING(f"don't download webex as it already exists: {LOCAL_APP_PATH}")
        dl_status = True
        delete_after_installation = False
    else:
        dl_status = download_file(url, LOCAL_APP_PATH, cdntoken)

    if dl_status == False:
        delete_downloaded_file(LOCAL_APP_PATH)
        os.remove(size_txt_file)
        LOGGER_ERROR("!!! Failed !!!!")
    else:
        write_file_size_to_txt_file(size_txt_file, get_file_size(LOCAL_APP_PATH))

        if downloadonly:
            LOGGER_INFO(f"successfully downloaded: {LOCAL_APP_PATH}")
            sys.exit(0)

        # prepare install downloaded installation package
        if versiontuple(version) < versiontuple(webex_curver):
            LOGGER_INFO(
                "lower version is requested, uninstalling current app")
            prepare_webex_downgrades(platform, chip_info)
        prepare_test_build(platform)
        install_app(platform)
        time.sleep(WAIT_SHORT_TIME)
        launch_app(platform, language or "en_US")
        time.sleep(WAIT_WINDOW_ACTION_TIME)

        if delete_after_installation:
            delete_downloaded_file(LOCAL_APP_PATH)
            os.remove(size_txt_file)

        DynamicConfig(SETTINGS_PATH).set('appVersion', version)
        LOGGER_INFO("Webex {} installed successfully".format(version))
        # logging.info(
        #     "Webex {} launched, enjoy your journey!".format(version))

def initWebex():
    """
    Kill current Webex app process, and launch it again.
    """
    kill_process(current_platform())
    launch_app_to_top(current_platform())
    LOGGER_INFO(f'Webex launched, enjoy your journey!', color='GREEN')
    time.sleep(WAIT_WINDOW_ACTION_TIME)

def get_app_version(version=None):
    app_version = version
    if not app_version:
        LOGGER_DEBUG(f'AppVersionFile: {APP_VERSION_PATH}', color='GREEN')
    # Check macOS app version from Info.plist
        if str(APP_VERSION_PATH).endswith('.plist'):
            try:
                if os.path.exists(APP_VERSION_PATH):
                    with open(APP_VERSION_PATH, 'rb') as f:
                        plist_data = plistlib.load(f)
                        app_version = plist_data.get('CFBundleShortVersionString')
                        if app_version:
                            LOGGER_INFO(f'Read app version from Info.plist: {app_version}', color='GREEN')
                else:
                    LOGGER_WARNING(f'Info.plist not found at {APP_VERSION_PATH}')
            except Exception as e:
                LOGGER_WARNING(f'Failed to read Info.plist: {e}')
        else:
            # Read from version.txt file (Windows/Linux)
            app_version = fileHandler.readFile(APP_VERSION_PATH)
        if not app_version:
            LOGGER_WARNING("Failed to read app version; defaulting to 0.0.0.0")
            app_version = "0.0.0.0"
            
    return app_version

def get_latest_version():
    settings = DynamicConfig(SETTINGS_PATH)
    install_option = settings.installOptions
    
    if install_option:
        version = install_option.version
        source = install_option.source
        qtversion = install_option.qtversion
        arch = install_option.arch
        cdntoken = install_option.cdntoken
        http2 = install_option.http2

    platform = current_platform()
    chip_info = get_chip_info(platform)

    if source == 'galway':
        builds_source = GalwayBuildsSource(qtversion = qtversion, arch=arch, cdn_token=cdntoken, http2=http2)
    elif source == 'sym':
        builds_source = SymBuildsSource(qtversion = qtversion, arch=arch, http2=http2)
    else:
        builds_source = ShanghaiBuildsSource(qtversion = qtversion, arch=arch, http2=http2)

    if version == 'latest':
        version = builds_source.get_latest_master_version(
            platform, chip_info)
    elif version == 'eft':
        version = builds_source.get_latest_eft_version(
            platform, chip_info)
        LOGGER_INFO(f"[eft version] {version}")

    if not version:
        LOGGER_INFO("version is empty")
        sys.exit(0)

    return version

def get_local_app_version():
    """
    Get the local Webex app version from the settings file.
    """
    app_version = fileHandler.readFile(APP_VERSION_PATH)
    return app_version

def is_app_version_same_as_latest():
    """
    Check if the current app version matches the latest version.
    """
    builds_source = ShanghaiBuildsSource(qtversion='6', arch='x64', http2=True)
    platform = current_platform()
    chip_info = get_chip_info(platform)
    app_version = get_local_app_version() 
    latest_app_version = builds_source.get_latest_master_version(platform, chip_info)
    
    if not latest_app_version:
        LOGGER_ERROR("App version is not set in settings.")
        return False
    
    if app_version == latest_app_version:
        LOGGER_INFO(f"App version {latest_app_version} matches local version {app_version}.")
        return True
    else:
        LOGGER_WARNING(f"App version {latest_app_version} does not match local version {app_version}.")
        return False

def launch_edge_browser(url="", platform=None, user_profile=None):
    """
    Launch Microsoft Edge browser
    Args:
        url (str): Optional URL to open (default: empty string for homepage)
        platform (str): Platform type (auto-detected if None)
        user_profile (str): Optional Edge profile to use
    """
    if platform is None:
        platform = current_platform()
    
    if platform == PLATFORM_WIN:
        # Common Edge installation paths on Windows
        edge_paths = [
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
            os.path.join(os.path.expanduser('~'), r"AppData\Local\Microsoft\Edge\Application\msedge.exe")
        ]
        
        edge_exe = None
        for path in edge_paths:
            if os.path.exists(path):
                edge_exe = path
                break
        
        if not edge_exe:
            LOGGER_ERROR("Microsoft Edge not found on this system")
            return False
        
        # Build command
        cmd_parts = [f'"{edge_exe}"']
        
        if user_profile:
            cmd_parts.append(f'--profile-directory="{user_profile}"')
        
        if url:
            cmd_parts.append(f'"{url}"')
        
        cmd = ' '.join(cmd_parts)
        LOGGER_INFO(f"Launching Edge browser with command: {cmd}")
        
        try:
            # Use Popen instead of check_call to avoid blocking on browser process
            subprocess.Popen(cmd, shell=True)
            time.sleep(2)  # Give browser time to start
            return True
        except Exception as e:
            LOGGER_ERROR(f"Failed to launch Edge browser: {e}")
            return False
            
    elif platform == PLATFORM_MAC:
        cmd_parts = ['open', '-a', 'Microsoft Edge']
        
        if url:
            cmd_parts.extend(['--args', url])
        
        cmd = ' '.join(cmd_parts)
        LOGGER_INFO(f"Launching Edge browser with command: {cmd}")
        
        try:
            # Use Popen instead of check_call to avoid blocking on browser process
            subprocess.Popen(cmd, shell=True)
            time.sleep(2)  # Give browser time to start
            return True
        except Exception as e:
            LOGGER_ERROR(f"Failed to launch Edge browser: {e}")
            return False
            
    elif platform in [PLATFORM_UBUNTU_1804, PLATFORM_UBUNTU_2004, PLATFORM_CENTOS]:
        # Common Edge installation paths on Linux
        edge_commands = [
            'microsoft-edge',
            'microsoft-edge-stable',
            'microsoft-edge-beta',
            'microsoft-edge-dev'
        ]
        
        edge_cmd = None
        for cmd_name in edge_commands:
            if has_program(cmd_name):
                edge_cmd = cmd_name
                break
        
        if not edge_cmd:
            LOGGER_ERROR("Microsoft Edge not found on this system")
            return False
        
        cmd_parts = [edge_cmd]
        
        if user_profile:
            cmd_parts.append(f'--profile-directory="{user_profile}"')
        
        if url:
            cmd_parts.append(f'"{url}"')
        
        cmd = ' '.join(cmd_parts)
        LOGGER_INFO(f"Launching Edge browser with command: {cmd}")
        
        try:
            # Use Popen instead of check_call to avoid blocking on browser process
            subprocess.Popen(cmd, shell=True)
            time.sleep(2)  # Give browser time to start
            return True
        except Exception as e:
            LOGGER_ERROR(f"Failed to launch Edge browser: {e}")
            return False
    
    else:
        LOGGER_ERROR(f"Unsupported platform: {platform}")
        return False


def launch_edge_with_webex_url(meeting_id="", platform=None):
    """
    Launch Edge browser with Webex meeting URL
    Args:
        meeting_id (str): Webex meeting ID (optional)
        platform (str): Platform type (auto-detected if None)
    """
    if meeting_id:
        webex_url = f"https://web.webex.com/join/{meeting_id}"
        LOGGER_INFO(f"Launching Edge browser with Webex meeting URL: {webex_url}")
        return launch_edge_browser(url=webex_url, platform=platform)
    else:
        webex_url = "https://web.webex.com"
        LOGGER_INFO(f"Launching Edge browser with Webex homepage: {webex_url}")
        return launch_edge_browser(url=webex_url, platform=platform)


def get_edge_process(platform=None):
    """
    Get Microsoft Edge browser process info
    Args:
        platform (str): Platform type (auto-detected if None)
    Returns:
        list: List of Edge process objects
    """
    if platform is None:
        platform = current_platform()
    
    res = []
    if platform == PLATFORM_WIN:
        for p in psutil.process_iter(attrs=['name', 'username']):
            if p.info['name'] == 'msedge.exe':
                res.append(p)
    elif platform == PLATFORM_MAC:
        cmd = 'ps ax | grep "Microsoft Edge" | grep -v grep'
        for p in os.popen(cmd):
            if 'Microsoft Edge' in p:
                res.append(p.split()[0])
    elif platform in [PLATFORM_UBUNTU_1804, PLATFORM_UBUNTU_2004, PLATFORM_CENTOS]:
        cmd = 'ps ax | grep "microsoft-edge" | grep -v grep'
        for p in os.popen(cmd):
            res.append(p.split()[0])
    
    return res


def kill_edge_process(platform=None):
    """
    Kill all Microsoft Edge browser processes
    Args:
        platform (str): Platform type (auto-detected if None)
    """
    if platform is None:
        platform = current_platform()
    
    if platform == PLATFORM_WIN:
        proc = get_edge_process(platform)
        if len(proc) != 0:
            LOGGER_INFO('Trying to kill existing Microsoft Edge processes')
            for pid in proc:
                try:
                    pid.kill()
                    time.sleep(1)
                except:
                    break
            LOGGER_INFO('Microsoft Edge processes killed')
        else:
            LOGGER_WARNING('Microsoft Edge is not running')
    elif platform == PLATFORM_MAC:
        try:
            cmd = 'pkill -f "Microsoft Edge"'
            subprocess.check_call(cmd, shell=True)
            LOGGER_INFO('Microsoft Edge processes killed')
        except:
            LOGGER_WARNING('Failed to kill Microsoft Edge or it was not running')
    elif platform in [PLATFORM_UBUNTU_1804, PLATFORM_UBUNTU_2004, PLATFORM_CENTOS]:
        try:
            cmd = 'pkill -f microsoft-edge'
            subprocess.check_call(cmd, shell=True)
            LOGGER_INFO('Microsoft Edge processes killed')
        except:
            LOGGER_WARNING('Failed to kill Microsoft Edge or it was not running')

