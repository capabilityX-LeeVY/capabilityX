from pathlib import Path
from rs_sdk.utils import image_handler
from config.paths import FULLSCREEN_IMAGE_PATH


def capture_fullscreen(image_name = 'screenshot') -> str:
    """
    Capture a full screenshot and save it using the YAML step name as the filename.

    The filename is derived automatically from the ``step_name`` injected by the
    framework (taken from the ``name`` field of the current YAML step).  No
    explicit ``parameters`` block is required in the test case.

    Args:
        **kwargs: Runtime keyword arguments injected by the function loader.
                  ``step_name`` (str) is expected and used as the image filename.

    Returns:
        str: Absolute path to the saved screenshot file.
    """
    control_image_output = image_handler.capture_full_screen()
    control_image = control_image_output.img
    control_image_path = str(Path(FULLSCREEN_IMAGE_PATH) / f"{image_name}.jpg")
    image_handler.save_image(image_name, img=control_image, output_path=FULLSCREEN_IMAGE_PATH.as_posix())
    return control_image_path
