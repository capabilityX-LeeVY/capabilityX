import base64
import io
import mss
import platform
import time

from pathlib import Path
from PIL import ImageGrab, Image
from mimetypes import guess_type
from collections import namedtuple
from common.utils.logger import LOGGER_ERROR, LOGGER_DEBUG


ImageCaptureResult = namedtuple('ImageCaptureResult', ['byte_data', 'img'])

def image_base64_encode(image_path):
    mime_type, _ = guess_type(image_path)
    mime_type = mime_type or 'application/octet-stream'
    with open(image_path, "rb") as image_file:
        base64_encoded_data = base64.b64encode(image_file.read()).decode('utf-8')
    return f"data:{mime_type};base64,{base64_encoded_data}"

# def capture_image_from_currentBoundingRectangle(control_bounding_rect, padding=10, left_extra=0, right_extra=0, top_extra=0, bottom_extra=0):
#     try:
#         if platform.system().lower() == 'windows':
#             left = control_bounding_rect.left
#             top = control_bounding_rect.top
#             right = control_bounding_rect.right
#             bottom = control_bounding_rect.bottom
#         elif platform.system().lower() == 'darwin':
#             left = control_bounding_rect.x
#             top = control_bounding_rect.y
#             right = control_bounding_rect.x + control_bounding_rect.width
#             bottom = control_bounding_rect.y + control_bounding_rect.height
#             left, top, right, bottom = map(int, (left, top, right, bottom))
#         left -= (padding + left_extra)
#         right += (padding + right_extra)
#         top -= (padding - top_extra)
#         bottom += (padding - bottom_extra)
#         with mss.mss() as sct:
#             screenshot = sct.grab({'left': left, 'top': top, 'width': right - left, 'height': bottom - top})
#             img = Image.frombytes('RGB', (screenshot.width, screenshot.height), screenshot.rgb)
#         byte_io = io.BytesIO()
#         img.save(byte_io, format='png')
#         byte_data = byte_io.getvalue()
#         return ImageCaptureResult(byte_data=byte_data, img=img)
#     except Exception as e:
#         LOGGER_ERROR(f"Error capturing image: {e}")
#         return ImageCaptureResult(byte_data=None, img=None)

_cached_scale_factor = None

def reset_scale_factor_cache():
    """Reset DPI scale factor cache to force re-detection"""
    global _cached_scale_factor
    _cached_scale_factor = None

def get_scale_factor():
    global _cached_scale_factor
    
    if _cached_scale_factor is not None:
        return _cached_scale_factor
    
    system = platform.system().lower()
    if system == "windows":
        try:
            import ctypes
            try:
                dpi = ctypes.windll.user32.GetDpiForSystem()
                scale = dpi / 96.0
            except:
                user32 = ctypes.windll.user32
                hdc = user32.GetDC(0)
                try:
                    dpi = ctypes.windll.gdi32.GetDeviceCaps(hdc, 88)
                    scale = dpi / 96.0
                finally:
                    user32.ReleaseDC(0, hdc)
            
            if 0.5 <= scale <= 5.0:
                _cached_scale_factor = scale
                return scale
        except:
            pass
                
    elif system == "darwin":
        try:
            import AppKit
            screen = AppKit.NSScreen.mainScreen() #type: ignore
            if screen:
                scale = screen.backingScaleFactor()
                if 0.5 <= scale <= 3.0:
                    _cached_scale_factor = scale
                    return scale
        except:
            pass
    
    _cached_scale_factor = 1.0
    return _cached_scale_factor

# def capture_image_from_currentBoundingRectangle(control_bounding_rect, padding=None, left_extra=0, right_extra=0, top_extra=0, bottom_extra=0):
#     try:
#         system = platform.system().lower()
#         if padding is None:
#             padding = 10 if system == 'windows' else 3
#         if system == 'windows':
#             left = control_bounding_rect.left
#             top = control_bounding_rect.top
#             right = control_bounding_rect.right
#             bottom = control_bounding_rect.bottom
#         elif system == 'darwin':
#             left = control_bounding_rect.x
#             top = control_bounding_rect.y
#             right = control_bounding_rect.x + control_bounding_rect.width
#             bottom = control_bounding_rect.y + control_bounding_rect.height
#             left, top, right, bottom = map(int, (left, top, right, bottom))
        
#         left -= (padding + left_extra)
#         right += (padding + right_extra)
#         top -= (padding + top_extra)
#         bottom += (padding + bottom_extra)
        
#         if system == 'windows':
#             try:
#                 with mss.mss() as sct:
#                     monitors = sct.monitors
#                     if len(monitors) > 1:
#                         min_x = min(m['left'] for m in monitors[1:])
#                         min_y = min(m['top'] for m in monitors[1:])
#                         max_x = max(m['left'] + m['width'] for m in monitors[1:])
#                         max_y = max(m['top'] + m['height'] for m in monitors[1:])
                        
#                         MAX_COORD = max_x + 1000
#                         MIN_COORD = min_x - 1000
#                     else:
#                         MAX_COORD = 30720
#                         MIN_COORD = -30720
#             except:
#                 MAX_COORD = 30720
#                 MIN_COORD = -30720
            
#             left = max(MIN_COORD, min(left, MAX_COORD))
#             top = max(MIN_COORD, min(top, MAX_COORD))
#             right = max(left + 1, min(right, MAX_COORD))
#             bottom = max(top + 1, min(bottom, MAX_COORD))
        
#         width = max(1, right - left)
#         height = max(1, bottom - top)
        
#         with mss.mss() as sct:
#             screenshot = sct.grab({'left': left, 'top': top, 'width': width, 'height': height})
#             img = Image.frombytes('RGB', (screenshot.width, screenshot.height), screenshot.rgb)
#         byte_io = io.BytesIO()
#         img.save(byte_io, format='png')
#         byte_data = byte_io.getvalue()
#         return ImageCaptureResult(byte_data=byte_data, img=img)
#     except Exception as e:
#         LOGGER_ERROR(f"Error capturing image: {e}")
#         return ImageCaptureResult(byte_data=None, img=None)

def capture_image_from_currentBoundingRectangle(
    control_bounding_rect,
    padding=None,
    left_extra=0,
    right_extra=0,
    top_extra=0,
    bottom_extra=0
):
    '''Capture image from the specified bounding rectangle with optional padding and extra margins.'''
    try:
        system = platform.system().lower()
        if padding is None:
            padding = 8 if system == 'windows' else 3
            
        scale = get_scale_factor()
        adjusted_padding = int(padding * scale)
        left_extra = int(left_extra * scale)
        right_extra = int(right_extra * scale)
        top_extra = int(top_extra * scale)
        bottom_extra = int(bottom_extra * scale)

        if system == 'windows':
            left, top, right, bottom = control_bounding_rect.left, control_bounding_rect.top, control_bounding_rect.right, control_bounding_rect.bottom
        elif system == 'darwin':
            left, top = control_bounding_rect.x, control_bounding_rect.y
            right, bottom = left + control_bounding_rect.width, top + control_bounding_rect.height
        else:
            raise RuntimeError("Unsupported platform")

        left -= adjusted_padding + left_extra
        right += adjusted_padding + right_extra
        top -= adjusted_padding + top_extra
        bottom += adjusted_padding + bottom_extra

        with mss.mss() as sct:
            if len(sct.monitors) > 1:
                monitors = sct.monitors[1:]
                min_x, min_y = min(m['left'] for m in monitors), min(m['top'] for m in monitors)
                max_x, max_y = max(m['left'] + m['width'] for m in monitors), max(m['top'] + m['height'] for m in monitors)
            else:
                min_x, min_y, max_x, max_y = 0, 0, sct.monitors[0]["width"], sct.monitors[0]["height"]
            
            left = max(min_x, min(left, max_x))
            top = max(min_y, min(top, max_y))
            right = max(left + 1, min(right, max_x))
            bottom = max(top + 1, min(bottom, max_y))

            screenshot = sct.grab({'left': left, 'top': top, 'width': right - left, 'height': bottom - top})
            img = Image.frombytes('RGB', (screenshot.width, screenshot.height), screenshot.rgb)

        byte_io = io.BytesIO()
        img.save(byte_io, format='JPEG', quality=85)
        return ImageCaptureResult(byte_data=byte_io.getvalue(), img=img)

    except Exception as e:
        LOGGER_ERROR(f"Error capturing image: {e}")
        return ImageCaptureResult(byte_data=None, img=None)

def capture_full_screen(monitor_index: int = 1) -> ImageCaptureResult:
    """
    Args:
        1 = primary monitor
        2 = secondary monitor, etc.
        0 = all monitors combined into one image (virtual screen) - may not work well on all platforms or configurations.
    """
    try:
        with mss.mss() as sct:
            monitors = sct.monitors
            if monitor_index < 0 or monitor_index >= len(monitors):
                LOGGER_ERROR(f"capture_full_screen: Invalid monitor_index {monitor_index}. Available: 0-{len(monitors) - 1}")
                return ImageCaptureResult(byte_data=None, img=None)
            screenshot = sct.grab(monitors[monitor_index])
            img = Image.frombytes('RGB', (screenshot.width, screenshot.height), screenshot.rgb)

        byte_io = io.BytesIO()
        img.save(byte_io, format='JPEG', quality=85)
        return ImageCaptureResult(byte_data=byte_io.getvalue(), img=img)

    except Exception as e:
        LOGGER_ERROR(f"Error capturing full screen: {e}")
        return ImageCaptureResult(byte_data=None, img=None)

def save_image(image_name, image_data=None, img=None, output_path="."):
    """
    :param image_data: The binary image data (optional).
    :param img: The PIL.Image object (optional).
    """
    try:
        if isinstance(output_path, str):
            output_path = Path(output_path)
        output_path.mkdir(parents=True, exist_ok=True)
        file_path = output_path / f"{image_name}.jpg"
        if img is not None:
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            img.save(file_path, format='JPEG', quality=85)
        elif image_data is not None:
            image = Image.open(io.BytesIO(image_data))
            if image.mode in ("RGBA", "P"):
                image = image.convert("RGB")
            image.save(file_path, format='JPEG', quality=85)
        else:
            raise ValueError("Either image_data or img must be provided.")
        
        return file_path.resolve().as_posix()
    except Exception as e:
        LOGGER_ERROR(f"Error saving image: {e}")
        return None

   
