"""
Test Steps Extractor
Extracts structured test information from JIRA bug descriptions
Author: WebexRegressShield Team
"""

import re
import json
from typing import List, Dict, Optional, Any, Union
from datetime import datetime

from common.utils.logger import LOGGER_INFO, LOGGER_WARNING, LOGGER_ERROR


class JiraStepsExtractor:
    """
    Extracts test steps and related information from JIRA bug descriptions
    """
    
    def __init__(self):
        """Initialize the Test Steps Extractor"""
        self.patterns = self._initialize_patterns()
    
    def _initialize_patterns(self) -> Dict[str, str]:
        """Initialize regex patterns for different sections"""
        return {
            'prerequisites': r'Prerequisites?[:\s]*\\?[-]*([^\\]*?)(?=\\?Steps?[:\s]|$)',
            'steps': r'Steps?[:\s]*\\?([^*]*?)(?=\*?Expected Result|$)',
            'expected_result': r'\*?Expected Result[:\s]*\*?\\?([^*]*?)(?=\*?Actual Result|\*?Suggested resolution|$)',
            'actual_result': r'\*?Actual Result[:\s]*\*?\\?([^*]*?)(?=\*?Suggested resolution|\*?Attachments|$)',
            'suggested_resolution': r'\*?Suggested resolution[s]*[:\s]*\*?\\?([^*]*?)(?=\*?Attachments|\*?Failed WCAG|$)',
            'wcag_checkpoints': r'\*?Failed WCAG[^:]*[:\s]*\*?\\?([^*]*?)(?=\*?User Impact|\*?Automation|$)',
            'user_impact': r'\*?User Impact[:\s]*\*?\\?([^*]*?)(?=\*?Automation|$)',
            'attachments': r'\*?Attachments[:\s]*\*?\\?([^*]*?)(?=\*?Failed WCAG|\*?User Impact|$)',
            'automation': r'\*?Automation\*?\\?([^*]*?)$',
            'step_number': r'\\?(\d+)\.\s*([^\\]*?)(?=\\|$)',
            'wcag_number': r'(\d+\.\d+\.\d+)',
            'attachment_file': r'([^:\s]+\.(png|jpg|jpeg|gif|mp4|avi|mov|pdf|doc|docx))[:\s]*\[([^\]]+)\]'
        }
    
    def clean_text(self, text: str) -> str:
        """
        Clean and normalize text
        
        Args:
            text: Raw text to clean
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        # Remove extra whitespace and normalize
        cleaned = re.sub(r'\s+', ' ', text.strip())
        
        # Remove control characters
        cleaned = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', cleaned)
        
        # Replace backslashes used as line breaks
        cleaned = cleaned.replace('\\', ' ')
        
        # Remove excessive spaces
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        return cleaned
    
    def extract_prerequisites(self, text: str) -> List[str]:
        """
        Extract prerequisites from text
        
        Args:
            text: Text containing prerequisites
            
        Returns:
            List of prerequisite strings
        """
        try:
            match = re.search(self.patterns['prerequisites'], text, re.IGNORECASE | re.DOTALL)
            if not match:
                return []
            
            prereq_text = match.group(1).strip()
            
            # Split by lines and clean up
            prereq_lines = []
            for line in prereq_text.split('\\'):
                cleaned_line = self.clean_text(line.lstrip('-').strip())
                if cleaned_line and len(cleaned_line) > 3:
                    prereq_lines.append(cleaned_line)
            
            return prereq_lines
            
        except Exception as e:
            LOGGER_ERROR(f"Failed to extract prerequisites: {e}")
            return []
    
    def extract_steps(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract numbered test steps from text
        
        Args:
            text: Text containing test steps
            
        Returns:
            List of step dictionaries with step_number and description
        """
        try:
            # First find the steps section
            steps_match = re.search(self.patterns['steps'], text, re.IGNORECASE | re.DOTALL)
            if not steps_match:
                return []
            
            steps_text = steps_match.group(1).strip()
            LOGGER_INFO(f"text is {steps_text}")

            # Find numbered steps
            step_matches = re.findall(self.patterns['step_number'], steps_text, re.DOTALL)
            LOGGER_INFO(f"step_matches is {step_matches}")

            return step_matches
            
        except Exception as e:
            LOGGER_ERROR(f"Failed to extract steps: {e}")
            return []
    
    def extract_expected_result(self, text: str) -> str:
        """
        Extract expected result from text
        
        Args:
            text: Text containing expected result
            
        Returns:
            Expected result string
        """
        try:
            match = re.search(self.patterns['expected_result'], text, re.IGNORECASE | re.DOTALL)
            if match:
                return self.clean_text(match.group(1))
            return ""
            
        except Exception as e:
            LOGGER_ERROR(f"Failed to extract expected result: {e}")
            return ""
    
    def extract_actual_result(self, text: str) -> str:
        """
        Extract actual result from text
        
        Args:
            text: Text containing actual result
            
        Returns:
            Actual result string
        """
        try:
            match = re.search(self.patterns['actual_result'], text, re.IGNORECASE | re.DOTALL)
            if match:
                return self.clean_text(match.group(1))
            return ""
            
        except Exception as e:
            LOGGER_ERROR(f"Failed to extract actual result: {e}")
            return ""
    
    def extract_suggested_resolution(self, text: str) -> str:
        """
        Extract suggested resolution from text
        
        Args:
            text: Text containing suggested resolution
            
        Returns:
            Suggested resolution string
        """
        try:
            match = re.search(self.patterns['suggested_resolution'], text, re.IGNORECASE | re.DOTALL)
            if match:
                return self.clean_text(match.group(1))
            return ""
            
        except Exception as e:
            LOGGER_ERROR(f"Failed to extract suggested resolution: {e}")
            return ""
    
    def extract_wcag_checkpoints(self, text: str) -> List[str]:
        """
        Extract WCAG checkpoint numbers from text
        
        Args:
            text: Text containing WCAG checkpoints
            
        Returns:
            List of WCAG checkpoint numbers
        """
        try:
            # First find the WCAG section
            wcag_match = re.search(self.patterns['wcag_checkpoints'], text, re.IGNORECASE | re.DOTALL)
            if not wcag_match:
                return []
            
            wcag_text = wcag_match.group(1).strip()
            
            # Extract checkpoint numbers like "1.3.1"
            checkpoints = re.findall(self.patterns['wcag_number'], wcag_text)
            return list(set(checkpoints))  # Remove duplicates
            
        except Exception as e:
            LOGGER_ERROR(f"Failed to extract WCAG checkpoints: {e}")
            return []
    
    def extract_user_impact(self, text: str) -> str:
        """
        Extract user impact from text
        
        Args:
            text: Text containing user impact
            
        Returns:
            User impact string
        """
        try:
            match = re.search(self.patterns['user_impact'], text, re.IGNORECASE | re.DOTALL)
            if match:
                return self.clean_text(match.group(1))
            return ""
            
        except Exception as e:
            LOGGER_ERROR(f"Failed to extract user impact: {e}")
            return ""
    
    def extract_attachments(self, text: str) -> List[Dict[str, str]]:
        """
        Extract attachment information from text
        
        Args:
            text: Text containing attachments
            
        Returns:
            List of attachment dictionaries
        """
        try:
            # First find the attachments section
            attachments_match = re.search(self.patterns['attachments'], text, re.IGNORECASE | re.DOTALL)
            if not attachments_match:
                return []
            
            attachments_text = attachments_match.group(1).strip()
            
            # Extract file names and URLs
            attachment_matches = re.findall(self.patterns['attachment_file'], attachments_text, re.IGNORECASE)
            
            attachments = []
            for filename, ext, url in attachment_matches:
                attachments.append({
                    'filename': filename.strip(),
                    'extension': ext.lower(),
                    'url': url.strip(),
                    'type': self._get_file_type(ext.lower())
                })
            
            return attachments
            
        except Exception as e:
            LOGGER_ERROR(f"Failed to extract attachments: {e}")
            return []
    
    def extract_automation_info(self, text: str) -> str:
        """
        Extract automation information from text
        
        Args:
            text: Text containing automation info
            
        Returns:
            Automation information string
        """
        try:
            match = re.search(self.patterns['automation'], text, re.IGNORECASE | re.DOTALL)
            if match:
                return self.clean_text(match.group(1))
            return ""
            
        except Exception as e:
            LOGGER_ERROR(f"Failed to extract automation info: {e}")
            return ""
    
    def _get_file_type(self, extension: str) -> str:
        """
        Get file type category based on extension
        
        Args:
            extension: File extension
            
        Returns:
            File type category
        """
        image_types = ['png', 'jpg', 'jpeg', 'gif', 'bmp', 'svg']
        video_types = ['mp4', 'avi', 'mov', 'wmv', 'flv']
        document_types = ['pdf', 'doc', 'docx', 'txt', 'rtf']
        
        if extension in image_types:
            return 'image'
        elif extension in video_types:
            return 'video'
        elif extension in document_types:
            return 'document'
        else:
            return 'other'
    
    def extract_all(self, text: str) -> Dict[str, Any]:
        """
        Extract all test information from text
        
        Args:
            text: Text containing test information
            
        Returns:
            Dictionary containing all extracted information
        """
        try:
            if not text:
                return {}
            
            # Clean the input text
            cleaned_text = re.sub(r'\s+', ' ', text.strip())
            
            # Extract all sections
            extracted_info = {
                'prerequisites': self.extract_prerequisites(cleaned_text),
                'steps': self.extract_steps(cleaned_text),
                'expected_result': self.extract_expected_result(cleaned_text),
                'actual_result': self.extract_actual_result(cleaned_text),
                'suggested_resolution': self.extract_suggested_resolution(cleaned_text),
                'failed_wcag_checkpoints': self.extract_wcag_checkpoints(cleaned_text),
                'user_impact': self.extract_user_impact(cleaned_text),
                'attachments': self.extract_attachments(cleaned_text),
                'automation': self.extract_automation_info(cleaned_text),
                'extraction_metadata': {
                    'extracted_at': datetime.now().isoformat(),
                    'text_length': len(text),
                    'cleaned_text_length': len(cleaned_text),
                    'steps_count': len(self.extract_steps(cleaned_text)),
                    'prerequisites_count': len(self.extract_prerequisites(cleaned_text)),
                    'attachments_count': len(self.extract_attachments(cleaned_text)),
                    'wcag_checkpoints_count': len(self.extract_wcag_checkpoints(cleaned_text))
                }
            }
            
            return extracted_info
            
        except Exception as e:
            LOGGER_ERROR(f"Failed to extract all information: {e}")
            return {
                'error': str(e),
                'extraction_metadata': {
                    'extracted_at': datetime.now().isoformat(),
                    'success': False
                }
            }
    
    def format_as_text(self, extracted_info: Dict[str, Any]) -> str:
        """
        Format extracted information as readable text
        
        Args:
            extracted_info: Dictionary containing extracted information
            
        Returns:
            Formatted text string
        """
        try:
            if not extracted_info or 'error' in extracted_info:
                return "No test information found or extraction failed."
            
            formatted_lines = []
            
            # Prerequisites
            if extracted_info.get('prerequisites'):
                formatted_lines.append("PREREQUISITES:")
                for i, prereq in enumerate(extracted_info['prerequisites'], 1):
                    formatted_lines.append(f"  {i}. {prereq}")
                formatted_lines.append("")
            
            # Steps
            if extracted_info.get('steps'):
                formatted_lines.append("TEST STEPS:")
                for step in extracted_info['steps']:
                    formatted_lines.append(f"  {step['step_number']}. {step['description']}")
                formatted_lines.append("")
            
            # Expected Result
            if extracted_info.get('expected_result'):
                formatted_lines.append("EXPECTED RESULT:")
                formatted_lines.append(f"  {extracted_info['expected_result']}")
                formatted_lines.append("")
            
            # Actual Result
            if extracted_info.get('actual_result'):
                formatted_lines.append("ACTUAL RESULT:")
                formatted_lines.append(f"  {extracted_info['actual_result']}")
                formatted_lines.append("")
            
            # Suggested Resolution
            if extracted_info.get('suggested_resolution'):
                formatted_lines.append("SUGGESTED RESOLUTION:")
                formatted_lines.append(f"  {extracted_info['suggested_resolution']}")
                formatted_lines.append("")
            
            # WCAG Checkpoints
            if extracted_info.get('failed_wcag_checkpoints'):
                formatted_lines.append("FAILED WCAG CHECKPOINTS:")
                formatted_lines.append(f"  {', '.join(extracted_info['failed_wcag_checkpoints'])}")
                formatted_lines.append("")
            
            # User Impact
            if extracted_info.get('user_impact'):
                formatted_lines.append("USER IMPACT:")
                formatted_lines.append(f"  {extracted_info['user_impact']}")
                formatted_lines.append("")
            
            # Attachments
            if extracted_info.get('attachments'):
                formatted_lines.append("ATTACHMENTS:")
                for attachment in extracted_info['attachments']:
                    formatted_lines.append(f"  - {attachment['filename']} ({attachment['type'].upper()})")
                formatted_lines.append("")
            
            # Automation
            if extracted_info.get('automation'):
                formatted_lines.append("AUTOMATION:")
                formatted_lines.append(f"  {extracted_info['automation']}")
                formatted_lines.append("")
            
            # Metadata
            if extracted_info.get('extraction_metadata'):
                metadata = extracted_info['extraction_metadata']
                formatted_lines.append("EXTRACTION SUMMARY:")
                formatted_lines.append(f"  Steps found: {metadata.get('steps_count', 0)}")
                formatted_lines.append(f"  Prerequisites: {metadata.get('prerequisites_count', 0)}")
                formatted_lines.append(f"  WCAG checkpoints: {metadata.get('wcag_checkpoints_count', 0)}")
                formatted_lines.append(f"  Attachments: {metadata.get('attachments_count', 0)}")
                formatted_lines.append(f"  Extracted at: {metadata.get('extracted_at', 'Unknown')}")
            
            return "\n".join(formatted_lines)
            
        except Exception as e:
            LOGGER_ERROR(f"Failed to format extracted information: {e}")
            return f"Error formatting information: {e}"
    
    def format_as_json(self, extracted_info: Dict[str, Any], indent: int = 2) -> str:
        """
        Format extracted information as JSON
        
        Args:
            extracted_info: Dictionary containing extracted information
            indent: JSON indentation level
            
        Returns:
            JSON string
        """
        try:
            return json.dumps(extracted_info, indent=indent, ensure_ascii=False)
        except Exception as e:
            LOGGER_ERROR(f"Failed to format as JSON: {e}")
            return json.dumps({'error': str(e)}, indent=indent)
    
    def extract_steps_only(self, text: str) -> List[str]:
        """
        Extract only the test steps as a simple list of strings
        
        Args:
            text: Text containing test steps
            
        Returns:
            List of step descriptions
        """
        try:
            steps = self.extract_steps(text)
            return [step['description'] for step in steps]
        except Exception as e:
            LOGGER_ERROR(f"Failed to extract steps only: {e}")
            return []
    
    def validate_extraction(self, extracted_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate the extracted information and provide quality metrics
        
        Args:
            extracted_info: Dictionary containing extracted information
            
        Returns:
            Dictionary containing validation results
        """
        try:
            validation = {
                'is_valid': True,
                'warnings': [],
                'quality_score': 0,
                'completeness': {}
            }
            
            # Check completeness
            sections = ['prerequisites', 'steps', 'expected_result', 'actual_result']
            for section in sections:
                has_content = bool(extracted_info.get(section))
                validation['completeness'][section] = has_content
                if has_content:
                    validation['quality_score'] += 25
            
            # Check for warnings
            if not extracted_info.get('steps'):
                validation['warnings'].append("No test steps found")
                validation['is_valid'] = False
            
            if len(extracted_info.get('steps', [])) < 3:
                validation['warnings'].append("Very few test steps found (less than 3)")
            
            if not extracted_info.get('expected_result'):
                validation['warnings'].append("No expected result found")
            
            if not extracted_info.get('actual_result'):
                validation['warnings'].append("No actual result found")
            
            # Normalize quality score
            validation['quality_score'] = min(100, validation['quality_score'])
            
            return validation
            
        except Exception as e:
            LOGGER_ERROR(f"Failed to validate extraction: {e}")
            return {
                'is_valid': False,
                'error': str(e),
                'quality_score': 0
            }


if __name__ == "__main__":
    # Test the extractor with sample data
    extractor = JiraStepsExtractor()
    
    sample_text = """View your issue at Applause Testing Services

*Action details*

*Action Performed:*
Prerequisites:
-Download and install the Webex app
-Log in with a test account, e.g., test@example.com

Steps:
1. Using Windows + JAWS, open the Webex App.
2. Tab to focus on the 'Meetings' button from the left-side menu and press Enter to activate it.
3. Tab to focus on the 'Start a Webex meeting' or a scheduled meeting button and press Enter to start the meeting.

*Expected Result:*
When the user navigates to the Participants list, the screen reader should announce the list properly.

*Actual Result:*
The screen reader announces incorrect information with verbose content.

*Failed WCAG 2.1 checkpoint(s):*
1.3.1

*User Impact:*
Users with disabilities may have difficulty using the feature.

*Automation*
Applause-automated"""
    
    print("=== Testing Test Steps Extractor ===")
    
    # Extract all information
    result = extractor.extract_all(sample_text)
    
    # Print formatted result
    print(extractor.format_as_text(result))
    
    # Validate the extraction
    validation = extractor.validate_extraction(result)
    print(f"\nValidation: {validation}")