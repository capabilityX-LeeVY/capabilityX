"""
screen_reader_ui_analyzer.py

Analyze UI elements from current window screenshot and generate screen reader compatibility report.
This function extracts all visible UI elements using OCR/Vision AI and saves the analysis to a report.
"""

import os
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()
pythonpath = os.getenv("PYTHONPATH")
if pythonpath:
    full_path = os.path.abspath(pythonpath)
    if full_path not in sys.path:
        sys.path.insert(0, full_path)

from models.openai_client import OpenAIClient
from common.utils.logger import LOGGER_INFO, LOGGER_DEBUG, LOGGER_ERROR
from config.paths import SCREEN_READER_REPORT_PATH
from rs_sdk.utils.control_recorder import ControlRecorder
from core.processor.srText_processor import ScreenReaderDataProcessor


def analyze_ui_elements_for_screen_reader(window_name: str = "Current Window", save_image: bool = True):
    """
    Analyze all UI elements in the current window for screen reader compatibility.
    
    This function:
    1. Captures a screenshot of the current window using ControlRecorder
    2. Uses OpenAI Vision API to extract all visible UI elements
    3. Generates a markdown report with all detected elements
    4. Saves the report to SCREEN_READER_REPORT_PATH
    
    Args:
        window_name (str): Name of the window being analyzed (for report title)
        save_image (bool): Whether to save the captured screenshot
    
    Returns:
        bool: True if analysis completed successfully, False otherwise
    """
    try:
        LOGGER_INFO("=" * 80, "CYAN")
        LOGGER_INFO("🔍 Starting UI Elements Analysis for Screen Reader", "CYAN")
        LOGGER_INFO("=" * 80, "CYAN")
        
        # Step 1: Capture current window screenshot
        LOGGER_INFO("📸 Step 1: Capturing window screenshot...", "BLUE")
        control_recorder = ControlRecorder()
        current_control_window_image_abs_path, current_control_window_image_bytes = control_recorder.record_window_image()
        
        if not current_control_window_image_abs_path:
            LOGGER_ERROR("❌ Failed to capture window screenshot", "RED")
            return False
            
        LOGGER_INFO(f"✅ Screenshot captured: {current_control_window_image_abs_path}", "GREEN")
        
        # Step 2: Extract UI elements using OpenAI Vision API
        LOGGER_INFO("🤖 Step 2: Extracting UI elements using AI Vision...", "BLUE")
        client = OpenAIClient()
        result = client.extract_ui_elements(current_control_window_image_abs_path)
        
        if not result:
            LOGGER_ERROR("❌ Failed to extract UI elements", "RED")
            return False
            
        LOGGER_INFO(f"✅ UI elements extracted successfully", "GREEN")
        LOGGER_DEBUG(f"Extracted content preview:\n{result[:200]}...", "YELLOW")
        
        # Step 3: Generate markdown report
        LOGGER_INFO("📝 Step 3: Generating screen reader compatibility report...", "BLUE")
        
        # Create report directory if it doesn't exist
        report_dir = Path(SCREEN_READER_REPORT_PATH)
        report_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate report filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"ui_elements_{window_name.lower().replace(' ', '_')}_{timestamp}.md"
        report_path = report_dir / report_filename
        
        # Build comprehensive report
        report_content = _build_report(
            window_name=window_name,
            screenshot_path=current_control_window_image_abs_path,
            ui_elements=result,
            timestamp=timestamp,
            report_path=report_path
        )
        
        # Step 4: Save report to file
        LOGGER_INFO(f"💾 Step 4: Saving report to {report_path}...", "BLUE")
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
            
        LOGGER_INFO("=" * 80, "GREEN")
        LOGGER_INFO(f"✅ SUCCESS: Report saved to {report_path}", "GREEN")
        LOGGER_INFO("=" * 80, "GREEN")
        
        # Step 5: Generate Screen Reader data file
        LOGGER_INFO(f"📝 Step 5: Generating Screen Reader data file...", "BLUE")
        srText_processor = ScreenReaderDataProcessor()
        file_name_path = srText_processor.get_screen_reader_data()
        
        if file_name_path:
            LOGGER_INFO(f"📄 Screen Reader data file generated: {file_name_path}", "GREEN")
        else:
            LOGGER_ERROR(f"⚠️ Failed to generate Screen Reader data file", "YELLOW")
        
        # Step 6: Compare UI elements with Screen Reader data
        if file_name_path and os.path.exists(file_name_path):
            enhanced_ui_table = _compare_ui_with_sr_data(
                result, 
                file_name_path, 
                similarity_threshold=0.6,
                report_path=str(report_path)
            )
            
            # Rebuild report with enhanced comparison table
            LOGGER_INFO("📝 Updating report with comparison results...", "BLUE")
            enhanced_report = _build_report(
                window_name=window_name,
                screenshot_path=current_control_window_image_abs_path,
                ui_elements=enhanced_ui_table,
                timestamp=timestamp,
                report_path=report_path
            )
            
            # Save updated report
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(enhanced_report)
            
            LOGGER_INFO(f"✅ Report updated with SR comparison at {report_path}", "GREEN")
        else:
            LOGGER_ERROR(f"⚠️ Screen Reader data file not found: {file_name_path}", "YELLOW")
        
        # Print summary
        element_count = result.count('\n|') - 2  # Subtract header rows
        LOGGER_INFO(f"📊 Summary:", "CYAN")
        LOGGER_INFO(f"   • Window: {window_name}", "CYAN")
        LOGGER_INFO(f"   • Elements detected: ~{element_count}", "CYAN")
        LOGGER_INFO(f"   • Screenshot: {current_control_window_image_abs_path}", "CYAN")
        LOGGER_INFO(f"   • Report: {report_path}", "CYAN")
        LOGGER_INFO(f"   • Screen Reader data: {file_name_path}", "CYAN")
        
        return True
        
    except Exception as e:
        LOGGER_ERROR(f"❌ Error in analyze_ui_elements_for_screen_reader: {str(e)}", "RED")
        import traceback
        LOGGER_ERROR(traceback.format_exc(), "RED")
        return False


def _build_report(window_name: str, screenshot_path: str, ui_elements: str, timestamp: str, report_path: Path) -> str:
    """
    Build comprehensive markdown report for screen reader analysis.
    
    Args:
        window_name (str): Name of the analyzed window
        screenshot_path (str): Path to the screenshot image
        ui_elements (str): Extracted UI elements in markdown table format
        timestamp (str): Timestamp of the analysis
        report_path (Path): Path where the report will be saved (for relative path calculation)
    
    Returns:
        str: Complete markdown report content
    """
    # Calculate element count (avoid backslash in f-string)
    newline_count = ui_elements.count('\n')
    pipe_count = ui_elements.count('|')
    element_count = pipe_count // (newline_count + 1) - 2
    
    # Calculate relative path for screenshot image
    screenshot_rel_path = os.path.relpath(screenshot_path, os.path.dirname(report_path))
    screenshot_html = f'<img src="{screenshot_rel_path}" alt="{window_name}_screenshot" style="max-width: 800px; height: auto;">'
    
    report = f"""# Screen Reader UI Elements Analysis Report

## Window Information

- **Window Name**: {window_name}
- **Analysis Date**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
- **Screenshot**: `{screenshot_path}`
- **Report Generated**: {timestamp}

---

## Screenshot

{screenshot_html}

---

## UI Elements Detected

The following UI elements were detected in the window using AI Vision analysis:

{ui_elements}

---

*Report generated by Webex Accessibility Test Framework*
"""
    return report


def _compare_ui_with_sr_data(ui_elements_markdown: str, sr_data_file_path: str, similarity_threshold: float = 0.6, report_path: str | None = None) -> str:
    """
    Compare UI elements with Screen Reader data using LLM and generate comparison table.
    
    This function uses an LLM to intelligently compare UI elements with Screen Reader data,
    leveraging semantic understanding for better matching accuracy.
    
    Args:
        ui_elements_markdown (str): Markdown table with UI elements
        sr_data_file_path (str): Path to Screen Reader data file
        similarity_threshold (float): Minimum similarity for match (default: 0.6)
        report_path (str): Path to the report file (will be used to save UI elements temporarily)
    
    Returns:
        str: Enhanced markdown table with validation status and SR descriptions
    """
    LOGGER_INFO("🔍 Step 6: Comparing UI elements with Screen Reader data using LLM...", "BLUE")
    
    try:
        # Create temporary UI elements file for LLM comparison
        if report_path:
            # Use the same directory as the report
            temp_ui_path = report_path.replace('.md', '_temp_ui_elements.md')
        else:
            # Use a default path
            temp_dir = Path(SCREEN_READER_REPORT_PATH)
            temp_dir.mkdir(parents=True, exist_ok=True)
            temp_ui_path = temp_dir / 'temp_ui_elements.md'
        
        # Save UI elements table to temporary file
        with open(temp_ui_path, 'w', encoding='utf-8') as f:
            f.write(ui_elements_markdown)
        
        LOGGER_INFO(f"📄 Temporary UI elements file: {temp_ui_path}", "YELLOW")
        LOGGER_INFO(f"📄 Screen Reader data file: {sr_data_file_path}", "YELLOW")
        
        # Use OpenAI client to compare using LLM
        client = OpenAIClient()
        llm_result = client.compare_ui_with_sr_data(
            ui_report_path=str(temp_ui_path),
            sr_data_path=sr_data_file_path
        )
        
        # Clean up temporary file
        try:
            if os.path.exists(temp_ui_path):
                os.remove(temp_ui_path)
                LOGGER_DEBUG(f"🗑️ Cleaned up temporary file: {temp_ui_path}", "YELLOW")
        except Exception as cleanup_error:
            LOGGER_DEBUG(f"⚠️ Could not remove temporary file: {cleanup_error}", "YELLOW")
        
        if not llm_result:
            LOGGER_ERROR("❌ LLM comparison failed, falling back to original table", "RED")
            return ui_elements_markdown
        
        # Extract the comparison table from LLM result
        # The LLM should return a complete markdown table
        LOGGER_INFO("✅ LLM comparison completed successfully", "GREEN")
        
        # Parse the LLM result to extract statistics
        try:
            pass_count = llm_result.count('✅ PASS')
            fail_count = llm_result.count('❌ FAIL')
            total_elements = pass_count + fail_count
            
            if total_elements > 0:
                LOGGER_INFO(f"📊 Comparison Summary:", "CYAN")
                LOGGER_INFO(f"   • Total UI Elements: {total_elements}", "CYAN")
                LOGGER_INFO(f"   • Passed (found in SR): {pass_count} ({pass_count/total_elements*100:.1f}%)", "GREEN")
                LOGGER_INFO(f"   • Failed (not in SR): {fail_count} ({fail_count/total_elements*100:.1f}%)", "RED")
                LOGGER_INFO(f"   • Similarity Threshold: {similarity_threshold:.0%}", "CYAN")
        except Exception as stats_error:
            LOGGER_DEBUG(f"⚠️ Could not extract statistics: {stats_error}", "YELLOW")
        
        return llm_result
        
    except Exception as e:
        LOGGER_ERROR(f"❌ Error in LLM comparison: {str(e)}", "RED")
        import traceback
        LOGGER_ERROR(traceback.format_exc(), "RED")
        # Fall back to original table
        return ui_elements_markdown


# Alias for backward compatibility (if the longer name was used)
anaylze_screen_reader_from_all_ui_elements = analyze_ui_elements_for_screen_reader
