import time
import re
from typing import Optional
from common.utils.logger import LOGGER_INFO, LOGGER_ERROR

class GTFunction(object):
    def __init__(self):
        pass

    def _resolve_action_variables(self, value):
        if isinstance(value, str):
            from core.mac.RSApplicationGT import CRSActionResult

            groups = re.findall(r"\$\{([^{}]*?)\}", value)
            resolved_value = value
            for group in groups:
                action_result = CRSActionResult.GetActionResult(group)
                if action_result is not None:
                    resolved_value = resolved_value.replace(f"${{{group}}}", str(action_result))
            return resolved_value

        if isinstance(value, dict):
            return {key: self._resolve_action_variables(item) for key, item in value.items()}

        if isinstance(value, list):
            return [self._resolve_action_variables(item) for item in value]

        return value

    def call_by_name(self, name: str, *args, **kwargs):
        func = getattr(self, name, None)
        if not callable(func):
            raise AttributeError(f"Unknown function: {name}")
        return func(*args, **kwargs)
    
    def get_correlation_id_from_log(self, **kwargs) -> Optional[str]:
        from test_space.test_functions.basic_functions import webex_app_log_parser
        correlation_id = webex_app_log_parser.get_correlation_id_from_log()
        if correlation_id:
            LOGGER_INFO(f"Correlation ID found: {correlation_id}")
        else:
            LOGGER_ERROR("Correlation ID not found in logs.")
        return correlation_id
    
    def get_meeting_join_result(self, **kwargs) -> dict:
        from test_space.test_functions.basic_functions.get_guest_join_metrics import MeetingMetricsClient
        columns = kwargs.get("columns", None)
        if columns is None:
            columns = ["outcome", "mediaOutcome", "resultName", "identifiers_webexSiteName"]
        client = MeetingMetricsClient()
        result = client.get_meeting_join_result(columns)
        LOGGER_INFO(f"Meeting join result : {result}")
        return result

    def capture_fullscreen(self,**kwargs):
        from rs_sdk.utils.image_handler import capture_full_screen,save_image
        from rs_sdk.utils.image_handler import ImageCaptureResult
        from config.paths import FULLSCREEN_IMAGE_PATH
        fileName = kwargs.get("image_name","unknown_step")
        output_path = FULLSCREEN_IMAGE_PATH
        result: ImageCaptureResult = capture_full_screen(1)
        save_image(f"{fileName}", img=result.img, output_path=output_path.as_posix())
        LOGGER_INFO(f"Full screen image saved: {output_path}/{fileName}.jpg")

    def ui_element_wait_time(self, **kwargs):
        wait_time = kwargs.get("seconds", 5)
        LOGGER_INFO(f"Waiting for {wait_time} seconds for UI element.")
        time.sleep(wait_time)

    def wait_seconds(self, **kwargs):
        seconds = int(kwargs.get("seconds", 5))
        LOGGER_INFO(f"=== Starting {seconds} second wait ===")
        time.sleep(seconds)

    def print_hello_world(self, **kwargs):
        message = kwargs.get("message", "Hello, World!")
        import re
        from core.mac.RSApplicationGT import CRSActionResult
        groups = re.findall(r"\$\{([^{}]*?)\}", message)
        for group in groups:
            value = CRSActionResult.GetActionResult(group)
            if value is not None:
                message = message.replace(f"${{{group}}}", str(value))
        LOGGER_INFO(message)

    def bundle_logs(self, **kwargs):
        from test_space.test_functions.basic_functions.webex_app_log_pack import bundle_logs
        bundle_logs()
        LOGGER_INFO(f"Logs have been bundled successfully.")

    def open_browser(self, **kwargs):
        from test_space.test_functions.platform_functions.web_functions import open_browser as _open_browser
        site_url = kwargs.get("site_url", "https://web.webex.com")
        browser = kwargs.get("browser", "edge")
        return _open_browser(site_url=site_url, browser=browser)

    def close_browser(self, **kwargs):
        from test_space.test_functions.platform_functions.web_functions import close_browser as _close_browser
        browser = kwargs.get("browser", "all")
        return _close_browser(browser=browser)

    def click_macos_automation_permission(self, **kwargs):
        """Click macOS automation/access permission dialogs such as the Notes Allow prompt."""
        import subprocess
        import time

        button_name = kwargs.get("button_name", "Allow")
        retry = int(kwargs.get("retry", 3))
        wait_time = float(kwargs.get("wait_time", 1))
        candidates = [name.strip() for name in str(button_name).split(",") if name.strip()]

        def click_one(expected):
            script = f'''
tell application "System Events"
    repeat with p in application processes
        try
            repeat with w in windows of p
                try
                    click button "{expected}" of w
                    return "clicked:" & (name of p as text)
                end try
                try
                    repeat with s in sheets of w
                        try
                            click button "{expected}" of s
                            return "clicked_sheet:" & (name of p as text)
                        end try
                    end repeat
                end try
                try
                    click (first UI element of w whose title is "{expected}" or name is "{expected}" or description is "{expected}")
                    return "clicked_element:" & (name of p as text)
                end try
            end repeat
        end try
    end repeat
end tell
return "not_found"
'''
            result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, check=False)
            return (result.stdout or result.stderr or "").strip()

        last_output = "not_found"
        for attempt in range(max(retry, 1)):
            for expected in candidates:
                last_output = click_one(expected)
                LOGGER_INFO(f"click_macos_automation_permission attempt {attempt + 1}: {expected} -> {last_output}")
                if "clicked" in last_output:
                    time.sleep(wait_time)
                    return {"status": "success", "message": last_output}
            time.sleep(1)

        time.sleep(wait_time)
        return {"status": "not_found", "message": last_output}

    def create_macos_note_with_link(self, **kwargs):
        """Create and show an Apple Notes note containing a meeting hyperlink."""
        import html
        import json
        import subprocess
        import time

        link = kwargs.get("link", "https://cisco.webex.com/meet/minl5")
        title = kwargs.get("title", "WRS Mac Universal Link")
        display_text = kwargs.get("display_text", link)
        delete_existing = kwargs.get("delete_existing", True)
        wait_time = float(kwargs.get("wait_time", 2))
        allow_timeout = float(kwargs.get("allow_timeout", 20))

        if not str(link).startswith(("http://", "https://")):
            link = f"https://{link}"

        note_body = f'<div><a href="{html.escape(str(link), quote=True)}">{html.escape(str(display_text))}</a></div>'
        delete_script = ""
        if delete_existing:
            delete_script = """
    repeat with targetAccount in accounts
        repeat with targetFolder in folders of targetAccount
            try
                delete (notes of targetFolder whose name is noteTitle)
            end try
        end repeat
    end repeat
"""

        script = f'''
tell application "Notes"
    activate
    set noteTitle to {json.dumps(str(title))}
    set noteBody to {json.dumps(note_body)}
{delete_script}
    set targetFolder to missing value
    repeat with targetAccount in accounts
        try
            set targetFolder to folder "Notes" of targetAccount
            exit repeat
        end try
    end repeat
    if targetFolder is missing value then
        set targetFolder to folder 1 of account 1
    end if
    set newNote to make new note at targetFolder with properties {{name:noteTitle, body:noteBody}}
    show newNote
end tell
return "created"
'''
        process = subprocess.Popen(["osascript", "-e", script], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        deadline = time.time() + max(allow_timeout, 1)
        while process.poll() is None and time.time() < deadline:
            self.click_macos_automation_permission(button_name="Allow", retry=1, wait_time=0.2)
            time.sleep(0.5)

        if process.poll() is None:
            LOGGER_INFO("Notes creation is still waiting after automation permission attempts; waiting for user response")

        stdout, stderr = process.communicate()
        output = (stdout or stderr or "").strip()
        if process.returncode != 0:
            LOGGER_ERROR(f"Failed to create Apple Notes meeting link note: {output}")
            raise RuntimeError(output)
        LOGGER_INFO(f"Created Apple Notes meeting link note: {output}")
        time.sleep(wait_time)
        return {"status": "success", "message": output, "link": link}

    def click_macos_note_link(self, **kwargs):
        """Click a hyperlink in the currently shown Apple Notes note."""
        import subprocess
        import time

        link_text = kwargs.get("link_text", kwargs.get("link", "cisco.webex.com/meet/minl5"))
        bundle_id = kwargs.get("bundle_id", "com.apple.Notes")
        wait_time = float(kwargs.get("wait_time", 5))

        def _matches(text):
            return str(link_text).lower() in str(text or "").lower()

        try:
            from core.mac.RSApplication import CRSApplication

            app_ref = CRSApplication.ApplicationByBundleID(bundle_id)
            if app_ref is not None:
                app_ref.activate()
                time.sleep(1)

                def walk(elem, depth=0, allow_non_link=False):
                    if depth > 12:
                        return None
                    try:
                        role = elem.AXRole
                    except Exception:
                        role = ""
                    names = []
                    for attr in ("AXTitle", "AXDescription", "AXValue"):
                        try:
                            value = getattr(elem, attr)
                            if value:
                                names.append(str(value))
                        except Exception:
                            pass
                    if (role == "AXLink" or allow_non_link) and any(_matches(name) for name in names):
                        return elem
                    try:
                        children = elem.AXChildren or []
                    except Exception:
                        children = []
                    for child in children:
                        found = walk(child, depth + 1, allow_non_link)
                        if found is not None:
                            return found
                    return None

                windows = list(app_ref.windows())
                for allow_non_link in (False, True):
                    for win in windows:
                        link = walk(win, allow_non_link=allow_non_link)
                        if link is not None:
                            try:
                                win.perform_ax_action("AXRaise")
                            except Exception:
                                pass
                            link.perform_ax_action("AXPress")
                            LOGGER_INFO(f"Clicked Apple Notes link by AX: {link_text}")
                            time.sleep(wait_time)
                            return {"status": "success", "message": f"clicked_notes_link:{link_text}"}
        except Exception as exc:
            LOGGER_INFO(f"Apple Notes AX link click failed: {exc}")

        script = f'''
on click_matching_link(target_element, expected_text)
    try
        set elementRole to ""
        try
            set elementRole to role of target_element as text
        end try
        set elementTitle to ""
        try
            set elementTitle to title of target_element as text
        end try
        set elementName to ""
        try
            set elementName to name of target_element as text
        end try
        set elementDescription to ""
        try
            set elementDescription to description of target_element as text
        end try
        set elementValue to ""
        try
            set elementValue to value of target_element as text
        end try
        set allText to elementTitle & " " & elementName & " " & elementDescription & " " & elementValue
        if allText contains expected_text and elementRole contains "AXLink" then
            click target_element
            return true
        end if
    end try
    try
        repeat with child_element in UI elements of target_element
            if my click_matching_link(child_element, expected_text) then return true
        end repeat
    end try
    return false
end click_matching_link

tell application "Notes" to activate
delay 1
tell application "System Events"
    if not (exists process "Notes") then return "process_not_found"
    tell process "Notes"
        repeat with w in windows
            if my click_matching_link(w, "{link_text}") then return "clicked"
        end repeat
    end tell
end tell
return "not_found"
'''
        result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, check=False)
        output = (result.stdout or result.stderr or "").strip()
        LOGGER_INFO(f"Apple Notes link click AppleScript output: {output}")
        if output != "clicked":
            raise RuntimeError(f"Failed to click Apple Notes link '{link_text}': {output}")
        time.sleep(wait_time)
        return {"status": "success", "message": f"clicked_notes_link:{link_text}"}

    def click_macos_window_relative(self, **kwargs):
        """Click a relative point in the front window of a macOS application.

        This is useful for browser-rendered pages where AX focus/navigation is unstable.
        x_ratio and y_ratio are relative to the front window bounds, from 0.0 to 1.0.
        """
        import subprocess
        import time
        from core.mac._input import Mouse
        from common.utils.logger import LOGGER_INFO, LOGGER_ERROR

        process_name = kwargs.get("process_name", "Safari")
        x_ratio = float(kwargs.get("x_ratio", 0.5))
        y_ratio = float(kwargs.get("y_ratio", 0.5))
        wait_time = float(kwargs.get("wait_time", 1))
        retry = int(kwargs.get("retry", 5))

        script = f'''
tell application "System Events"
    if not (exists process "{process_name}") then return "process_not_found"
    tell process "{process_name}"
        set frontmost to true
        if not (exists window 1) then return "window_not_found"
        set windowPosition to position of window 1
        set windowSize to size of window 1
        return (item 1 of windowPosition as text) & "," & (item 2 of windowPosition as text) & "," & (item 1 of windowSize as text) & "," & (item 2 of windowSize as text)
    end tell
end tell
'''
        output = ""
        for attempt in range(max(retry, 1)):
            subprocess.run(["osascript", "-e", f'tell application "{process_name}" to activate'], check=False)
            time.sleep(0.5)
            result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, check=False)
            output = (result.stdout or result.stderr or "").strip()
            try:
                x, y, width, height = [float(part.strip()) for part in output.split(",")]
                break
            except Exception as exc:
                LOGGER_INFO(
                    f"click_macos_window_relative retry {attempt + 1}/{retry} failed to read "
                    f"window bounds: {output}, error: {exc}"
                )
                time.sleep(1)
        else:
            LOGGER_ERROR(f"click_macos_window_relative failed to read window bounds after retries: {output}")
            time.sleep(wait_time)
            return {"status": "failed", "message": output}

        click_x = int(x + width * x_ratio)
        click_y = int(y + height * y_ratio)
        Mouse().click_mouse_button_left((click_x, click_y))
        LOGGER_INFO(
            f"click_macos_window_relative clicked {process_name} at ({click_x}, {click_y}) "
            f"using ratios ({x_ratio}, {y_ratio}) and bounds ({x}, {y}, {width}, {height})"
        )
        time.sleep(wait_time)
        return {"status": "success", "message": f"clicked:{click_x},{click_y}"}

    def install_downloaded_webex_app(self, **kwargs):
        """Install the Webex app from the latest DMG downloaded by the browser.

        The first-time-user browser flow downloads a file such as
        "Webex Installer.dmg" into ~/Downloads. This function waits for that DMG
        to finish downloading, mounts it, then installs Webex from either a direct
        Webex.app, a pkg, or the Webex Installer.app wrapper inside the DMG.
        """
        import os
        import plistlib
        import shutil
        import subprocess
        import time
        from pathlib import Path

        timeout = float(kwargs.get("timeout", 180))
        installer_timeout = float(kwargs.get("installer_timeout", min(timeout, 60)))
        fallback_after = float(kwargs.get("fallback_after", min(installer_timeout, 30)))
        download_dir = Path(kwargs.get("download_dir", Path.home() / "Downloads")).expanduser()
        app_destination = Path(kwargs.get("app_destination", "/Applications/Webex.app"))
        launch_after_install = kwargs.get("launch_after_install", True)
        deadline = time.time() + max(timeout, 1)

        def installed():
            return app_destination.is_dir() and (app_destination / "Contents" / "Info.plist").exists()

        def latest_dmg():
            candidates = [
                path for path in download_dir.glob("*Webex*.dmg")
                if path.is_file() and not path.name.endswith(".download")
            ]
            if not candidates:
                return None
            installer_candidates = [
                path for path in candidates
                if "installer" in path.name.lower()
            ]
            return max(installer_candidates or candidates, key=lambda path: path.stat().st_mtime)

        def direct_webex_dmg():
            candidates = [
                path for path in download_dir.glob("*Webex*.dmg")
                if path.is_file()
                and not path.name.endswith(".download")
                and "installer" not in path.name.lower()
            ]
            if not candidates:
                return None
            return max(candidates, key=lambda path: (path.stat().st_size, path.stat().st_mtime))

        def detach_matching_volumes(pattern):
            for stale_mount in Path("/Volumes").glob(pattern):
                subprocess.run(
                    ["hdiutil", "detach", str(stale_mount)],
                    check=False,
                    capture_output=True,
                    text=True,
                )

        def install_from_direct_dmg():
            fallback_dmg = direct_webex_dmg()
            if fallback_dmg is None:
                return False

            LOGGER_INFO(f"Falling back to direct Webex dmg install: {fallback_dmg}")
            detach_matching_volumes("Webex*")
            fallback_attach = subprocess.run(
                ["hdiutil", "attach", str(fallback_dmg), "-nobrowse", "-plist"],
                capture_output=True,
                check=False,
            )
            if fallback_attach.returncode != 0:
                LOGGER_ERROR(
                    f"Failed to attach fallback dmg {fallback_dmg}: "
                    f"{fallback_attach.stderr.decode(errors='ignore') or fallback_attach.stdout.decode(errors='ignore')}"
                )
                return False

            fallback_mounts = []
            try:
                fallback_plist = plistlib.loads(fallback_attach.stdout)
                fallback_mounts = [
                    Path(entity.get("mount-point"))
                    for entity in fallback_plist.get("system-entities", [])
                    if entity.get("mount-point")
                ]
                fallback_apps = []
                fallback_pkgs = []
                for mount_path in fallback_mounts:
                    fallback_apps.extend(
                        path for path in mount_path.rglob("Webex.app")
                        if "Webex Installer.app" not in str(path)
                    )
                    fallback_pkgs.extend(mount_path.rglob("*.pkg"))

                fallback_apps = [path for path in fallback_apps if path.exists()]
                fallback_pkgs = [path for path in fallback_pkgs if path.exists()]
                if fallback_apps:
                    source_app = fallback_apps[0]
                    if app_destination.exists() or app_destination.is_symlink():
                        shutil.rmtree(app_destination)
                    shutil.copytree(source_app, app_destination, symlinks=True)
                    LOGGER_INFO(f"Copied fallback {source_app} to {app_destination}")
                    return installed()
                if fallback_pkgs:
                    subprocess.run(["installer", "-pkg", str(fallback_pkgs[0]), "-target", "/"], check=True)
                    LOGGER_INFO(f"Installed fallback Webex pkg: {fallback_pkgs[0]}")
                    return installed()
                LOGGER_ERROR(f"No Webex.app/pkg found in fallback dmg mounts: {fallback_mounts}")
                return False
            finally:
                for mount_path in fallback_mounts:
                    subprocess.run(["hdiutil", "detach", str(mount_path)], check=False, capture_output=True, text=True)

        dmg_path = None
        last_size = -1
        stable_seen_at = 0.0
        while time.time() < deadline:
            partial_files = list(download_dir.glob("*Webex*.download"))
            candidate = latest_dmg()
            if candidate is not None:
                size = candidate.stat().st_size
                if size > 0 and size == last_size and not partial_files:
                    if stable_seen_at == 0.0:
                        stable_seen_at = time.time()
                    elif time.time() - stable_seen_at >= 2:
                        dmg_path = candidate
                        break
                else:
                    stable_seen_at = 0.0
                last_size = size
            time.sleep(1)

        if dmg_path is None:
            message = f"No completed Webex dmg found in {download_dir} within {timeout}s"
            LOGGER_ERROR(message)
            raise FileNotFoundError(message)

        detach_matching_volumes("Webex Installer*")

        LOGGER_INFO(f"Installing Webex from downloaded dmg: {dmg_path}")
        attach_result = subprocess.run(
            ["hdiutil", "attach", str(dmg_path), "-nobrowse", "-plist"],
            capture_output=True,
            check=False,
        )
        if attach_result.returncode != 0:
            message = (
                f"Failed to attach {dmg_path}: "
                f"{attach_result.stderr.decode(errors='ignore') or attach_result.stdout.decode(errors='ignore')}"
            )
            LOGGER_ERROR(message)
            raise RuntimeError(message)
        plist_data = plistlib.loads(attach_result.stdout)
        mount_points = [
            entity.get("mount-point")
            for entity in plist_data.get("system-entities", [])
            if entity.get("mount-point")
        ]
        if not mount_points:
            raise RuntimeError(f"No mount point returned after attaching {dmg_path}")

        mounted_paths = [Path(point) for point in mount_points]
        try:
            webex_apps = []
            pkg_files = []
            installer_apps = []
            for mount_path in mounted_paths:
                webex_apps.extend(
                    path for path in mount_path.rglob("Webex.app")
                    if "Webex Installer.app" not in str(path)
                )
                pkg_files.extend(mount_path.rglob("*.pkg"))
                installer_apps.extend(mount_path.rglob("Webex Installer.app"))

            webex_apps = [path for path in webex_apps if path.exists()]
            pkg_files = [path for path in pkg_files if path.exists()]
            installer_apps = [path for path in installer_apps if path.exists()]

            if webex_apps:
                source_app = webex_apps[0]
                if app_destination.exists():
                    shutil.rmtree(app_destination)
                shutil.copytree(source_app, app_destination, symlinks=True)
                LOGGER_INFO(f"Copied {source_app} to {app_destination}")
            elif pkg_files:
                pkg_file = pkg_files[0]
                subprocess.run(["installer", "-pkg", str(pkg_file), "-target", "/"], check=True)
                LOGGER_INFO(f"Installed Webex from pkg: {pkg_file}")
            elif installer_apps:
                installer_app = installer_apps[0]
                if not installer_app.exists():
                    mounted_tree = []
                    for mount_path in mounted_paths:
                        mounted_tree.extend(str(path) for path in mount_path.rglob("*") if len(mounted_tree) < 50)
                    raise FileNotFoundError(
                        f"Webex Installer.app disappeared before launch: {installer_app}. Mounted tree: {mounted_tree}"
                    )

                LOGGER_INFO(f"Launching Webex installer app from mounted dmg: {installer_app}")
                open_process = subprocess.Popen(
                    ["open", str(installer_app)],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )

                def click_open_downloaded_app_dialog():
                    from core.mac._input import Mouse

                    button_names = ["Open", "打开"]
                    for attempt in range(15):
                        focus_script = '''
tell application "System Events"
    repeat with p in processes
        try
            repeat with w in windows of p
                set windowText to ""
                try
                    set windowText to windowText & (name of w as text)
                end try
                try
                    set windowText to windowText & " " & ((value of static texts of w) as text)
                end try
                try
                    set windowText to windowText & " " & ((name of UI elements of w) as text)
                end try
                if windowText contains "downloaded from the Internet" or windowText contains "Are you sure you want to open it" or windowText contains "This item is on the disk image" then
                    try
                        set frontmost of p to true
                    end try
                    try
                        perform action "AXRaise" of w
                    end try
                    set windowPosition to position of w
                    set windowSize to size of w
                    return (name of p as text) & "|" & (item 1 of windowPosition as text) & "," & (item 2 of windowPosition as text) & "," & (item 1 of windowSize as text) & "," & (item 2 of windowSize as text)
                end if
            end repeat
        end try
    end repeat
end tell
return "not_found"
'''
                        focus_result = subprocess.run(["osascript", "-e", focus_script], capture_output=True, text=True, check=False)
                        focus_output = (focus_result.stdout or focus_result.stderr or "").strip()
                        dialog_bounds = None
                        if "|" in focus_output:
                            _, bounds_text = focus_output.split("|", 1)
                            try:
                                dialog_bounds = [float(part.strip()) for part in bounds_text.split(",")]
                                LOGGER_INFO(f"Focused downloaded-app security dialog: {focus_output}")
                            except Exception as exc:
                                LOGGER_INFO(f"Failed to parse downloaded-app dialog bounds '{focus_output}': {exc}")

                        for button_name in button_names:
                            script = f'''
tell application "System Events"
    repeat with p in processes
        try
            repeat with w in windows of p
                set windowText to ""
                try
                    set windowText to windowText & (name of w as text)
                end try
                try
                    set windowText to windowText & " " & ((value of static texts of w) as text)
                end try
                try
                    set windowText to windowText & " " & ((name of UI elements of w) as text)
                end try
                if not (windowText contains "downloaded from the Internet" or windowText contains "Are you sure you want to open it" or windowText contains "This item is on the disk image") then
                    error "skip unrelated window"
                end if
                try
                    set frontmost of p to true
                end try
                try
                    perform action "AXRaise" of w
                end try
                try
                    click button "{button_name}" of w
                    return "clicked:" & (name of p as text)
                end try
                try
                    repeat with s in sheets of w
                        try
                            click button "{button_name}" of s
                            return "clicked_sheet:" & (name of p as text)
                        end try
                    end repeat
                end try
                try
                    click (first UI element of w whose title is "{button_name}" or name is "{button_name}" or description is "{button_name}")
                    return "clicked_element:" & (name of p as text)
                end try
            end repeat
        end try
    end repeat
end tell
return "not_found"
'''
                            result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, check=False)
                            output = (result.stdout or result.stderr or "").strip()
                            if "clicked" in output:
                                LOGGER_INFO(f"Clicked downloaded-app security dialog button '{button_name}': {output}")
                                time.sleep(2)
                                return True
                        time.sleep(1)

                        if dialog_bounds is not None:
                            x, y, width, height = dialog_bounds
                            click_x = int(x + width * 0.50)
                            click_y = int(y + height * 0.745)
                            Mouse().click_mouse_button_left((click_x, click_y))
                            LOGGER_INFO(
                                f"Clicked downloaded-app security dialog Open by relative position "
                                f"({click_x}, {click_y}) from bounds {dialog_bounds}"
                            )
                            time.sleep(2)
                            return True

                    LOGGER_INFO(f"Waiting for downloaded-app security dialog Open button, attempt {attempt + 1}/15")
                    if installed():
                        return False
                    if attempt >= 2:
                        subprocess.run(
                            ["osascript", "-e", 'tell application "System Events" to key code 36'],
                            check=False,
                            capture_output=True,
                            text=True,
                        )
                        LOGGER_INFO("Sent Return key as fallback for downloaded-app security dialog Open button")
                    time.sleep(1)
                    if open_process.poll() is not None:
                        return False

                time.sleep(1)
                if open_process.poll() is not None and open_process.returncode != 0:
                    stdout, stderr = open_process.communicate()
                    raise RuntimeError(f"Failed to open {installer_app}: {stderr or stdout}")

                click_open_downloaded_app_dialog()
                install_started_at = time.time()
                install_deadline = install_started_at + max(installer_timeout, 1)
                fallback_deadline = install_started_at + max(fallback_after, 1)
                while time.time() < install_deadline:
                    if installed():
                        LOGGER_INFO(f"Webex app detected after launching installer: {app_destination}")
                        break
                    if time.time() >= fallback_deadline and install_from_direct_dmg():
                        LOGGER_INFO(f"Webex app installed by direct dmg fallback: {app_destination}")
                        break
                    time.sleep(2)
                else:
                    if not install_from_direct_dmg():
                        raise TimeoutError(f"Timed out waiting for Webex installer app to install {app_destination}")

                if not installed() and not install_from_direct_dmg():
                    raise FileNotFoundError(f"Webex installer app exited but {app_destination} was not installed")

                subprocess.run(
                    ["osascript", "-e", 'tell application "Webex Installer" to quit'],
                    check=False,
                    capture_output=True,
                    text=True,
                )
                time.sleep(2)
            else:
                raise FileNotFoundError(f"No Webex.app, pkg, or Webex Installer.app found in mounted dmg: {mounted_paths}")
        finally:
            for mount_path in mounted_paths:
                for attempt in range(3):
                    detach_result = subprocess.run(
                        ["hdiutil", "detach", str(mount_path)],
                        check=False,
                        capture_output=True,
                        text=True,
                    )
                    if detach_result.returncode == 0:
                        break
                    LOGGER_INFO(
                        f"Detach {mount_path} failed on attempt {attempt + 1}: "
                        f"{detach_result.stderr or detach_result.stdout}"
                    )
                    time.sleep(2)
                else:
                    subprocess.run(
                        ["hdiutil", "detach", "-force", str(mount_path)],
                        check=False,
                        capture_output=True,
                        text=True,
                    )

        if not installed():
            raise FileNotFoundError(f"Webex app was not installed at {app_destination}")

        if launch_after_install:
            subprocess.run(["open", str(app_destination)], check=False)
            time.sleep(8)

        LOGGER_INFO(f"Downloaded Webex app installed successfully: {app_destination}")
        return {"status": "success", "message": f"installed from {dmg_path}"}

    def click_macos_dialog_button(self, **kwargs):
        """Click a button in a macOS application dialog/sheet if it exists.

        This is intentionally conservative: it only searches windows/sheets for native
        dialog buttons and returns not_found when no dialog is present, avoiding accidental
        key presses on the web page that can trigger duplicate downloads.
        """
        import subprocess
        import time

        process_name = kwargs.get("process_name", "Safari")
        button_name = kwargs.get("button_name", "Allow")
        wait_time = float(kwargs.get("wait_time", 1))
        retry = int(kwargs.get("retry", 3))
        candidates = [name.strip() for name in str(button_name).split(",") if name.strip()]

        def click_one(expected):
            script = f'''
tell application "System Events"
    if not (exists process "{process_name}") then return "process_not_found"
    tell process "{process_name}"
        repeat with w in windows
            try
                click button "{expected}" of w
                return "clicked:window_button"
            end try
            try
                repeat with s in sheets of w
                    try
                        click button "{expected}" of s
                        return "clicked:sheet_button"
                    end try
                    try
                        click (first UI element of s whose title is "{expected}" or name is "{expected}" or description is "{expected}")
                        return "clicked:sheet_element"
                    end try
                end repeat
            end try
            try
                click (first UI element of w whose title is "{expected}" or name is "{expected}" or description is "{expected}")
                return "clicked:window_element"
            end try
        end repeat
    end tell
end tell
return "not_found"
'''
            result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, check=False)
            return (result.stdout or result.stderr or "").strip()

        last_output = "not_found"
        for attempt in range(max(retry, 1)):
            for expected in candidates:
                output = click_one(expected)
                last_output = f"name='{expected}' -> {output}"
                LOGGER_INFO(f"click_macos_dialog_button attempt {attempt + 1}: {last_output}")
                if "clicked" in output:
                    time.sleep(wait_time)
                    return {"status": "success", "message": last_output}
            time.sleep(1)

        LOGGER_INFO(f"click_macos_dialog_button not found: {last_output}")
        time.sleep(wait_time)
        return {"status": "not_found", "message": last_output}

    def _resolve_webex_process_name(self, process_name="auto"):
        import subprocess

        if process_name and str(process_name).lower() != "auto":
            return process_name

        script = '''
tell application "System Events"
    set processNames to name of every process whose visible is true
    return processNames
end tell
'''
        result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, check=False)
        output = (result.stdout or "").strip()
        names = [item.strip() for item in output.split(",") if item.strip()]
        for item in names:
            lower_name = item.lower()
            if "webex" in lower_name and "toolhub" not in lower_name and "installer" not in lower_name:
                LOGGER_INFO(f"Resolved Webex process name from visible apps: {item}")
                return item
        LOGGER_INFO(f"Could not resolve visible Webex process from: {names}")
        return "Webex"

    def _get_macos_process_window_bounds(self, process_name="auto", retry=10):
        import subprocess
        import time

        output = ""
        for attempt in range(max(int(retry), 1)):
            resolved_process_name = self._resolve_webex_process_name(process_name)
            if resolved_process_name != "Webex":
                subprocess.run(
                    ["osascript", "-e", f'tell application "System Events" to set frontmost of process "{resolved_process_name}" to true'],
                    check=False,
                )
            else:
                subprocess.run(["open", "/Applications/Webex.app"], check=False)
            time.sleep(1)
            script = f'''
tell application "System Events"
    if not (exists process "{resolved_process_name}") then return "process_not_found"
    tell process "{resolved_process_name}"
        set frontmost to true
        if not (exists window 1) then return "window_not_found"
        set windowPosition to position of window 1
        set windowSize to size of window 1
        return (item 1 of windowPosition as text) & "," & (item 2 of windowPosition as text) & "," & (item 1 of windowSize as text) & "," & (item 2 of windowSize as text)
    end tell
end tell
'''
            result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, check=False)
            output = (result.stdout or result.stderr or "").strip()
            try:
                bounds = [float(part.strip()) for part in output.split(",")]
                LOGGER_INFO(f"Using Webex process for guest info input: {resolved_process_name}")
                return resolved_process_name, bounds
            except Exception as exc:
                LOGGER_INFO(
                    f"_get_macos_process_window_bounds retry {attempt + 1}/{retry} failed: {output}, error: {exc}"
                )
        raise RuntimeError(f"Failed to read Webex window bounds: {output}")

    def _click_macos_window_bounds_relative(self, bounds, x_ratio, y_ratio):
        import time
        from core.mac._input import Mouse

        x, y, width, height = bounds
        click_x = int(x + width * float(x_ratio))
        click_y = int(y + height * float(y_ratio))
        Mouse().click_mouse_button_left((click_x, click_y))
        LOGGER_INFO(f"Clicked Webex at ({click_x}, {click_y}) using ratios ({x_ratio}, {y_ratio})")
        time.sleep(0.5)

    def _paste_macos_text(self, text):
        import subprocess
        import time
        from core.mac.RSKeyboard import CRSKeyboard

        subprocess.run("pbcopy", text=True, input=str(text), check=False)
        CRSKeyboard.SendKeys(["command", "a"])
        CRSKeyboard.CommandV()
        time.sleep(0.5)

    def fill_webex_guest_name(self, **kwargs):
        """Fill the Name field on the Webex guest information page."""
        import time

        process_name = kwargs.get("process_name", "auto")
        guest_name = kwargs.get("guest_name", "mia")
        retry = int(kwargs.get("retry", 10))
        wait_time = float(kwargs.get("wait_time", 1))
        name_x_ratio = float(kwargs.get("name_x_ratio", 0.50))
        name_y_ratio = float(kwargs.get("name_y_ratio", 0.345))

        _, bounds = self._get_macos_process_window_bounds(process_name=process_name, retry=retry)
        self._click_macos_window_bounds_relative(bounds, name_x_ratio, name_y_ratio)
        self._paste_macos_text(guest_name)
        LOGGER_INFO(f"Filled Webex guest name: {guest_name}")
        time.sleep(wait_time)
        return guest_name

    def extract_webex_guest_captcha(self, **kwargs):
        """Capture the Webex guest page and return the visible verification characters."""
        import os
        import re

        from common.utils.logger import LOGGER_ERROR
        from config.paths import FULLSCREEN_IMAGE_PATH
        from models.openai_client import OpenAIClient
        from rs_sdk.utils.image_handler import capture_full_screen, save_image

        screenshot_name = kwargs.get("screenshot_name", "webex_guest_captcha")
        result = capture_full_screen(1)
        if result.img is None:
            message = "Failed to capture screen for captcha recognition."
            LOGGER_ERROR(message)
            raise RuntimeError(message)

        save_image(screenshot_name, img=result.img, output_path=FULLSCREEN_IMAGE_PATH.as_posix())
        image_path = os.path.join(FULLSCREEN_IMAGE_PATH.as_posix(), f"{screenshot_name}.jpg")
        prompt = kwargs.get("prompt") or (
            "The screenshot shows a Webex guest join page. Read the green verification "
            "characters displayed inside the white captcha image. Return only the exact "
            "characters, using lowercase letters if they are letters. Do not include any "
            "explanation, spaces, punctuation, labels, or quotes. Pay close attention to "
            "digits versus letters; for example, return digit 8 as 8, not g."
        )
        ai_result = OpenAIClient().ai_analyze_image(image_path, message=prompt)
        LOGGER_INFO(f"Captcha AI raw result: {ai_result}")
        captcha = re.sub(r"[^A-Za-z0-9]", "", str(ai_result or "")).lower()
        if not captcha:
            raise RuntimeError(f"Failed to extract captcha characters from AI result: {ai_result}")
        LOGGER_INFO(f"Extracted Webex captcha characters: {captcha}")
        return captcha

    def fill_webex_guest_captcha(self, **kwargs):
        """Fill the verification characters field on the Webex guest information page."""
        import time

        process_name = kwargs.get("process_name", "auto")
        captcha = kwargs.get("captcha", "")
        retry = int(kwargs.get("retry", 10))
        wait_time = float(kwargs.get("wait_time", 1))
        captcha_x_ratio = float(kwargs.get("captcha_x_ratio", 0.50))
        captcha_y_ratio = float(kwargs.get("captcha_y_ratio", 0.615))
        captcha = self._resolve_action_variables(captcha)
        if not captcha:
            raise ValueError("fill_webex_guest_captcha requires captcha text")

        _, bounds = self._get_macos_process_window_bounds(process_name=process_name, retry=retry)
        self._click_macos_window_bounds_relative(bounds, captcha_x_ratio, captcha_y_ratio)
        self._paste_macos_text(captcha)
        LOGGER_INFO(f"Filled Webex captcha characters: {captcha}")
        time.sleep(wait_time)
        return captcha

    def fill_webex_guest_info_with_captcha(self, **kwargs):
        """Backward-compatible wrapper for filling name, extracting captcha, and filling captcha."""
        guest_name = kwargs.get("guest_name", kwargs.get("name", "mia"))
        self.fill_webex_guest_name(**{**kwargs, "guest_name": guest_name})
        captcha = self.extract_webex_guest_captcha(**kwargs)
        self.fill_webex_guest_captcha(**{**kwargs, "captcha": captcha})
        return captcha

    def _webex_guest_captcha_error_visible(self, **kwargs):
        """Return True when the Webex guest information page shows the captcha error."""
        process_name = kwargs.get("process_name", "Webex")
        bundle_id = kwargs.get("bundle_id", "Cisco-Systems.Spark")
        error_texts = kwargs.get("error_texts", ["Incorrect characters", "Try again"])
        expected = [str(text).lower() for text in error_texts if str(text).strip()]

        def _matches(text):
            lower_text = str(text or "").lower()
            return any(item in lower_text for item in expected)

        try:
            from core.mac.RSApplication import CRSApplication

            app_ref = CRSApplication.ApplicationByBundleID(bundle_id)
            if app_ref is None:
                LOGGER_INFO("Webex captcha error check: Webex app reference not found")
                return False
            app_ref.activate()

            def walk(elem, depth=0):
                if depth > 10:
                    return False
                for attr in ("AXTitle", "AXDescription", "AXValue"):
                    try:
                        if _matches(getattr(elem, attr)):
                            return True
                    except Exception:
                        pass
                try:
                    children = elem.AXChildren or []
                except Exception:
                    children = []
                return any(walk(child, depth + 1) for child in children)

            for win in list(app_ref.windows()):
                if walk(win):
                    LOGGER_INFO("Webex captcha error check: found captcha validation error by AX")
                    return True
        except Exception as exc:
            LOGGER_INFO(f"Webex captcha error AX check failed: {exc}")

        try:
            import subprocess

            script = f'''
on error_visible(target_element)
    try
        set elementTitle to ""
        try
            set elementTitle to title of target_element as text
        end try
        set elementName to ""
        try
            set elementName to name of target_element as text
        end try
        set elementDescription to ""
        try
            set elementDescription to description of target_element as text
        end try
        set elementValue to ""
        try
            set elementValue to value of target_element as text
        end try
        set allText to elementTitle & " " & elementName & " " & elementDescription & " " & elementValue
        if allText contains "Incorrect characters" or allText contains "Try again" then return true
    end try
    try
        repeat with child_element in UI elements of target_element
            if my error_visible(child_element) then return true
        end repeat
    end try
    return false
end error_visible

tell application "System Events"
    if not (exists process "{process_name}") then return "process_not_found"
    tell process "{process_name}"
        repeat with w in windows
            if my error_visible(w) then return "error_visible"
        end repeat
    end tell
end tell
return "not_found"
'''
            result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, check=False)
            output = (result.stdout or result.stderr or "").strip()
            LOGGER_INFO(f"Webex captcha error AppleScript check: {output}")
            if output == "error_visible":
                return True
        except Exception as exc:
            LOGGER_INFO(f"Webex captcha error AppleScript check failed: {exc}")

        try:
            import os

            from config.paths import FULLSCREEN_IMAGE_PATH
            from models.openai_client import OpenAIClient
            from rs_sdk.utils.image_handler import capture_full_screen, save_image

            screenshot_name = kwargs.get("error_screenshot_name", "webex_guest_captcha_error_check")
            result = capture_full_screen(1)
            if result.img is None:
                return False
            save_image(screenshot_name, img=result.img, output_path=FULLSCREEN_IMAGE_PATH.as_posix())
            image_path = os.path.join(FULLSCREEN_IMAGE_PATH.as_posix(), f"{screenshot_name}.jpg")
            ai_result = OpenAIClient().ai_analyze_image(
                image_path,
                message=(
                    "Check whether this Webex page shows a red captcha validation error such as "
                    "'Incorrect characters. Try again.' Return only YES or NO."
                ),
            )
            LOGGER_INFO(f"Webex captcha error AI check: {ai_result}")
            return str(ai_result or "").strip().lower().startswith("yes")
        except Exception as exc:
            LOGGER_INFO(f"Webex captcha error AI check failed: {exc}")
            return False

    def _webex_guest_prejoin_page_visible(self, **kwargs):
        """Return True when Webex has moved from guest verification to the pre-join page."""
        process_name = kwargs.get("process_name", "Webex")
        bundle_id = kwargs.get("bundle_id", "Cisco-Systems.Spark")
        expected_texts = kwargs.get("expected_texts", ["Get ready to join", "Join meeting"])
        expected = [str(text).lower() for text in expected_texts if str(text).strip()]

        def _matches(text):
            lower_text = str(text or "").lower()
            return any(item in lower_text for item in expected)

        try:
            from core.mac.RSApplication import CRSApplication

            app_ref = CRSApplication.ApplicationByBundleID(bundle_id)
            if app_ref is None:
                LOGGER_INFO("Webex pre-join page check: Webex app reference not found")
                return False
            app_ref.activate()

            def walk(elem, depth=0):
                if depth > 10:
                    return False
                for attr in ("AXTitle", "AXDescription", "AXValue"):
                    try:
                        if _matches(getattr(elem, attr)):
                            return True
                    except Exception:
                        pass
                try:
                    children = elem.AXChildren or []
                except Exception:
                    children = []
                return any(walk(child, depth + 1) for child in children)

            for win in list(app_ref.windows()):
                if walk(win):
                    LOGGER_INFO("Webex pre-join page check: found pre-join text by AX")
                    return True
        except Exception as exc:
            LOGGER_INFO(f"Webex pre-join page AX check failed: {exc}")

        try:
            import subprocess

            expected_script = " or ".join([f'allText contains "{text}"' for text in expected_texts])
            script = f'''
on prejoin_visible(target_element)
    try
        set elementTitle to ""
        try
            set elementTitle to title of target_element as text
        end try
        set elementName to ""
        try
            set elementName to name of target_element as text
        end try
        set elementDescription to ""
        try
            set elementDescription to description of target_element as text
        end try
        set elementValue to ""
        try
            set elementValue to value of target_element as text
        end try
        set allText to elementTitle & " " & elementName & " " & elementDescription & " " & elementValue
        if {expected_script} then return true
    end try
    try
        repeat with child_element in UI elements of target_element
            if my prejoin_visible(child_element) then return true
        end repeat
    end try
    return false
end prejoin_visible

tell application "System Events"
    if not (exists process "{process_name}") then return "process_not_found"
    tell process "{process_name}"
        repeat with w in windows
            if my prejoin_visible(w) then return "prejoin_visible"
        end repeat
    end tell
end tell
return "not_found"
'''
            result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, check=False)
            output = (result.stdout or result.stderr or "").strip()
            LOGGER_INFO(f"Webex pre-join page AppleScript check: {output}")
            if output == "prejoin_visible":
                return True
        except Exception as exc:
            LOGGER_INFO(f"Webex pre-join page AppleScript check failed: {exc}")

        try:
            import os

            from config.paths import FULLSCREEN_IMAGE_PATH
            from models.openai_client import OpenAIClient
            from rs_sdk.utils.image_handler import capture_full_screen, save_image

            screenshot_name = kwargs.get("prejoin_screenshot_name", "webex_guest_prejoin_check")
            result = capture_full_screen(1)
            if result.img is None:
                return False
            save_image(screenshot_name, img=result.img, output_path=FULLSCREEN_IMAGE_PATH.as_posix())
            image_path = os.path.join(FULLSCREEN_IMAGE_PATH.as_posix(), f"{screenshot_name}.jpg")
            ai_result = OpenAIClient().ai_analyze_image(
                image_path,
                message=(
                    "Check whether this Webex screenshot is the pre-join page after guest verification. "
                    "Return YES only if it shows the 'Get ready to join' / pre-join page with a meeting title "
                    "or personal room name and a 'Join meeting' button. Return NO if it is still the guest "
                    "information/captcha page, shows an incorrect characters error, is loading, or is any other page. "
                    "Return only YES or NO."
                ),
            )
            LOGGER_INFO(f"Webex pre-join page AI check: {ai_result}")
            return str(ai_result or "").strip().lower().startswith("yes")
        except Exception as exc:
            LOGGER_INFO(f"Webex pre-join page AI check failed: {exc}")
            return False

    def click_webex_guest_next_with_captcha_retry(self, **kwargs):
        """Click Next and retry refreshed captcha until Webex reaches the pre-join page."""
        import time

        process_name = kwargs.get("process_name", "Webex")
        button_name = kwargs.get("button_name", "Next")
        refresh_button_name = kwargs.get("refresh_button_name", "Refresh captcha")
        retry = int(kwargs.get("retry", 5))
        wait_time = float(kwargs.get("wait_time", 2))
        wait_after_next = float(kwargs.get("wait_after_next", 2))
        captcha_retry = int(kwargs.get("captcha_retry", 5))
        wait_after_refresh = float(kwargs.get("wait_after_refresh", 1))
        screenshot_name = kwargs.get("screenshot_name", "webex_guest_captcha_retry")
        captcha = None

        click_result = self.click_macos_button(
            process_name=process_name,
            button_name=button_name,
            retry=retry,
            wait_time=wait_after_next,
        )
        for attempt in range(max(captcha_retry, 0) + 1):
            if self._webex_guest_prejoin_page_visible(
                process_name=process_name,
                prejoin_screenshot_name=f"{screenshot_name}_prejoin_{attempt + 1}",
            ):
                LOGGER_INFO("Webex guest verification succeeded; pre-join page is visible")
                time.sleep(wait_time)
                return {"status": "success", "message": f"clicked_next_prejoin_visible:{captcha or 'initial_captcha'}"}

            if attempt >= max(captcha_retry, 0):
                break

            captcha_error_visible = self._webex_guest_captcha_error_visible(
                process_name=process_name,
                error_screenshot_name=f"{screenshot_name}_error_{attempt + 1}",
            )
            LOGGER_INFO(
                "Webex pre-join page is not visible after Next; "
                f"captcha_error_visible={captcha_error_visible}. Refreshing captcha and retrying "
                f"({attempt + 1}/{captcha_retry})"
            )

            self.click_macos_button(
                process_name=process_name,
                button_name=refresh_button_name,
                retry=retry,
                wait_time=wait_after_refresh,
            )

            captcha = self.extract_webex_guest_captcha(screenshot_name=f"{screenshot_name}_{attempt + 1}")
            self.fill_webex_guest_captcha(
                process_name=kwargs.get("captcha_process_name", "auto"),
                captcha=captcha,
                retry=kwargs.get("captcha_field_retry", 10),
                wait_time=kwargs.get("captcha_wait_time", 1),
            )
            click_result = self.click_macos_button(
                process_name=process_name,
                button_name=button_name,
                retry=retry,
                wait_time=wait_after_next,
            )

        message = "Webex pre-join page is still not visible after captcha refresh/retry"
        LOGGER_ERROR(message)
        time.sleep(wait_time)
        raise RuntimeError(message)

    def close_webex_app(self, **kwargs):
        """Close Webex desktop app on macOS without relying on keyboard focus."""
        import subprocess
        import time
        import json

        bundle_id = kwargs.get("bundle_id", "Cisco-Systems.Spark")
        app_name = kwargs.get("app_name", "Webex")
        wait_time = float(kwargs.get("wait_time", 3))

        try:
            from core.mac import terminate_app_by_bundle_id

            terminate_app_by_bundle_id(bundle_id)
            LOGGER_INFO(f"Requested Webex termination by bundle id: {bundle_id}")
        except Exception as exc:
            LOGGER_ERROR(f"Failed to terminate by bundle id '{bundle_id}': {exc}. Falling back to AppleScript/pkill.")
            subprocess.run(["osascript", "-e", f'tell application "{app_name}" to quit'], check=False)
            time.sleep(1)
            subprocess.run(["pkill", "-x", app_name], check=False)

        time.sleep(wait_time)
        process_check = subprocess.run(["pgrep", "-x", app_name], capture_output=True, text=True, check=False)
        if process_check.returncode == 0:
            LOGGER_ERROR(f"{app_name} main process is still running after termination request. Trying pkill fallback.")
            subprocess.run(["pkill", "-x", app_name], check=False)
            time.sleep(1)
            process_check = subprocess.run(["pgrep", "-x", app_name], capture_output=True, text=True, check=False)

        if process_check.returncode == 0:
            message = f"Failed to close {app_name}; main process is still running: {process_check.stdout.strip()}"
            LOGGER_ERROR(message)
            raise RuntimeError(message)

        LOGGER_INFO(f"{app_name} app closed successfully; no main process found.")
        return {"status": "success", "message": f"Closed {app_name}"}

    def input_macos_text(self, **kwargs):
        """Input text into the current macOS/Webex text field without normal metadata lookup."""
        import subprocess
        import time

        from common.handler.settingsHandler import DynamicConfig
        from config.account_config import account_config
        from config.paths import SETTINGS_PATH
        from core.mac.RSKeyboard import CRSKeyboard

        value = kwargs.get("value")
        field_hint = str(kwargs.get("field_hint", "")).lower()
        bundle_id = kwargs.get("bundle_id", "Cisco-Systems.Spark")
        wait_time = float(kwargs.get("wait_time", 1))

        settings = DynamicConfig(SETTINGS_PATH)
        account = settings.get("account")

        if value == "${email}":
            input_text = account_config.get_email(account)
            if input_text is None:
                message = f"Account '{account}' does not have an email configured."
                LOGGER_ERROR(message)
                raise Exception(message)
        elif value == "${password}":
            input_text = account_config.get_password(account)
            if input_text is None:
                message = f"Account '{account}' does not have a password configured."
                LOGGER_ERROR(message)
                raise Exception(message)
        elif value is not None:
            input_text = self._resolve_action_variables(value)
        else:
            message = "input_macos_text requires 'value'."
            LOGGER_ERROR(message)
            raise ValueError(message)

        def _matches_hint(elem, role=None):
            if field_hint == "password" and role == "AXSecureTextField":
                return True
            if not field_hint:
                return True
            names = []
            for attr in ("AXTitle", "AXDescription", "AXValue", "avaliableInfo"):
                try:
                    item = getattr(elem, attr)
                    if item:
                        names.append(str(item).lower())
                except Exception:
                    pass
            if any(field_hint in item for item in names):
                return True
            return field_hint in ("email", "password") and role in ("AXTextField", "AXSecureTextField")

        def _find_text_field(elem, depth=0):
            if depth > 10:
                return None
            try:
                role = elem.AXRole
            except Exception:
                role = getattr(elem, "role", None)

            if role in ("AXTextField", "AXSecureTextField", "AXTextArea", "AXTextView") and _matches_hint(elem, role):
                return elem

            try:
                children = elem.AXChildren or []
            except Exception:
                try:
                    children = elem.children or []
                except Exception:
                    children = []

            for child in children:
                found = _find_text_field(child, depth + 1)
                if found is not None:
                    return found
            return None

        focused_input = False
        try:
            from core.mac.RSApplication import CRSApplication

            app_ref = CRSApplication.ApplicationByBundleID(bundle_id)
            if app_ref is not None:
                app_ref.activate()
                windows = list(app_ref.windows())
                for win in windows:
                    text_field = _find_text_field(win)
                    if text_field is None:
                        continue
                    try:
                        win.perform_ax_action("AXRaise")
                    except Exception:
                        pass
                    try:
                        text_field.set_string("AXFocused", "true")
                    except Exception:
                        pass
                    try:
                        text_field.perform_ax_action("AXPress")
                    except Exception:
                        pass
                    focused_input = True
                    break
        except Exception as exc:
            LOGGER_ERROR(f"input_macos_text failed to focus text field via AX: {exc}")

        subprocess.run("pbcopy", text=True, input=str(input_text), check=False)
        CRSKeyboard.CommandV()
        time.sleep(wait_time)
        LOGGER_INFO(f"input_macos_text pasted value for field_hint='{field_hint}' focused_input={focused_input}")
        return {"status": "success", "message": "input pasted"}

    def click_macos_button(self, **kwargs):
        """Click a macOS button by name without relying on the framework's current AX context.

        For Webex, prefer native AX traversal + AXPress across all Webex windows. This is more
        reliable for the separate pre-join window than the normal `key` action. Fall back to
        System Events for Safari/system dialogs. Despite the function name, this also supports
        links such as the guest pre-join "sign in" element.
        """
        import subprocess
        import time
        import json

        button_name = kwargs.get("button_name")
        process_name = kwargs.get("process_name")
        bundle_id = kwargs.get("bundle_id", "Cisco-Systems.Spark")
        wait_time = float(kwargs.get("wait_time", 1))
        retry = int(kwargs.get("retry", 3))
        if not button_name:
            raise ValueError("click_macos_button requires 'button_name'")

        candidates = [name.strip() for name in str(button_name).split(",") if name.strip()]

        def _text_matches(text, expected):
            return bool(text) and expected.lower() in str(text).lower()

        def _click_webex_button_with_ax():
            if process_name and process_name.lower() != "webex":
                return None
            try:
                from core.mac.RSApplication import CRSApplication

                app_ref = CRSApplication.ApplicationByBundleID(bundle_id)
                if app_ref is None:
                    return None
                app_ref.activate()
                windows = list(app_ref.windows())

                def walk(elem, expected, depth=0):
                    if depth > 10:
                        return None
                    try:
                        role = elem.AXRole
                    except Exception:
                        role = None
                    names = []
                    for attr in ("AXTitle", "AXDescription", "AXValue"):
                        try:
                            value = getattr(elem, attr)
                            if value:
                                names.append(str(value))
                        except Exception:
                            pass
                    if role in ("AXButton", "AXLink", "AXStaticText", "AXGroup") and any(_text_matches(name, expected) for name in names):
                        return elem
                    try:
                        children = elem.AXChildren or []
                    except Exception:
                        children = []
                    for child in children:
                        found = walk(child, expected, depth + 1)
                        if found is not None:
                            return found
                    return None

                for expected in candidates:
                    for win in windows:
                        button = walk(win, expected)
                        if button is not None:
                            try:
                                win.perform_ax_action("AXRaise")
                            except Exception:
                                pass
                            button.perform_ax_action("AXPress")
                            return f"clicked:AXPress:{expected}"
            except Exception as exc:
                return f"ax_error:{exc}"
            return None

        def _click_safari_text_with_js(expected):
            if process_name and process_name.lower() != "safari":
                return None
            js_code = f"""
(() => {{
  const expected = {json.dumps(expected.lower())};
  const normalize = (text) => (text || '').replace(/\s+/g, ' ').trim().toLowerCase();
  const candidates = Array.from(document.querySelectorAll('button, a, [role="button"], [tabindex], div, span'));
  const target = candidates.find((element) => normalize(element.innerText || element.textContent).includes(expected));
  if (!target) return 'not_found';
  target.scrollIntoView({{ block: 'center', inline: 'center' }});
  target.click();
  return 'clicked:javascript';
}})();
"""
            script = f'''
tell application "Safari"
    if not (exists front window) then return "window_not_found"
    try
        return do JavaScript {json.dumps(js_code)} in current tab of front window
    on error errMsg
        return "js_error:" & errMsg
    end try
end tell
'''
            result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, check=False)
            return (result.stdout or result.stderr or "").strip()

        def _click_with_system_events(expected):
            process_block = (
                f'tell process "{process_name}"' if process_name
                else 'set frontProc to first application process whose frontmost is true\n    tell frontProc'
            )
            exists_check = f'if not (exists process "{process_name}") then return "process_not_found"\n    ' if process_name else ""
            script = f'''
on click_matching_element(target_element, expected_text)
    try
        set elementTitle to ""
        try
            set elementTitle to title of target_element as text
        end try
        set elementName to ""
        try
            set elementName to name of target_element as text
        end try
        set elementDescription to ""
        try
            set elementDescription to description of target_element as text
        end try
        if elementTitle contains expected_text or elementName contains expected_text or elementDescription contains expected_text then
            click target_element
            return true
        end if
    end try
    try
        repeat with child_element in UI elements of target_element
            if my click_matching_element(child_element, expected_text) then return true
        end repeat
    end try
    return false
end click_matching_element

tell application "System Events"
    {exists_check}{process_block}
        repeat with w in windows
            try
                if my click_matching_element(w, "{expected}") then return "clicked:recursive"
            end try
            try
                click (first UI element of w whose title contains "{expected}" or name contains "{expected}" or description contains "{expected}")
                return "clicked:window"
            end try
            try
                repeat with s in sheets of w
                    try
                        click (first UI element of s whose title contains "{expected}" or name contains "{expected}" or description contains "{expected}")
                        return "clicked:sheet"
                    end try
                end repeat
            end try
            try
                repeat with g in groups of w
                    try
                        click (first UI element of g whose title contains "{expected}" or name contains "{expected}" or description contains "{expected}")
                        return "clicked:group"
                    end try
                end repeat
            end try
        end repeat
    end tell
end tell
return "not_found"
'''
            result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, check=False)
            return (result.stdout or result.stderr or "").strip()

        last_output = "not_found"
        for attempt in range(max(retry, 1)):
            ax_output = _click_webex_button_with_ax()
            if ax_output and ax_output.startswith("clicked"):
                LOGGER_INFO(f"click_macos_button attempt {attempt + 1}: {ax_output}")
                time.sleep(wait_time)
                return {"status": "success", "message": ax_output}
            if ax_output:
                last_output = ax_output

            for expected in candidates:
                js_output = _click_safari_text_with_js(expected)
                if js_output:
                    last_output = f"name='{expected}' -> {js_output}"
                    LOGGER_INFO(f"click_macos_button attempt {attempt + 1}: {last_output}")
                    if "clicked" in js_output:
                        time.sleep(wait_time)
                        return {"status": "success", "message": last_output}

                output = _click_with_system_events(expected)
                last_output = f"name='{expected}' -> {output}"
                LOGGER_INFO(f"click_macos_button attempt {attempt + 1}: {last_output}")
                if "clicked" in output:
                    time.sleep(wait_time)
                    return {"status": "success", "message": last_output}
            time.sleep(1)

        LOGGER_ERROR(f"click_macos_button failed: {last_output}")
        time.sleep(wait_time)
        return {"status": "not_found", "message": last_output}

    def connect_webex_app_main_window(self, **kwargs):
        """Connect to and raise the Webex main/pre-join window on macOS."""
        import time
        from common.handler.settingsHandler import DynamicConfig
        from config.paths import SETTINGS_PATH
        from core.mac.RSApplication import CRSApplication

        settings = DynamicConfig(SETTINGS_PATH)
        bundle_id = kwargs.get("bundle_id") or settings.get("bundleID") or "Cisco-Systems.Spark"
        target_button = kwargs.get("target_button", "Join meeting")
        wait_time = float(kwargs.get("wait_time", 15))
        deadline = time.time() + max(wait_time, 1)

        def _window_has_button(win, name):
            def walk(elem, depth=0):
                if depth > 10:
                    return False
                try:
                    role = elem.AXRole
                except Exception:
                    role = None
                names = []
                for attr in ("AXTitle", "AXDescription", "AXValue"):
                    try:
                        value = getattr(elem, attr)
                        if value:
                            names.append(str(value))
                    except Exception:
                        pass
                if role in ("AXButton", "AXLink", "AXStaticText", "AXGroup") and any(name.lower() in item.lower() for item in names):
                    return True
                try:
                    children = elem.AXChildren or []
                except Exception:
                    children = []
                return any(walk(child, depth + 1) for child in children)
            return walk(win)

        last_error = None
        while time.time() < deadline:
            try:
                app_ref = CRSApplication.ApplicationByBundleID(bundle_id)
                if app_ref is not None:
                    app_ref.activate()
                    windows = list(app_ref.windows())
                    if windows:
                        target_window = next((win for win in windows if _window_has_button(win, target_button)), windows[0])
                        target_window.perform_ax_action("AXRaise")
                        LOGGER_INFO(f"Connected to Webex app window by bundle id: {bundle_id}")
                        return {"status": "success", "message": "Connected to Webex app window"}
            except Exception as exc:
                last_error = exc
            time.sleep(0.5)

        message = f"Failed to connect Webex app window by bundle id '{bundle_id}': {last_error}"
        LOGGER_ERROR(message)
        raise RuntimeError(message)

    def send_stress_message_to_webex(self, **kwargs):
        from core.managers.function_loader import FunctionLoader

        function_loader = FunctionLoader()
        function_name = "send_stress_message_to_webex"
        if function_loader.get_function_info(function_name) is None:
            raise AttributeError(f"Unknown function: {function_name}")

        return function_loader.execute_function(function_name, **kwargs)

    def open_terminal_and_run_command(self, **kwargs):
        from core.managers.function_loader import FunctionLoader

        function_loader = FunctionLoader()
        function_name = "open_terminal_and_run_command"
        if function_loader.get_function_info(function_name) is None:
            raise AttributeError(f"Unknown function: {function_name}")

        return function_loader.execute_function(function_name, **self._resolve_action_variables(kwargs))

    def close_terminal_session(self, **kwargs):
        from core.managers.function_loader import FunctionLoader

        function_loader = FunctionLoader()
        function_name = "close_terminal_session"
        if function_loader.get_function_info(function_name) is None:
            raise AttributeError(f"Unknown function: {function_name}")

        return function_loader.execute_function(function_name, **self._resolve_action_variables(kwargs))

    def open_background_process_and_run_command(self, **kwargs):
        from core.managers.function_loader import FunctionLoader

        function_loader = FunctionLoader()
        function_name = "open_background_process_and_run_command"
        if function_loader.get_function_info(function_name) is None:
            raise AttributeError(f"Unknown function: {function_name}")

        return function_loader.execute_function(function_name, **self._resolve_action_variables(kwargs))

    def close_background_process_session(self, **kwargs):
        from core.managers.function_loader import FunctionLoader

        function_loader = FunctionLoader()
        function_name = "close_background_process_session"
        if function_loader.get_function_info(function_name) is None:
            raise AttributeError(f"Unknown function: {function_name}")

        return function_loader.execute_function(function_name, **self._resolve_action_variables(kwargs))

    def replace_txt_file(self, **kwargs):
        from core.managers.function_loader import FunctionLoader

        function_loader = FunctionLoader()
        function_name = "replace_txt_file"
        if function_loader.get_function_info(function_name) is None:
            raise AttributeError(f"Unknown function: {function_name}")

        return function_loader.execute_function(function_name, **kwargs)

    def start_wme_thread_monitor(self, **kwargs):
        from core.managers.function_loader import FunctionLoader

        function_loader = FunctionLoader()
        function_name = "start_wme_thread_monitor"
        if function_loader.get_function_info(function_name) is None:
            raise AttributeError(f"Unknown function: {function_name}")

        return function_loader.execute_function(function_name, **self._resolve_action_variables(kwargs))

    def finalize_wme_thread_monitor(self, **kwargs):
        from core.managers.function_loader import FunctionLoader

        function_loader = FunctionLoader()
        function_name = "finalize_wme_thread_monitor"
        if function_loader.get_function_info(function_name) is None:
            raise AttributeError(f"Unknown function: {function_name}")

        return function_loader.execute_function(function_name, **self._resolve_action_variables(kwargs))

    def connect_webex_window(self, **kwargs):
        from core.mac.AXClasses import NativeUIElement
        ctrl_id = kwargs.get("ctrl_id", "main_window")
        prefix_to_remove = kwargs.get("prefix_to_remove", "SparkApp.")
        if prefix_to_remove and ctrl_id.startswith(prefix_to_remove):
            ctrl_id = ctrl_id[len(prefix_to_remove):]
            ctrl_id = ctrl_id.split('.')[0]
        app_ref = kwargs.get("app_ref")
        if app_ref:
            windows = list(app_ref.windows())
            target = next((w for w in windows if w.identifier and ctrl_id in w.identifier), None)
            if target is None:
                LOGGER_ERROR(f"No window found with identifier containing '{ctrl_id}'")
                return
            target.perform_ax_action("AXRaise")
            app_ref.activate()
            LOGGER_INFO(f"Connected to Webex window with identifier containing '{ctrl_id}'")

    def ai_verify_current_state(self, **kwargs):
        import os
        from rs_sdk.utils.image_handler import capture_full_screen, save_image
        from config.paths import FULLSCREEN_IMAGE_PATH
        from models.openai_client import OpenAIClient

        prompt = kwargs.get("prompt", None)
        if prompt is None:
            prompt = (
                "Analyze the current application state. "
                "Describe: 1) What window or screen is visible? "
                "2) Are the expected UI controls present? "
                "3) Is there any error message or unexpected state? "
                "Output format: "
                "If the state looks correct, respond '[SUCCESS]Success. [Brief description].' "
                "If something looks wrong, respond '[FAILURE]Failed. [What is wrong].' "
                "Only output 1 sentence."
            )

        step_name = kwargs.get("step_name", "ai_verify")
        result = capture_full_screen(1)
        if result.img is None:
            LOGGER_ERROR("[ai_verify_current_state] Failed to capture screen")
            return "[FAILURE]Failed. Could not capture screenshot."

        save_image(step_name, img=result.img, output_path=FULLSCREEN_IMAGE_PATH.as_posix())
        image_path = os.path.join(FULLSCREEN_IMAGE_PATH.as_posix(), f"{step_name}.jpg")

        LOGGER_INFO(f"[ai_verify_current_state] Screenshot saved: {image_path}")
        client = OpenAIClient()
        ai_result = client.ai_analyze_image(image_path, message=prompt)

        if ai_result:
            LOGGER_INFO(f"[ai_verify_current_state] AI result: {ai_result}")
        else:
            ai_result = "[FAILURE]Failed. AI analysis returned no result."
            LOGGER_ERROR(f"[ai_verify_current_state] {ai_result}")

        return ai_result