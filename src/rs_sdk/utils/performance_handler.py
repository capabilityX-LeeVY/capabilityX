"""
Performance Handler Module

This module handles performance-related operations including:
- Performance trend chart generation from database data
- Chart insertion into markdown files
- Performance data visualization
"""

import os
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib
from common.utils.logger import LOGGER_INFO, LOGGER_ERROR, LOGGER_WARNING, LOGGER_DEBUG
from test_space.management.handlers.test_case_db_handler import TestCaseDBHandler

# Use a non-interactive backend for matplotlib
matplotlib.use('Agg')


class PerformanceHandler:
    """
    Handles performance-related operations including chart generation and markdown insertion
    """
    
    def __init__(self):
        """Initialize the PerformanceHandler"""
        pass
    
    def generate_performance_charts(self, performance_report_path, report_id=None, test_suite=None, app_version=None):
        """
        Generate performance trend charts from database data
        
        Args:
            performance_report_path (str): Path to the performance report markdown file
            report_id (str, optional): Report ID to filter by
            test_suite (str, optional): Test suite to filter by  
            app_version (str, optional): App version to filter by
            
        Returns:
            list: List of generated chart file paths
        """
        try:
            LOGGER_INFO(f"Generating performance charts for: {performance_report_path}", "CYAN")
            
            # Get performance data from database
            db_handler = TestCaseDBHandler()
            performance_df = db_handler.get_performance_data(
                report_id=report_id, 
                test_suite=test_suite, 
                app_version=app_version
            )

            if performance_df.empty:
                LOGGER_WARNING("No performance data found in database", "YELLOW")
                return []

            LOGGER_INFO(f"Retrieved {len(performance_df)} performance records from database", "GREEN")

            report_dir = Path(performance_report_path).parent
            
            # Create img directory if it doesn't exist
            img_dir = report_dir / 'img'
            img_dir.mkdir(exist_ok=True)
            LOGGER_INFO(f"Created/verified img directory: {img_dir}", "CYAN")
            
            generated_charts = []

            # Generate CPU performance chart
            cpu_chart_path = self._generate_cpu_chart_from_db(performance_df, img_dir, performance_report_path)
            if cpu_chart_path:
                generated_charts.append(str(cpu_chart_path))

            # Generate Memory performance chart
            memory_chart_path = self._generate_memory_chart_from_db(performance_df, img_dir, performance_report_path)
            if memory_chart_path:
                generated_charts.append(str(memory_chart_path))

            LOGGER_INFO(f"Performance charts generated successfully: {generated_charts}", "GREEN")
            return generated_charts

        except Exception as e:
            LOGGER_ERROR(f"Failed to generate performance charts: {str(e)}", "RED")
            return []
    
    def _generate_cpu_chart_from_db(self, performance_df, img_dir, performance_report_path):
        """
        Generate CPU performance trend chart from database data
        
        Args:
            performance_df (DataFrame): Performance data from database
            img_dir (Path): Directory to save the chart images
            performance_report_path (str): Path to the performance report markdown file
            
        Returns:
            str: Path to generated chart file, or None if failed
        """
        try:
            LOGGER_INFO("Generating CPU performance chart from database data...", "CYAN")
            
            if performance_df.empty:
                LOGGER_WARNING("No performance data available for CPU chart", "YELLOW")
                return None
            
            # Check if we have CPU data columns
            if 'main_cpu' not in performance_df.columns and 'media_cpu' not in performance_df.columns:
                LOGGER_WARNING("No CPU columns found in performance data", "YELLOW")
                return None
            
            # Generate CPU chart
            plt.figure(figsize=(14, 8))
            
            # Prepare data
            control_names = performance_df['control_name'].tolist()
            
            # Truncate control names for better display
            truncated_controls = [self._truncate_text(name, 20) for name in control_names]
            x_positions = range(len(truncated_controls))
            
            # Plot main CPU data if available
            if 'main_cpu' in performance_df.columns:
                main_cpu_values = performance_df['main_cpu'].fillna(0).tolist()
                plt.plot(x_positions, main_cpu_values, marker='o', linewidth=2, markersize=6, 
                        label='Main CPU', color='#1f77b4')
                LOGGER_DEBUG(f"Main CPU data points: {len(main_cpu_values)}")
            
            # Plot media CPU data if available
            if 'media_cpu' in performance_df.columns:
                media_cpu_values = performance_df['media_cpu'].fillna(0).tolist()
                plt.plot(x_positions, media_cpu_values, marker='s', linewidth=2, markersize=6, 
                        label='Media CPU', color='#ff7f0e')
                LOGGER_DEBUG(f"Media CPU data points: {len(media_cpu_values)}")
            
            # Build dynamic title with app_version and test_suite info
            title_parts = ['CPU Usage Trend (Main + Media)']
            
            # Add app_version if available
            if 'app_version' in performance_df.columns:
                app_versions = performance_df['app_version'].dropna().unique()
                if len(app_versions) > 0:
                    title_parts.append(f"App: {app_versions[0]}")
            
            # Add test_suite if available
            if 'test_suite' in performance_df.columns:
                test_suites = performance_df['test_suite'].dropna().unique()
                if len(test_suites) > 0:
                    title_parts.append(f"Suite: {test_suites[0]}")
            
            dynamic_title = ' | '.join(title_parts)
            plt.title(dynamic_title, fontsize=16, fontweight='bold', pad=20)
            plt.xlabel('Control Actions', fontsize=12)
            plt.ylabel('CPU Usage (%)', fontsize=12)
            plt.xticks(x_positions, truncated_controls, rotation=45, ha='right')
            plt.legend(fontsize=10)
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            
            cpu_chart_path = img_dir / 'cpu_trend_chart.png'
            LOGGER_INFO(f"Saving CPU chart to: {cpu_chart_path}", "CYAN")
            
            plt.savefig(cpu_chart_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            # Verify file was created
            if cpu_chart_path.exists():
                LOGGER_INFO(f"CPU trend chart successfully saved to: {cpu_chart_path}", "GREEN")
                LOGGER_INFO(f"Chart file size: {cpu_chart_path.stat().st_size} bytes", "GREEN")
                
                # Insert chart into markdown
                self.insert_chart_into_markdown(performance_report_path, cpu_chart_path, "CPU Usage Trend")
                return str(cpu_chart_path)
            else:
                LOGGER_ERROR(f"Failed to save CPU chart - file not found: {cpu_chart_path}", "RED")
                return None
                
        except Exception as e:
            LOGGER_WARNING(f"Failed to generate CPU chart: {str(e)}", "YELLOW")
            return None
    
    def _generate_memory_chart_from_db(self, performance_df, img_dir, performance_report_path):
        """
        Generate Memory performance trend chart from database data
        
        Args:
            performance_df (DataFrame): Performance data from database
            img_dir (Path): Directory to save the chart images
            performance_report_path (str): Path to the performance report markdown file
            
        Returns:
            str: Path to generated chart file, or None if failed
        """
        try:
            LOGGER_INFO("Generating Memory performance chart from database data...", "CYAN")
            
            if performance_df.empty:
                LOGGER_WARNING("No performance data available for Memory chart", "YELLOW")
                return None
            
            # Check if we have Memory data columns
            if 'main_mem' not in performance_df.columns and 'media_mem' not in performance_df.columns:
                LOGGER_WARNING("No Memory columns found in performance data", "YELLOW")
                return None
            
            # Generate Memory chart
            plt.figure(figsize=(14, 8))
            
            # Prepare data
            control_names = performance_df['control_name'].tolist()
            
            # Truncate control names for better display
            truncated_controls = [self._truncate_text(name, 20) for name in control_names]
            x_positions = range(len(truncated_controls))
            
            # Plot main memory data if available
            if 'main_mem' in performance_df.columns:
                main_mem_values = performance_df['main_mem'].fillna(0).tolist()
                plt.plot(x_positions, main_mem_values, marker='o', linewidth=2, markersize=6, 
                        label='Main Memory', color='#2ca02c')
                LOGGER_DEBUG(f"Main Memory data points: {len(main_mem_values)}")
            
            # Plot media memory data if available  
            if 'media_mem' in performance_df.columns:
                media_mem_values = performance_df['media_mem'].fillna(0).tolist()
                plt.plot(x_positions, media_mem_values, marker='s', linewidth=2, markersize=6, 
                        label='Media Memory', color='#d62728')
                LOGGER_DEBUG(f"Media Memory data points: {len(media_mem_values)}")
            
            # Build dynamic title with app_version and test_suite info
            title_parts = ['Memory Usage Trend (Main + Media)']
            
            # Add app_version if available
            if 'app_version' in performance_df.columns:
                app_versions = performance_df['app_version'].dropna().unique()
                if len(app_versions) > 0:
                    title_parts.append(f"App: {app_versions[0]}")
            
            # Add test_suite if available
            if 'test_suite' in performance_df.columns:
                test_suites = performance_df['test_suite'].dropna().unique()
                if len(test_suites) > 0:
                    title_parts.append(f"Suite: {test_suites[0]}")
            
            dynamic_title = ' | '.join(title_parts)
            plt.title(dynamic_title, fontsize=16, fontweight='bold', pad=20)
            plt.xlabel('Control Actions', fontsize=12)
            plt.ylabel('Memory Usage (MB)', fontsize=12)
            plt.xticks(x_positions, truncated_controls, rotation=45, ha='right')
            plt.legend(fontsize=10)
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            
            mem_chart_path = img_dir / 'memory_trend_chart.png'
            LOGGER_INFO(f"Saving Memory chart to: {mem_chart_path}", "CYAN")
            
            plt.savefig(mem_chart_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            # Verify file was created
            if mem_chart_path.exists():
                LOGGER_INFO(f"Memory trend chart successfully saved to: {mem_chart_path}", "GREEN")
                LOGGER_INFO(f"Chart file size: {mem_chart_path.stat().st_size} bytes", "GREEN")
                
                # Insert chart into markdown
                self.insert_chart_into_markdown(performance_report_path, mem_chart_path, "Memory Usage Trend")
                return str(mem_chart_path)
            else:
                LOGGER_ERROR(f"Failed to save Memory chart - file not found: {mem_chart_path}", "RED")
                return None
                
        except Exception as e:
            LOGGER_WARNING(f"Failed to generate Memory chart: {str(e)}", "YELLOW")
            return None
    
    def _truncate_text(self, text, max_length=20):
        """
        Truncate text to specified max length with ellipsis
        
        Args:
            text (str): Text to truncate
            max_length (int): Maximum allowed length
        
        Returns:
            str: Truncated text
        """
        if len(str(text)) <= max_length:
            return str(text)
        return str(text)[:max_length-3] + "..."
    
    def insert_chart_into_markdown(self, markdown_path, chart_path, chart_title):
        """
        Insert chart image into the markdown file
        
        Args:
            markdown_path (str): Path to the markdown file
            chart_path (Path): Path to the chart image
            chart_title (str): Title for the chart
        """
        try:
            LOGGER_INFO(f"Inserting chart '{chart_title}' into markdown file: {markdown_path}", "CYAN")
            
            # Read current content
            with open(markdown_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Create chart section with HTML img tag for better web display
            chart_filename = chart_path.name
            chart_section = f'\n\n## {chart_title}\n\n<img src="./img/{chart_filename}" alt="{chart_title}" style="max-width: 1000px; height: auto;">\n\n'
            
            LOGGER_DEBUG(f"Chart section to insert: {repr(chart_section)}", "BLUE")
            
            # Find a good place to insert the chart
            original_content = content
            
            # Strategy: Always append to the end of the file for consistency
            if "# AI Performance Analysis" in content:
                # Insert before AI analysis section
                content = content.replace("# AI Performance Analysis", chart_section + "# AI Performance Analysis")
                LOGGER_INFO(f"Chart inserted before AI Performance Analysis section", "GREEN")
            else:
                # Simply append to the end of the file
                content = content.rstrip() + chart_section
                LOGGER_INFO(f"Chart appended to end of file", "GREEN")
            
            # Verify that content actually changed
            if content == original_content:
                LOGGER_WARNING(f"Content was not modified - chart may not have been inserted", "YELLOW")
            else:
                LOGGER_INFO(f"Content successfully modified, chart section added", "GREEN")
            
            # Write back to file
            with open(markdown_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            LOGGER_INFO(f"Chart '{chart_title}' successfully inserted into {markdown_path}", "GREEN")
            LOGGER_INFO(f"Chart image path: {chart_path}", "GREEN")
                
        except Exception as e:
            LOGGER_ERROR(f"Failed to insert chart into markdown: {str(e)}", "RED")
            raise
