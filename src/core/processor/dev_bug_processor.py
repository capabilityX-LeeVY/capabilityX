import sys
from typing import List, Optional
import pandas as pd
import os
import json
from dotenv import load_dotenv
load_dotenv()
pythonpath = os.getenv("PYTHONPATH")
if pythonpath:
    full_path = os.path.abspath(pythonpath)
    if full_path not in sys.path:
        sys.path.insert(0, full_path)

from models.openai_client import OpenAIClient
from common.utils.logger import LOGGER_INFO, LOGGER_WARNING, LOGGER_ERROR

class BugProcessor:
    """Bug data processor for batch processing CSV data and calling GPT API"""

    def __init__(self, input_file: str = '/Users/yanfzhen/workspace/WebexRegressSheild/dev_bugs.xlsx', output_file: str = 'data_with_response.xlsx', template_file: str = 'src/prompts/bug_analysis_template.md'):
        """
        Initialize Bug processor
        
        Args:
            input_file: Input Excel file path
            output_file: Output Excel file path
            template_file: Markdown template file path
        """
        self.input_file = input_file
        self.output_file = output_file
        self.template_file = template_file
        self.openai_client = OpenAIClient()
        self.df: Optional[pd.DataFrame] = None
        self.template_content: str = ""
    
    def load_template(self) -> None:
        """Load markdown template file"""
        try:
            with open(self.template_file, 'r', encoding='utf-8') as file:
                self.template_content = file.read()
            LOGGER_INFO(f"Successfully loaded template: {self.template_file}")
        except FileNotFoundError:
            LOGGER_WARNING(f"Warning: Template file not found {self.template_file}, using simple format")
            self.template_content = "Please analyze the following data: {column1_data}, {column2_data}"
        except Exception as e:
            LOGGER_ERROR(f"Error loading template: {e}")
            self.template_content = "Please analyze the following data: {column1_data}, {column2_data}"

    def read_excel_data(self) -> None:
        """Read Excel data"""
        try:
            self.df = pd.read_excel(self.input_file)
            LOGGER_INFO(f"Successfully read {len(self.df)} rows of data from Excel file")
        except FileNotFoundError:
            LOGGER_ERROR(f"Error: File not found {self.input_file}")
            raise
        except Exception as e:
            LOGGER_ERROR(f"Error reading Excel file: {e}")
            raise
    
    def prepare_header(self) -> None:
        """Prepare header, add analysis columns if needed"""
        if self.df is None or self.df.empty:
            return
            
        # Add columns for the analysis outputs
        if 'Meeting_Module' not in self.df.columns:
            self.df['Meeting_Module'] = ''
        if 'Accessibility_Category' not in self.df.columns:
            self.df['Accessibility_Category'] = ''
        if 'Accessibility_Subcategory' not in self.df.columns:
            self.df['Accessibility_Subcategory'] = ''
        if 'WCAG_Standard' not in self.df.columns:
            self.df['WCAG_Standard'] = ''
        if 'Complete_Analysis' not in self.df.columns:
            self.df['Complete_Analysis'] = ''
    
    def create_prompt(self, column1_data: str, column2_data: str) -> str:
        """
        Create prompt using template
        
        Args:
            column1_data: Data from first column
            column2_data: Data from second column
            
        Returns:
            Formatted prompt string
        """
        if not self.template_content:
            return f"Please analyze: {column1_data}, {column2_data}"
        
        # Replace placeholders in template
        prompt = self.template_content.replace("{column1_data}", str(column1_data))
        prompt = prompt.replace("{column2_data}", str(column2_data))
        
        return prompt

    def parse_gpt_response(self, response: str) -> tuple:
        """
        Parse GPT response JSON and extract the five components
        
        Args:
            response: GPT response string
            
        Returns:
            tuple: (meeting_module, accessibility_category, accessibility_subcategory, wcag_standard, complete_analysis)
        """
        try:
            # Try to find JSON in the response
            response_clean = response.strip()
            
            # Find the JSON block in the response
            start_idx = response_clean.find('{')
            end_idx = response_clean.rfind('}') + 1
            
            if start_idx != -1 and end_idx != 0:
                json_str = response_clean[start_idx:end_idx]
                parsed_data = json.loads(json_str)
                
                meeting_module = parsed_data.get('meeting_module', 'Unknown')
                accessibility_category = parsed_data.get('accessibility_category', 'Unknown')
                accessibility_subcategory = parsed_data.get('accessibility_subcategory', 'Unknown')
                wcag_standard = parsed_data.get('wcag_standard', 'Unknown')
                complete_analysis = json.dumps(parsed_data.get('complete_analysis', {}), indent=2)
                
                return meeting_module, accessibility_category, accessibility_subcategory, wcag_standard, complete_analysis
            else:
                return 'Parse Error', 'Parse Error', 'Parse Error', 'Parse Error', response
                
        except json.JSONDecodeError as e:
            LOGGER_ERROR(f"JSON parsing error: {e}")
            return 'JSON Error', 'JSON Error', 'JSON Error', 'JSON Error', response
        except Exception as e:
            LOGGER_ERROR(f"Response parsing error: {e}")
            return 'Error', 'Error', 'Error', 'Error', response

    def call_gpt_api(self, prompt: str) -> str:
        """
        Call GPT API
        
        Args:
            prompt: Input prompt
            
        Returns:
            GPT response result
        """
        try:
            response = self.openai_client.chat(prompt)
            return response if response is not None else "Error: No response from API"
        except Exception as e:
            return f"Error: {e}"
    
    def format_jira_link(self, jira_id: str) -> str:
        """
        Convert Jira ID to clickable link format
        
        Args:
            jira_id: Jira issue ID (e.g., SPARK-694239)
            
        Returns:
            Formatted link string
        """
        if pd.isna(jira_id) or str(jira_id).strip() == '' or str(jira_id) == 'Issue key':
            return jira_id
        
        jira_id_str = str(jira_id).strip()
        if jira_id_str.startswith('SPARK-'):
            jira_url = f"https://jira-eng-gpk2.cisco.com/jira/browse/{jira_id_str}"
            return f'=HYPERLINK("{jira_url}","{jira_id_str}")'
        
        return jira_id_str

    def process_rows(self) -> None:
        """Process all data rows"""
        if self.df is None or len(self.df) == 0:
            LOGGER_WARNING("No data rows to process")
            return
        
        # Get column names (assuming first 3 columns contain the data to process)
        columns = self.df.columns.tolist()
        if len(columns) < 3:
            LOGGER_ERROR("Error: Excel file must have at least 3 columns")
            return
        
        # Process each row
        for i, (index, row) in enumerate(self.df.iterrows()):
            # Skip rows with missing data in first 3 columns
            if pd.isna(row[columns[0]]) or pd.isna(row[columns[1]]) or pd.isna(row[columns[2]]):
                continue

            # Create structured prompt using template
            prompt = self.create_prompt(row[columns[1]], row[columns[2]])
            LOGGER_INFO(f"Processing row {i + 1}: {row[columns[0]]}")

            gpt_response = self.call_gpt_api(prompt)
            
            # Parse the response into five components
            meeting_module, accessibility_category, accessibility_subcategory, wcag_standard, complete_analysis = self.parse_gpt_response(gpt_response)
            
            # Update the five columns
            self.df.at[index, 'Meeting_Module'] = meeting_module
            self.df.at[index, 'Accessibility_Category'] = accessibility_category
            self.df.at[index, 'Accessibility_Subcategory'] = accessibility_subcategory
            self.df.at[index, 'WCAG_Standard'] = wcag_standard
            self.df.at[index, 'Complete_Analysis'] = complete_analysis
            
            # Format Jira ID as clickable link
            self.df.at[index, columns[0]] = self.format_jira_link(row[columns[0]])
    
    def write_excel_data(self) -> None:
        """Write processed data to Excel file with clickable links"""
        try:
            if self.df is not None:
                # Use openpyxl engine to support hyperlinks
                self.df.to_excel(self.output_file, index=False, engine='openpyxl')
                LOGGER_INFO(f"Completed, output file: {self.output_file}")
            else:
                LOGGER_ERROR("Error: No data to write")
        except Exception as e:
            LOGGER_ERROR(f"Error writing Excel file: {e}")
            raise
    
    def process(self) -> None:
        """Execute complete processing workflow"""
        LOGGER_INFO("Starting bug data processing...")
        self.load_template()
        self.read_excel_data()
        self.prepare_header()
        self.process_rows()
        self.write_excel_data()
        LOGGER_INFO("Bug data processing completed!")


# Usage example
if __name__ == "__main__":
    processor = BugProcessor()
    processor.process()
