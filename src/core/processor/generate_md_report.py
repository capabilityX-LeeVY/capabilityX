#!/usr/bin/env python3
"""
Generate Markdown report from bug statistics
"""

import pandas as pd
import sys


def generate_markdown_report(excel_file: str, output_md: str = None):
    """
    Excel generate Markdown report
    
    Args:
        excel_file: Path to the statistics Excel file
        output_md: Path to the output Markdown file
    """
    try:
        # Read statistics data
        df = pd.read_excel(excel_file, sheet_name='Statistics')
        
        if output_md is None:
            output_md = excel_file.replace('.xlsx', '.md')
        
        # Generate Markdown content
        md_content = []
        md_content.append("# Accessibility Bug Statistics Report\n")
        
        # Get total information
        total_row = df[df['Module'] == 'TOTAL'].iloc[0]
        total_bugs = total_row['Count']
        
        md_content.append(f"**Total Bugs**: {total_bugs}\n")
        md_content.append(f"**Report Time**: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        md_content.append("\n---\n")
        
        # Generate table
        md_content.append("\n## Detailed Statistics\n")
        md_content.append("| Module | Sub-item | Count | Percentage | Status |\n")
        md_content.append("| :--- | :--- | ---: | ---: | :---: |\n")
        
        # Exclude TOTAL row
        data_rows = df[df['Module'] != 'TOTAL']
        
        for _, row in data_rows.iterrows():
            module = row['Module'] if row['Module'] else ''
            sub_item = row['Sub-item']
            count = row['Count']
            percentage = row['Percentage']
            status = row['Status']
            
            md_content.append(f"| {module} | {sub_item} | {count} | {percentage} | {status} |\n")
        
        # Add total row
        md_content.append("| **TOTAL** | **All Categories** | **" + str(total_bugs) + "** | **100.0%** | 📊 |\n")
        
        # Generate summary by category
        md_content.append("\n---\n")
        md_content.append("\n## Summary by Module\n")
        
        # Group statistics by module
        module_stats = {}
        for _, row in data_rows.iterrows():
            if row['Module']:
                module = row['Module']
                if module not in module_stats:
                    module_stats[module] = {'count': 0, 'items': 0}
                module_stats[module]['count'] += row['Count']
                module_stats[module]['items'] += 1
        
        # Sort and display
        sorted_modules = sorted(module_stats.items(), key=lambda x: x[1]['count'], reverse=True)
        
        md_content.append("\n| Module | Bug Count | Sub-items | Percentage |\n")
        md_content.append("| :--- | ---: | ---: | ---: |\n")
        
        for module, stats in sorted_modules:
            count = stats['count']
            items = stats['items']
            percentage = f"{(count/total_bugs*100):.1f}%"
            md_content.append(f"| {module} | {count} | {items} | {percentage} |\n")
        
        # Write to file
        with open(output_md, 'w', encoding='utf-8') as f:
            f.writelines(md_content)
        
        print(f"✅ Markdown report generated: {output_md}")
        
        # Also output to console
        print("\n" + "".join(md_content))
        
    except Exception as e:
        print(f"❌ Failed to generate Markdown report: {e}")
        sys.exit(1)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate Markdown report from Excel statistics file")
    parser.add_argument('--input', '-i',
                       default='data_statistics_report.xlsx',
                       help='Input Excel statistics file path')
    parser.add_argument('--output', '-o',
                       help='Output Markdown file path (optional)')
    
    args = parser.parse_args()
    generate_markdown_report(args.input, args.output)
