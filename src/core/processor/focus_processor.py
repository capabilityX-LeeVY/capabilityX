import os
import cv2
import numpy as np
import pandas as pd
import shutil
import imagehash
import requests

from pathlib import Path
from PIL import Image
from common.handler.fileHandler import getSortedFiles
from rs_sdk.utils.control_db import ControlDB as localControlDB
from rs_sdk.utils import image_handler
from common.utils.logger import LOGGER_DEBUG, LOGGER_ERROR, LOGGER_INFO, LOGGER_WARNING
from config.paths import SETTINGS_PATH, COLOR_CONFIG_PATH, CONTROL_IMAGE_PATH, FOCUS_RING_RESULT_PATH
from common.handler.settingsHandler import DynamicConfig
from tools.markdownToDataframe import MarkdownToDataframe
from db.cloudMySQL import accData
from config.config import CONTROL_DB
from typing import Optional


class aiCheck:
    def __init__(self, base_url: str = "http://gc-hgh05-level2-lab-irc-5.cisco.com:9912/gpt"):
        self.endpoint = f"{base_url}/analyze_image/"
    
    def analyze_image(self, image: str, prompt: Optional[str] = None) -> str:
        with open(image, "rb") if os.path.exists(image) else open(os.devnull, "rb") as f:
            try:
                response = requests.post(
                    self.endpoint,
                    files={"image": f},
                    data={"message": prompt} if prompt else {}
                )
                result = response.json().get("result", "")
                return result.replace("Output:", "").strip() if result.startswith("Output:") else result
            except Exception as e:
                return f"Error: {e}"

class FocusRingProcessor:

    def __init__(self, image_output_path=CONTROL_IMAGE_PATH, results_output_path=FOCUS_RING_RESULT_PATH):
        self.local_DB = localControlDB()
        self.image_output_path = Path(image_output_path)
        self.results_output_path = Path(results_output_path)
        self.focus_controls_path = (self.image_output_path / "currentControls").as_posix()
        self.pre_controls_path = (self.image_output_path / "preControls").as_posix()
        self.color_config = DynamicConfig(COLOR_CONFIG_PATH)
        self.focus_ring_color = self.color_config.get("focusRingColorDefault")
        self.lower_color = self.color_config.get("focusRingColor", self.color_config.get("focusRingColorDefault"), "lower")
        self.upper_color = self.color_config.get("focusRingColor", self.color_config.get("focusRingColorDefault"), "upper")
        self.settings = DynamicConfig(SETTINGS_PATH)
        self.app_version = DynamicConfig(SETTINGS_PATH).get('appVersion')
        self.ai_checker = aiCheck()
        self._ai_cache: dict = {}

    def _ensure_paths(self):
        os.makedirs(self.results_output_path, exist_ok=True)
        os.makedirs(self.focus_controls_path, exist_ok=True)
        os.makedirs(self.pre_controls_path, exist_ok=True)

    def _get_image_data(self, image_path):
        img = Image.open(image_path)
        phash_val = str(imagehash.phash(img))
        with open(image_path, "rb") as f:
            img_bytes = f.read()
        return phash_val, img_bytes

    def _is_acceptable_image(self, img_hash, expected_focus_state=None, hamming_threshold=10):
        try:
            if not img_hash:
                return False
            accepted_images = accData.fetchAcceptedImages(CONTROL_DB, expected_focus_state=expected_focus_state)
            if accepted_images.empty:
                return False
            current_hash = imagehash.hex_to_hash(img_hash)
            for _, row in accepted_images.iterrows():
                accepted_hash_str = row.get('img_hash')
                if accepted_hash_str:
                    try:
                        accepted_hash = imagehash.hex_to_hash(accepted_hash_str)
                        hamming_distance = current_hash - accepted_hash
                        if hamming_distance <= hamming_threshold:
                            return True
                    except (ValueError, TypeError) as e:
                        continue
            return False
            
        except Exception as e:
            return False

    def generate_controls_image_by_bytes(self):
        results = self.local_DB.fetch_control_history()
        if results.empty if isinstance(results, pd.DataFrame) else not results:
            LOGGER_ERROR("No image data or an error occurred.")
            return
        
        for _, row in results.iterrows() if isinstance(results, pd.DataFrame) else results:
            image_name = row.get('Description')
            control_focus_ring = row.get('Image')
            pre_control_focus_ring = row.get('PreControlImage')

            if image_name:
                if control_focus_ring is not None:
                    image_handler.save_image(image_name, image_data=control_focus_ring, output_path=self.focus_controls_path)
                if pre_control_focus_ring is not None:
                    image_handler.save_image(image_name, image_data=pre_control_focus_ring, output_path=self.pre_controls_path)


    def has_focus_ring(self, file_path):
        focus_ring_detected = False
        multiple_focus_ring_detected = False
        inner_ring_detected = False
        prev_bbox = None
        third_percentage = 0.3
        area_in_ring_outerline = 0
        detected_ring_count = 0
        try:
            # image = cv2.imread(file_path)
            stream = np.fromfile(file_path, dtype=np.uint8)
            image = cv2.imdecode(stream, cv2.IMREAD_COLOR)
            if image is None:
                LOGGER_ERROR(f"Unable to read image: {file_path}")
                return focus_ring_detected, multiple_focus_ring_detected, inner_ring_detected
            
            image_height, image_width = image.shape[:2]
            image = cv2.GaussianBlur(image, (3, 3), 0.1)
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            lower_color = np.array(self.lower_color)
            upper_color = np.array(self.upper_color)
            mask_color = cv2.inRange(hsv, lower_color, upper_color)

            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (1, 1))
            mask_color = cv2.morphologyEx(mask_color, cv2.MORPH_CLOSE, kernel)

            contours, hierarchy = cv2.findContours(mask_color, cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
            if hierarchy is None:
                return focus_ring_detected, multiple_focus_ring_detected, inner_ring_detected
            
            hierarchy = hierarchy[0]

            valid_contours = []
            parent_child_map = {}
            for i, contour in enumerate(contours):
                area = cv2.contourArea(contour)
                perimeter = cv2.arcLength(contour, True)
                x, y, w, h = cv2.boundingRect(contour)
                if area >= 100 and perimeter >= 50 and w > 10 and h > 10:
                    valid_contours.append(i)
                    parent_child_map[i] = []
            for i in valid_contours:
                if i >= hierarchy.shape[0]:
                    continue
                
                try:
                    hierarchy_entry = hierarchy[i]
                    if len(hierarchy_entry) < 4:
                        continue
                except (IndexError, TypeError) as e:
                    continue
                    
                child_idx = hierarchy_entry[2]
                while child_idx != -1:
                    if child_idx >= hierarchy.shape[0]:
                        break
                    try:
                        child_hierarchy_entry = hierarchy[child_idx]
                        if len(child_hierarchy_entry) < 4:
                            break
                    except (IndexError, TypeError):
                        break
                        
                    if child_idx in valid_contours:
                        parent_child_map[i].append(int(child_idx))
                    child_idx = child_hierarchy_entry[0]

            large_focus_rings = []
            
            if valid_contours:
                contour_areas = []
                for i in valid_contours:
                    if i < len(contours):
                        area = cv2.contourArea(contours[i])
                        contour_areas.append((area, i))
                
                if contour_areas:
                    contour_areas.sort(reverse=True)
                    
                    for area, idx in contour_areas:
                        if area > 5000:
                            contour = contours[idx]
                            is_ring, is_solid, _ = self._detect_ring_vs_solid(contour, image, mask_color)
                            if is_ring or is_solid:
                                large_focus_rings.append((idx, contour, area))
                    
                    largest_contour_idx = contour_areas[0][1]
                    largest_contour = contours[largest_contour_idx]

            for i in valid_contours:
                if i >= len(contours):
                    continue
                contour = contours[i] if isinstance(contours, list) else contours[int(i)]
                perimeter = cv2.arcLength(contour, True)
                area = cv2.contourArea(contour)
                x, y, w, h = cv2.boundingRect(contour)
                aspect_ratio = perimeter/area if area > 0 else 0

                count_sharp_corners = self._count_sharp_corners(contour)
                compactness = area / (perimeter ** 2)

                contour_points = contour[:, 0, :]
                # is_edge_contour_top = True
                # is_edge_contour_bottom = True
                # is_edge_contour_left = True
                # is_edge_contour_right = True
                # for point in contour_points:
                #     px, py = point
                #     if py >= image_height * third_percentage:
                #         is_edge_contour_top = False
                #     if py <= image_height * (1 - third_percentage):
                #         is_edge_contour_bottom = False
                #     if px >= image_width * third_percentage:
                #         is_edge_contour_left = False
                #     if px <= image_width * (1 - third_percentage):
                #         is_edge_contour_right = False

                # is_circle = False
                # is_quadrilateral = False
                # is_capsule = False
                # is_half_capsule = False                
                shape = cv2.approxPolyDP(contour, 0.01 * perimeter, True)
                num_vertices = len(shape)
                circularity = (4 * np.pi * area) / (perimeter * perimeter) if perimeter > 0 else 0
                # is_circle = 0.8 <= circularity <= 1.2

                # if num_vertices > 4:
                #     ellipse = cv2.fitEllipse(contour)
                #     (cx, cy), (major_axis, minor_axis), _ = ellipse
                #     axis_aspect_ratio = major_axis / minor_axis if minor_axis > 0 else 0
                #     if axis_aspect_ratio > 2.5:
                #         is_capsule = True

                #         top_half = contour[contour[:, 0, 1] < cy]
                #         bottom_half = contour[contour[:, 0, 1] > cy]
                #         if len(top_half) > 0 and len(bottom_half) > 0:
                #             top_arc = cv2.arcLength(top_half, True)
                #             bottom_arc = cv2.arcLength(bottom_half, True)
                #             if abs(top_arc - bottom_arc) > 0.3 * perimeter:
                #                 is_half_capsule = True

                # inner_indices = parent_child_map.get(i, [])
                mask_outer = np.zeros_like(mask_color)
                cv2.drawContours(mask_outer, [contour], -1, 255, thickness=cv2.FILLED) # type: ignore
                area_in_ring_outerline = cv2.countNonZero(mask_outer)
                _blue_in_outer = cv2.countNonZero(cv2.bitwise_and(mask_outer, mask_color))
                quick_color_ratio = _blue_in_outer / area_in_ring_outerline if area_in_ring_outerline > 0 else 0

                horizontal_symmetry, vertical_symmetry = self._is_mask_symmetry(mask_outer)

                hull = cv2.convexHull(contour)
                hull_area = cv2.contourArea(hull)
                convexity = area / hull_area if hull_area > 0 else 0
                hull_perimeter = cv2.arcLength(hull, True)
                area_ratio = area / hull_area
                if hull_perimeter == 0 or perimeter == 0:  # skip invalid shapes
                    continue

                perimeter_ratio = perimeter / hull_perimeter
                final_score = round(area_ratio / perimeter_ratio, 3)

                if perimeter_ratio < 1.1 and self._count_90_angles(contour) > 1 and num_vertices in (4, 8):
                    is_quadrilateral = True

                if area_in_ring_outerline < 150: # skip small shapes
                    continue
                if perimeter_ratio > 1.2 and perimeter < 150: # skip small shapes
                    continue
                if (w <= 20 or h <= 20) and area <= 250: # skip small shapes
                    continue
                
                # if h <= 25 and convexity < 0.5:
                    # continue  # Skip small, low-convexity rings
                
                _curvature_filtered = False
                if convexity > 0.85 and convexity < 1.0:
                    curvature_variance = self._calculate_curvature_variance(contour)
                    _curvature_filtered = curvature_variance > 0.105
                
                if (h < 30 or w < 30):
                    if convexity < 0.2:
                        continue
                  
                if area < 300 and large_focus_rings:
                    current_center_x, current_center_y = x + w//2, y + h//2
                    is_inside_large_ring = False
                    
                    for large_idx, large_contour, large_area in large_focus_rings:
                        point_test = cv2.pointPolygonTest(large_contour, (current_center_x, current_center_y), False)
                        if point_test >= 0:
                            is_inside_large_ring = True
                            break
                    
                    if is_inside_large_ring:
                        continue  # Skip this small contour as it's inside a large focus ring
                # LOGGER_INFO(f"file: {file_path}| area: {area}")
                is_ring, is_solid, is_low_contrast = self._detect_ring_vs_solid(contour, image, mask_color)

                is_like_character_hole = not (is_ring or is_solid or is_low_contrast) and area < 1000 and i > 10
                if is_like_character_hole:
                    continue

                if _curvature_filtered and not (is_ring and quick_color_ratio < 0.6):
                    continue  # Skip contours with highly irregular boundaries

                if is_ring:
                    if is_low_contrast:
                        is_complete, closure_ratio = self._is_contour_complete(contour, image_width, image_height)
                        if not is_complete:
                            continue  # Skip open contours with low contrast

                    if quick_color_ratio >= 0.95 and area < 700:
                        continue  # Fully-solid small element, not a focus ring
                    _bbox_aspect = min(w, h) / max(w, h) if max(w, h) > 0 else 0
                    if is_low_contrast and quick_color_ratio > 0.80 and _bbox_aspect < 0.70:
                        continue  # Non-circular solid blue element, not a focus ring

                    if circularity < 0.6 and num_vertices >= 10 and quick_color_ratio >= 0.6:
                        continue # Skip irregular ring shapes (not thin-border rings)
                    if convexity > 0.95 and num_vertices >= 10:
                        sharp_corners = self._count_sharp_corners(contour, sharp_angle_threshold=70, min_segment_length=10)
                        if sharp_corners > 0:
                            continue  # Skip irregular ring shapes
                    
                    contour_points = contour[:, 0, :]
                    total_perimeter_points = len(contour_points)
                    # aspect_ratio = max(w, h) / min(w, h) if min(w, h) > 0 else 0
                    has_ui_content = self._has_ui_content(contour, image, mask_color, area_threshold=1000)
                    if (area < 500 or h < 30 or w < 30) and not has_ui_content:
                        continue  # Skip this small ring as it's likely an empty text hole

                    center_x, center_y = x + w//2, y + h//2
                    quadrants = {'top_left': 0, 'top_right': 0, 'bottom_left': 0, 'bottom_right': 0}
                    
                    for point in contour_points:
                        px, py = point
                        if px < center_x and py < center_y:
                            quadrants['top_left'] += 1
                        elif px >= center_x and py < center_y:
                            quadrants['top_right'] += 1
                        elif px < center_x and py >= center_y:
                            quadrants['bottom_left'] += 1
                        else:
                            quadrants['bottom_right'] += 1
                    
                    quadrant_ratios = [count/total_perimeter_points for count in quadrants.values()]
                    # min_quadrant_ratio = min(quadrant_ratios)
                    
                    # sparse_quadrants = sum(1 for ratio in quadrant_ratios if ratio < 0.1)
                    
                    if num_vertices < 8 and final_score < 0.1: # skip non-closed shapes
                        continue

                    focus_ring_detected = True
                    nested_children_count = 0
                    third_child_idx = -1
                    
                    if i >= len(contours):
                        continue
                    x, y, w, h = cv2.boundingRect(contours[i])
                    curr_bbox = (x, y, w, h)
                    if prev_bbox is not None:
                        px, py, pw, ph = prev_bbox
                        is_nested = (px <= x and py <= y and px + pw >= x + w and py + ph >= y + h) or \
                                    (x <= px and y <= py and x + w >= px + pw and y + h >= py + ph)
                        if not is_nested:  
                            multiple_focus_ring_detected = True
                    prev_bbox = (x, y, w, h) 
                    
                    if i < hierarchy.shape[0]:
                        try:
                            hierarchy_entry = hierarchy[i]
                            if hasattr(hierarchy_entry, '__len__') and len(hierarchy_entry) >= 4 and hierarchy_entry[3] == -1:
                                nested_children_count, third_child_idx, second_child_idx = self._count_and_id_nested_children(i, parent_child_map)
                        except (IndexError, TypeError):
                            pass
                        
                        if nested_children_count > 2:
                            candidate_indices = []
                            if third_child_idx != -1 and third_child_idx < len(contours):
                                candidate_indices.append(third_child_idx)
                            if second_child_idx != -1 and second_child_idx < len(contours):
                                candidate_indices.append(second_child_idx)
                            
                            for candidate_idx in candidate_indices:
                                mask_innermost_filled = np.zeros_like(mask_color, dtype=np.uint8)
                                cv2.drawContours(mask_innermost_filled, [contours[candidate_idx]], -1, 255, thickness=cv2.FILLED) # type: ignore

                                mask_innermost_border = np.zeros_like(mask_color, dtype=np.uint8)
                                cv2.drawContours(mask_innermost_border, [contours[candidate_idx]], -1, 255, thickness=1)  # type: ignore
                                mask_innermost_cleaned = cv2.bitwise_xor(mask_innermost_filled, mask_innermost_border)
                                innermost_cleaned_area = cv2.countNonZero(mask_innermost_cleaned)

                                mask_blue_innermost = cv2.bitwise_and(mask_innermost_cleaned, mask_color)
                                blue_area_in_innermost = cv2.countNonZero(mask_blue_innermost)
                                if innermost_cleaned_area == 0: # skip empty shapes
                                    continue
                                    
                                inner_contour = contours[candidate_idx]
                                inner_area = cv2.contourArea(inner_contour)
                                inner_is_ring, inner_is_solid, _ = self._detect_ring_vs_solid(inner_contour, image, mask_color)
                                
                                if (blue_area_in_innermost / innermost_cleaned_area < 0.05 and
                                    inner_is_ring and not inner_is_solid and
                                    inner_area > 1000):
                                    inner_ring_detected = True
                                    break
                        prev_bbox = (x, y, w, h)
                
                if is_solid:
                    if convexity > 0.45:
                        is_thick_border_ring = (
                            area > 3000 and
                            convexity >= 0.95 and
                            0.25 <= quick_color_ratio <= 0.72 and
                            num_vertices <= 6
                        )
                        if not is_thick_border_ring:
                            continue  # Skip irregular solid shapes
                    curvature_variance = self._calculate_curvature_variance(contour)
                    if curvature_variance > 0.1:
                        continue  # Skip contours with highly irregular boundaries
                    is_complete, closure_ratio = self._is_contour_complete(contour, image_width, image_height)
                    if not is_complete:
                        continue  #Skip open contours
                
                if num_vertices <= 2: # skip line shapes
                    continue
                    
                if 0 < horizontal_symmetry <= 0.2 and 0 < vertical_symmetry <= 0.2: # skip non-symmetric shapes
                    continue
                
                if circularity < 0.1 and num_vertices < 6: # skip imperfect near-circular shapes
                    continue

                if num_vertices < 8: # skip non-closed shapes
                    if final_score < 0.1 and closure_ratio > 0.001:
                        continue
                    
                if (count_sharp_corners > 0 and compactness > 0.01) or count_sharp_corners > 3: # skip shapes with too many less than 60-degree angles
                    continue
                
                focus_ring_detected = True
                nested_children_count = 0
                third_child_idx = -1
                second_child_idx = -1

                # Multiple focus ring detection for second path
                x, y, w, h = cv2.boundingRect(contour)
                curr_bbox = (x, y, w, h)
                if prev_bbox is not None:
                    px, py, pw, ph = prev_bbox
                    is_nested = (px <= x and py <= y and px + pw >= x + w and py + ph >= y + h) or \
                                (x <= px and y <= py and x + w >= px + pw and y + h >= py + ph)
                    if not is_nested:  
                        multiple_focus_ring_detected = True
                prev_bbox = (x, y, w, h)
                
                # Check for inner ring in this path too
                # if i < hierarchy.shape[0]:
                #     try:
                #         hierarchy_entry = hierarchy[i]
                #         if hasattr(hierarchy_entry, '__len__') and len(hierarchy_entry) >= 4 and hierarchy_entry[3] == -1:
                #             nested_children_count, third_child_idx, second_child_idx = self._count_and_id_nested_children(i, parent_child_map)

                #             if nested_children_count > 2:
                #                 candidate_indices = []
                #                 if third_child_idx != -1 and third_child_idx < len(contours):
                #                     candidate_indices.append(third_child_idx)
                #                 if second_child_idx != -1 and second_child_idx < len(contours):
                #                     candidate_indices.append(second_child_idx)
                                
                #                 for candidate_idx in candidate_indices:
                #                     mask_innermost_filled = np.zeros_like(mask_color, dtype=np.uint8)
                #                     cv2.drawContours(mask_innermost_filled, [contours[candidate_idx]], -1, 255, thickness=cv2.FILLED) # type: ignore

                #                     mask_innermost_border = np.zeros_like(mask_color, dtype=np.uint8)
                #                     cv2.drawContours(mask_innermost_border, [contours[candidate_idx]], -1, 255, thickness=1)  # type: ignore
                #                     mask_innermost_cleaned = cv2.bitwise_xor(mask_innermost_filled, mask_innermost_border)
                #                     innermost_cleaned_area = cv2.countNonZero(mask_innermost_cleaned)

                #                     mask_blue_innermost = cv2.bitwise_and(mask_innermost_cleaned, mask_color)
                #                     blue_area_in_innermost = cv2.countNonZero(mask_blue_innermost)
                #                     if innermost_cleaned_area == 0: # skip empty shapes
                #                         continue
                                        
                #                     inner_contour = contours[candidate_idx]
                #                     inner_area = cv2.contourArea(inner_contour)
                #                     inner_is_ring, inner_is_solid, _ = self._detect_ring_vs_solid(inner_contour, image, mask_color)
                #                     if (blue_area_in_innermost / innermost_cleaned_area < 0.05 and
                #                         inner_is_ring and not inner_is_solid and
                #                         inner_area > 1000):
                #                         inner_ring_detected = True
                #                         break  # Found valid inner ring, stop checking
                #             else:
                #                 pass
                #         else:
                #             pass
                #     except (IndexError, TypeError):
                #         pass
                # else:
                #     pass

                # Save debug image with all detected rings
                colors = [
                    (0, 255, 0),      # Green
                    (255, 0, 0),      # Blue
                    (0, 0, 255),      # Red
                    (255, 255, 0),    # Cyan
                    (255, 0, 255),    # Magenta
                    (0, 255, 255),    # Yellow
                    (128, 0, 128),    # Purple
                    (255, 128, 0),    # Orange
                ]
                color = colors[detected_ring_count % len(colors)]
                cv2.drawContours(image, [contour], -1, color, 3)
                x_label, y_label = x, y - 10
                if y_label < 20:
                    y_label = y + h + 20
                cv2.putText(image, f"Ring {detected_ring_count + 1}", (x_label, y_label),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                detected_ring_count += 1
            # Save debug image with all detected rings
            if detected_ring_count > 0:
                image_name = os.path.basename(file_path)
                output_cv2_image_folder = os.path.join(self.image_output_path, "debug")
                if not os.path.exists(output_cv2_image_folder):
                    os.makedirs(output_cv2_image_folder)
                output_filename = os.path.join(output_cv2_image_folder, image_name)
                summary_text = f"{detected_ring_count}"
                cv2.putText(image, summary_text, (10, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                cv2.putText(image, summary_text, (10, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 1)
                cv2.imwrite(output_filename, image)
            
            if not focus_ring_detected:
                total_blue_px = cv2.countNonZero(mask_color)
                blue_fraction = total_blue_px / (image_width * image_height)
                if blue_fraction < 0.20 and min(image_width, image_height) >= 50:
                    min_row_blue = int(image_width * 0.70)
                    has_top_border = any(
                        cv2.countNonZero(mask_color[r:r + 1, :]) >= min_row_blue
                        for r in range(min(5, image_height))
                    )
                    bottom_search_start = int(image_height * 0.75)
                    has_bottom_border = any(
                        cv2.countNonZero(mask_color[r:r + 1, :]) >= min_row_blue
                        for r in range(bottom_search_start, image_height)
                    )
                    if has_top_border and has_bottom_border:
                        focus_ring_detected = True

            return focus_ring_detected, multiple_focus_ring_detected, inner_ring_detected

        except Exception as e:
            LOGGER_ERROR(f"Error processing file {file_path}: {e}")
            return focus_ring_detected, multiple_focus_ring_detected, inner_ring_detected
    
    def _count_descendants(self, idx, parent_child_map):
        """Recursively count descendants for the given index."""
        count = len(parent_child_map[idx])
        for child in parent_child_map[idx]:
            count += self._count_descendants(child, parent_child_map)
        return count
    
    def _count_nested_children(self, idx, parent_child_map):
        """Recursively count nested children for the given index."""
        if idx not in parent_child_map or not parent_child_map[idx]:
            return 0    

        first_child = parent_child_map[idx][0]  
        return 1 + self._count_nested_children(first_child, parent_child_map)
    
    def _count_and_id_nested_children(self, idx, parent_child_map, depth=1):
        """Recursively count and identify the deepest valid child for inner ring detection."""
        if idx not in parent_child_map or not parent_child_map[idx]:  
            return depth - 1, -1, -1  
        
        first_child = parent_child_map[idx][0]  
        
        if depth == 2:
            if first_child in parent_child_map and parent_child_map[first_child]:
                child_count, third_child, _ = self._count_and_id_nested_children(first_child, parent_child_map, depth + 1)
                return child_count, third_child, first_child
            else:
                return depth, first_child, -1
        elif depth == 3:
            return depth, first_child, -1
        else:
            child_count, third_child, second_child = self._count_and_id_nested_children(first_child, parent_child_map, depth + 1)
            return child_count, third_child, second_child

    def _is_coutour_symmetric(self, contour):
        """Check if the contour is symmetric."""
        x, y, w, h = cv2.boundingRect(contour)
        center_x = x + w // 2
        center_y = y + h // 2

        left_contour = contour[contour[:, 0, 0] < center_x]
        right_contour = contour[contour[:, 0, 0] > center_x]

        if len(left_contour) == 0 or len(right_contour) == 0:
            return 0, 0

        left_width = cv2.boundingRect(left_contour)[2]
        right_width = cv2.boundingRect(right_contour)[2]

        horizontal_ratio = min(left_width, right_width) / max(left_width, right_width)

        top_contour = contour[contour[:, 0, 1] < center_y]
        bottom_contour = contour[contour[:, 0, 1] > center_y]

        if len(top_contour) == 0 or len(bottom_contour) == 0:
            return horizontal_ratio, 0

        top_height = cv2.boundingRect(top_contour)[3]
        bottom_height = cv2.boundingRect(bottom_contour)[3]

        vertical_ratio = min(top_height, bottom_height) / max(top_height, bottom_height)

        return horizontal_ratio, vertical_ratio
    
    def _is_mask_symmetry(self, mask):
        """Check if the contour is symmetric."""
        h, w = mask.shape
        binary_mask = (mask > 0).astype(np.uint8)

        mid_w = w // 2
        left_half = binary_mask[:, :mid_w]
        right_half = cv2.flip(binary_mask[:, -mid_w:], 1)
        horizontal_symmetry = np.sum(left_half & right_half) / (np.sum(left_half | right_half) + 1e-5)

        mid_h = h // 2
        top_half = binary_mask[:mid_h, :]
        bottom_half = cv2.flip(binary_mask[-mid_h:, :], 0)
        vertical_symmetry = np.sum(top_half & bottom_half) / (np.sum(top_half | bottom_half) + 1e-5)

        return horizontal_symmetry, vertical_symmetry
    
    def _skeletonize(self, mask):
        """Skeletonize the contour."""
        skeleton = np.zeros_like(mask)
        kernel = np.ones((3, 3), np.uint8)

        while True:
            eroded = cv2.erode(mask, kernel)
            temp = cv2.subtract(mask, eroded)
            skeleton = cv2.bitwise_or(skeleton, temp)
            mask = eroded

            if cv2.countNonZero(mask) == 0:
                break

        return skeleton

    def _calculate_angle(self, pt1, pt2, pt3):
        v1 = np.array(pt1) - np.array(pt2)
        v2 = np.array(pt3) - np.array(pt2)
        dot_product = np.dot(v1, v2)
        magnitude = np.linalg.norm(v1) * np.linalg.norm(v2)
        if magnitude == 0:
            return 0
        angle = np.arccos(np.clip(dot_product / magnitude, -1, 1))
        return np.degrees(angle)

    def _count_90_angles(self, contour):
        """Count the number of 90-degree angles in the contour."""
        approx = cv2.approxPolyDP(contour, 0.015 * cv2.arcLength(contour, True), True)
        num_vertices = len(approx)
        if num_vertices < 2:
            return 0
        angles = []
        if 2 <= num_vertices < 10:
            for i in range(num_vertices):
                pt1 = tuple(approx[i - 1][0])
                pt2 = tuple(approx[i][0])
                # pt3 = tuple(approx[(i + 1) % 4][0])
                pt3 = tuple(approx[(i + 1) % num_vertices][0])
                angle = self._calculate_angle(pt1, pt2, pt3)
                angles.append(angle)
            right_angle_count = sum(80 <= angle <= 110 for angle in angles)
        else:
            right_angle_count = 0
        return right_angle_count
    
    def _count_sharp_corners(self, contour, sharp_angle_threshold=60, min_segment_length=10):
        if contour is None or len(contour) < 3:
            return 0
        
        contour = cv2.approxPolyDP(contour, epsilon=5, closed=True)
        if contour is None or len(contour) < 3:
            return 0
        
        contour = np.squeeze(contour)
        if contour.ndim != 2 or contour.shape[0] < 3:
            return 0

        sampled_pts = [contour[0]]
        for pt in contour[1:]:
            if np.linalg.norm(np.array(pt) - np.array(sampled_pts[-1])) >= min_segment_length:
                sampled_pts.append(pt)

        if len(sampled_pts) < 3:
            return 0

        count = 0
        total_points = len(sampled_pts)
        for i in range(total_points):
            pt1 = np.array(sampled_pts[i - 1])
            pt2 = np.array(sampled_pts[i])
            pt3 = np.array(sampled_pts[(i + 1) % total_points])

            v1 = pt1 - pt2
            v2 = pt3 - pt2

            norm_v1 = np.linalg.norm(v1)
            norm_v2 = np.linalg.norm(v2)
            if norm_v1 < 1e-5 or norm_v2 < 1e-5:
                continue

            cos_angle = np.dot(v1, v2) / (norm_v1 * norm_v2)
            cos_angle = np.clip(cos_angle, -1.0, 1.0)
            angle_deg = np.degrees(np.arccos(cos_angle))

            if angle_deg < sharp_angle_threshold:
                count += 1

        return count

    def _calculate_curvature_variance(self, contour, window_size=5):
        if contour is None or len(contour) < 10:
            return 0.0
        
        contour_points = contour[:, 0, :]
        n_points = len(contour_points)
        
        if n_points < window_size * 2:
            return 0.0
        
        curvatures = []
        
        for i in range(n_points):
            prev_idx = (i - window_size) % n_points
            next_idx = (i + window_size) % n_points
            
            p1 = contour_points[prev_idx]
            p2 = contour_points[i]
            p3 = contour_points[next_idx]
            
            v1 = np.array(p2) - np.array(p1)
            v2 = np.array(p3) - np.array(p2)
            
            cross_product = np.cross(v1, v2)
            norm_v1 = np.linalg.norm(v1)
            norm_v2 = np.linalg.norm(v2)
            
            if norm_v1 > 0 and norm_v2 > 0:
                curvature = abs(cross_product) / (norm_v1 * norm_v2 + 1e-10)
                curvatures.append(curvature)
        
        if len(curvatures) == 0:
            return 0.0
        
        curvatures = np.array(curvatures)
        curvature_variance = np.var(curvatures)
        
        return curvature_variance

    def _has_ui_content(self, contour, image, mask_color, area_threshold=500):
        try:
            area = cv2.contourArea(contour)
            interior_mask = np.zeros_like(mask_color)
            cv2.drawContours(interior_mask, [contour], -1, 255, thickness=cv2.FILLED) # type: ignore
            if area >= area_threshold:
                kernel = np.ones((4, 4), np.uint8)
                interior_mask = cv2.erode(interior_mask, kernel, iterations=2)
            else:
                kernel = np.ones((3, 3), np.uint8)
                interior_mask = cv2.erode(interior_mask, kernel, iterations=1)
            interior_region = image[interior_mask > 0]
            if len(interior_region) <= 10:
                return False
            interior_hsv = cv2.cvtColor(interior_region.reshape(-1, 1, 3), cv2.COLOR_BGR2HSV)
            interior_hsv = interior_hsv.reshape(-1, 3)

            val_values = interior_hsv[:, 2]
            val_range = np.max(val_values) - np.min(val_values)
            has_ui_content = (val_range > 80)
            
            return has_ui_content
            
        except Exception:
            return False

    def _is_contour_complete(self, contour, image_width, image_height):
        """
        Check if contour is complete and properly closed.
        Returns (is_complete, closure_ratio):
            - is_complete: True if contour is valid, False if it should be filtered out
            - closure_ratio: The ratio of perimeter difference (closed vs open)
        """
        try:
            if contour is None or len(contour) < 5:
                return False, 0.0
            contour_points = contour[:, 0, :]

            total_points = len(contour_points)
            if total_points < 5:
                return False, 0.0
                
            perimeter_closed = cv2.arcLength(contour, True)
            perimeter_open = cv2.arcLength(contour, False)
            if perimeter_closed == 0:
                return False, 0.0
                
            closure_ratio = abs(perimeter_closed - perimeter_open) / perimeter_closed
            if closure_ratio > 0.2:
                return False, closure_ratio
            
            x, y, w, h = cv2.boundingRect(contour)
            h_margin = w * 0.15
            v_margin = h * 0.15
            edges = {'left': 0, 'right': 0, 'top': 0, 'bottom': 0}
            for point in contour_points:
                px, py = point
                if px <= x + h_margin:
                    edges['left'] += 1
                if px >= x + w - h_margin:
                    edges['right'] += 1
                if py <= y + v_margin:
                    edges['top'] += 1
                if py >= y + h - v_margin:
                    edges['bottom'] += 1
            left_ratio = edges['left'] / total_points
            right_ratio = edges['right'] / total_points
            top_ratio = edges['top'] / total_points
            bottom_ratio = edges['bottom'] / total_points
            min_edge_ratio = min(left_ratio, right_ratio, top_ratio, bottom_ratio)
            if min_edge_ratio < 0.08:
                return False, closure_ratio
            if left_ratio > 0 and right_ratio > 0:
                lr_ratio = max(left_ratio, right_ratio) / min(left_ratio, right_ratio)
                if lr_ratio > 2.5:
                    return False, closure_ratio
            if top_ratio > 0 and bottom_ratio > 0:
                tb_ratio = max(top_ratio, bottom_ratio) / min(top_ratio, bottom_ratio)
                if min_edge_ratio < 0.1 and tb_ratio > 2.5:
                    return False, closure_ratio
            
            return True, closure_ratio
            
        except Exception as e:
            return False, 0.0
    
    def _calculate_enhanced_color_difference(self, contour, hsv_image, mask_filled, mask_color):
        try:
            x, y, w, h = cv2.boundingRect(contour)
            edge_center_score = self._analyze_edge_center_difference(contour, hsv_image, mask_filled, mask_color)
            if edge_center_score < 0.02:
                return edge_center_score
            morphological_score = self._analyze_morphological_difference(hsv_image, mask_filled, mask_color)
            gradient_score = self._analyze_focus_ring_gradient(hsv_image, mask_filled, mask_color, contour)
            combined_score = (edge_center_score * 0.8 + morphological_score * 0.15 + gradient_score * 0.05)
            return combined_score
            
        except Exception as e:
            return 0.05
    
    def _analyze_edge_center_difference(self, contour, hsv_image, mask_filled, mask_color):
        try:
            area = cv2.contourArea(contour)
            if area < 1000:
                kernel_size = (3, 3)
                erosion_iterations = 1
                thickness = 2
            elif area < 3000:
                kernel_size = (4, 4)
                erosion_iterations = 1
                thickness = 3
            else:
                kernel_size = (5, 5)
                erosion_iterations = 2
                thickness = 3
            
            edge_mask = np.zeros_like(mask_filled)
            cv2.drawContours(edge_mask, [contour], -1, 255, thickness=thickness)  # type: ignore
            edge_mask = cv2.bitwise_and(edge_mask, mask_color)
            
            kernel = np.ones(kernel_size, np.uint8)
            center_mask = cv2.erode(mask_filled, kernel, iterations=erosion_iterations)
            center_mask = cv2.bitwise_and(center_mask, mask_color)
            
            edge_pixels = hsv_image[edge_mask > 0]
            center_pixels = hsv_image[center_mask > 0]
            
            if len(center_pixels) < 5:
                if erosion_iterations > 1:
                    center_mask = cv2.erode(mask_filled, kernel, iterations=1)
                    center_mask = cv2.bitwise_and(center_mask, mask_color)
                    center_pixels = hsv_image[center_mask > 0]
                
                if len(center_pixels) < 5 and kernel_size[0] > 3:
                    smaller_kernel = np.ones((3, 3), np.uint8)
                    center_mask = cv2.erode(mask_filled, smaller_kernel, iterations=1)
                    center_mask = cv2.bitwise_and(center_mask, mask_color)
                    center_pixels = hsv_image[center_mask > 0]
            
            if len(edge_pixels) < 5 or len(center_pixels) < 5:
                return 0.0
                
            edge_sat_mean = np.mean(edge_pixels[:, 1]) / 255.0
            center_sat_mean = np.mean(center_pixels[:, 1]) / 255.0
            edge_val_mean = np.mean(edge_pixels[:, 2]) / 255.0
            center_val_mean = np.mean(center_pixels[:, 2]) / 255.0
            
            sat_diff = abs(edge_sat_mean - center_sat_mean)
            val_diff = abs(edge_val_mean - center_val_mean)
            
            score = sat_diff * 0.5 + val_diff * 0.5
            
            return score
            
        except Exception:
            return 0.0
    
    def _analyze_morphological_difference(self, hsv_image, mask_filled, mask_color):
        try:
            filled_area = cv2.countNonZero(mask_filled)
            
            if filled_area < 1000:
                kernel_size = (3, 3)
                inner_iterations = 1
            elif filled_area < 3000:
                kernel_size = (3, 3)
                inner_iterations = 2
            else:
                kernel_size = (3, 3)
                inner_iterations = 3
                
            kernel = np.ones(kernel_size, np.uint8)
            eroded_mask = cv2.erode(mask_filled, kernel, iterations=1)
            outer_ring = cv2.subtract(mask_filled, eroded_mask)
            outer_ring = cv2.bitwise_and(outer_ring, mask_color)
            
            inner_mask = cv2.erode(mask_filled, kernel, iterations=inner_iterations)
            inner_mask = cv2.bitwise_and(inner_mask, mask_color)
            
            outer_pixels = hsv_image[outer_ring > 0]
            inner_pixels = hsv_image[inner_mask > 0]
            
            if len(inner_pixels) < 3 and inner_iterations > 1:
                inner_mask = cv2.erode(mask_filled, kernel, iterations=inner_iterations-1)
                inner_mask = cv2.bitwise_and(inner_mask, mask_color)
                inner_pixels = hsv_image[inner_mask > 0]
            
            if len(outer_pixels) < 3 or len(inner_pixels) < 3:
                return 0.0
                
            outer_sat = np.mean(outer_pixels[:, 1]) / 255.0
            inner_sat = np.mean(inner_pixels[:, 1]) / 255.0
            
            return abs(outer_sat - inner_sat)
            
        except Exception:
            return 0.0
    
    def _analyze_focus_ring_gradient(self, hsv_image, mask_filled, mask_color, contour):
        try:
            x, y, w, h = cv2.boundingRect(contour)
            perimeter = cv2.arcLength(contour, True)
            area = cv2.contourArea(contour)
            
            if min(w, h) < 15:
                return 0.0
                
            aspect_ratio = max(w, h) / min(w, h)
            if aspect_ratio > 3.0:
                return 0.0
            
            sat_channel = hsv_image[:, :, 1].astype(np.float32)
            roi_mask = np.zeros_like(mask_filled)
            cv2.drawContours(roi_mask, [contour], -1, 255, thickness=cv2.FILLED)  # type: ignore
            analysis_mask = cv2.bitwise_and(roi_mask, mask_color)
            if cv2.countNonZero(analysis_mask) < 20:
                return 0.0
            
            masked_sat = np.zeros_like(sat_channel)
            masked_sat[analysis_mask > 0] = sat_channel[analysis_mask > 0]
            grad_x = cv2.Sobel(masked_sat, cv2.CV_32F, 1, 0, ksize=3)
            grad_y = cv2.Sobel(masked_sat, cv2.CV_32F, 0, 1, ksize=3)
            gradient_magnitude = np.sqrt(grad_x**2 + grad_y**2)
            gradient_values = gradient_magnitude[analysis_mask > 0]
            
            if len(gradient_values) == 0:
                return 0.0
            
            avg_gradient = np.mean(gradient_values) / 255.0
            max_gradient = np.max(gradient_values) / 255.0
            std_gradient = np.std(gradient_values) / 255.0
            
            if avg_gradient < 0.05:
                return 0.0
            if avg_gradient > 0.4:
                return 0.0
                
            shape_factor = 1.0
            
            circularity = (4 * np.pi * area) / (perimeter * perimeter) if perimeter > 0 else 0
            if 0.6 <= circularity <= 1.3:
                shape_factor *= 1.2
            elif circularity < 0.3:
                shape_factor *= 0.5
            
            gradient_score = avg_gradient * shape_factor
            
            return min(gradient_score * 0.8, 0.3)
            
        except Exception:
            return 0.0

    def _check_two_tone_ring_structure(self, contour, hsv_image, mask_color):
        try:
            mask_contour = np.zeros_like(mask_color)
            cv2.drawContours(mask_contour, [contour], -1, 255, thickness=cv2.FILLED)
            combined_mask = cv2.bitwise_and(mask_contour, mask_color)
            contour_pixels = hsv_image[combined_mask > 0]
            
            if len(contour_pixels) < 100:
                return False
            
            v_values = contour_pixels[:, 2]
            v_mean = np.mean(v_values)
            v_std = np.std(v_values)
            v_range = np.max(v_values) - np.min(v_values)
            
            if v_range < 50:
                return False
            
            if v_std < 30:
                return False
            
            v_channel = hsv_image[:, :, 2]
            mask_light = (combined_mask > 0) & (v_channel >= v_mean)
            mask_dark = (combined_mask > 0) & (v_channel < v_mean)
            light_pixels = np.count_nonzero(mask_light)
            dark_pixels = np.count_nonzero(mask_dark)
            
            if light_pixels < 50 or dark_pixels < 50:
                return False
            
            total_pixels = light_pixels + dark_pixels
            minority_pixels = min(light_pixels, dark_pixels)
            minority_ratio = minority_pixels / total_pixels if total_pixels > 0 else 0
            
            if minority_ratio < 0.25:
                return False
            
            ring_mask = mask_light if light_pixels < dark_pixels else mask_dark
            y_coords, x_coords = np.where(ring_mask)
            
            if len(y_coords) < 50:
                return False
            
            M = cv2.moments(contour)
            if M["m00"] == 0:
                return False
            
            center_x = int(M["m10"] / M["m00"])
            center_y = int(M["m01"] / M["m00"])
            distances = np.sqrt((y_coords - center_y)**2 + (x_coords - center_x)**2)
            dist_std = np.std(distances)
            dist_min = np.min(distances)
            
            if dist_min > 10:
                return False
            
            if dist_std >= 15 or dist_std < 3:
                return False
            
            kernel = np.ones((3, 3), np.uint8)
            eroded = cv2.erode(ring_mask.astype(np.uint8), kernel, iterations=3)
            remaining = np.count_nonzero(eroded)
            retention_rate = remaining / len(y_coords) if len(y_coords) > 0 else 0
            
            if dist_min < 5 and retention_rate > 0.5:
                return False
            
            return True
            
        except Exception as e:
            LOGGER_ERROR(f"Error in _check_two_tone_ring_structure: {e}")
            return False

    def _detect_ring_vs_solid(self, contour, image, mask_color):
        try:
            mask_filled = np.zeros_like(mask_color)
            cv2.drawContours(mask_filled, [contour], -1, 255, thickness=cv2.FILLED)  # type: ignore
            filled_area = cv2.countNonZero(mask_filled)
            
            hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            blue_filled_mask = cv2.bitwise_and(mask_filled, mask_color)
            filled_nonzero_mask = blue_filled_mask > 0
            
            color_difference = 0.0
            area = cv2.contourArea(contour)
            if np.any(filled_nonzero_mask):
                all_hsv_values = hsv_image[filled_nonzero_mask]
                if len(all_hsv_values) >= 10:
                    color_difference = self._calculate_enhanced_color_difference(contour, hsv_image, mask_filled, mask_color)
            
            total_color_match = cv2.countNonZero(blue_filled_mask)
            overall_color_ratio = total_color_match / filled_area if filled_area > 0 else 0
            if overall_color_ratio >= 1:
                hull = cv2.convexHull(contour)
                contour_area = cv2.contourArea(contour)
                hull_area = cv2.contourArea(hull)
                compactness = contour_area / hull_area if hull_area > 0 else 0
                
                if compactness > 0.95:
                    is_two_tone_ring = self._check_two_tone_ring_structure(contour, hsv_image, mask_color)
                    if is_two_tone_ring:
                        return True, False, False
                return False, True, False
                
                # if round(compactness, 2) == 1:
                #     blue_region_hsv = hsv_image[filled_nonzero_mask]
                #     if len(blue_region_hsv) > 10:
                #         v_values = blue_region_hsv[:, 2]
                #         if not (np.std(v_values) > 50 or (np.max(v_values) - np.min(v_values)) > 100):
                #             return False, True, False
                #     else:
                #         return False, True, False
                # else:
                #     return False, True, False
            
            if 0.9 <= overall_color_ratio < 1 and color_difference < 0.05:
                is_two_tone_ring = self._check_two_tone_ring_structure(contour, hsv_image, mask_color)
                if is_two_tone_ring:
                    return True, False, False
                return False, True, False

            kernel_boundary = np.ones((3, 3), np.uint8)
            boundary_mask = cv2.subtract(mask_filled, cv2.erode(mask_filled, kernel_boundary, iterations=1))
            inner_mask = cv2.erode(mask_filled, np.ones((4, 4), np.uint8), iterations=2)
            
            boundary_area = cv2.countNonZero(boundary_mask)
            inner_area = cv2.countNonZero(inner_mask)
            total_color_match = color_difference*overall_color_ratio
            if boundary_area > 0 and inner_area > 0:
                boundary_hsv = hsv_image[boundary_mask > 0]
                inner_hsv = hsv_image[inner_mask > 0]
                
                if len(boundary_hsv) > 5 and len(inner_hsv) > 5:
                    sat_diff = abs(np.mean(boundary_hsv[:, 1]) - np.mean(inner_hsv[:, 1])) / 255.0
                    val_diff = abs(np.mean(boundary_hsv[:, 2]) - np.mean(inner_hsv[:, 2])) / 255.0
                    hue_diff = abs(np.mean(boundary_hsv[:, 0]) - np.mean(inner_hsv[:, 0]))
                    hue_diff = min(hue_diff, 360 - hue_diff)
                    
                    if 0.95 <= overall_color_ratio < 1 and color_difference > 0.05 and sat_diff < 0.03 and val_diff < 0.25:
                        return False, True, False
                    
                    if 0.95 <= overall_color_ratio < 1 and color_difference < 0.1 and sat_diff >= 0.03 and val_diff >= 0.25:
                        return False, True, False
                    
                    if 0.95 <= overall_color_ratio < 1 and color_difference < 0.01 and  0.5 <= hue_diff < 1.2:
                        return False, True, False
                    
                    if 0.5 <= overall_color_ratio < 0.6 and color_difference < 0.05 and area < 500:
                        return False, True, False
                    
            is_low_contrast = 0.010 <= color_difference < 0.07
            is_hollow_ring = is_bordered_solid = is_solid_no_border = False
            
            if color_difference >= 0.07 or is_low_contrast:
                erosion_classifications = []
                erosion_kernel = np.ones((3, 3), np.uint8)
                
                for erosion_step in range(1, 4):
                    mask_outer_boundary = cv2.erode(mask_filled, erosion_kernel, iterations=erosion_step)
                    outer_layer = cv2.subtract(mask_filled, mask_outer_boundary)
                    inner_layer = cv2.subtract(mask_outer_boundary, cv2.erode(mask_filled, erosion_kernel, iterations=erosion_step * 2))
                    
                    if cv2.countNonZero(outer_layer) == 0:
                        break
                    if cv2.countNonZero(inner_layer) == 0:
                        continue
                    
                    outer_mask = outer_layer > 0
                    inner_mask = inner_layer > 0
                    
                    if np.any(outer_mask) and np.any(inner_mask):
                        outer_mean = np.mean(hsv_image[outer_mask], axis=0)
                        inner_mean = np.mean(hsv_image[inner_mask], axis=0)
                        
                        sat_diff = inner_mean[1] / 255.0 - outer_mean[1] / 255.0
                        is_ring_like = (outer_mean[1] < inner_mean[1] or outer_mean[2] > inner_mean[2])
                        erosion_classifications.append((erosion_step, is_ring_like, sat_diff))
                
                num_classifications = len(erosion_classifications)
                if num_classifications >= 2:
                    sat_diffs = [diff for _, _, diff in erosion_classifications]
                    ring_votes = sum(1 for _, is_ring, _ in erosion_classifications if is_ring)
                    
                    has_reversal = any(sat_diffs[i] * sat_diffs[i+1] < 0 for i in range(num_classifications - 1))
                    is_converging = abs(sat_diffs[0]) > 0.05 and abs(sat_diffs[-1]) < abs(sat_diffs[0]) * 0.7
                    
                    if has_reversal:
                        # perimeter = cv2.arcLength(contour, True)
                        # circularity = (4 * np.pi * area) / (perimeter * perimeter) if perimeter > 0 else 0
                        # is_too_thick = False
                        # if circularity > 0.8:
                        #     M = cv2.moments(contour)
                        #     if M["m00"] > 0:
                        #         center_x = int(M["m10"] / M["m00"])
                        #         center_y = int(M["m01"] / M["m00"])
                        #         contour_points = contour[:, 0, :]
                        #         distances = np.sqrt((contour_points[:, 0] - center_x)**2 + (contour_points[:, 1] - center_y)**2)
                        #         inner_radius = np.min(distances)
                        #         outer_radius = np.max(distances)
                        #         ring_width = outer_radius - inner_radius
                        #         is_too_thick = ring_width > 6
                        is_solid_no_border = (overall_color_ratio > 0.8 and color_difference < 0.05)
                        is_hollow_ring = not is_solid_no_border
                    # elif overall_color_ratio > 0.9 and color_difference < 0.1:
                    elif (overall_color_ratio >= 0.6 and color_difference < 0.12) or (overall_color_ratio >= 0.2 and color_difference < 0.08):
                        is_solid_no_border = True
                    elif ring_votes == num_classifications:
                        is_solid_no_border = is_converging and overall_color_ratio > 0.85
                        is_bordered_solid = not is_solid_no_border
                    else:
                        is_bordered_solid = True
                elif num_classifications == 1:
                    is_hollow_ring = erosion_classifications[0][1]
                    is_bordered_solid = not is_hollow_ring
            else:
                is_solid_no_border = overall_color_ratio > 0.75
            
            contour_area = cv2.contourArea(contour)
            hull_area = cv2.contourArea(cv2.convexHull(contour))
            convexity = contour_area / hull_area if hull_area > 0 else 0
            size_ratio = contour_area / (hsv_image.shape[0] * hsv_image.shape[1])
            
            if (not is_hollow_ring and not is_bordered_solid and contour_area < 1000 and 
                overall_color_ratio > 0.9 and convexity > 0.8 and size_ratio > 0.02):
                is_solid_no_border = True
            
            if is_hollow_ring or is_bordered_solid:
                return True, False, is_low_contrast
            elif is_solid_no_border:
                return False, True, is_low_contrast
            else:
                return False, False, is_low_contrast
        except Exception as e:
            LOGGER_ERROR(f"Error in _detect_ring_vs_solid: {e}")
            return True, False, False

    def _ai_check(self, img_hash, file_path, cache_key_suffix, prompt, success_analysis_result):
        cache_key = (img_hash, cache_key_suffix)
        if cache_key in self._ai_cache:
            ai_result = self._ai_cache[cache_key]
        else:
            ai_result = self.ai_checker.analyze_image(image=file_path, prompt=prompt)
            self._ai_cache[cache_key] = ai_result
        if "✅" in ai_result.strip():
            return success_analysis_result, "✅ Compliant", "Viewed by AI. No action needed."
        return None

    def _get_hu_moments(self, contour):
        moments = cv2.moments(contour)
        hu_moments = cv2.HuMoments(moments).flatten()
        return np.log(np.abs(hu_moments))

    def _classify_shape(self, contour):
        hu = self._get_hu_moments(contour)
        hu0, hu2 = hu[0], hu[2]

        if hu0 < 0.18 and hu2 < 0.001:
            return "Circle"
        elif 0.18 < hu0 < 0.22 and 0.002 < hu2 < 0.005:
            return "Capsule"
        elif 0.21 < hu0 < 0.24 and 0.003 < hu2 < 0.008:
            return "Square"
        elif 0.22 < hu0 < 0.30 and 0.010 < hu2 < 0.020:
            return "Rectangle"
        elif 0.28 < hu0 < 0.35 and 0.015 < hu2 < 0.025:
            return "Trapezoid"
        elif hu0 > 0.40 and hu2 > 0.05:
            return "U-Shape"
        else:
            return "Unknown Shape"
    
    def validate_onFocus_controls(self):
        self._ensure_paths()
        folder_path = Path(self.image_output_path) / "currentControls"
        results = []
        output_file = None
        if not os.path.exists(folder_path):
            LOGGER_ERROR(f"Folder not found: {folder_path}")
            return

        sorted_files = getSortedFiles(folder_path)
        for file_name in sorted_files:
            # LOGGER_DEBUG(f"Processing file: {file_name}")
            file_path = (Path(folder_path) / file_name).as_posix()
            image_name = Path(file_name).name
            img_hash, img_bytes = self._get_image_data(file_path)
            reference = "WCAG 2.4.7 Focus Visible" # https://www.w3.org/WAI/WCAG21/Understanding/focus-visible.html

            if os.path.isfile(file_path) and file_name.lower().endswith(('.png', '.jpg')):
                focus_ring, multi_rings, inner_ring = self.has_focus_ring(file_path)
                if focus_ring and not multi_rings and not inner_ring:
                    analysis_result = f"A valid focus ring detected."
                    compliance = f"✅ Compliant"
                    suggestion = "N/A"
                elif focus_ring and inner_ring:
                    analysis_result = f"A duplicate focus ring was detected within the existing focus ring."
                    compliance = f"❌ Non-compliant"
                    suggestion = "Ensure that only one focus ring is present around the focused control."
                elif focus_ring and multi_rings:
                    analysis_result = f"Multiple focus rings were detected."
                    compliance = f"❌ Non-compliant"
                    suggestion = "Ensure that only one focus ring is present around the focused control."
                elif not focus_ring:
                    analysis_result = f"No focus ring detected, or the focus ring is partial."
                    compliance = f"❌ Non-compliant"
                    suggestion = "Ensure that a clear and complete focus ring is visible around the focused control."

                if compliance.startswith("❌"):
                    is_acceptable_image = self._is_acceptable_image(img_hash, expected_focus_state='focused')
                    if is_acceptable_image:
                        compliance = f"☑️ Accepted"
                        suggestion = "Viewed. No action needed."
                    elif "A duplicate focus ring was detected within the existing focus ring." in analysis_result:
                        pass
                    elif "Multiple focus rings were detected." in analysis_result:
                        ai_update = self._ai_check(
                            img_hash, file_path, 'multi_rings',
                            prompt=(
                                f"You are an accessibility compliance checker. This is a cropped screenshot of a UI taken during keyboard navigation testing.\n\n"
                                f"Our automated CV detector found multiple distinct {self.focus_ring_color} ring-shaped contours in this image and flagged it as having multiple focus rings. "
                                f"Please verify this finding carefully.\n\n"
                                f"A valid {self.focus_ring_color} focus ring is a ring-shaped highlight that wraps around ALL FOUR sides of a UI element (top, bottom, left, right), "
                                f"is in high contrast with the background, and is NOT part of the control's normal unfocused appearance (e.g., not an icon border, decoration, or normal button border).\n\n"
                                f"Count only the number of distinct, valid {self.focus_ring_color} focus rings surrounding SEPARATE UI elements.\n"
                                f"Note: concentric rings around the SAME element (e.g., an inner and outer ring on one button) count as ONE focus ring occurrence, not multiple.\n\n"
                                f"Compliance rules:\n"
                                f"- EXACTLY ONE valid {self.focus_ring_color} focus ring found → '✅ Compliant'\n"
                                f"- MORE THAN ONE valid {self.focus_ring_color} focus ring on SEPARATE elements → '❌ Non-compliant'\n"
                                f"- ZERO valid focus rings → '❌ Non-compliant'\n\n"
                                f"Respond with ONLY '✅ Compliant' or '❌ Non-compliant'."
                            ),
                            success_analysis_result="AI check: Only one focus ring confirmed, CV false alarm on multiple rings."
                        )
                        if ai_update:
                            analysis_result, compliance, suggestion = ai_update
                    else:
                        ai_update = self._ai_check(
                            img_hash, file_path, 'focused',
                            prompt=(
                                f"You are an accessibility compliance checker. This is a cropped screenshot of a UI control that currently has keyboard focus.\n\n"
                                f"Your task: determine whether a valid WCAG focus ring is present.\n\n"
                                f"A valid focus ring MUST meet ALL of the following criteria (WCAG 2.4.7 / 2.4.11):\n"
                                f"1. It must be a ring-shaped highlight that wraps around ALL FOUR sides of the UI element (top, bottom, left, and right).\n"
                                f"   - A single bottom underline or partial border is NOT a valid focus ring.\n"
                                f"   - TRUNCATED means: an entire side (or the majority of a side) of the ring is absent because the element is near the image crop boundary and that side of the ring simply does not appear. This is ❌ Non-compliant — do NOT assume the ring continues beyond the image edge.\n"
                                f"   - CLIPPED means: the ring is clearly present on all four sides but one side loses only the very outermost 1–3 pixels at the absolute image boundary. This is still ✅ Compliant.\n"
                                f"   - If you cannot clearly see ring pixels on a full side, treat it as TRUNCATED → ❌ Non-compliant.\n"
                                f"   - For a solid {self.focus_ring_color} filled control(not like a checkbox or radio button), the focus ring may appear as a thick {self.focus_ring_color} border or a slightly darker or lighter {self.focus_ring_color} band at the outer perimeter — look carefully for a tonal difference at the edge → ✅ Compliant.\n"
                                f"2. The ring color MUST be '{self.focus_ring_color}'.\n"
                                f"   - If {self.focus_ring_color} occupies only a very small area of the image (e.g., a few scattered pixels, a tiny accent, or less than ~5% of the image area), it is NOT a focus ring → ❌ Non-compliant.\n"
                                f"3. The ring must be in high contrast with the background.\n\n"
                                f"Note: Our automated CV detector flagged this as non-compliant (focus ring missing or incomplete). "
                                f"Please re-examine carefully — the ring may be thin or subtle, but it must still be clearly visible on all four sides.\n\n"
                                f"Respond with ONLY '✅ Compliant' if a valid {self.focus_ring_color} focus ring meeting all criteria above is present, "
                                f"When in doubt, return ❌ Non-compliant. Exception: very small control(visible control height AND width ≤ 30px) that appear to be a regular rectangle shape (e.g., a checkbox), a valid closed {self.focus_ring_color} focus ring meeting all criteria is present → ✅ Compliant.\n\n"
                                f"or '❌ Non-compliant' if no valid focus ring is found."
                            ),
                            success_analysis_result="AI check: A focus ring is present."
                        )
                        if ai_update:
                            analysis_result, compliance, suggestion = ai_update

                relative_path = os.path.relpath(file_path, self.results_output_path)
                # absolute_path = os.path.abspath(file_path)
                result = (image_name, relative_path, img_hash, analysis_result, compliance, reference, suggestion)
                results.append(result)
            else:
                LOGGER_WARNING(f"[SKIPPED] Not a valid image file: {file_path}")
        
        md_file = f'public_fr-report-onfocus_{self.app_version}.md'
        output_file = os.path.join(self.results_output_path, md_file)
        self.focus_ring_result_to_markdown(results, output_file)
        self.to_deduplicated_nonCompliant_md(output_file, 'focused_controls_deduplicated_nonCompliant_data')
        # return pd.DataFrame(results)
        return output_file
    
    def validate_onFocusLost_controls(self):
        self._ensure_paths()
        folder_path = Path(self.image_output_path) / "preControls"
        results = []
        output_file = None
        if not os.path.exists(folder_path):
            LOGGER_ERROR(f"Folder not found: {folder_path}")
            return

        sorted_files = getSortedFiles(folder_path)
        for file_name in sorted_files:
            file_path = (Path(folder_path) / file_name).as_posix()
            image_name = Path(file_name).name
            img_hash, img_bytes = self._get_image_data(file_path)
            reference = "WCAG 2.4.7 Focus Visible" # https://www.w3.org/WAI/WCAG21/Understanding/focus-visible.html

            if os.path.isfile(file_path) and file_name.lower().endswith(('.png', '.jpg')):
                focus_ring, multi_rings, inner_ring = self.has_focus_ring(file_path)
                if focus_ring:
                    analysis_result = f"A focus ring was detected even with the focus on another control."
                    compliance = f"❌ Non-compliant"
                    suggestion = "Ensure that no focus ring is visible when the control is not focused."
                else:
                    analysis_result = f"No focus ring detected."
                    compliance = f"✅ Compliant"
                    suggestion = "N/A"
                
                if compliance.startswith("❌"):
                    is_acceptable_image = self._is_acceptable_image(img_hash, expected_focus_state='unfocused')
                    if is_acceptable_image:
                        compliance = f"☑️ Accepted"
                        suggestion = "Viewed. No action needed."
                    else:
                        ai_update = self._ai_check(
                            img_hash, file_path, 'unfocused',
                            prompt=(
                                f"You are an accessibility compliance checker. This is a cropped screenshot of a UI control that does NOT currently have keyboard focus.\n\n"
                                f"Your task: determine whether a WCAG keyboard focus ring is present when it should NOT be.\n\n"
                                f"Our automated CV detector flagged this image because it found {self.focus_ring_color} pixels arranged in a ring-like pattern — but this may be a false alarm.\n\n"
                                f"A real keyboard focus ring is a distinct {self.focus_ring_color} border or outline that clearly encircles the entire control as a focus indicator. It is NOT a focus ring if:\n"
                                f"1. The {self.focus_ring_color} color belongs to the control's own design (e.g., a {self.focus_ring_color} icon, text, logo, button fill, or the control's normal background/border).\n"
                                f"2. The {self.focus_ring_color} area is part of a decorative element, image, or illustration within the control.\n"
                                f"3. The {self.focus_ring_color} forms a ring-like shape but is clearly an integral part of the control's unfocused appearance.\n\n"
                                f"Only flag it as a focus ring if there is an extra {self.focus_ring_color} outline drawn around the control that would NOT appear in its normal unfocused state.\n\n"
                                f"Note: Our automated CV detector flagged this as non-compliant (focus ring present when it should not be). "
                                f"Please re-examine carefully — the {self.focus_ring_color} may simply be part of the control's normal design.\n\n"
                                f"Respond with ONLY '✅ Compliant' if there is NO keyboard focus ring (the {self.focus_ring_color} is part of the control's normal appearance), "
                                f"or '❌ Non-compliant' if a real keyboard focus ring IS present."
                            ),
                            success_analysis_result="AI check: No focus ring detected."
                        )
                        if ai_update:
                            analysis_result, compliance, suggestion = ai_update
                
                relative_path = os.path.relpath(file_path, self.results_output_path)
                # absolute_path = os.path.abspath(file_path)
                result = (image_name, relative_path, img_hash, analysis_result, compliance, reference, suggestion)
                results.append(result)
            else:
                LOGGER_WARNING(f"[SKIPPED] Not a valid image file: {file_path}")

        md_filename = f'public_fr-report-lostfocus_{self.app_version}.md'
        output_file = os.path.join(self.results_output_path, md_filename)
        self.focus_ring_result_to_markdown(results, output_file)
        self.to_deduplicated_nonCompliant_md(output_file, 'lostfocus_controls_deduplicated_nonCompliant_data')
        # return pd.DataFrame(results)
        return output_file

    def validate_image_focused_status(self, image_full_path):
        results = []
        file_path = Path(image_full_path).as_posix()
        image_name = Path(file_path).name

        if os.path.isfile(file_path) and image_name.lower().endswith(('.png', '.jpg')):
            img_hash, img_bytes = self._get_image_data(file_path)
            focus_ring, multi_rings, inner_ring = self.has_focus_ring(file_path)
            if focus_ring and not multi_rings and not inner_ring:
                analysis_result = f"A valid focus ring detected."
                compliance = f"✅Success"
            elif focus_ring and inner_ring:
                analysis_result = f"A duplicate focus ring was detected within the existing focus ring."
                compliance = f"❌WCAG 2.4.7"
            elif focus_ring and multi_rings:
                analysis_result = f"Multiple focus rings were detected."
                compliance = f"❌WCAG 2.4.7"
            elif not focus_ring:
                analysis_result = f"No focus ring detected, or the focus ring is partial."
                compliance = f"❌WCAG 2.4.7"
                
            if compliance.startswith("❌"):
                is_acceptable_image = self._is_acceptable_image(img_hash, expected_focus_state='focused')
                if is_acceptable_image:
                    compliance = f"☑️ Accepted"

            relative_path = os.path.relpath(file_path, self.results_output_path)
            result = (image_name, relative_path, analysis_result, compliance)
            results.append(result)
        else:
            LOGGER_WARNING(f"[SKIPPED] Not a valid image file: {file_path}")
        
        return compliance

    def focus_ring_result_to_markdown(self, focus_ring_results, output_file):
        if not focus_ring_results:
            return
        markdown_table = '|No.|Image|Control Name|Analysis Result|Compliance|Reference|Suggestion|\n'
        markdown_table += '|---|---|---|---|---|---|---|\n'
        for idx, (file_name, file_path, img_hash, analysis_result, compliance, Reference, Suggestion) in enumerate(focus_ring_results, start=1):
            # image_html = f'<img src="file://{file_path}" alt="{file_name}" style="max-width: 300px; height: auto;">'
            # control_name = os.path.splitext(file_name.split("_", 1)[-1])[0]
            control_name = file_name
            image_html = f'<img src="{file_path}" alt="{file_name}" data-img-mhash="{img_hash}" style="max-width: 300px; height: auto;">'
            image_name = file_name.split("_", 1)[-1]
            markdown_table += f"|{idx}|{image_html}|{control_name}|{analysis_result}|{compliance}|{Reference}|{Suggestion}|\n"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(markdown_table)

    def to_deduplicated_nonCompliant_md(self, md_file, output_file):
        if not os.path.exists(md_file):
            LOGGER_ERROR(f"Focus ring detection result file not found: {md_file}")
            return
        df: pd.DataFrame = MarkdownToDataframe.MarkdownToDataframe(md_file)
        df = df[df["Compliance"].str.contains('Non-compliant')] #type: ignore
        LOGGER_INFO(f'Total non-compliant results: {len(df)}')
        if df.empty:
            return
        # df = df.drop_duplicates(subset=["Control Name", "Analysis Result"], keep="first")
        df_unknown = df[df["Control Name"].str.lower() == "unknown"]
        df_known = df[df["Control Name"].str.lower() != "unknown"]
        df_known_deduplicated = df_known.drop_duplicates(subset=["Control Name", "Analysis Result"], keep="first") # type: ignore
        df = pd.concat([df_known_deduplicated, df_unknown], ignore_index=True) # type: ignore

        nonCompliantResults = os.path.join(self.results_output_path, f'{output_file}.md')
        with open(nonCompliantResults, 'w', encoding="utf-8") as f:
            f.write("| " + " | ".join(df.columns) + " |\n")
            f.write("|" + "|".join(["---"] * len(df.columns)) + "|\n")
            for _, row in df.iterrows():
                f.write("| " + " | ".join(map(str, row)) + " |\n")
        LOGGER_INFO(f'non-compliant results after drop duplicates: {len(df)}, saved to {nonCompliantResults}')


    def focus_ring_result_to_html(self, focus_ring_results, column_name, output_html_path):
        if os.path.exists(output_html_path):
            with open(output_html_path, 'r', encoding='utf-8') as file:
                html_content = file.read()

            header_index = html_content.find("<tr>")
            if header_index != -1:
                header_end = html_content.find("</tr>", header_index)
                html_content = html_content[:header_end] + f'<th>{column_name}</th>' + html_content[header_end:]

            row_start = html_content.find("<tr>", header_end)
            i = 0
            while row_start != -1:
                row_end = html_content.find("</tr>", row_start)
                if row_end == -1:
                    break

                focus_result = focus_ring_results[i] if i < len(focus_ring_results) else "No result"

                def wrap_with_link(result):
                    if "for" in result:
                        parts = result.split(" for ")
                        description = parts[0]
                        file_path = os.path.abspath(parts[1])
                        return f'{description} <a href="{file_path}" target="_blank">{file_path}</a>'
                    return result

                focus_result_with_link = wrap_with_link(focus_result)
                if "No focus ring detected" in focus_result:
                    new_cell = f'<td><span class="no-focus-ring">{focus_result_with_link}</span></td>'
                else:
                    new_cell = f'<td>{focus_result_with_link}</td>'

                html_content = html_content[:row_end] + new_cell + html_content[row_end:]
                row_start = html_content.find("<tr>", row_end)
                i += 1
        else:
            html_content = f'''
            <html>
                <head>
                    <title>Focus Ring Detection Results</title>
                    <style>
                        table {{
                            width: 100%;
                            border-collapse: collapse;
                        }}
                        th, td {{
                            padding: 8px;
                            text-align: left;
                            border: 1px solid #ddd;
                        }}
                        th {{
                            background-color: #f2f2f2;
                        }}
                        .no-focus-ring {{
                            color: red;
                            font-weight: bold;
                        }}
                    </style>
                </head>
                <body>
                    <h2>Focus Ring Detection Results</h2>
                    <table>
                        <tr>
                            <th>{column_name}</th>
                        </tr>'''

            if not focus_ring_results:
                focus_ring_results = ["No results found"]
                return

            for focus_result in focus_ring_results:
                def wrap_with_link(result):
                    if "for" in result:
                        parts = result.split(" for ")
                        description = parts[0]
                        file_path = os.path.abspath(parts[1])
                        return f'{description} <a href="{file_path}" target="_blank">{file_path}</a>'
                    return result

                focus_result_with_link = wrap_with_link(focus_result)
                html_content += f'<tr><td>{focus_result_with_link}</td></tr>'

            html_content += '''
                    </table>
                </body>
            </html>'''

        with open(output_html_path, 'w', encoding='utf-8') as file:
            file.write(html_content)

