"""
UI Response Time Report Handler

This module handles UI response time report generation and visualization.
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from pathlib import Path
from typing import Optional, List
from common.utils.logger import LOGGER_INFO, LOGGER_ERROR, LOGGER_DEBUG, LOGGER_WARNING
from test_space.management.handlers.test_case_db_handler import TestCaseDBHandler


class UIResponseReportHandler:
    """Handles UI response time report generation and data visualization"""
    
    def __init__(self, db_handler: TestCaseDBHandler):
        self.db_handler = db_handler
    
    def generate_ui_response_report(self, report_path: str, report_id: Optional[str] = None, 
                                  test_suite: Optional[str] = None) -> bool:
        """
        Generate UI response time report with charts and analysis
        
        Args:
            report_path: Path to save the report
            report_id: Specific report ID to analyze
            test_suite: Test suite to filter by
            
        Returns:
            bool: True if report generated successfully
        """
        try:
            # Get UI response data from database
            ui_response_df = self._get_ui_response_data(report_id, test_suite)
            
            if ui_response_df.empty:
                LOGGER_WARNING("No UI response data found for report generation")
                return False
                
            LOGGER_INFO(f"Generating UI response report with {len(ui_response_df)} measurements")
            
            # Create report directory
            report_dir = Path(report_path).parent
            img_dir = report_dir / 'img'
            img_dir.mkdir(exist_ok=True)
            
            # Generate charts
            chart_paths = []
            
            # Response time trend chart
            trend_chart = self._generate_response_time_trend_chart(ui_response_df, img_dir)
            if trend_chart:
                chart_paths.append(trend_chart)
            
            # Success rate chart
            success_chart = self._generate_success_rate_chart(ui_response_df, img_dir)
            if success_chart:
                chart_paths.append(success_chart)
                
            # Performance distribution chart
            distribution_chart = self._generate_response_distribution_chart(ui_response_df, img_dir)
            if distribution_chart:
                chart_paths.append(distribution_chart)
            
            # Generate markdown report
            self._generate_markdown_report(ui_response_df, report_path, chart_paths)
            
            LOGGER_INFO(f"UI response report generated successfully: {report_path}")
            return True
            
        except Exception as e:
            LOGGER_ERROR(f"Failed to generate UI response report: {e}")
            return False
    
    def _get_ui_response_data(self, report_id: Optional[str], test_suite: Optional[str]) -> pd.DataFrame:
        """Get UI response data from navigate report table"""
        try:
            connection = self.db_handler._get_db_connection()
            if not connection:
                return pd.DataFrame()
                
            with connection.cursor() as cursor:
                where_conditions = ["ui_response_enabled = TRUE"]  # Only get records with UI response enabled
                query_params = []
                
                if report_id:
                    where_conditions.append("report_id = %s")
                    query_params.append(report_id)
                    
                if test_suite:
                    where_conditions.append("test_suite = %s")
                    query_params.append(test_suite)
                
                base_query = """
                    SELECT 
                        report_id, test_case, test_suite, locate_control_name as control_name, 
                        ui_response_time_ms as response_time_ms,
                        ui_response_success as success, 
                        ui_response_expected_state as expected_state, 
                        ui_response_actual_state as actual_state, 
                        ui_response_polling_count as polling_count,
                        ui_response_timeout_occurred as timeout_occurred, 
                        ui_response_error_message as error_message, 
                        app_version, device_name, step_start_time as test_time, created_at
                    FROM TestCaseNavigateReport
                """
                
                if where_conditions:
                    sql_statement = base_query + " WHERE " + " AND ".join(where_conditions) + " ORDER BY created_at ASC"
                    cursor.execute(sql_statement, query_params)
                else:
                    # Get most recent report_id with UI response data
                    recent_query = """
                        SELECT report_id FROM TestCaseNavigateReport 
                        WHERE ui_response_enabled = TRUE 
                        ORDER BY created_at DESC LIMIT 1
                    """
                    cursor.execute(recent_query)
                    recent_result = cursor.fetchone()
                    
                    if not recent_result:
                        return pd.DataFrame()
                        
                    most_recent_report_id = recent_result[0]
                    sql_statement = base_query + " WHERE report_id = %s AND ui_response_enabled = TRUE ORDER BY created_at ASC"
                    cursor.execute(sql_statement, [most_recent_report_id])
                
                results = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]
                
                return pd.DataFrame(results, columns=columns)
                
        except Exception as e:
            LOGGER_ERROR(f"Failed to get UI response data: {e}")
            return pd.DataFrame()
        finally:
            if connection:
                connection.close()
    
    def _generate_response_time_trend_chart(self, df: pd.DataFrame, img_dir: Path) -> Optional[str]:
        """Generate response time trend chart"""
        try:
            plt.figure(figsize=(12, 6))
            
            # Prepare data
            control_names = [self._truncate_text(name, 25) for name in df['control_name'].tolist()]
            response_times = df['response_time_ms'].tolist()
            success_mask = df['success'].tolist()
            
            # Color code by success/failure
            colors = ['green' if success else 'red' for success in success_mask]
            
            # Create bar chart
            bars = plt.bar(range(len(control_names)), response_times, color=colors, alpha=0.7)
            
            # Add value labels on bars
            for i, (bar, time_val) in enumerate(zip(bars, response_times)):
                plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 50,
                        f'{time_val:.0f}ms', ha='center', va='bottom', fontsize=8)
            
            plt.title('UI Response Times by Control', fontsize=14, fontweight='bold')
            plt.xlabel('Control Names', fontsize=12)
            plt.ylabel('Response Time (ms)', fontsize=12)
            plt.xticks(range(len(control_names)), control_names, rotation=45, ha='right')
            
            # Add legend
            success_patch = patches.Rectangle((0, 0), 1, 1, facecolor='green', alpha=0.7, label='Success')
            failure_patch = patches.Rectangle((0, 0), 1, 1, facecolor='red', alpha=0.7, label='Timeout/Failure')
            plt.legend(handles=[success_patch, failure_patch])
            
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            
            chart_path = img_dir / 'ui_response_trend_chart.png'
            plt.savefig(chart_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            LOGGER_INFO(f"UI response trend chart saved: {chart_path}")
            return str(chart_path)
            
        except Exception as e:
            LOGGER_WARNING(f"Failed to generate response time trend chart: {e}")
            return None
    
    def _generate_success_rate_chart(self, df: pd.DataFrame, img_dir: Path) -> Optional[str]:
        """Generate success rate pie chart"""
        try:
            success_count = len(df[df['success'] == True])
            failure_count = len(df[df['success'] == False])
            
            if success_count + failure_count == 0:
                return None
                
            plt.figure(figsize=(8, 8))
            
            labels = ['Success', 'Timeout/Failure']
            sizes = [success_count, failure_count]
            colors = ['green', 'red']
            explode = (0.1, 0)  # explode success slice
            
            plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', 
                   explode=explode, shadow=True, startangle=90)
            
            plt.title(f'UI Response Success Rate\n(Total: {success_count + failure_count} measurements)', 
                     fontsize=14, fontweight='bold')
            
            chart_path = img_dir / 'ui_response_success_rate.png'
            plt.savefig(chart_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            LOGGER_INFO(f"UI response success rate chart saved: {chart_path}")
            return str(chart_path)
            
        except Exception as e:
            LOGGER_WARNING(f"Failed to generate success rate chart: {e}")
            return None
    
    def _generate_response_distribution_chart(self, df: pd.DataFrame, img_dir: Path) -> Optional[str]:
        """Generate response time distribution histogram"""
        try:
            successful_responses = df[df['success'] == True]['response_time_ms']
            
            if len(successful_responses) == 0:
                return None
                
            plt.figure(figsize=(10, 6))
            
            plt.hist(successful_responses, bins=20, alpha=0.7, color='skyblue', edgecolor='black')
            
            # Add statistics
            mean_time = successful_responses.mean()
            median_time = successful_responses.median()
            
            plt.axvline(mean_time, color='red', linestyle='--', label=f'Mean: {mean_time:.1f}ms')
            plt.axvline(median_time, color='orange', linestyle='--', label=f'Median: {median_time:.1f}ms')
            
            plt.title('UI Response Time Distribution (Successful Responses Only)', 
                     fontsize=14, fontweight='bold')
            plt.xlabel('Response Time (ms)', fontsize=12)
            plt.ylabel('Frequency', fontsize=12)
            plt.legend()
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            
            chart_path = img_dir / 'ui_response_distribution.png'
            plt.savefig(chart_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            LOGGER_INFO(f"UI response distribution chart saved: {chart_path}")
            return str(chart_path)
            
        except Exception as e:
            LOGGER_WARNING(f"Failed to generate response distribution chart: {e}")
            return None
    
    def _generate_markdown_report(self, df: pd.DataFrame, report_path: str, chart_paths: List[str]):
        """Generate markdown report with UI response analysis"""
        try:
            report_content = []
            
            # Header
            report_content.append("# UI Response Time Analysis Report\n")
            report_content.append(f"Generated on: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            
            # Summary statistics
            successful_df = df[df['success'] == True]
            total_measurements = len(df)
            successful_measurements = len(successful_df)
            success_rate = (successful_measurements / total_measurements * 100) if total_measurements > 0 else 0
            
            report_content.append("## Summary Statistics\n")
            report_content.append(f"- **Total Measurements**: {total_measurements}")
            report_content.append(f"- **Successful Responses**: {successful_measurements}")
            report_content.append(f"- **Success Rate**: {success_rate:.1f}%")
            
            if not successful_df.empty:
                mean_response = successful_df['response_time_ms'].mean()
                median_response = successful_df['response_time_ms'].median()
                min_response = successful_df['response_time_ms'].min()
                max_response = successful_df['response_time_ms'].max()
                
                report_content.append(f"- **Average Response Time**: {mean_response:.1f}ms")
                report_content.append(f"- **Median Response Time**: {median_response:.1f}ms")
                report_content.append(f"- **Fastest Response**: {min_response:.1f}ms")
                report_content.append(f"- **Slowest Response**: {max_response:.1f}ms\n")
            
            # Charts
            for chart_path in chart_paths:
                chart_name = Path(chart_path).stem
                relative_path = f"img/{Path(chart_path).name}"
                report_content.append(f"## {chart_name.replace('_', ' ').title()}\n")
                report_content.append(f"![{chart_name}]({relative_path})\n")
            
            # Detailed results table
            report_content.append("## Detailed Results\n")
            report_content.append("| Control Name | Response Time (ms) | Success | Expected State | Polling Count |")
            report_content.append("|--------------|-------------------|---------|----------------|---------------|")
            
            for _, row in df.iterrows():
                status = "✅" if row['success'] else "❌"
                control_name = self._truncate_text(row['control_name'], 30)
                expected_state = self._truncate_text(row['expected_state'], 40)
                
                report_content.append(
                    f"| {control_name} | {row['response_time_ms']:.1f} | {status} | {expected_state} | {row['polling_count']} |"
                )
            
            # Write report
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(report_content))
                
            LOGGER_INFO(f"UI response markdown report generated: {report_path}")
            
        except Exception as e:
            LOGGER_WARNING(f"Failed to generate markdown report: {e}")
    
    def _truncate_text(self, text: str, max_length: int) -> str:
        """Truncate text to specified length"""
        if not text:
            return ""
        return text[:max_length] + "..." if len(text) > max_length else text
