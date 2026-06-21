#!/usr/bin/env python3
"""
Accessibility Category Module Analysis
Analyze Meeting Module distribution for a specified accessibility category.
Supported: Keyboard Operation, Screen Reader, Color, Writing, Scaling, Visual & Acoustic, Language, User Guidance, Layout & Design, Usability, Braille
"""

import sys
import os
import pandas as pd
from collections import defaultdict
from typing import Dict, List
from dotenv import load_dotenv

load_dotenv()
pythonpath = os.getenv("PYTHONPATH")
if pythonpath:
    full_path = os.path.abspath(pythonpath)
    if full_path not in sys.path:
        sys.path.insert(0, full_path)

from common.utils.logger import LOGGER_INFO, LOGGER_WARNING, LOGGER_ERROR


class CategoryModuleAnalysis:
    """Analyze Meeting Module distribution for a specified accessibility category."""
    
    # Predefined categories and their matching keywords
    CATEGORY_KEYWORDS = {
        'Keyboard Operation': ['keyboard', 'focus', 'keyboard operation'],
        'Screen Reader': ['screen reader', 'screenreader', 'jaws', 'nvda', 'sr'],
        'Color': ['color', 'color contrast', 'high contrast'],
        'Writing': ['writing', 'font', 'character height', 'icon'],
        'Scaling': ['scaling', 'zoom', 'adjusting window size'],
        'Visual & Acoustic': ['visual', 'acoustic', 'high contrast', 'optical'],
        'Language': ['language', 'localization'],
        'User Guidance': ['navigation', 'user guidance', 'user control'],
        'Layout & Design': ['layout', 'design', 'ui', 'mask layout'],
        'Usability': ['usability', 'self-help', 'input assistance'],
        'Braille': ['braille']
    }
    
    def __init__(self, input_file: str, category: str = 'Keyboard Operation'):
        """
        Initialize the analyzer
        
        Args:
            input_file: Path to the input Excel file
            category: The category name to analyze (default is 'Keyboard Operation')
        """
        self.input_file = input_file
        self.category = category
        self.df = None
        self.filtered_df = None
        self.module_stats = []
    
    def load_data(self) -> None:
        """Load Excel data"""
        try:
            self.df = pd.read_excel(self.input_file)
            LOGGER_INFO(f"Successfully loaded {len(self.df)} rows of data")
            
            # Check for required columns
            required_columns = ['Accessibility_Category', 'Meeting_Module']
            missing_columns = [col for col in required_columns if col not in self.df.columns]
            
            if missing_columns:
                LOGGER_ERROR(f"Missing required columns: {missing_columns}")
                raise ValueError(f"Missing required columns: {missing_columns}")
                
        except Exception as e:
            LOGGER_ERROR(f"Failed to load data: {e}")
            raise
    
    def get_category_keywords(self) -> List[str]:
        """
        Get matching keywords for the current category
        
        Returns:
            List of keywords
        """
        # Try to get from predefined dictionary
        for key, keywords in self.CATEGORY_KEYWORDS.items():
            if self.category.lower() in key.lower() or key.lower() in self.category.lower():
                return keywords
        
        # If not predefined, use the category name itself
        return [self.category.lower()]
    
    def filter_by_category(self) -> None:
        """Filter data for the specified category"""
        try:
            keywords = self.get_category_keywords()
            
            # Build filter condition - use OR logic to match any keyword
            mask = pd.Series([False] * len(self.df), index=self.df.index)
            
            for keyword in keywords:
                mask |= self.df['Accessibility_Category'].str.contains(keyword, case=False, na=False)
            
            self.filtered_df = self.df[mask].copy()
            
            LOGGER_INFO(f"Filtered {len(self.filtered_df)} rows related to '{self.category}'")
            LOGGER_INFO(f"Using matching keywords: {', '.join(keywords)}")
            
            if len(self.filtered_df) == 0:
                LOGGER_WARNING(f"Warning: No data found related to '{self.category}'")
                print(f"\n⚠️  Warning: No data matching '{self.category}' found")
                print(f"Attempted keywords: {', '.join(keywords)}")
                print("\nAvailable categories:")
                if 'Accessibility_Category' in self.df.columns:
                    unique_categories = self.df['Accessibility_Category'].dropna().unique()
                    for cat in sorted(unique_categories):
                        print(f"  • {cat}")
                
        except Exception as e:
            LOGGER_ERROR(f"Failed to filter data: {e}")
            raise
    
    def analyze_by_module(self) -> None:
        """Analyze statistics by Meeting Module"""
        try:
            if self.filtered_df is None or len(self.filtered_df) == 0:
                LOGGER_WARNING("No data available for analysis")
                return
            
            # Count the number of each Module
            module_counts = defaultdict(int)
            total_bugs = len(self.filtered_df)
            
            for _, row in self.filtered_df.iterrows():
                module = row['Meeting_Module']
                
                # Handle missing or unknown values
                if pd.isna(module) or str(module).strip() == '':
                    module = 'Unknown'
                else:
                    module = str(module).strip()
                
                module_counts[module] += 1
            
            # Calculate percentages and sort
            self.module_stats = []
            for module, count in sorted(module_counts.items(), key=lambda x: x[1], reverse=True):
                percentage = (count / total_bugs * 100) if total_bugs > 0 else 0
                self.module_stats.append({
                    'Meeting_Module': module,
                    'Count': count,
                    'Percentage': percentage,
                    'Percentage_Str': f"{percentage:.1f}%"
                })
            
            LOGGER_INFO(f"Analysis completed: {total_bugs} '{self.category}' bugs across {len(module_counts)} different Modules")
            
        except Exception as e:
            LOGGER_ERROR(f"Analysis failed: {e}")
            raise
    
    def print_report(self) -> None:
        """Print analysis report to console"""
        print("\n" + "="*100)
        print(f"{self.category} - Meeting Module Distribution Analysis")
        print("="*100)
        
        total_bugs = sum(item['Count'] for item in self.module_stats)
        print(f"\nTotal {self.category}: {total_bugs}")
        print(f"Number of Meeting Modules involved: {len(self.module_stats)}")
        print("\n")
        
        # Print table
        print(f"{'Meeting Module':<40} | {'Count':>8} | {'Percentage':>12} | {'Bar':<30}")
        print("-"*100)
        
        for item in self.module_stats:
            bar_length = int(item['Percentage'] / 3)  # One character per 3%
            bar = '█' * bar_length
            
            print(f"{item['Meeting_Module']:<40} | {item['Count']:>8} | {item['Percentage_Str']:>12} | {bar:<30}")
        
        print("="*100)
        print("\n")
    
    def print_subcategory_breakdown(self) -> None:
        """Print subcategory breakdown for each Module"""
        if self.filtered_df is None or len(self.filtered_df) == 0:
            return
            
        if 'Accessibility_Subcategory' not in self.filtered_df.columns:
            LOGGER_WARNING("No Accessibility_Subcategory column, skipping subcategory analysis")
            return
        
        print("\n" + "="*100)
        print(f"Subcategory breakdown of {self.category} for each Meeting Module")
        print("="*100 + "\n")
        
        for module_item in self.module_stats:
            module = module_item['Meeting_Module']
            module_df = self.filtered_df[
                (self.filtered_df['Meeting_Module'] == module) | 
                ((pd.isna(self.filtered_df['Meeting_Module']) | (self.filtered_df['Meeting_Module'] == '')) & (module == 'Unknown'))
            ]
            
            if len(module_df) == 0:
                continue
            
            print(f"\n📁 {module} ({module_item['Count']} bugs, {module_item['Percentage_Str']})")
            print("-" * 80)
            
            # Count subcategories
            subcategory_counts = module_df['Accessibility_Subcategory'].value_counts()
            
            for subcat, count in subcategory_counts.items():
                percentage = (count / module_item['Count'] * 100)
                print(f"  • {str(subcat)[:60]:<60} : {count:>3} ({percentage:>5.1f}%)")
        
        print("\n" + "="*100 + "\n")
    
    def save_detailed_report(self, output_file=None) -> None:
        """
        Save detailed report to Excel
        
        Args:
            output_file: Output file path (optional)
        """
        if output_file is None:
            # Generate file name based on category
            safe_category = self.category.replace(' ', '_').replace('&', 'and').lower()
            output_file = self.input_file.replace('.xlsx', f'_{safe_category}_module_analysis.xlsx')
        
        try:
            with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
                # Write summary statistics
                summary_df = pd.DataFrame(self.module_stats)
                summary_df.to_excel(writer, sheet_name='Module Summary', index=False)
                
                # Write detailed data
                if self.filtered_df is not None and len(self.filtered_df) > 0:
                    sheet_name = f'{self.category[:25]} Details'  # Excel sheet name limit is 31 chars
                    self.filtered_df.to_excel(writer, sheet_name=sheet_name, index=False)
                
                # If there are subcategories, create detailed breakdown sheet
                if self.filtered_df is not None and 'Accessibility_Subcategory' in self.filtered_df.columns:
                    detailed_breakdown = []
                    
                    for module_item in self.module_stats:
                        module = module_item['Meeting_Module']
                        module_df = self.filtered_df[
                            (self.filtered_df['Meeting_Module'] == module) | 
                            ((pd.isna(self.filtered_df['Meeting_Module']) | (self.filtered_df['Meeting_Module'] == '')) & (module == 'Unknown'))
                        ]
                        
                        subcategory_counts = module_df['Accessibility_Subcategory'].value_counts()
                        
                        for subcat, count in subcategory_counts.items():
                            percentage = (count / module_item['Count'] * 100)
                            detailed_breakdown.append({
                                'Meeting_Module': module,
                                'Subcategory': subcat,
                                'Count': count,
                                'Percentage_in_Module': f"{percentage:.1f}%",
                                'Module_Total': module_item['Count']
                            })
                    
                    breakdown_df = pd.DataFrame(detailed_breakdown)
                    breakdown_df.to_excel(writer, sheet_name='Subcategory Breakdown', index=False)
                
                # Adjust column widths
                for sheet_name in writer.sheets:
                    worksheet = writer.sheets[sheet_name]
                    for column in worksheet.columns:
                        max_length = 0
                        column_letter = column[0].column_letter
                        for cell in column:
                            try:
                                if len(str(cell.value)) > max_length:
                                    max_length = len(str(cell.value))
                            except:
                                pass
                        adjusted_width = min(max_length + 2, 50)
                        worksheet.column_dimensions[column_letter].width = adjusted_width
            
            LOGGER_INFO(f"Detailed report saved to: {output_file}")
            print(f"\n✅ Detailed report saved to: {output_file}")
            
        except Exception as e:
            LOGGER_ERROR(f"Failed to save report: {e}")
            raise
    
    def process(self, save_report: bool = True) -> None:
        """
        Execute the full analysis process
        
        Args:
            save_report: Whether to save the detailed report to Excel
        """
        LOGGER_INFO(f"Starting analysis of Meeting Module distribution for '{self.category}'...")
        self.load_data()
        self.filter_by_category()
        
        if self.filtered_df is not None and len(self.filtered_df) > 0:
            self.analyze_by_module()
            self.print_report()
            self.print_subcategory_breakdown()
            
            if save_report:
                self.save_detailed_report()
        else:
            print(f"\n❌ No data found for category '{self.category}', unable to continue analysis")
        
        LOGGER_INFO("Analysis completed!")


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Analyze the distribution of Meeting Modules within a specified accessibility category",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example usages:
  # Analyze Keyboard Operation (default)
  python keyboard_module_analysis.py --input data_with_response.xlsx
  
  # Analyze Screen Reader category
  python keyboard_module_analysis.py --input data_with_response.xlsx --category "Screen Reader"
  
  # Analyze Color category
  python keyboard_module_analysis.py --input data_with_response.xlsx --category "Color"
  
  # List all available predefined categories
  python keyboard_module_analysis.py --list-categories
  
  # Specify output file
  python keyboard_module_analysis.py --input data.xlsx --category "Keyboard Operation" --output report.xlsx
  
  # Display only in console, do not save file
  python keyboard_module_analysis.py --input data.xlsx --category "Screen Reader" --no-save

Available predefined categories:
  • Keyboard Operation
  • Screen Reader
  • Color
  • Writing
  • Scaling
  • Visual & Acoustic
  • Language
  • User Guidance
  • Layout & Design
  • Usability
  • Braille
        """
    )
    
    parser.add_argument('--input', '-i', 
                       default='/Users/yanfzhen/workspace/WebexRegressSheild/data_with_response.xlsx',
                       help='Input Excel file path')
    parser.add_argument('--category', '-c',
                       default='Keyboard Operation',
                       help='Category name to analyze (default: Keyboard Operation)')
    parser.add_argument('--output', '-o',
                       help='Output report file path (optional)')
    parser.add_argument('--no-save',
                       action='store_true',
                       help='Do not save detailed report, display only in console')
    parser.add_argument('--list-categories',
                       action='store_true',
                       help='List all predefined categories')
    
    args = parser.parse_args()
    
    # If the user requests to list categories
    if args.list_categories:
        print("\nAvailable predefined categories:")
        print("="*80)
        for category, keywords in CategoryModuleAnalysis.CATEGORY_KEYWORDS.items():
            print(f"\n📂 {category}")
            print(f"   Matching keywords: {', '.join(keywords)}")
        print("\n" + "="*80)
        print("\nNote: You can also use any custom category name")
        sys.exit(0)
    
    try:
        analyzer = CategoryModuleAnalysis(args.input, args.category)
        analyzer.process(save_report=not args.no_save)
    except Exception as e:
        LOGGER_ERROR(f"Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
