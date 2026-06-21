import locale
import platform
import ctypes
import socket
import subprocess

def getOSInfo():
    osInfo = ""
    os_name = platform.system()
    release = platform.release()
    architecture = platform.architecture()[0]

    if os_name.lower() == "windows":
        os_version = platform.version()
        
        # Windows 11 detection based on build number
        # Windows 11 starts from build 22000
        build_number = int(os_version.split('.')[2]) if len(os_version.split('.')) >= 3 else 0
        
        if build_number >= 22000:
            windows_version = "Windows 11"
            # Determine Windows 11 release based on build number
            if build_number >= 26100:  # 24H2
                release_name = "24H2"
            elif build_number >= 22631:  # 23H2
                release_name = "23H2"
            elif build_number >= 22621:  # 22H2
                release_name = "22H2"
            elif build_number >= 22000:  # 21H2 (original release)
                release_name = "21H2"
            else:
                release_name = release
            osInfo = f"{windows_version} {release_name} ({os_version}) {architecture}"
        else:
            osInfo = f"{os_name} {release} ({os_version}) {architecture}"
    else:
        version, _, build = platform.mac_ver()
        os_version = f"{version}, {build}"
        osInfo = f"MacOS ({os_version})"
    
    return osInfo

def getSystemLanguageCode():
    current_platform = platform.system()
    if current_platform == "Windows":
        windll = getattr(ctypes, 'windll', None)
        if windll:
            lang_code = locale.windows_locale.get(windll.kernel32.GetUserDefaultUILanguage())
        else:
            lang_code = "en_US"
    elif current_platform == "Darwin":
        lang_code, _ = locale.getdefaultlocale()
    return lang_code or "en_US"

def getHostName() -> str:
    """
    Get the hostname of the current machine.
    
    Returns:
        str: Hostname, or 'Unknown' if unable to get hostname
    """
    try:
        hostname = socket.gethostname()
        return hostname if hostname else 'Unknown'
    except Exception:
        return 'Unknown'

def getSerialNumber() -> str:
    current_os = platform.system().lower()
    try:
        if current_os == "windows":
            output = subprocess.check_output(
                ["powershell", "-Command", "Get-CimInstance -Class Win32_BIOS | Select-Object -ExpandProperty SerialNumber"],
                stderr=subprocess.DEVNULL
            ).decode().strip()
            if output and "O.E.M" not in output and output != "":
                return output
            else:
                return "000000"
        elif current_os == "darwin":
            output = subprocess.check_output(
                ["system_profiler", "SPHardwareDataType"], stderr=subprocess.DEVNULL
            ).decode().splitlines()
            for line in output:
                if "Serial Number" in line:
                    return line.split(":")[1].strip()
            return "000000"
        elif current_os == "linux":
            try:
                with open("/sys/class/dmi/id/product_serial", "r") as f:
                    return f.read().strip()
            except FileNotFoundError:
                output = subprocess.check_output(
                    ["sudo", "dmidecode", "-s", "system-serial-number"],
                    stderr=subprocess.DEVNULL
                ).decode().strip()
                return output
    except Exception as e:
        return "000000"
    return "000000"

def getIP() -> str:
    """
    Get the local IP address of the current machine.
    
    Returns:
        str: Local IP address, or '127.0.0.1' if unable to determine IP
    """
    try:
        # Connect to a remote address to determine local IP
        # This doesn't actually send data, just determines routing
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            return ip if ip else "127.0.0.1"
    except Exception:
        # Fallback: try to get IP from hostname
        try:
            hostname = socket.gethostname()
            ip = socket.gethostbyname(hostname)
            return ip if ip and ip != "127.0.0.1" else "127.0.0.1"
        except Exception:
            return "127.0.0.1"

if __name__ == "__main__":
    print(getOSInfo())
    print(getSystemLanguageCode())
    print(getHostName())
    print(getSerialNumber())
    print(getIP())
