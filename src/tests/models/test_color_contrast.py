
import requests
import os
import sys
from datetime import datetime

from dotenv import load_dotenv
from pathlib import Path

# Load .env from project root
project_root = Path(__file__).resolve().parents[3]
env_path = project_root / '.env'
load_dotenv(dotenv_path=env_path)

pythonpath = os.getenv("PYTHONPATH")
if pythonpath:
    full_path = os.path.abspath(pythonpath)
    if full_path not in sys.path:
        sys.path.insert(0, full_path)

from models.openai_client import OpenAIClient
from prompts.color_contrast_prompt import COLOR_CONTRAST_ANALYSIS_PROMPT


def analyze_specific_element(element_name, image_path, output_dir=None, custom_prompt=None):
    """
    Analyze a specific UI element in an image for WCAG 2.2 AA color contrast compliance.
    
    Args:
        element_name (str): Name of the UI element to analyze (e.g., "Server-Adresse", "Submit Button")
        image_path (str): Path to the image containing the element
        output_dir (str, optional): Directory to save results. If None, saves to parent_dir/report_cc
        custom_prompt (str, optional): Custom analysis prompt. If None, generates default prompt
    
    Returns:
        str: Path to the generated report file, or None if analysis failed.
    """
    
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Target image not found: {image_path}")
    
    # Set output directory to parent_dir/report_cc if not specified (same as analyze_multiple_images)
    if output_dir is None:
        parent_dir = os.path.dirname(os.path.normpath(image_path))
        # If image is in img/ subdirectory, go up one more level
        if os.path.basename(parent_dir) == "img":
            parent_dir = os.path.dirname(parent_dir)
        output_dir = os.path.join(parent_dir, "report_cc")
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate custom prompt if not provided
    if custom_prompt is None:
        custom_prompt = f"""
You are an accessibility compliance checker specializing in WCAG 2.2 color contrast evaluation.

🎯 Task:
Analyze the color contrast specifically for the **"{element_name}"** element in this UI screenshot.
Your goal is to determine whether the foreground text color and its background color meet WCAG 2.2 AA and AAA standards.

🧭 Steps:

1. **Focus Area**
   - Identify the element labeled "{element_name}".
   - Sample its actual **foreground color (text)** and **background color (immediate area behind text)** in HEX format.
   - Ignore distant background regions, borders, gradients, or shadows—sample only the pixels directly behind the text baseline.

2. **Compute Relative Luminance**
   - Convert both HEX colors to relative luminance (L) using:
     L = 0.2126 * R + 0.7152 * G + 0.0722 * B (after gamma correction to linear RGB).

3. **Calculate Contrast Ratio**
   - ratio = (L1 + 0.05) / (L2 + 0.05)
     where L1 is the lighter color, L2 is the darker color.

4. **Apply WCAG 2.2 Standards**
   Compare the ratio against the following thresholds:
   - **AA Normal text** (<18pt or <14pt bold): ≥ 4.5:1
   - **AA Large text** (≥18pt or ≥14pt bold): ≥ 3.0:1
   - **AAA Normal text**: ≥ 7.0:1
   - **AAA Large text**: ≥ 4.5:1

5. **Determine Compliance**
   - Evaluate PASS / FAIL for each level (AA/AAA and Normal/Large).
   - If FAIL, compute the minimal adjustment (darken or lighten foreground) to reach the AA threshold.

6. **Return analysis in TABLE FORMAT.**

📄 **REQUIRED Output Format - MARKDOWN TABLE:**

| Element Type | Element Description | Location | Foreground Color | Background Color | Contrast Ratio | WCAG 2.2 AA Normal | Status | Priority | Suggested Fix |
|--------------|---------------------|----------|------------------|------------------|----------------|--------------------| -------|----------|---------------|
| Label/Button/Text | {element_name} | <precise location description> | <hex> | <hex> | <ratio>:1 | AA Normal Text (≥4.5:1) | PASS/FAIL | High/Medium/Low | <specific color recommendation> |

🧩 Example Output:

| Element Type | Element Description | Location | Foreground Color | Background Color | Contrast Ratio | WCAG 2.2 AA Normal | Status | Priority | Suggested Fix |
|--------------|---------------------|----------|------------------|------------------|----------------|--------------------| -------|----------|---------------|
| Label | Server-Adresse | Settings panel, below Benutzername field, on light gray background | #74767A | #F5F5F5 | 3.47:1 | AA Normal Text (≥4.5:1) | FAIL | High | Darken text to #5A5C60 (4.50:1) or #43454A (7.00:1) |

⚠️ **CRITICAL RULES:**
- Use EXACT markdown table format shown above
- Include the header row with all columns
- Status must be either "PASS" or "FAIL"
- Priority: High (contrast < 3.0), Medium (3.0-4.4), Low (≥4.5)
- Suggested Fix: Provide specific hex color with achieved ratio
"""
    
    try:
        client = OpenAIClient()
        print(f"🔍 Analyzing element: {element_name}")
        print(f"📸 Image: {os.path.basename(image_path)}")
        print("Performing WCAG 2.2 AA color contrast analysis...")
        
        analysis_result = client.ai_analyze_image(image_path, message=custom_prompt)
        
        if analysis_result is None:
            print("❌ Failed to get analysis result from AI")
            return None
        
        print("✅ Analysis completed successfully")
        
    except Exception as e:
        print(f"❌ Error during AI analysis: {str(e)}")
        return None
    
    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    image_name = os.path.splitext(os.path.basename(image_path))[0]
    # Sanitize element name for filename
    safe_element_name = element_name.replace(" ", "_").replace(":", "").replace("/", "_")
    result_filename = f"element_analysis_{safe_element_name}_{image_name}_{timestamp}.md"
    result_path = os.path.join(output_dir, result_filename)
    
    # Generate relative path from report_cc to image
    relative_image_path = os.path.relpath(image_path, output_dir)
    
    # Parse the table from AI result
    import re
    result_str = str(analysis_result)
    
    # Check if result contains a table
    has_table = '|' in result_str and ('Element Type' in result_str or 'Element Description' in result_str)
    
    # Save analysis result to markdown file
    with open(result_path, 'w', encoding='utf-8') as f:
        f.write(f"# WCAG 2.2 AA Color Contrast Analysis - {element_name}\n\n")
        f.write(f"**Analysis Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"**Target Element:** {element_name}\n\n")
        f.write(f"**Source Image:** {image_path}\n\n")
        f.write(f"**WCAG Standards Applied:** WCAG 2.2 AA\n\n")
        
        # Add image with thumbnail
        image_basename = os.path.basename(image_path)
        img_tag = f'<img src="{relative_image_path}" alt="{image_name}" style="width: 80px; height: auto; border: 1px solid #ccc; border-radius: 3px;">'
        
        f.write("## Analysis Results\n\n")
        
        if has_table:
            # If AI returned a table, add image column and format it
            lines = result_str.split('\n')
            in_table = False
            header_written = False
            separator_written = False
            
            for line in lines:
                if '|' in line:
                    # Check if this is a header row
                    if 'Element Type' in line and not header_written:
                        # Write header with Image columns
                        f.write("| Image | Image Name | Element Type | Element Description | Location | Foreground Color | Background Color | Contrast Ratio | WCAG Standard | Status | Priority | Suggested Fix |\n")
                        header_written = True
                        in_table = True
                    # Check if this is a separator row
                    elif '---' in line and header_written and not separator_written:
                        # Write separator with Image columns
                        f.write("|-------|------------|--------------|---------------------|----------|------------------|------------------|----------------|---------------|--------|----------|---------------|\n")
                        separator_written = True
                    # Data row
                    elif in_table and header_written and separator_written and 'Element Type' not in line and '---' not in line:
                        # Add image thumbnail and status icons
                        formatted_line = line
                        # Add status icons
                        formatted_line = re.sub(r'\|\s*PASS\s*\|', '| ✅ PASS |', formatted_line)
                        formatted_line = re.sub(r'\|\s*FAIL\s*\|', '| ❌ FAIL |', formatted_line)
                        f.write(f"| {img_tag} | {image_name} {formatted_line}\n")
                else:
                    if in_table:
                        in_table = False
        else:
            # AI didn't return table format, create a simple table from the text
            escaped_result = result_str.replace('|', '\\|')
            f.write("| Image | Image Name | Analysis Result |\n")
            f.write("|-------|------------|----------------|\n")
            f.write(f"| {img_tag} | {image_name} | {escaped_result} |\n")
            f.write("\n\n")
            f.write("⚠️ **Note**: AI response was not in expected table format. Showing raw result above.\n\n")
        
        # Add full-size image at bottom
        f.write("\n\n---\n\n")
        f.write("## Source Image\n\n")
        f.write(f'<img src="{relative_image_path}" alt="{image_name}" style="max-width: 60%; height: auto; border: 1px solid #ddd; border-radius: 4px; margin: 20px 0;">\n\n')
        f.write("---\n\n")
        f.write("*Report generated by automated WCAG 2.2 AA compliance analyzer*\n")
    
    print(f"📊 Analysis result saved to: {result_path}")
    print(f"🔍 Report contains detailed analysis of '{element_name}' element")
    return result_path


def test_analyze_image(image_path=None, output_dir=None):
    """
    Analyze image for WCAG 2.2 AA color contrast compliance (full analysis).
    
    Args:
        image_path (str, optional): Path to the image to analyze. 
                                  Defaults to sample image.
        output_dir (str, optional): Directory to save results. 
                                  If None, saves to parent_dir/report_cc (same as analyze_multiple_images)
    
    Returns:
        str: Path to the generated report file, or None if analysis failed.
    """
    if image_path is None:
        image_path = fr"src\tests\models\sample\benchmark\color_contrast\img\SettingsPhoneService1_2025-11-13.png"
    
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Target image not found: {image_path}")
    
    # Set output directory to parent_dir/report_cc if not specified (same as analyze_multiple_images)
    if output_dir is None:
        parent_dir = os.path.dirname(os.path.normpath(image_path))
        # If image is in img/ subdirectory, go up one more level
        if os.path.basename(parent_dir) == "img":
            parent_dir = os.path.dirname(parent_dir)
        output_dir = os.path.join(parent_dir, "report_cc")
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    try:
        client = OpenAIClient()
        print(f"Analyzing image: {image_path}")
        print("Performing WCAG 2.2 AA color contrast analysis...")
        
        analysis_result = client.ai_analyze_image(image_path, message=COLOR_CONTRAST_ANALYSIS_PROMPT)
        
        if analysis_result is None:
            print("❌ Failed to get analysis result from AI")
            return None
        
        print("✅ Analysis completed successfully")
        
    except Exception as e:
        print(f"❌ Error during AI analysis: {str(e)}")
        return None
    
    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    image_name = os.path.splitext(os.path.basename(image_path))[0]
    result_filename = f"accessibility_audit_{image_name}_{timestamp}.md"
    result_path = os.path.join(output_dir, result_filename)
    
    # Generate relative path from report_cc to image
    relative_image_path = os.path.relpath(image_path, output_dir)
    
    # Save analysis result to markdown file
    with open(result_path, 'w', encoding='utf-8') as f:
        f.write(f"# WCAG 2.2 AA Color Contrast Audit Report\n\n")
        f.write(f"**Analysis Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"**Source Image:** {image_path}\n\n")
        f.write(f"**WCAG Standards Applied:** WCAG 2.2 AA\n\n")
        f.write(f'<img src="{relative_image_path}" alt="{image_name}" style="max-width: 60%; height: auto; border: 1px solid #ddd; border-radius: 4px; margin: 20px 0;">\n\n')
        f.write("---\n\n")
        f.write("## Color Contrast Analysis Results\n\n")
        f.write(str(analysis_result))
        f.write("\n\n---\n\n")
        f.write("*Report generated by automated WCAG 2.2 AA compliance analyzer*\n")
    
    print(f"📊 Analysis result saved to: {result_path}")
    print(f"🔍 Report contains detailed WCAG 2.2 AA compliance analysis")
    return result_path


def analyze_multiple_images(image_directory, output_dir=None, project_name=None):
    """
    Analyze multiple images in a directory for color contrast compliance.
    
    Args:
        image_directory (str): Path to directory containing images to analyze (e.g., "GenAI-AdaLabs/img")
        output_dir (str, optional): Directory to save results. If None, creates "report_cc" in parent directory
        project_name (str, optional): Project name for the report. If None, uses parent directory name
    
    Returns:
        dict: Dictionary with 'report_path' and 'individual_results' list
    """
    if not os.path.exists(image_directory):
        raise FileNotFoundError(f"Image directory not found: {image_directory}")
    
    # Get parent directory and use it as project name if not provided
    parent_dir = os.path.dirname(os.path.normpath(image_directory))
    if project_name is None:
        project_name = os.path.basename(parent_dir)
    
    # Set output directory to parent_dir/report_cc if not specified
    if output_dir is None:
        output_dir = os.path.join(parent_dir, "report_cc")
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    print(f"📂 Output directory: {output_dir}")
    
    # Get all image files
    image_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff'}
    image_files = [
        os.path.join(image_directory, f) 
        for f in os.listdir(image_directory) 
        if os.path.splitext(f.lower())[1] in image_extensions
    ]
    
    if not image_files:
        print(f"❌ No image files found in {image_directory}")
        return {'report_path': None, 'individual_results': []}
    
    print(f"📁 Found {len(image_files)} image(s) to analyze in {project_name}")
    print(f"📍 Image directory: {image_directory}")
    
    # Analyze each image and collect results
    analysis_results = []
    for i, image_path in enumerate(image_files, 1):
        print(f"\n🖼️  Analyzing image {i}/{len(image_files)}: {os.path.basename(image_path)}")
        try:
            # Analyze image using OpenAI
            client = OpenAIClient()
            image_name = os.path.basename(image_path)
            
            analysis_result = client.ai_analyze_image(image_path, message=COLOR_CONTRAST_ANALYSIS_PROMPT)
            
            if analysis_result:
                analysis_results.append({
                    'image_name': image_name,
                    'image_path': image_path,
                    'result': analysis_result
                })
                print(f"✅ Analysis completed for {image_name}")
            else:
                print(f"❌ Failed to analyze {image_name}")
                
        except Exception as e:
            print(f"❌ Error analyzing {image_path}: {str(e)}")
    
    if not analysis_results:
        print("❌ No successful analyses to generate report")
        return {'report_path': None, 'individual_results': []}
    
    # Generate consolidated report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_filename = f"accessibility_audit_{project_name}_{timestamp}.md"
    report_path = os.path.join(output_dir, report_filename)
    
    print(f"\n📝 Generating consolidated report: {report_filename}")
    
    # Function to clean and format the result
    def clean_and_format_result(result_text):
        """
        Remove summaries, notes, and filter out unwanted element types
        CRITICAL BLOCKING RULES:
        - Block ANY row containing "disabled", "inactive", "gray", "grayed", "dimmed" in description
        - Block ANY row with element_type or description containing border/divider/panel keywords
        - Add status icons (✅ PASS, ❌ FAIL)
        """
        import re
        
        # Remove everything after "## Accessibility Summary" or "## Analysis Notes" or similar
        patterns_to_remove = [
            r'\n##\s+Accessibility Summary.*$',
            r'\n##\s+Summary.*$',
            r'\n\*\*ANALYSIS NOTES\*\*.*$',
            r'\n##\s+Analysis Notes.*$',
            r'\n```\s*\n##\s+Accessibility Summary.*?```',
        ]
        
        cleaned_text = result_text
        for pattern in patterns_to_remove:
            cleaned_text = re.sub(pattern, '', cleaned_text, flags=re.DOTALL | re.IGNORECASE)
        
        # Filter out unwanted element types from table rows
        lines = cleaned_text.split('\n')
        filtered_lines = []
        
        # Comprehensive blocking keywords - MUST block if ANY appear
        unwanted_types = [
            # Disabled/Inactive states
            'disabled', 'inactive', 'grayed', 'gray', 'dimmed', 'not clickable',
            # Borders and edges
            'border', 'edge', 'outline', 'frame', 'button border', 'button edge',
            # Dividers and separators
            'divider', 'separator', 'line', 'divider/separator',
            # Panels and backgrounds
            'panel', 'panel border', 'panel header', 'background', 'overlay', 
            'backdrop', 'underlay', 'container',
            # Decorative effects
            'shadow', 'glow', 'gradient', 'halo', 'ring', 'button shadow',
            # Focus and hover states
            'focus', 'hover', 'active', 'indicator', 'focus ring',
            # Icons only (not blocking 'image' text in descriptions)
            'icon', 'graphic'
        ]
        
        unwanted_desc_keywords = [
            # Disabled/Inactive descriptions (CRITICAL - must catch "Weiter (disabled, gray)")
            'disabled', 'inactive', 'grayed out', 'grayed', 'gray', 'dimmed',
            'not clickable', 'not enabled', '(disabled', 'disabled)', 'disabled,',
            # Hidden/Invisible states
            'not visible', 'hidden', 'assumed', 'inferred',
            # Focus/Hover descriptions
            'focus ring', 'hover state', 'focus state', 'focus indicator',
            # Background/Panel descriptions (only decorative backgrounds)
            'overlay', 'backdrop',
            # Border/Divider descriptions (structural only)
            'divider line', 'separator line',
            # Icon/Graphic descriptions (visual only, not text about images)
            'icon only', 'graphic element',
            # Decorative descriptions
            'shadow', 'glow', 'gradient', 'halo', 'ring'
        ]
        
        for line in lines:
            # Check if this is a table row with unwanted element type
            if line.strip().startswith('|'):
                # Extract the first column (element type)
                columns = [col.strip() for col in line.split('|')]
                if len(columns) > 1:
                    element_type = columns[1].lower()
                    
                    # CRITICAL: Block if element_type contains ANY unwanted keyword
                    if any(unwanted in element_type for unwanted in unwanted_types):
                        continue  # Skip this row
                    
                    # CRITICAL: Check the element description (second column after type)
                    if len(columns) > 2:
                        element_desc = columns[2].lower()
                        
                        # CRITICAL BLOCKING: Skip if description contains ANY unwanted keyword
                        # This should catch "Weiter (disabled, gray)", "Border", "Divider", etc.
                        if any(keyword in element_desc for keyword in unwanted_desc_keywords):
                            continue  # Skip this row
            
            filtered_lines.append(line)
        
        cleaned_text = '\n'.join(filtered_lines)
        
        # Add status icons (only PASS and FAIL, no EXEMPT since we skip those elements entirely)
        cleaned_text = re.sub(r'\|\s*PASS\s*\|', '| ✅ PASS |', cleaned_text)
        cleaned_text = re.sub(r'\|\s*FAIL\s*\|', '| ❌ FAIL |', cleaned_text)
        
        return cleaned_text.strip()
    
    # Write consolidated report
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(f"# WCAG 2.2 AA Color Contrast Audit Report\n\n")
        f.write(f"## Project: {project_name}\n\n")
        f.write(f"**Analysis Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"**Total Images Analyzed:** {len(analysis_results)}\n\n")
        
        # Collect all FAIL items across all images for overall summary
        all_fail_items = []
        for idx, result_data in enumerate(analysis_results, 1):
            image_name = result_data['image_name']
            image_path = result_data['image_path']
            result = result_data['result']
            
            # Parse the result to extract FAIL rows
            import re
            result_str = str(result)
            lines = result_str.split('\n')
            
            for line in lines:
                # Check for FAIL status - handle both raw "FAIL" and icon "❌ FAIL"
                # Use case-insensitive matching and check for FAIL in the Status column (position 8)
                if '|' in line and 'FAIL' in line.upper():
                    # This might be a FAIL row, extract it
                    columns = [col.strip() for col in line.split('|')]
                    # Valid table row: should have Element Type | ... | Status (8th column) | ...
                    if len(columns) >= 11 and 'FAIL' in columns[8].upper():
                        # Generate relative path for thumbnail
                        relative_image_path = os.path.relpath(image_path, output_dir)
                        fail_item = {
                            'image_name': image_name,
                            'image_path': relative_image_path,
                            'element_type': columns[1],
                            'element_description': columns[2],
                            'location': columns[3],
                            'foreground_color': columns[4],
                            'background_color': columns[5],
                            'contrast_ratio': columns[6],
                            'wcag_standard': columns[7],
                            'priority': columns[9],
                            'suggested_fix': columns[10]
                        }
                        all_fail_items.append(fail_item)
        
        # Write Overall FAIL Summary if there are any failures
        if all_fail_items:
            f.write("## ⚠️ Overall FAIL Summary\n\n")
            f.write(f"**Total FAIL Items:** {len(all_fail_items)}\n\n")
            f.write("| Image | Image Name | Element Type | Element Description | Location | Foreground Color | Background Color | Contrast Ratio | WCAG Standard | Status | Priority | Suggested Fix |\n")
            f.write("|-------|------------|--------------|---------------------|----------|------------------|------------------|----------------|---------------|--------|----------|---------------|\n")
            
            for fail_item in all_fail_items:
                # Create thumbnail image tag (80px width)
                img_tag = f'<img src="{fail_item["image_path"]}" alt="{fail_item["image_name"]}" style="width: 80px; height: auto; border: 1px solid #ccc; border-radius: 3px;">'
                
                # Extract image name without extension for cleaner display
                image_name_only = os.path.splitext(fail_item['image_name'])[0]
                
                f.write(f"| {img_tag} | {image_name_only} | {fail_item['element_type']} | {fail_item['element_description']} | {fail_item['location']} | {fail_item['foreground_color']} | {fail_item['background_color']} | {fail_item['contrast_ratio']} | {fail_item['wcag_standard']} | ❌ FAIL | {fail_item['priority']} | {fail_item['suggested_fix']} |\n")
            
            f.write("\n")
        else:
            f.write("## ✅ Overall Summary\n\n")
            f.write("**All elements passed WCAG 2.2 AA compliance! No failures detected.**\n\n")
        
        f.write("---\n\n")
        
        # Add each image analysis
        for idx, result_data in enumerate(analysis_results, 1):
            image_name = result_data['image_name']
            image_path = result_data['image_path']
            result = result_data['result']
            
            # Clean and format the result
            formatted_result = clean_and_format_result(str(result))
            
            # Generate relative path for image embedding (from report_cc to img)
            relative_image_path = os.path.relpath(image_path, output_dir)
            
            f.write(f"## {idx}. {image_name}\n\n")
            # Adjusted image size: max-width 60% instead of 100%
            f.write(f'<img src="{relative_image_path}" alt="{os.path.splitext(image_name)[0]}" style="max-width: 60%; height: auto; border: 1px solid #ddd; border-radius: 4px; margin: 20px 0;">\n\n')
            f.write(formatted_result)
            f.write("\n\n")
            
            if idx < len(analysis_results):
                f.write("---\n\n")
        
        f.write("\n---\n\n")
        f.write("*Report generated by WCAG 2.2 AA compliance analyzer*\n")
    
    print(f"\n✅ Batch analysis completed!")
    print(f"📊 Consolidated report saved to: {report_path}")
    print(f"📈 Total images analyzed: {len(analysis_results)}")
    
    return {
        'report_path': report_path,
        'individual_results': analysis_results
    }


def analyze_recursive_directories(parent_dir, output_dir=None):
    """
    Recursively analyze subdirectories and generate a consolidated overall_report.md.
    
    For example, given:
        src/tests/models/sample/Merak-Ready/
            Merak_CheckForUpdates/img/
            Merak_EULA/img/
            Merak_GuestJoin/img/
    
    This will:
    1. Analyze each subdirectory one by one
    2. Extract FAIL items from each subdirectory's report
    3. Generate overall_report.md in parent directory with consolidated results
    
    Args:
        parent_dir (str): Parent directory containing subdirectories with images
        output_dir (str, optional): Output directory for overall report. If None, uses parent_dir
    
    Returns:
        dict: Dictionary with 'overall_report_path', 'subdirectory_reports', 'total_fail_items'
    """
    if not os.path.exists(parent_dir):
        raise FileNotFoundError(f"Parent directory not found: {parent_dir}")
    
    # Convert to absolute path to avoid issues
    parent_dir = os.path.abspath(parent_dir)
    
    # Find all subdirectories that contain an 'img' folder
    subdirs_with_images = []
    try:
        items = os.listdir(parent_dir)
    except PermissionError:
        raise PermissionError(f"Permission denied to read directory: {parent_dir}")
    except Exception as e:
        raise Exception(f"Error reading directory {parent_dir}: {str(e)}")
    
    for item in items:
        item_path = os.path.join(parent_dir, item)
        if os.path.isdir(item_path):
            img_dir = os.path.join(item_path, "img")
            # Check if img directory exists
            if os.path.exists(img_dir) and os.path.isdir(img_dir):
                subdirs_with_images.append(item_path)
            else:
                # Check if subdirectory has images directly (needs preprocessing)
                image_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff'}
                has_images = any(
                    f.lower().endswith(tuple(image_extensions))
                    for f in os.listdir(item_path)
                    if os.path.isfile(os.path.join(item_path, f))
                )
                if has_images:
                    # Preprocess this subdirectory
                    print(f"📦 Preprocessing subdirectory: {os.path.basename(item_path)}")
                    try:
                        preprocessed_img_dir = preprocess_project_directory(item_path)
                        subdirs_with_images.append(item_path)
                    except Exception as e:
                        print(f"⚠️  Warning: Failed to preprocess {os.path.basename(item_path)}: {str(e)}")
    
    if not subdirs_with_images:
        print(f"⚠️  No subdirectories with images found in {parent_dir}")
        print(f"ℹ️  Attempting to analyze parent directory directly...")
        # Try to analyze parent directory if it has an img folder
        img_dir = os.path.join(parent_dir, "img")
        if os.path.exists(img_dir):
            result = analyze_multiple_images(
                image_directory=img_dir,
                output_dir=output_dir,
                project_name=os.path.basename(parent_dir)
            )
            return {
                'overall_report_path': result['report_path'],
                'subdirectory_reports': [result],
                'total_fail_items': 0
            }
        else:
            # Check if parent has images directly
            image_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff'}
            has_images = any(
                f.lower().endswith(tuple(image_extensions))
                for f in os.listdir(parent_dir)
                if os.path.isfile(os.path.join(parent_dir, f))
            )
            if has_images:
                print(f"📦 Preprocessing parent directory...")
                preprocessed_img_dir = preprocess_project_directory(parent_dir)
                result = analyze_multiple_images(
                    image_directory=preprocessed_img_dir,
                    output_dir=output_dir,
                    project_name=os.path.basename(parent_dir)
                )
                return {
                    'overall_report_path': result['report_path'],
                    'subdirectory_reports': [result],
                    'total_fail_items': 0
                }
            else:
                raise FileNotFoundError(f"No images found in {parent_dir} or its subdirectories")
    
    print(f"\n📁 Found {len(subdirs_with_images)} subdirectory(ies) to analyze:")
    for subdir in subdirs_with_images:
        print(f"   - {os.path.basename(subdir)}")
    print()
    
    # Analyze each subdirectory
    subdirectory_reports = []
    for i, subdir_path in enumerate(subdirs_with_images, 1):
        subdir_name = os.path.basename(subdir_path)
        print(f"\n{'='*80}")
        print(f"🔍 Analyzing subdirectory {i}/{len(subdirs_with_images)}: {subdir_name}")
        print(f"{'='*80}\n")
        
        img_dir = os.path.join(subdir_path, "img")
        result = analyze_multiple_images(
            image_directory=img_dir,
            output_dir=None,  # Will create report_cc in subdirectory
            project_name=subdir_name
        )
        
        if result['report_path']:
            subdirectory_reports.append({
                'subdir_name': subdir_name,
                'subdir_path': subdir_path,
                'report_path': result['report_path'],
                'individual_results': result['individual_results']
            })
            print(f"✅ Completed analysis for {subdir_name}")
        else:
            print(f"❌ Failed to analyze {subdir_name}")
    
    if not subdirectory_reports:
        print("\n❌ No successful subdirectory analyses to generate overall report")
        return {
            'overall_report_path': None,
            'subdirectory_reports': [],
            'total_fail_items': 0
        }
    
    # Generate overall_report.md in parent directory
    print(f"\n{'='*80}")
    print(f"📊 Generating consolidated overall_report.md")
    print(f"{'='*80}\n")
    
    if output_dir is None:
        output_dir = parent_dir
    
    overall_report_path = os.path.join(output_dir, "overall_report.md")
    
    # Extract FAIL items and PASS images from all subdirectory reports
    all_fail_items = []
    all_pass_images = []
    
    for subdir_report in subdirectory_reports:
        report_path = subdir_report['report_path']
        subdir_name = subdir_report['subdir_name']
        
        # Read the subdirectory report to extract FAIL items
        with open(report_path, 'r', encoding='utf-8') as f:
            report_content = f.read()
        
        # Parse FAIL items from "Overall FAIL Summary" section
        import re
        fail_section_match = re.search(
            r'## ⚠️ Overall FAIL Summary.*?\n\n(.*?)\n\n---',
            report_content,
            re.DOTALL
        )
        
        if fail_section_match:
            fail_table = fail_section_match.group(1)
            lines = fail_table.split('\n')
            
            # Skip header and separator lines - process from line 2 onwards
            for line in lines[2:]:
                if line.strip().startswith('|') and '|' in line:
                    columns = [col.strip() for col in line.split('|')]
                    
                    # Skip rows that are headers or separators
                    # Check if this is a separator row (contains only dashes and pipes)
                    if len(columns) >= 3 and all(col == '' or set(col.replace(' ', '')) <= {'-', '|'} for col in columns):
                        continue
                    
                    # Skip rows that look like headers (contain "Image", "Element Type", etc.)
                    if len(columns) >= 3 and any(header in columns[1] for header in ['Image', 'Element Type', 'Foreground Color']):
                        continue
                    
                    # Valid data row
                    if len(columns) >= 11 and columns[1] and '<img' in columns[1]:  # Valid row with actual image tag
                        # Extract image filename from the image tag
                        img_match = re.search(r'src="[^"]*?([^/\\]+\.(?:png|jpg|jpeg|PNG|JPG|JPEG))"', columns[1])
                        if img_match:
                            img_filename = img_match.group(1)
                            # Reconstruct image tag with correct path from parent directory
                            corrected_img_path = os.path.join(subdir_name, 'img', img_filename)
                            corrected_image_tag = f'<img src="{corrected_img_path}" alt="{os.path.splitext(img_filename)[0]}" style="width: 80px; height: auto; border: 1px solid #ccc; border-radius: 3px;">'
                        else:
                            corrected_image_tag = columns[1]  # Fallback to original if parsing fails
                        
                        # Extract fail item with subdirectory context
                        fail_items = {
                            'subdirectory': subdir_name,
                            'image_tag': corrected_image_tag,
                            'image_name': columns[2],
                            'element_type': columns[3],
                            'element_description': columns[4],
                            'location': columns[5],
                            'foreground_color': columns[6],
                            'background_color': columns[7],
                            'contrast_ratio': columns[8],
                            'wcag_standard': columns[9],
                            'priority': columns[11],
                            'suggested_fix': columns[12] if len(columns) > 12 else ''
                        }
                        all_fail_items.append(fail_items)
        
        # Check if all images in this subdirectory passed
        if not fail_section_match or '**All elements passed WCAG 2.2 AA compliance!**' in report_content:
            # Extract image names from individual results
            for result_data in subdir_report['individual_results']:
                image_name = result_data['image_name']
                image_path = result_data['image_path']
                
                # Generate relative path for thumbnail (from parent_dir to subdirectory's img)
                relative_image_path = os.path.relpath(image_path, output_dir)
                
                all_pass_images.append({
                    'subdirectory': subdir_name,
                    'image_name': os.path.splitext(image_name)[0],
                    'image_path': relative_image_path
                })
    
    # Write consolidated overall_report.md
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    parent_dir_name = os.path.basename(os.path.normpath(parent_dir))
    
    with open(overall_report_path, 'w', encoding='utf-8') as f:
        f.write(f"# Overall WCAG 2.2 AA Color Contrast Audit Report\n\n")
        f.write(f"## Project: {parent_dir_name}\n\n")
        f.write(f"**Analysis Date:** {timestamp}\n\n")
        f.write(f"**Total Subdirectories Analyzed:** {len(subdirectory_reports)}\n\n")
        
        # Add links to individual subdirectory reports (moved before FAIL Summary)
        f.write("## 📋 Individual Subdirectory Reports\n\n")
        for subdir_report in subdirectory_reports:
            subdir_name = subdir_report['subdir_name']
            report_path = subdir_report['report_path']
            relative_report_path = os.path.relpath(report_path, output_dir)
            f.write(f"- [{subdir_name}]({relative_report_path})\n")
        
        f.write("\n---\n\n")
        
        # Write consolidated FAIL summary
        if all_fail_items:
            f.write("## ⚠️ FAIL Summary\n\n")
            f.write(f"**Total FAIL Items Across All Subdirectories:** {len(all_fail_items)}\n\n")
            f.write("| Subdirectory | Image | Image Name | Element Type | Element Description | Location | Foreground Color | Background Color | Contrast Ratio | WCAG Standard | Status | Priority | Suggested Fix |\n")
            f.write("|--------------|-------|------------|--------------|---------------------|----------|------------------|------------------|----------------|---------------|--------|----------|---------------|\n")
            
            for fail_item in all_fail_items:
                f.write(f"| {fail_item['subdirectory']} | {fail_item['image_tag']} | {fail_item['image_name']} | {fail_item['element_type']} | {fail_item['element_description']} | {fail_item['location']} | {fail_item['foreground_color']} | {fail_item['background_color']} | {fail_item['contrast_ratio']} | {fail_item['wcag_standard']} | ❌ FAIL | {fail_item['priority']} | {fail_item['suggested_fix']} |\n")
            
            f.write("\n")
        else:
            f.write("## ✅ Summary\n\n")
            f.write("**All elements across all subdirectories passed WCAG 2.2 AA compliance! No failures detected.**\n\n")
        
        f.write("---\n\n")
        
        # Write PASS summary table
        if all_pass_images:
            f.write("## ✅ PASS Summary\n\n")
            f.write(f"**Total Images Passed:** {len(all_pass_images)}\n\n")
            f.write("| Subdirectory | Image | Image Name | Compliance |\n")
            f.write("|--------------|-------|------------|------------|\n")
            
            for pass_item in all_pass_images:
                img_tag = f'<img src="{pass_item["image_path"]}" alt="{pass_item["image_name"]}" style="width: 80px; height: auto; border: 1px solid #ccc; border-radius: 3px;">'
                f.write(f"| {pass_item['subdirectory']} | {img_tag} | {pass_item['image_name']} | ✅ PASS |\n")
            
            f.write("\n")
        
        f.write("---\n\n")
        f.write("*Overall report generated by WCAG 2.2 AA compliance analyzer*\n")
    
    print(f"\n✅ Consolidated overall report generated!")
    print(f"📊 Overall report saved to: {overall_report_path}")
    print(f"📈 Total subdirectories analyzed: {len(subdirectory_reports)}")
    print(f"⚠️  Total FAIL items: {len(all_fail_items)}")
    print(f"✅ Total PASS images: {len(all_pass_images)}")
    
    return {
        'overall_report_path': overall_report_path,
        'subdirectory_reports': subdirectory_reports,
        'total_fail_items': len(all_fail_items)
    }


def preprocess_project_directory(project_dir):
    """
    Preprocess a project directory by organizing images into an 'img' subdirectory.
    
    Args:
        project_dir (str): Path to project directory (e.g., "src/tests/models/sample/GenAI-AdaLabs")
    
    Returns:
        str: Path to the img directory
    """
    if not os.path.exists(project_dir):
        raise FileNotFoundError(f"Project directory not found: {project_dir}")
    
    # Create img subdirectory
    img_dir = os.path.join(project_dir, "img")
    os.makedirs(img_dir, exist_ok=True)
    
    # Find all image files in the root of project directory
    image_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff'}
    image_files = [
        f for f in os.listdir(project_dir)
        if os.path.isfile(os.path.join(project_dir, f)) and 
        os.path.splitext(f.lower())[1] in image_extensions
    ]
    
    if not image_files:
        print(f"ℹ️  No images found in root of {project_dir}")
        return img_dir
    
    print(f"\n🔄 Preprocessing: Moving {len(image_files)} image(s) to img/ subdirectory...")
    
    # Move images to img directory
    import shutil
    moved_count = 0
    for image_file in image_files:
        src_path = os.path.join(project_dir, image_file)
        dst_path = os.path.join(img_dir, image_file)
        
        # Skip if file already exists in destination
        if os.path.exists(dst_path):
            print(f"⚠️  Skipping {image_file} (already exists in img/)")
            continue
        
        try:
            shutil.move(src_path, dst_path)
            print(f"✅ Moved: {image_file} -> img/")
            moved_count += 1
        except Exception as e:
            print(f"❌ Error moving {image_file}: {str(e)}")
    
    print(f"✅ Preprocessing complete: {moved_count} image(s) moved to {img_dir}\n")
    return img_dir


if __name__ == "__main__":
    # Test batch analysis with custom directory
    # Example: analyze_multiple_images("GenAI-AdaLabs")
    # This will create a consolidated report in the GenAI-AdaLabs directory
    
    import argparse
    parser = argparse.ArgumentParser(description='WCAG 2.2 AA Color Contrast Analyzer')
    parser.add_argument('--dir', type=str, help='Directory containing images to analyze (will preprocess if needed)')
    parser.add_argument('--output', type=str, help='Output directory for report (default: project_dir/report_cc)')
    parser.add_argument('--project', type=str, help='Project name for the report (default: directory name)')
    parser.add_argument('--no-preprocess', action='store_true', help='Skip preprocessing (assume images already in img/)')
    parser.add_argument('--recursive', action='store_true', help='Recursively analyze subdirectories and generate overall_report.md')
    parser.add_argument('--clean', action='store_true', help='Delete all existing .md report files before analysis')
    parser.add_argument('--element', type=str, help='Analyze a specific element (e.g., "Server-Adresse", "Submit Button")')
    parser.add_argument('--image', type=str, help='Path to single image (for --element mode or single image analysis)')
    parser.add_argument('--prompt', type=str, help='Custom analysis prompt file path (for --element mode)')
    
    args = parser.parse_args()
    
    # Handle --element flag for specific element analysis
    if args.element:
        if not args.image:
            print("❌ Error: --element requires --image parameter")
            parser.print_help()
            exit(1)
        
        # Load custom prompt if provided
        custom_prompt = None
        if args.prompt:
            if os.path.exists(args.prompt):
                with open(args.prompt, 'r', encoding='utf-8') as f:
                    custom_prompt = f.read()
                print(f"📝 Loaded custom prompt from: {args.prompt}")
            else:
                print(f"⚠️  Warning: Prompt file not found: {args.prompt}")
                print("Using default prompt template instead.")
        
        print(f"\n🎯 Analyzing specific element: {args.element}")
        print(f"{'='*80}\n")
        
        result = analyze_specific_element(
            element_name=args.element,
            image_path=args.image,
            output_dir=args.output,
            custom_prompt=custom_prompt
        )
        
        if result:
            print(f"\n🎉 Element analysis completed successfully!")
            print(f"📄 Report: {result}")
        else:
            print(f"\n❌ Element analysis failed.")
        
        exit(0)
    
    # Handle --clean flag
    if args.clean and args.dir:
        print(f"\n🗑️  Cleaning existing report files in: {args.dir}")
        print(f"{'='*80}\n")
        
        deleted_count = 0
        if args.recursive:
            # Clean reports in all subdirectories
            for root, dirs, files in os.walk(args.dir):
                for file in files:
                    if file.endswith('.md') and ('accessibility_audit_' in file or 'element_analysis_' in file or file == 'overall_report.md'):
                        file_path = os.path.join(root, file)
                        try:
                            os.remove(file_path)
                            print(f"✅ Deleted: {os.path.relpath(file_path, args.dir)}")
                            deleted_count += 1
                        except Exception as e:
                            print(f"❌ Error deleting {file_path}: {str(e)}")
        else:
            # Clean reports in single directory
            report_cc_dir = os.path.join(args.dir, 'report_cc')
            if os.path.exists(report_cc_dir):
                for file in os.listdir(report_cc_dir):
                    if file.endswith('.md'):
                        file_path = os.path.join(report_cc_dir, file)
                        try:
                            os.remove(file_path)
                            print(f"✅ Deleted: {os.path.relpath(file_path, args.dir)}")
                            deleted_count += 1
                        except Exception as e:
                            print(f"❌ Error deleting {file_path}: {str(e)}")
        
        print(f"\n✅ Cleanup complete: {deleted_count} report file(s) deleted\n")
        print(f"{'='*80}\n")
    
    if args.dir:
        if args.recursive:
            # Recursive analysis mode
            print(f"\n🔄 Starting recursive analysis of directory: {args.dir}")
            print(f"{'='*80}\n")
            
            result = analyze_recursive_directories(
                parent_dir=args.dir,
                output_dir=args.output
            )
            
            if result['overall_report_path']:
                print(f"\n🎉 Recursive analysis completed successfully!")
                print(f"📄 Overall Report: {result['overall_report_path']}")
                print(f"📊 Total subdirectories analyzed: {len(result['subdirectory_reports'])}")
                print(f"⚠️  Total FAIL items: {result['total_fail_items']}")
            else:
                print(f"\n❌ Recursive analysis failed.")
        else:
            # Batch analysis mode with preprocessing (single directory)
            project_dir = args.dir
            
            # Check if we need to preprocess
            img_dir = os.path.join(project_dir, "img")
            if not args.no_preprocess and not os.path.exists(img_dir):
                # No img directory exists, run preprocessing
                img_dir = preprocess_project_directory(project_dir)
            elif not args.no_preprocess:
                # img directory exists, but check if there are images in root
                image_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff'}
                root_images = [
                    f for f in os.listdir(project_dir)
                    if os.path.isfile(os.path.join(project_dir, f)) and 
                    os.path.splitext(f.lower())[1] in image_extensions
                ]
                if root_images:
                    # Found images in root, run preprocessing
                    img_dir = preprocess_project_directory(project_dir)
                else:
                    print(f"ℹ️  Using existing img directory: {img_dir}")
            
            # Run analysis
            result = analyze_multiple_images(
                image_directory=img_dir,
                output_dir=args.output,
                project_name=args.project
            )
            if result['report_path']:
                print(f"\n🎉 Batch analysis completed successfully.")
                print(f"📄 Report: {result['report_path']}")
    elif args.image:
        # Single image analysis mode with specified image
        result = test_analyze_image(image_path=args.image, output_dir=args.output)
        if result:
            print(f"\n🎉 Single image analysis completed successfully.")
            print(f"📄 Report: {result}")
    else:
        # Default: Single image analysis mode with default image
        result = test_analyze_image()
        if result:
            print(f"\n🎉 Single image analysis completed successfully.")
            print(f"📄 Report: {result}")
    
    print("\n🔍 WCAG 2.2 AA color contrast analysis completed.")
