
import requests
import os
import sys
from datetime import datetime

from dotenv import load_dotenv
from pathlib import Path
load_dotenv()
pythonpath = os.getenv("PYTHONPATH")
if pythonpath:
    full_path = os.path.abspath(pythonpath)
    if full_path not in sys.path:
        sys.path.insert(0, full_path)

from models.openai_client import OpenAIClient
from common.handler.settingsHandler import DynamicConfig
from config.paths import SETTINGS_PATH
from tools.Jira.reportParserToJira import CReportParserToJira

def test_analyze_image(image_path=None, output_dir=None):
    """
    Analyze image for focus ring detection and validation.
    
    Args:
        image_path (str, optional): Path to the image to analyze. 
                                  Defaults to sample image.
        output_dir (str, optional): Directory to save results. 
                                  Defaults to standard results directory.
    
    Returns:
        str: Path to the generated report file, or None if analysis failed.
    """
    # if image_path is None:
    #     image_path = fr"src/tests/models/sample/focus_ring_02.png"
    
    if output_dir is None:
        output_dir = os.path.join("src", "tests", "models", "results", "focus_ring")
    
    if not image_path:
        raise ValueError("image_path cannot be None")
    image = Path(image_path)
    image_name = image.name if image_path else "default_image_name"
    relative_path = str(Path(os.path.relpath(image, output_dir)).as_posix())
    print(f"relative_path: {relative_path}")
    message = f"""
You are a focus ring detection expert conducting a comprehensive screenshot analysis. Your task is to identify and validate focus rings (accessibility indicators) in UI elements.

**CRITICAL FOCUS RING DETECTION REQUIREMENTS:**

1. **COLOR SPECIFICATION** (MANDATORY):
   - ONLY detect focus rings with BLUE color in HSV range:
   - Hue: 100-124
   - Saturation: 43-255  
   - Value: 46-255
   - Reject any rings that do not match this exact blue color range
   - Convert and verify colors are within [100, 43, 46] to [124, 255, 255] HSV

2. **SHAPE VALIDATION** (REQUIRED):
   - CIRCLE: Perfect circular focus ring around element
   - OVAL/ELLIPSE: Elliptical focus ring (wider than tall or taller than wide)
   - RECTANGLE: Square-cornered rectangular focus ring
   - ROUNDED RECTANGLE: Rectangle with rounded corners
   - Reject any other irregular or complex shapes

3. **LINE THICKNESS ANALYSIS** (REQUIRED):
   - THIN: 1-2 pixel thickness
   - THICK: 3+ pixel thickness
   - Measure and classify the ring border width
   - Document exact pixel thickness when possible

4. **SINGLE RING VALIDATION** (CRITICAL RULE):
   - MUST be exactly ONE focus ring per focused element
   - REJECT any "ring within ring" or "double ring" patterns
   - REJECT any nested or overlapping ring structures
   - ONLY accept single, continuous ring boundaries

5. **COMPREHENSIVE DETECTION**:
   - Scan EVERY visible UI element for potential focus rings
   - Check buttons, inputs, links, menu items, tabs, controls
   - Identify both currently focused and any visible focus indicators
   - Document element type and location precisely

**MANDATORY OUTPUT FORMAT:**

ONLY output the markdown table. No additional text, headers, or explanations.

|No.|Image|Control Name|Analysis Result|Compliance|Reference|Suggestion|
|---|---|---|---|---|---|---|

**COLUMN SPECIFICATIONS:**
- **No.**: Sequential number starting from 1
- **Image**: Use format: `<img src="{relative_path}" alt="[control_description]" data-img-mhash="[hash]" style="max-width: 300px; height: auto;">`
- **Control Name**: Name or description of the UI control element
- **Analysis Result**: Detailed analysis of focus ring detection findings
- **Compliance**: ✅ Compliant or ❌ Non-Compliant based on all criteria
- **Reference**: Always use "WCAG 2.4.7 Focus Visible"
- **Suggestion**: Specific recommendations or "N/A" if compliant

**IMAGE FORMAT SPECIFICATION:**
Use this exact format for the Image column:
```html
<img src="{relative_path}" alt="[control_description]" data-img-mhash="[hash]" style="max-width: 300px; height: auto;">
```

**ANALYSIS RESULT FORMAT:**
- "A valid focus ring detected." (for VALID rings)
**COMPLIANCE CRITERIA:**
- ✅ Compliant: Focus ring meets ALL four criteria (color, shape, thickness, single ring)
- ❌ Non-Compliant: Focus ring fails ANY criteria or no ring detected

**VALIDATION CRITERIA CHECKLIST:**
✓ Color within blue HSV range [100-124, 43-255, 46-255]
✓ Shape is circle, oval, rectangle, or rounded rectangle
✓ Thickness is measurable (thin or thick)
✓ Single ring only (no nested or double rings)
✓ Ring is continuous and complete

**OUTPUT REQUIREMENT:**
Generate ONLY the markdown table. No headers, summaries, or additional text.

**COMPLIANCE MARKING RULES:**
- Mark as ✅ Compliant ONLY if focus ring meets ALL four criteria:
  1. Correct blue color range [100-124, 43-255, 46-255] HSV
  2. Valid shape (circle/oval/rectangle/rounded rectangle)  
  3. Measurable thickness (thin or thick)
  4. Single ring only (no nested rings)

- Mark as ❌ Non-Compliant if focus ring fails ANY criteria or no ring detected

**EXAMPLE OUTPUT:**
|No.|Image|Control Name|Analysis Result|Compliance|Reference|Suggestion|
|---|---|---|---|---|---|---|
|1|<img src="{relative_path}" alt="Call me dropdown" data-img-mhash="0c5fe79b6257193f" style="max-width: 300px; height: auto;">|Call me dropdown|No focus ring detected. Border is gray and does not qualify.|❌ Non-Compliant|WCAG 2.4.7 Focus Visible|Add a blue focus ring in the HSV range [100-124, 43-255, 46-255] when focused.|

Generate sequential numbers, accurate control names, detailed analysis results, and appropriate compliance markers."""

    if not os.path.exists(image):
        raise FileNotFoundError(f"Target image not found: {image}")

    # Create results directory if it doesn't exist
    results_dir = output_dir
    os.makedirs(results_dir, exist_ok=True)

    try:
        client = OpenAIClient()
        print(f"Analyzing image: {image}")
        print("Performing focus ring detection and validation...")
        
        analysis_result = client.ai_analyze_image(image, message=message)
        
        # Check if we got a result
        if analysis_result is None:
            print("❌ Failed to get analysis result from AI")
            return None
        
        print("✅ Focus ring analysis completed successfully")
        
    except Exception as e:
        print(f"❌ Error during AI analysis: {str(e)}")
        return None
    
    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    image_name = os.path.splitext(os.path.basename(image))[0]
    result_filename = f"focus_ring_analysis_{image_name}_{timestamp}.md"
    result_path = os.path.join(results_dir, result_filename)
    
    # Generate relative path from results directory to the image
    # From: src/tests/models/results/focus_ring/ to src/tests/models/sample/
    relative_image_path = f"..{os.sep}..{os.sep}sample{os.sep}{os.path.basename(image)}"
    
    # Save analysis result to markdown file - ONLY TABLE CONTENT
    with open(result_path, 'w', encoding='utf-8') as f:
        # Only write the AI analysis result (which should be just the table)
        f.write(str(analysis_result))
    
    print(f"📊 Focus ring table saved to: {result_path}")
    print(f"🔍 File contains only the markdown table")
    return result_path


def analyze_multiple_images(image_directory, output_dir=None):
    """
    Analyze multiple images in a directory for focus ring detection.
    
    Args:
        image_directory (str): Path to directory containing images to analyze
        output_dir (str, optional): Directory to save results
    
    Returns:
        list: List of paths to generated report files
    """
    if not os.path.exists(image_directory):
        raise FileNotFoundError(f"Image directory not found: {image_directory}")
    
    # Get all image files
    image_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff'}
    image_files = [
        os.path.join(image_directory, f) 
        for f in os.listdir(image_directory) 
        if os.path.splitext(f.lower())[1] in image_extensions
    ]
    
    if not image_files:
        print(f"❌ No image files found in {image_directory}")
        return []
    
    print(f"📁 Found {len(image_files)} image(s) to analyze")
    
    results = []
    for i, image_path in enumerate(image_files, 1):
        print(f"\n🖼️  Analyzing image {i}/{len(image_files)}: {os.path.basename(image_path)}")
        try:
            result_path = test_analyze_image(image_path, output_dir)
            if result_path:
                results.append(result_path)
        except Exception as e:
            print(f"❌ Error analyzing {image_path}: {str(e)}")
    
    print(f"\n✅ Batch analysis completed. {len(results)} reports generated.")
    return results


if __name__ == "__main__":
    # Test single image analysis
    image_path = Path("/Users/weiqli/Downloads/Your report and log files will be sent to Cisco to resolve technical problems and may be shared wit.png")
    result = test_analyze_image(image_path)
    if result:
        print(f"\n🎉 Single image focus ring analysis completed successfully.")
        print(f"📄 Report: {result}")
    
    # Uncomment to test batch analysis
    # batch_results = analyze_multiple_images("src/tests/models/sample")
    # if batch_results:
    #     print(f"\n🎉 Batch analysis completed. Generated {len(batch_results)} reports.")
    settings = DynamicConfig(SETTINGS_PATH)
    settings.set('jira', True)
    md_file = Path(result) if result else None
    md_file = Path("/Users/weiqli/workF/WebexRegressSheild/src/tests/models/results/focus_ring/focus_ring_analysis_text_20250910_173112.md")
    jira = CReportParserToJira(md_file, issueType="Focus Ring")
    jira.ParserReportAndFileBugs()
    settings.set('jira', False)
    
    print("\n🔍 Focus ring detection and validation analysis completed.")
