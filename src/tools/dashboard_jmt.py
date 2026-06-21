import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import json
import pymysql
from pathlib import Path
from typing import Optional


class MysqlConnection(object):
    def __init__(self, host, port, user, password, dbName, charset='utf8mb4'):
        self.db = pymysql.connect(host=host, port=port, user=user, password=password, db=dbName, charset=charset)

    def __del__(self):
        if self.db:
            self.db.close()

    def Query(self, sql_statement, params=None):
        if self.db is None:
            return ((), ())

        cursor = self.db.cursor()
        try:
            cursor.execute(sql_statement, params)
            results = cursor.fetchall()
            columns = [item[0] for item in cursor.description]
            return (results, columns)
        except:
            print("Error: unable to fecth data", "RED")
        
        return ((), ())
        
    def Execute(self, sql_statement):
        if self.db is None:
            print('Execute failed, db is None', "RED")
            return False

        cursor = self.db.cursor()
        try:
            cursor.execute(sql_statement)
            self.db.commit()
            return True
        except Exception as e:
            msg = f'''Execute failed!,sql[{sql_statement}], error{e}'''
            print(msg, "RED")
            self.db.rollback()
            return False
        
    def ExecuteWithData(self, sql_statement, data):
        if self.db is None:
            print('Execute failed, db is None', "RED")
            return False

        cursor = self.db.cursor()
        try:
            cursor.execute(sql_statement, data)
            self.db.commit()
            return True
        except Exception as e:
            msg = f'''Execute failed!,sql[{sql_statement}], error{e}'''
            print(msg, "RED")
            self.db.rollback()
            return False
            
    def TableInfo(self):
        if self.db is None:
            return None
        cursor = self.db.cursor()
        columns = [item[0] for item in cursor.description]
        return columns


class JMTDashboard:
    def __init__(self, job_info_path: Path):
        self.job_info_path = job_info_path
        self.report_id = None
        self.job_info = {}
        self.load_job_info()
        
        host = 'gc-hgh05-level2-lab-irc-5.cisco.com'
        port = 3306
        user = 'test'
        password = 'pass'
        dbName = 'testcase_db'
        self.mysql_conn = MysqlConnection(host, port, user, password, dbName)
    
    def load_job_info(self):
        if self.job_info_path and self.job_info_path.exists():
            try:
                with open(self.job_info_path, "r", encoding="utf-8") as f:
                    self.job_info = json.load(f)
                # Extract report_id from job_info
                self.report_id = self.job_info.get('reportId') or self.job_info.get('report_id')
                if not self.report_id:
                    st.error("No reportId found in job info file")
            except Exception as e:
                st.error(f"Could not load job info from file: {e}")
                self.job_info = {}
        else:
            st.error(f"Job info file not found: {self.job_info_path}")
    
    def fetch_jmt_data(self, report_id=None, control_name=None, test_case=None):
        if report_id is None:
            report_id = self.report_id
        
        if not report_id:
            st.error("No report_id provided")
            return pd.DataFrame()
            
        try:
            # Build WHERE clause (parameterized)
            where_conditions = [
                "report_id = %s",
                "ui_response_enabled = TRUE",
                "ui_response_time_ms IS NOT NULL",
            ]
            params = [report_id]

            if control_name:
                where_conditions.append("locate_control_name = %s")
                params.append(control_name)
            if test_case:
                where_conditions.append("test_case LIKE %s")
                params.append(f"%{test_case}%")

            where_clause = " AND ".join(where_conditions)

            query = f"""
            WITH ranked AS (
                SELECT
                    *,
                    ROW_NUMBER() OVER (PARTITION BY app_version ORDER BY step_start_time DESC) AS rn
                FROM TestCaseNavigateReport
                WHERE {where_clause}
            )
            SELECT
                rn AS x,
                ROUND(ui_response_time_ms / 1000.0, 3) AS y, 
                app_version AS metric,
                step_start_time,
                rn AS `No.`,
                ROUND(ui_response_time_ms / 1000.0, 3) AS Response,
                app_version as appVersion,
                step_start_time as Time
            FROM ranked
            WHERE rn <= 60
            ORDER BY app_version ASC, rn ASC
            """
            
            results, columns = self.mysql_conn.Query(query, params=params)
            df = pd.DataFrame(results, columns=columns)
            
            return df
        except Exception as e:
            st.error(f"Error fetching JMT data: {e}")
            return pd.DataFrame()
    
    def render_trend_chart(self, df, title='JMT trend'):
        if df.empty:
            st.warning("No data available for trend chart.")
            return None
        
        fig = go.Figure()
        
        for version in df['metric'].unique():
            version_data = df[df['metric'] == version]
            fig.add_trace(go.Scatter(
                x=version_data['x'],
                y=version_data['y'],
                mode='lines+markers',
                name=version,
                line=dict(color='#00FF00', width=2),
                marker=dict(size=4)
            ))
        
        fig.update_layout(
            title=title,
            xaxis_title='x|metric',
            yaxis_title='',
            plot_bgcolor='#1e1e1e',
            paper_bgcolor='#1e1e1e',
            font=dict(color='white'),
            xaxis=dict(
                showgrid=True,
                gridcolor='#333',
                zeroline=False
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor='#333',
                zeroline=False
            ),
            height=300,
            margin=dict(l=50, r=20, t=50, b=50),
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.3,
                xanchor="left",
                x=0
            )
        )
        
        return fig
    
    def render_gauge(self, df, title='Avg. JMT (s)'):
        if df.empty:
            st.warning("No data available for gauge.")
            return None
        
        avg_value = df['y'].mean()
        
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=avg_value,
            number={'suffix': "", 'font': {'size': 60, 'color': '#00FF00'}},
            title={'text': title, 'font': {'size': 20, 'color': 'white'}},
            gauge={
                'axis': {'range': [None, avg_value * 2], 'tickcolor': 'white'},
                'bar': {'color': "rgba(0,0,0,0)"},
                'bgcolor': "rgba(0,0,0,0)",
                'borderwidth': 0,
                'steps': [
                    {'range': [0, avg_value * 0.7], 'color': '#00FF00'},
                    {'range': [avg_value * 0.7, avg_value * 1.3], 'color': '#FFA500'},
                    {'range': [avg_value * 1.3, avg_value * 2], 'color': '#FF0000'}
                ],
                'threshold': {
                    'line': {'color': "white", 'width': 4},
                    'thickness': 0.75,
                    'value': avg_value
                }
            }
        ))
        
        fig.update_layout(
            plot_bgcolor='#1e1e1e',
            paper_bgcolor='#1e1e1e',
            font=dict(color='white'),
            height=300,
            margin=dict(l=20, r=20, t=80, b=20)
        )
        
        return fig
    
    def render_details_table(self, df):
        if df.empty:
            st.warning("No data available for details table.")
            return
        
        display_df = df[['No.', 'Response', 'appVersion', 'Time']].copy()
        display_df['Time'] = pd.to_datetime(display_df['Time']).dt.strftime('%Y-%m-%d %H:%M:%S')
        
        st.markdown("### JMT Details")
        st.dataframe(display_df, use_container_width=True, height=400, hide_index=True)
    
    def render_section(self, title, control_name=None, test_case=None):
        """Render a section with trend, gauge, and details for specific criteria"""
        st.markdown(f"<h3 style='text-align: center; margin: 40px 0 20px 0;'>{title}</h3>", unsafe_allow_html=True)
        
        df = self.fetch_jmt_data(control_name=control_name, test_case=test_case)
        
        if df.empty:
            st.warning(f"No data available for {title}.")
            return
        
        # Create layout: trend and gauge on top, table below
        col1, col2 = st.columns([2, 1])
        
        with col1:
            trend_fig = self.render_trend_chart(df, title=f'{title} - Trend')
            if trend_fig:
                st.plotly_chart(trend_fig, use_container_width=True, key=f"{title}_trend_chart")
        
        with col2:
            gauge_fig = self.render_gauge(df, title=f'Avg. {title} (s)')
            if gauge_fig:
                st.plotly_chart(gauge_fig, use_container_width=True, key=f"{title}_gauge_chart")
        
        st.markdown("<hr style='margin: 20px 0;'>", unsafe_allow_html=True)
        self.render_details_table(df)
        st.markdown("<hr style='margin: 50px 0; border-top: 3px solid #444;'>", unsafe_allow_html=True)
    
    def render(self):
        st.markdown("<h2 style='text-align: center; margin: 30px 0;'>JMT Dashboard</h2>", unsafe_allow_html=True)
        
        if self.job_info:
            st.markdown(
                f"""
                <div style="text-align:center; font-size:16px; margin-top:-10px; margin-bottom:20px; color: #666;">
                    <b>App Version:</b> {self.job_info.get('appVersion', 'N/A')} &nbsp;|&nbsp;
                    <b>Device OS:</b> {self.job_info.get('deviceOS', 'N/A')} &nbsp;|&nbsp;
                    <b>Device Model:</b> {self.job_info.get('workflow', 'N/A')} &nbsp;|&nbsp;
                    <b>Report ID:</b> {self.job_info.get('reportId', 'N/A')} &nbsp;|&nbsp;
                    <b>Run Date:</b> {self.job_info.get('runDate', 'N/A')}
                </div>
                """,
                unsafe_allow_html=True
            )
        
        # Render three sections
        self.render_section("Start Meeting", control_name="Start meeting")
        self.render_section("Guest Join PMR", control_name="Join meeting", test_case="guest")
        self.render_section("Join PMR from Meetings Search", control_name="Join meeting", test_case="meetings_search")


def main():
    st.set_page_config(layout="wide", page_title="JMT Dashboard")
    job_info_path = Path("/Users/weiqli/Downloads/20250729-094151/wrs-job-info.json")
    
    dashboard = JMTDashboard(job_info_path)
    dashboard.render()


if __name__ == "__main__":
    main()
