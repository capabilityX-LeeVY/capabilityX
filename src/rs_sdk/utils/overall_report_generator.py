#!/usr/bin/env python3
"""
Overall Test Report Generator
Generates a comprehensive markdown report based on TestCaseNavigateReport data
"""

import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from config.paths import OVERALL_REPORT_PATH, SESSION_OUTPUT_PATH, WINDOW_IMAGE_PATH, NAVIGATION_REPORT_PATH
from test_space.management.handlers.test_case_db_handler import TestCaseDBHandler
from common.utils.logger import LOGGER_INFO, LOGGER_ERROR, LOGGER_WARNING


class OverallReportGenerator:
    """
    Generates overall test reports from TestCaseNavigateReport data
    """

    def __init__(self):
        """Initialize the report generator"""
        self.db_handler = TestCaseDBHandler()
        
    def _create_report_directory(self) -> bool:
        """
        Create the overall report directory if it doesn't exist
        
        Returns:
            bool: Success status
        """
        try:
            OVERALL_REPORT_PATH.mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            LOGGER_ERROR(f"Failed to create overall report directory: {str(e)}")
            return False
    
    def _get_test_case_summary(self, report_id: str) -> List[Dict]:
        """
        Get test case summary data from database
        
        Args:
            report_id (str): The report ID to analyze
            
        Returns:
            List[Dict]: Test case summary data
        """
        connection = self.db_handler._get_db_connection()
        if not connection:
            return []
        
        try:
            with connection.cursor() as cursor:
                query = f"""
                    SELECT 
                        test_case,
                        MAX(step_order) as max_step,
                        -- Get actual window image path from database
                        CASE 
                            WHEN MAX(window_image_path) IS NOT NULL AND MAX(window_image_path) != '' 
                            THEN MAX(window_image_path)
                            ELSE CONCAT(test_case, '_', MAX(step_order), '.png')
                        END as window_image_path,
                        -- KB Navigate aggregation
                        CASE 
                            WHEN SUM(CASE WHEN navigate_result LIKE '%Failed%' THEN 1 ELSE 0 END) > 0 
                            THEN 'Failed'
                            WHEN SUM(CASE WHEN navigate_result LIKE '%Success%' THEN 1 ELSE 0 END) > 0
                            THEN 'Success'
                            ELSE 'N/A'
                        END as kb_navigate_status,
                        -- Focus Ring aggregation  
                        CASE 
                            WHEN SUM(CASE WHEN focus_ring_result LIKE '%WCAG%' OR focus_ring_result LIKE '%Failed%' THEN 1 ELSE 0 END) > 0 
                            THEN 'Failed'
                            WHEN SUM(CASE WHEN focus_ring_result LIKE '%Success%' THEN 1 ELSE 0 END) > 0
                            THEN 'Success'
                            ELSE 'N/A'
                        END as focus_ring_status,
                        -- Screen Reader aggregation
                        CASE 
                            WHEN SUM(CASE WHEN screen_reader_result LIKE '%Failed%' OR screen_reader_result LIKE '%Non-compliant%' THEN 1 ELSE 0 END) > 0 
                            THEN 'Failed'
                            WHEN SUM(CASE WHEN screen_reader_result LIKE '%Success%' OR screen_reader_result LIKE '%Compliant%' THEN 1 ELSE 0 END) > 0
                            THEN 'Success'
                            ELSE 'N/A'
                        END as screen_reader_status,
                        -- AI Check aggregation (using llm_response as proxy)
                        CASE 
                            WHEN SUM(CASE WHEN llm_response LIKE '%error%' OR llm_response LIKE '%failed%' THEN 1 ELSE 0 END) > 0 
                            THEN 'Failed'
                            WHEN SUM(CASE WHEN llm_response IS NOT NULL AND llm_response != '' THEN 1 ELSE 0 END) > 0
                            THEN 'Success'
                            ELSE 'N/A'
                        END as ai_check_status,
                        -- UI Response aggregation
                        CASE 
                            WHEN SUM(CASE WHEN ui_response_time_ms > 10000 THEN 1 ELSE 0 END) > 0 
                            THEN 'Failed'
                            WHEN SUM(CASE WHEN ui_response_time_ms <= 10000 AND ui_response_time_ms > 0 THEN 1 ELSE 0 END) > 0
                            THEN 'Success'
                            ELSE 'N/A'
                        END as ui_response_status,
                        -- Performance CPU aggregation (threshold 80%)
                        CASE 
                            WHEN SUM(CASE WHEN main_cpu > 80 THEN 1 ELSE 0 END) > 0 
                            THEN 'Failed'
                            WHEN SUM(CASE WHEN main_cpu <= 80 AND main_cpu > 0 THEN 1 ELSE 0 END) > 0
                            THEN 'Success'
                            ELSE 'N/A'
                        END as performance_cpu_status,
                        -- Performance Memory aggregation (threshold 2048MB)
                        CASE 
                            WHEN SUM(CASE WHEN main_mem > 2048 THEN 1 ELSE 0 END) > 0 
                            THEN 'Failed'
                            WHEN SUM(CASE WHEN main_mem <= 2048 AND main_mem > 0 THEN 1 ELSE 0 END) > 0
                            THEN 'Success'
                            ELSE 'N/A'
                        END as performance_mem_status,
                        -- Performance GPU aggregation (threshold 60%)
                        CASE 
                            WHEN SUM(CASE WHEN main_gpu > 60 THEN 1 ELSE 0 END) > 0 
                            THEN 'Failed'
                            WHEN SUM(CASE WHEN main_gpu <= 60 AND main_gpu > 0 THEN 1 ELSE 0 END) > 0
                            THEN 'Success'
                            ELSE 'N/A'
                        END as performance_gpu_status
                    FROM TestCaseNavigateReport 
                    WHERE report_id = '{report_id}'
                    GROUP BY test_case
                    ORDER BY MIN(step_order) ASC
                """
                
                cursor.execute(query)
                results = cursor.fetchall()
                
                test_cases = []
                for row in results:
                    test_cases.append({
                        'test_case': row[0],
                        'max_step': row[1],
                        'window_image_path': row[2],  # This is now the actual path from database
                        'kb_navigate_status': row[3],
                        'focus_ring_status': row[4],
                        'screen_reader_status': row[5],
                        'ai_check_status': row[6],
                        'ui_response_status': row[7],
                        'performance_cpu_status': row[8],
                        'performance_mem_status': row[9],
                        'performance_gpu_status': row[10]
                    })
                
                return test_cases
                
        except Exception as e:
            LOGGER_ERROR(f"Failed to get test case summary: {str(e)}")
            import traceback
            LOGGER_ERROR(f"Traceback: {traceback.format_exc()}")
            return []
            
        finally:
            if connection:
                connection.close()
    
    def _get_window_image_path(self, window_image_path: str, test_case: str, max_step: int) -> str:
        """
        Process window image path for markdown display with dynamic relative path calculation
        
        Args:
            window_image_path (str): Window image path from database (could be HTML or plain path)
            test_case (str): Test case name
            max_step (int): Maximum step number
            
        Returns:
            str: Relative path to window image for markdown
        """
        try:
            if window_image_path and window_image_path != 'N/A' and window_image_path.strip():
                # Check if it's an HTML img tag (contains src attribute)
                if '<img' in window_image_path and 'src=' in window_image_path:
                    # Extract src path from HTML img tag
                    import re
                    src_match = re.search(r'src="([^"]*)"', window_image_path)
                    if src_match:
                        extracted_path = src_match.group(1).replace('\\', '/')
                        
                        if extracted_path.startswith('../') or extracted_path.startswith('./'):
                            abs_image_path = (NAVIGATION_REPORT_PATH / extracted_path).resolve()
                        else:
                            abs_image_path = (NAVIGATION_REPORT_PATH / extracted_path).resolve()
                        
                        try:
                            relative_path = os.path.relpath(abs_image_path, OVERALL_REPORT_PATH)
                            return relative_path.replace('\\', '/')
                        except ValueError:
                            LOGGER_WARNING(f"Cannot create relative path: {abs_image_path} -> {OVERALL_REPORT_PATH}")
                            return extracted_path
                
                # Handle actual file path from database
                if os.path.isabs(window_image_path):
                    # Absolute path - calculate relative path using global paths
                    try:
                        relative_path = os.path.relpath(window_image_path, OVERALL_REPORT_PATH)
                        return relative_path.replace('\\', '/')
                    except ValueError:
                        filename = os.path.basename(window_image_path)
                        relative_path = os.path.relpath(WINDOW_IMAGE_PATH / filename, OVERALL_REPORT_PATH)
                        return relative_path.replace('\\', '/')
                else:
                    # Relative path or filename
                    if '\\' in window_image_path or '/' in window_image_path:
                        path = window_image_path.replace('\\', '/')
                        abs_path = (NAVIGATION_REPORT_PATH / path).resolve()
                        relative_path = os.path.relpath(abs_path, OVERALL_REPORT_PATH)
                        return relative_path.replace('\\', '/')
                    else:
                        abs_path = WINDOW_IMAGE_PATH / window_image_path
                        relative_path = os.path.relpath(abs_path, OVERALL_REPORT_PATH)
                        return relative_path.replace('\\', '/')
            
            # Fallback: use WINDOW_IMAGE_PATH
            fallback_file = WINDOW_IMAGE_PATH / f"{test_case}_final.jpg"
            relative_path = os.path.relpath(fallback_file, OVERALL_REPORT_PATH)
            return relative_path.replace('\\', '/')
            
        except Exception as e:
            LOGGER_WARNING(f"Failed to process window image path '{window_image_path}': {str(e)}")
            return f"../../data/img/window/{test_case}.jpg"
    
    def _format_status(self, status: str) -> str:
        """
        Format status with appropriate emoji
        
        Args:
            status (str): Status from database ('Success', 'Failed', 'N/A')
            
        Returns:
            str: Formatted status with emoji
        """
        if status == 'Success':
            return '✅Success'
        elif status == 'Failed':
            return '❌Failed'
        else:
            return 'N/A'
    
    def _format_image_markdown(self, image_path: str, alt_text: str) -> str:
        """
        Format image path as markdown image tag
        
        Args:
            image_path (str): Path to image file
            alt_text (str): Alt text for image
            
        Returns:
            str: Formatted markdown image tag
        """
        return f'<img src="{image_path}" alt="{alt_text}" style="max-width: 200px; height: auto;">'
    
    def generate_overall_report(self, report_id: Optional[str] = None) -> Dict:
        """
        Generate overall test report
        
        Args:
            report_id (str, optional): Specific report ID. If None, uses current report_id
            
        Returns:
            dict: Generation result with success status and file path
        """
        try:
            # Get report_id if not provided
            if report_id is None:
                report_id = self.db_handler.get_current_report_id()
                
            if not report_id:
                LOGGER_ERROR("No report ID available for overall report generation")
                return {'success': False, 'error': 'No report ID available'}
            
            LOGGER_INFO(f"Generating overall report for report_id: {report_id}", "BLUE")
            
            # Create report directory
            if not self._create_report_directory():
                return {'success': False, 'error': 'Failed to create report directory'}
            
            # Get test case summary data
            test_cases = self._get_test_case_summary(report_id)
            
            if not test_cases:
                LOGGER_WARNING(f"No test case data found for report_id: {report_id}")
                return {'success': False, 'error': 'No test case data found'}
            
            # Generate report content
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_filename = f"overall_report_{report_id}_{timestamp}.md"
            report_file_path = OVERALL_REPORT_PATH / report_filename
            
            # Build markdown content
            markdown_content = self._build_markdown_content(report_id, test_cases)
            
            # Write report file
            with open(report_file_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            
            LOGGER_INFO(f"Overall report generated successfully: {report_file_path}", "GREEN")
            
            return {
                'success': True,
                'report_id': report_id,
                'file_path': str(report_file_path),
                'test_cases_count': len(test_cases)
            }
            
        except Exception as e:
            LOGGER_ERROR(f"Failed to generate overall report: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _build_markdown_content(self, report_id: str, test_cases: List[Dict]) -> str:
        """
        Build the markdown content for the overall report
        
        Args:
            report_id (str): Report ID
            test_cases (List[Dict]): Test case summary data
            
        Returns:
            str: Formatted markdown content
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        content = f"""# Overall Test Report

**Report ID**: {report_id}  
**Generated**: {timestamp}  
**Total Test Cases**: {len(test_cases)}

## Test Results Summary

| Test Case | Window Image | KB Navigate | Focus Ring | Screen Reader | AI Check | UI Response | CPU | Memory | GPU | Jira Issue |
|-----------|--------------|-------------|------------|---------------|----------|-------------|-----|--------|-----|------------|
"""
        
        for test_case in test_cases:
            # Get window image path and format
            window_image_path = self._get_window_image_path(
                test_case['window_image_path'], 
                test_case['test_case'], 
                test_case['max_step']
            )
            
            window_image_md = self._format_image_markdown(
                window_image_path, 
                test_case['test_case']
            )
            
            # Build table row with formatted statuses
            content += f"| {test_case['test_case']} | {window_image_md} | {self._format_status(test_case['kb_navigate_status'])} | {self._format_status(test_case['focus_ring_status'])} | {self._format_status(test_case['screen_reader_status'])} | {self._format_status(test_case['ai_check_status'])} | {self._format_status(test_case['ui_response_status'])} | {self._format_status(test_case['performance_cpu_status'])} | {self._format_status(test_case['performance_mem_status'])} | {self._format_status(test_case['performance_gpu_status'])} |  |\n"
        
        # Add summary statistics
        total_cases = len(test_cases)
        if total_cases == 0:
            # Handle empty case
            return f"""# Overall Test Report

**Report ID**: {report_id}  
**Generated**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}  
**Total Test Cases**: 0

No test cases found for this report.
"""
        success_counts = {
            'kb_navigate': len([tc for tc in test_cases if tc['kb_navigate_status'] == 'Success']),
            'focus_ring': len([tc for tc in test_cases if tc['focus_ring_status'] == 'Success']),
            'screen_reader': len([tc for tc in test_cases if tc['screen_reader_status'] == 'Success']),
            'ai_check': len([tc for tc in test_cases if tc['ai_check_status'] == 'Success']),
            'ui_response': len([tc for tc in test_cases if tc['ui_response_status'] == 'Success']),
            'performance_cpu': len([tc for tc in test_cases if tc['performance_cpu_status'] == 'Success']),
            'performance_mem': len([tc for tc in test_cases if tc['performance_mem_status'] == 'Success']),
            'performance_gpu': len([tc for tc in test_cases if tc['performance_gpu_status'] == 'Success'])
        }
        
        content += f"""

## Summary Statistics

| Metric | Success Rate | Success Count | Total Count |
|--------|--------------|---------------|-------------|
| KB Navigate | {(success_counts['kb_navigate']/total_cases*100):.1f}% | {success_counts['kb_navigate']} | {total_cases} |
| Focus Ring | {(success_counts['focus_ring']/total_cases*100):.1f}% | {success_counts['focus_ring']} | {total_cases} |
| Screen Reader | {(success_counts['screen_reader']/total_cases*100):.1f}% | {success_counts['screen_reader']} | {total_cases} |
| AI Check | {(success_counts['ai_check']/total_cases*100):.1f}% | {success_counts['ai_check']} | {total_cases} |
| UI Response | {(success_counts['ui_response']/total_cases*100):.1f}% | {success_counts['ui_response']} | {total_cases} |
| CPU Performance | {(success_counts['performance_cpu']/total_cases*100):.1f}% | {success_counts['performance_cpu']} | {total_cases} |
| Memory Performance | {(success_counts['performance_mem']/total_cases*100):.1f}% | {success_counts['performance_mem']} | {total_cases} |
| GPU Performance | {(success_counts['performance_gpu']/total_cases*100):.1f}% | {success_counts['performance_gpu']} | {total_cases} |

## Notes

- **KB Navigate**: Keyboard navigation functionality test results
- **Focus Ring**: Visual focus indicator compliance (WCAG 2.4.7)
- **Screen Reader**: Screen reader compatibility and accessibility
- **AI Check**: AI-powered quality assurance validation
- **UI Response**: User interface response time performance
- **CPU Performance**: CPU usage within threshold (≤80%)
- **Memory Performance**: Memory usage within threshold (≤1024MB)
- **GPU Performance**: GPU usage within threshold (≤60%)
- **Jira Issue**: Link to related Jira issues (to be filled manually)

---
*Report generated by WebexRegressSheild Overall Report Generator*
"""
        
        return content


def generate_overall_report_cli():
    """
    Command line interface for generating overall reports
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate Overall Test Report')
    parser.add_argument('--report_id', type=str, help='Specific report ID to generate report for')
    parser.add_argument('--output', type=str, help='Output file path (optional)')
    
    args = parser.parse_args()
    
    generator = OverallReportGenerator()
    result = generator.generate_overall_report(args.report_id)
    
    if result['success']:
        print(f"✅ Overall report generated successfully!")
        print(f"📊 Report ID: {result['report_id']}")
        print(f"📁 File Path: {result['file_path']}")
        print(f"📈 Test Cases: {result['test_cases_count']}")
    else:
        print(f"❌ Failed to generate overall report: {result['error']}")
        sys.exit(1)


if __name__ == "__main__":
    generate_overall_report_cli()
