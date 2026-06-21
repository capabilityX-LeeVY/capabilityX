#!/usr/bin/env python3
"""
Bug Statistics Analyzer
Analyzes and summarizes accessibility bugs by category and subcategory
"""

import sys
import os
import pandas as pd
from collections import defaultdict
from typing import Dict, List, Tuple
from dotenv import load_dotenv

load_dotenv()
pythonpath = os.getenv("PYTHONPATH")
if pythonpath:
    full_path = os.path.abspath(pythonpath)
    if full_path not in sys.path:
        sys.path.insert(0, full_path)

from common.utils.logger import LOGGER_INFO, LOGGER_WARNING, LOGGER_ERROR


class BugStatistics:
    """统计和分析可访问性bug的类别分布"""
    
    CATEGORY_MAPPING = {
        'Writing': 'Writing',
        'Font': 'Writing',
        'Color': 'Color',
        'Color Contrast': 'Color',
        'Scaling': 'Scaling',
        'Zoom': 'Scaling',
        'Keyboard': 'Keyboard Operation',
        'Keyboard Operation': 'Keyboard Operation',
        'Focus': 'Keyboard Operation',
        'Visual': 'Visual & Acoustic Barriers',
        'Acoustic': 'Visual & Acoustic Barriers',
        'High Contrast': 'Visual & Acoustic Barriers',
        'Screen Reader': 'Screenreader',
        'Screenreader': 'Screenreader',
        'JAWS': 'Screenreader',
        'NVDA': 'Screenreader',
        'Language': 'Language',
        'Localization': 'Language',
        'Navigation': 'User Guidance',
        'User Guidance': 'User Guidance',
        'Layout': 'Layout & Design',
        'Design': 'Layout & Design',
        'UI': 'Layout & Design',
        'Usability': 'Usability',
        'Braille': 'Braille'
    }
    
    # sub category
    STANDARD_STRUCTURE = {
        'Writing': [
            'Font',
            'Character height',
            'Icon',
            'Image polarity'
        ],
        'Color': [
            'Color contrast',
            'Color information',
            'Color convention',
            'Use of color'
        ],
        'Scaling': [
            'Adjustment via Zoom',
            'Adjusting window size',
            'Font graphics'
        ],
        'Keyboard Operation': [
            'Visible focus / Keyboard operation / Standard actions',
            'Series / Keyboard shortcuts'
        ],
        'Visual & Acoustic Barriers': [
            'High contrast',
            'Optical & acoustic effects'
        ],
        'Screenreader': [
            'Screen reader compatibility',
            'Screen reader test',
            'Screen reader for static text, label'
        ],
        'Language': [
            'Language'
        ],
        'User Guidance': [
            'Navigation elements / User control / Error prevention'
        ],
        'Layout & Design': [
            'Mask layout / Design of the form / UI element / Error message'
        ],
        'Usability': [
            'Self-help / Input assistance / Input verification / Other points'
        ],
        'Braille': [
            'Braille display output',
            'Braille input keyboard',
            'Braille translation accuracy',
            'Refreshable Braille device compatibility'
        ]
    }
    
    def __init__(self, input_file: str, output_file: str = None):
        """
        Initialize the statistics analyzer
        
        Args:
            input_file: path to input Excel file
            output_file: path to output statistics report file (optional)
        """
        self.input_file = input_file
        self.output_file = output_file or input_file.replace('.xlsx', '_statistics.xlsx')
        self.df: pd.DataFrame = None
        self.statistics: Dict = {}
    
    def load_data(self) -> None:
        """Load Excel data"""
        try:
            self.df = pd.read_excel(self.input_file)
            LOGGER_INFO(f"Successfully loaded {len(self.df)} rows of data")
            
            # Check required columns
            if 'Accessibility_Category' not in self.df.columns:
                LOGGER_ERROR("Error: Missing 'Accessibility_Category' column")
                raise ValueError("Missing required column: Accessibility_Category")
            
            if 'Accessibility_Subcategory' not in self.df.columns:
                LOGGER_ERROR("Error: Missing 'Accessibility_Subcategory' column")
                raise ValueError("Missing required column: Accessibility_Subcategory")
                
        except Exception as e:
            LOGGER_ERROR(f"Failed to load data: {e}")
            raise
    
    def normalize_category(self, category: str) -> str:
        """
        Standardize category name
        
        Args:
            category: Original category name
            
        Returns:
            Standardized category name
        """
        if pd.isna(category) or str(category).strip() == '':
            return 'Unknown'
        
        category_str = str(category).strip()
        
        # Try to match predefined mappings
        for key, value in self.CATEGORY_MAPPING.items():
            if key.lower() in category_str.lower():
                return value
        
        return category_str
    
    def analyze_data(self) -> None:
        """Analyze data and generate statistics"""
        try:
            # Initialize statistics structure
            stats = defaultdict(lambda: defaultdict(int))
            total_bugs = 0
            
            # Count each category and subcategory
            for _, row in self.df.iterrows():
                category = self.normalize_category(row['Accessibility_Category'])
                subcategory = row['Accessibility_Subcategory']
                
                if pd.isna(subcategory):
                    subcategory = 'Unspecified'
                else:
                    subcategory = str(subcategory).strip()
                
                stats[category][subcategory] += 1
                total_bugs += 1
            
            self.statistics = {
                'stats': dict(stats),
                'total': total_bugs
            }
            
            LOGGER_INFO(f"Analysis completed: {total_bugs} bugs, {len(stats)} categories")
            
        except Exception as e:
            LOGGER_ERROR(f"Data analysis failed: {e}")
            raise
    
    def generate_report(self) -> pd.DataFrame:
        """
        Generate statistics report DataFrame
        
        Returns:
            DataFrame containing statistics information
        """
        try:
            report_data = []
            total_bugs = self.statistics['total']
            stats = self.statistics['stats']
            
            # Generate report according to standard structure
            for module, subcategories in self.STANDARD_STRUCTURE.items():
                module_total = sum(stats.get(module, {}).values())
                
                for i, subcategory in enumerate(subcategories):
                    count = stats.get(module, {}).get(subcategory, 0)
                    percentage = (count / total_bugs * 100) if total_bugs > 0 else 0
                    status = '✅' if count > 0 else '❌'
                    
                    report_data.append({
                        'Module': module if i == 0 else '',
                        'Sub-item': subcategory,
                        'Count': count,
                        'Percentage': f"{percentage:.1f}%",
                        'Status': status
                    })
            
            # 添加未分类的类别
            for category, subcats in stats.items():
                if category not in self.STANDARD_STRUCTURE and category != 'Unknown':
                    for i, (subcat, count) in enumerate(subcats.items()):
                        percentage = (count / total_bugs * 100) if total_bugs > 0 else 0
                        status = '✅' if count > 0 else '❌'
                        
                        report_data.append({
                            'Module': category if i == 0 else '',
                            'Sub-item': subcat,
                            'Count': count,
                            'Percentage': f"{percentage:.1f}%",
                            'Status': status
                        })
            
            # add total row
            report_data.append({
                'Module': 'TOTAL',
                'Sub-item': 'All Categories',
                'Count': total_bugs,
                'Percentage': '100.0%',
                'Status': '📊'
            })
            
            report_df = pd.DataFrame(report_data)
            return report_df
            
        except Exception as e:
            LOGGER_ERROR(f"Failed to generate report: {e}")
            raise
    
    def print_report(self, report_df: pd.DataFrame) -> None:
        """
        Print formatted report to console
        
        Args:
            report_df: Report DataFrame
        """
        print("\n" + "="*100)
        print("Accessibility Bug Statistics Report")
        print("="*100)
        print(f"\nTotal Bugs: {self.statistics['total']}")
        print(f"Number of Categories: {len(self.statistics['stats'])}")
        print("\n")
        
        # Print table
        print(f"{'Module':<30} | {'Sub-item':<65} | {'Count':>7} | {'Percentage':>10} | {'Status':^6}")
        print("-"*130)
        
        current_module = None
        for _, row in report_df.iterrows():
            module = row['Module'] if row['Module'] else ''
            
            # If it's a new module, print a separator line
            if module and module != current_module and current_module is not None:
                print("-"*130)
            
            print(f"{module:<30} | {row['Sub-item']:<65} | {row['Count']:>7} | {row['Percentage']:>10} | {row['Status']:^6}")
            
            if module:
                current_module = module
        
        print("="*100 + "\n")
    
    def save_report(self, report_df: pd.DataFrame) -> None:
        """
        Save report to Excel file
        
        Args:
            report_df: Report DataFrame
        """
        try:
            with pd.ExcelWriter(self.output_file, engine='openpyxl') as writer:
                # Write statistics report
                report_df.to_excel(writer, sheet_name='Statistics', index=False)
                
                # Write raw data (optional)
                self.df.to_excel(writer, sheet_name='Raw Data', index=False)
                
                # Adjust column widths
                worksheet = writer.sheets['Statistics']
                worksheet.column_dimensions['A'].width = 32
                worksheet.column_dimensions['B'].width = 67
                worksheet.column_dimensions['C'].width = 10
                worksheet.column_dimensions['D'].width = 12
                worksheet.column_dimensions['E'].width = 8
            
            LOGGER_INFO(f"Report saved to: {self.output_file}")
            
        except Exception as e:
            LOGGER_ERROR(f"Failed to save report: {e}")
            raise
    
    def process(self) -> None:
        """Execute the complete statistical analysis process"""
        LOGGER_INFO("Starting statistical analysis...")
        self.load_data()
        self.analyze_data()
        report_df = self.generate_report()
        self.print_report(report_df)
        self.save_report(report_df)
        LOGGER_INFO("Statistical analysis completed!")


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Statistical analysis of accessibility bug distribution",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
examples:
  # Analyze default file
  python bug_statistics.py
  
  # Analyze specified file
  python bug_statistics.py --input data_with_response.xlsx
  
  # Specify output file
  python bug_statistics.py --input data_with_response.xlsx --output report.xlsx
        """
    )
    
    parser.add_argument('--input', '-i', 
                       default='/Users/yanfzhen/workspace/WebexRegressSheild/data_with_response.xlsx',
                       help='Input Excel file path')
    parser.add_argument('--output', '-o',
                       help='Output report file path (optional)')
    
    args = parser.parse_args()
    
    try:
        analyzer = BugStatistics(args.input, args.output)
        analyzer.process()
    except Exception as e:
        LOGGER_ERROR(f"Statistical analysis failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
