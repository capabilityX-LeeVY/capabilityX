import cv2
import numpy as np
import pyautogui
import time
import base64

from mimetypes import guess_type
from mss import mss
from common.utils.logger import LOGGER_INFO, LOGGER_DEBUG, LOGGER_WARNING, LOGGER_ERROR

def load_images(main_image_path, template_image_path):
    img_rgb = cv2.imread(main_image_path)
    img_gray = cv2.cvtColor(img_rgb, cv2.COLOR_BGR2GRAY)
    template = cv2.imread(template_image_path, 0)
    return img_rgb, img_gray, template

def match_template(img_gray, template):
    res = cv2.matchTemplate(img_gray, template, cv2.TM_CCOEFF_NORMED)
    threshold = np.array([0.8])
    res = np.array(res)
    loc = np.where(res >= threshold)
    return loc

def draw_rectangle(img_rgb, loc, w, h): 
    LOGGER_INFO("Detected loc ======> : ", loc)
    for pt in zip(*loc[::-1]): 
        cv2.rectangle(img_rgb, pt, (pt[0] + w, pt[1] + h), (0,255,255), 2) 
        LOGGER_INFO("Detected pt ======> : ", pt)
        cv2.imshow('Detected',img_rgb) 
    
    cv2.waitKey(5000) 
    cv2.destroyAllWindows()
    cv2.waitKey(1) 
    time.sleep(5)
    

def calculate_center_position(pt, w, h):
    center_x_image = pt[0] + w / 2
    center_y_image = pt[1] + h / 2
    return center_x_image, center_y_image

def convert_to_screen_coordinates(center_x_image, center_y_image, img_width, img_height):
    screen_width, screen_height = pyautogui.size()
    center_x_screen = center_x_image * screen_width / img_width
    center_y_screen = center_y_image * screen_height / img_height
    return center_x_screen, center_y_screen

def capture_and_save_screenshot(save_path):
    with mss() as sct:
        screenshot = sct.grab(sct.monitors[0])
    img = np.array(screenshot)
    cv2.imwrite(save_path, img)

def extract_json_from_txt(input_file, output_file):
        
    with open(input_file, 'r') as file:
        input_text = file.read()

    cleaned_text = input_text.replace('\\n', '').replace('\\', '')

    start_index = cleaned_text.find('{')
    end_index = cleaned_text.rfind('}')
    json_data = cleaned_text[start_index:end_index+1]
    
    with open(output_file, 'w') as output:
        output.write(json_data)
    
def write_to_file(content, filepath):
    with open(filepath, 'w', encoding='utf-8') as file:
        file.write(content + '\n')

def encodeImageToBase64(image_path):
    """encode a local image into data URL"""
    mime_type, _ = guess_type(image_path)
    if mime_type is None:
        mime_type = 'application/octet-stream'
    with open(image_path, "rb") as image_file:
        base64_encoded_data = base64.b64encode(image_file.read()).decode('utf-8')
    return f"data:{mime_type};base64,{base64_encoded_data}"

if __name__ == "__main__":
    extract_json_from_txt('src/document/ChatGPT_Prompt_Response.txt', 'src/document/ChatGPT_Prompt_Response.json')
