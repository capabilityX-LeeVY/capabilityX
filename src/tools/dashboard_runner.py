import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import json
import subprocess
import sys

from playwright.sync_api import sync_playwright
from pathlib import Path


st.set_page_config(layout="wide", page_title="WRS Dashboard")

class ComplianceDashboard:
    STATUS_MAP = {
        1: "Validated Pass",
        0: "Not validated",
        2: "In validated",
        3: "Skip",
        4: "Same Control",
        5: "No Traverse",
        6: "Workflow Skip",
        -1: "Loss Focus",
        -2: "Not Found",
        -3: "Invalid Type",
        -4: "Timeout",
        -5: "Loop",
        -6: "Unknown Error",
        -8: "No Control Name",
        "validated": "Validated Pass",
        "validate failed": "Validate Failed",
        "validated skiped": "Skip",
        "": "Unknown Status"
    }

    def __init__(self):
        self.output_path = Path("/Users/weiqli/Downloads/20250729-094151")
        self.report_root = self.output_path / "report"
        self.sqlite_path = self.output_path / "db" / "ControlINFO.db"
        self.job_info = self.output_path / "wrs-job-info.json"
        self.md_files_map = self.scan_md_files()
        self.db_df = self.fetch_control_history()
        # self.query_params = st.query_params
        self.query_params = st.experimental_get_query_params()


    def scan_md_files(self):
        md_files = {}
        for md_file in self.report_root.rglob("public_*.md"):
            with open(md_file, "r", encoding="utf-8") as f:
                content = f.read()
                compliant_count = content.lower().count("✅ compliant")
                non_compliant_count = content.lower().count("❌ non-compliant")
                md_files[md_file.name] = {
                    "path": md_file,
                    "compliant_count": compliant_count,
                    "non_compliant_count": non_compliant_count,
                    "compliant_rate": compliant_count / (compliant_count + non_compliant_count) * 100,
                    "non_compliant_rate": non_compliant_count / (compliant_count + non_compliant_count) * 100
                    if (compliant_count + non_compliant_count) > 0 else 0,
                }
        return md_files

    def fetch_control_history(self):
        try:
            conn = sqlite3.connect(self.sqlite_path)
            df = pd.read_sql_query("SELECT * FROM ControlINFO", conn)
            conn.close()
            return df
        except sqlite3.Error as e:
            st.error(f"Error connecting to database: {e}")
            return pd.DataFrame()

    def render_md_summary(self):
        # st.title("SR, FR and i18n Compliance Result")
        st.markdown("<h2 style='text-align: center; margin-bottom: 50px;'>SR, FR and i18n Compliance Result</h2>", unsafe_allow_html=True)

        st.markdown("""
            <style>
                .md-title {
                    display: flex;
                    justify-content: space-between;
                    align-items: baseline;
                    margin-bottom: 0.5rem;
                }
                .md-title h3 {
                    color: #2E86C1;
                    margin: 0;
                }
                .md-link {
                    color: #007bff;
                    font-size: 14px;
                    font-weight: 600;
                    text-decoration: underline;
                    transition: color 0.3s ease;
                }
                .md-link:hover {
                    color: #9dcfff;
                }
                .md-bar-container {
                    background-color: #e0e0e0;
                    border-radius: 6px;
                    height: 36px;
                    width: 100%;
                    margin: 8px 0;
                    overflow: hidden;
                }
                .md-bar-fill {
                    height: 100%;
                    background-color: #28a745;
                    text-align: right;
                    padding-right: 10px;
                    color: white;
                    line-height: 36px;
                    font-weight: bold;
                }
            </style>
        """, unsafe_allow_html=True)

        def get_header_title(md_name: str) -> str:
            if "_sr-" in md_name.lower():
                return "Screen Reader Analysis Results"
            elif "_fr-report-onfocus" in md_name.lower():
                return "On-Focus Analysis Results"
            elif "_fr-report-lostfocus" in md_name.lower():
                return "Lost-Focus Analysis Results"
            elif "_i18n-" in md_name.lower():
                return "Internationalization Analysis Results"
            else:
                return "General Markdown Analysis Results"

        def render_header(md_name: str):
            title = get_header_title(md_name)
            st.markdown(f"""
                <div class="md-title">
                    <h3>{title}</h3>
                    <a class="md-link" href="/?page=md_detail&file={md_name}">View Details</a>
                </div>
            """, unsafe_allow_html=True)
            return title

        focus_sections = {"lost": "", "on": ""}
        for md_name, stats in self.md_files_map.items():
            is_sr = "_sr-" in md_name.lower()
            is_on_fr = "_fr-report-onfocus" in md_name.lower()
            is_lost_fr = "_fr-report-lostfocus" in md_name.lower()
            is_i18n = "_i18n-" in md_name.lower()
            compliant = stats["compliant_count"]
            non_compliant = stats["non_compliant_count"]
            total = compliant + non_compliant
            percent = (compliant / total) * 100 if total > 0 else 0

            if is_sr:
                render_header(md_name)
                st.markdown(f"""
                    <div class="md-bar-container">
                        <div class="md-bar-fill" style="width: {percent:.2f}%;">
                            {percent:.2f}%
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                st.markdown(f"""
                    <div style="display: flex; gap: 40px; font-size:16px; align-items: center;">
                    <div>Total Items: <b>{total}</b></div>
                    <div>✅ Compliant: <b>{compliant}</b></div>
                    <div>
                        ❌ Pending Review: 
                        <a class="md-link" href="/?page=md_detail&file={md_name}&filter=non_compliant">
                            <b>{non_compliant}</b>
                        </a>
                    </div>
                    </div>
                    """, unsafe_allow_html=True)
                st.markdown("<hr style='margin: 70px 0;'>", unsafe_allow_html=True)
            elif is_on_fr or is_lost_fr:
                title = get_header_title(md_name)
                rate = stats["compliant_rate"]
                block_html = f"""
                <div style="background-color: #2a2a2a; padding: 1rem; border-radius: 0.5rem; margin-bottom: 1rem;">
                    <h4 style="margin-top: 0;">{title}</h4>
                    <div style="font-size: 32px; font-weight: bold; color: white;">{rate:.2f}%</div>
                    <div style="margin-top: 0.5rem; font-size: 16px;">
                        <span style="margin-right: 32px;">✅ Compliant: <strong>{compliant}</strong></span>
                        <span>
                            ❌ Non-Compliant: 
                            <a class="md-link" href="/?page=md_detail&file={md_name}&filter=non_compliant">
                                <strong>{non_compliant}</strong>
                            </a>
                        </span>
                    </div>
                    <div style="margin-top: 0.5rem; text-align: right;">
                        <a class="md-link" href="/?page=md_detail&file={md_name}">View Details</a>
                    </div>
                </div>
                """
                if is_lost_fr:
                    focus_sections["lost"] = block_html
                elif is_on_fr:
                    focus_sections["on"] = block_html

            elif is_i18n or True:
                render_header(md_name)
                cols = st.columns(1)
                html_for_others = f"""
                    <div style="
                        background-color: #2a2a2a;
                        color: white;
                        padding: 1rem;
                        border-radius: 0.5rem;
                        margin-bottom: 1rem;
                    ">
                        <div style="margin-bottom: 0.5rem; font-size: 16px;">
                            <span style="margin-right: 32px;">✅ Compliant: <strong>{compliant}</strong></span>
                            <span>
                                ❌ Non-Compliant: 
                                <a class="md-link" href="/?page=md_detail&file={md_name}&filter=non_compliant">
                                    <strong>{non_compliant}</strong>
                                </a>
                            </span>
                        </div>
                        <div style="display: flex; justify-content: center; gap: 48px; font-size: 32px;">
                            <div>Total Items: {total}</div>
                            <div>
                                Non-Compliant Rate: 
                                <span style="color: #E74C3C;">{stats['non_compliant_rate']:.2f}%</span>
                            </div>
                        </div>
                    </div>
                """

                cols[0].markdown(html_for_others, unsafe_allow_html=True)
                st.markdown("<hr style='margin: 70px 0;'>", unsafe_allow_html=True)

        if focus_sections["lost"] or focus_sections["on"]:
            col_lost, col_on = st.columns(2)
            if focus_sections["lost"]:
                with col_lost:
                    st.markdown(focus_sections["lost"], unsafe_allow_html=True)
            if focus_sections["on"]:
                with col_on:
                    st.markdown(focus_sections["on"], unsafe_allow_html=True)

            st.markdown("<hr style='margin: 70px 0;'>", unsafe_allow_html=True)

        st.markdown('<h3 style="font-weight: 600; text-align: center;">non-Compliant Rate</h3>', unsafe_allow_html=True)
        if not self.md_files_map:
            st.warning("No markdown data to display.")
        else:
            chart_data = pd.DataFrame([
                {"File": name, "Non-Compliant Rate": stats["non_compliant_rate"]}
                for name, stats in self.md_files_map.items()
            ])
            fig = px.bar(
                chart_data,
                x="File",
                y="Non-Compliant Rate",
                color="Non-Compliant Rate",
                color_continuous_scale="reds"
            )
            fig.update_layout(
                yaxis=dict(range=[0, 100]),
                yaxis_title="Non-Compliant Rate"
            )
            st.plotly_chart(fig, use_container_width=True, key="md_rate_bar_chart")


    def render_db_summary(self):
        # st.title("Navigation Result")
        st.markdown("<h2 style='text-align: center; margin-bottom: 85px;'>Navigation Result</h2>", unsafe_allow_html=True)
        if self.db_df.empty:
            st.error("No data available.")
        else:
            # valid_df = self.db_df[self.db_df["is_validated"].isin([0, 1])]
            valid_df = self.db_df
            status_counts = valid_df["is_validated"].value_counts()
            control_type_counts = valid_df["ControlLocalizedType"].value_counts()

            if self.db_df.empty:
                st.warning("No control status data to display.")
            else:
                st.markdown("""
                    <div>
                        <h6 style="font-weight: 600; text-align: left; margin: 0;">Controls Validation Status</h6>
                    </div>
                """, unsafe_allow_html=True)

                status_counts = self.db_df["is_validated"].value_counts()
                status_map = self.STATUS_MAP
                df_status = pd.DataFrame({
                    'Status Code': status_counts.index,
                    'Count': status_counts.values
                })
                df_status['Status'] = df_status['Status Code'].map(status_map).fillna(df_status['Status Code'].astype(str))

                chart_col, spacer, detail_col = st.columns([3, 0.8, 1.5])
                with chart_col:
                    fig = px.pie(
                        df_status,
                        values='Count',
                        names='Status',
                        title='',
                        color_discrete_sequence=px.colors.qualitative.Safe
                    )
                    st.plotly_chart(fig, use_container_width=True, key="db_status_pie_chart")
                with detail_col:
                    st.markdown(""" <div style="text-align: left; font-size: 16px; margin-top: 60px;">
                            <a class="md-link" href="/?page=db_detail" style="font-size: 14px;">View All</a>
                    """, unsafe_allow_html=True)
                    for _, row in df_status.iterrows():
                        status = row['Status']
                        count = row['Count']
                        st.markdown(f"""
                            <a class="md-link" href="/?page=db_detail&status={status}" style="margin-right: 16px;">
                                🔍 {status} ({count})
                            </a>
                        """, unsafe_allow_html=True)

            # st.markdown("<hr style='margin: 45px 0;'>", unsafe_allow_html=True)
            st.markdown("<hr style='margin: 30px 0 45px 0;'>", unsafe_allow_html=True)
            control_type_total = control_type_counts.sum()
            st.write("Total Controls:", control_type_total)

            st.write(control_type_counts)
            df_plot = pd.DataFrame({
                'Control Type': control_type_counts.index.astype(str),
                'Count': control_type_counts.values
            }).sort_values('Control Type')
            fig_donut = px.pie(
                df_plot,
                names='Control Type',
                values='Count',
                title='🧿 Control Type Donut (%)',
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            st.plotly_chart(fig_donut, use_container_width=True, key="donut_chart")

                        
    def render_markdown_with_images(self, markdown_text: str, base_path: Path):
        import streamlit as st
        import re

        lines = markdown_text.strip().splitlines()

        try:
            header_idx = next(
                i for i, line in enumerate(lines)
                if line.strip().startswith("|") and "Image" in line
            )
            sep_idx = header_idx + 1
        except StopIteration:
            st.markdown(markdown_text, unsafe_allow_html=True)
            return

        header_line = lines[header_idx]
        cols_header = [c.strip() for c in header_line.split("|")]
        if cols_header and cols_header[0] == '':
            cols_header = cols_header[1:]
        if cols_header and cols_header[-1] == '':
            cols_header = cols_header[:-1]

        data_lines = lines[sep_idx + 1:]

        for line in data_lines:
            if not line.strip() or line.strip().startswith("|-"):
                continue
            cols = [c.strip() for c in line.split("|")]
            if cols and cols[0] == '':
                cols = cols[1:]
            if cols and cols[-1] == '':
                cols = cols[:-1]

            if len(cols) != len(cols_header):
                continue

            st_cols = st.columns(len(cols_header))

            for idx, col_name in enumerate(cols_header):
                content = cols[idx]

                if "image" in col_name.lower():
                    m = re.search(r'src="([^"]+)"', content)
                    if m:
                        img_rel_path = m.group(1).replace("\\", "/")
                        img_abs_path = (base_path.parent / img_rel_path).resolve()
                        with st_cols[idx]:
                            if img_abs_path.exists():
                                st.image(str(img_abs_path), use_container_width=True)
                            else:
                                st.warning(f"Image not found: {img_abs_path}")
                    else:
                        with st_cols[idx]:
                            st.write(content)
                else:
                    with st_cols[idx]:
                        st.markdown(content)

            st.markdown("<hr style='border: none; border-top: 0.3px solid #474544; margin: 6px 0;'>", unsafe_allow_html=True)

    def render_chart(self):
        st.write("---")

        if not self.md_files_map and self.db_df.empty:
            st.info("No data to display.")
            return

    def render_md_detail(self):
        file_name = self.query_params.get("file", [None])[0]
        filter_type = self.query_params.get("filter", [None])[0]

        if file_name and file_name in self.md_files_map:
            st.title(f"{file_name}")
            st.link_button("⬅ Back to Summary", url="/")
            file_path = self.md_files_map[file_name]["path"]

            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                lines = content.strip().splitlines()

                if filter_type == "non_compliant":
                    lines = content.strip().splitlines()
                    header_line = None
                    separator_line = None
                    data_lines = []

                    for i, line in enumerate(lines):
                        if line.strip().startswith("|") and "Compliance" in line:
                            header_line = line
                            if i + 1 < len(lines):
                                next_line = lines[i + 1].strip()
                                if next_line.startswith("|") and all(c in "-| " for c in next_line):
                                    separator_line = next_line
                            continue

                    if separator_line:
                        for line in lines[lines.index(separator_line)+1:]:
                            if "❌" in line:
                                data_lines.append(line)

                    if header_line and separator_line and data_lines:
                        filtered_content = "\n".join([header_line, separator_line] + data_lines)
                        self.render_markdown_with_images(filtered_content, file_path)
                    else:
                        st.info("No non-compliant records found.")


                else:
                    self.render_markdown_with_images(content, file_path)
        else:
            st.error("Markdown file not found.")

    def render_db_detail(self):
        st.title("🔢 Database Table Details")

        if self.db_df.empty:
            st.error("No data available.")
            return

        status_filter = self.query_params.get("status", [None])[0]

        
        reverse_status_map = {v: k for k, v in self.STATUS_MAP.items()}

        if status_filter:
            code = reverse_status_map.get(status_filter)
            if code is not None:
                filtered_df = self.db_df[self.db_df["is_validated"] == code]
                st.markdown(f"### Showing only status: **{status_filter}** ({len(filtered_df)} records)")
                st.dataframe(filtered_df)
            else:
                st.warning(f"Invalid status filter: {status_filter}")
                st.dataframe(self.db_df)
        else:
            st.dataframe(self.db_df)

        st.link_button("⬅ Back to Summary", url="/")


    def apply_style(self):
        st.markdown("""
            <style>
                .block-container {
                    padding: 1.5rem 6rem;
                    max-width: 100%;
                }
                .stMetric {
                    background-color: #2a2a2a;
                    padding: 1rem;
                    border-radius: 0.5rem;
                    box-shadow: 0 0 6px rgba(0,0,0,0.2);
                    margin-bottom: 1rem;
                }
                a {
                    color: #61dafb;
                    font-weight: bold;
                }
                h3 {
                    margin-top: 3rem;
                }
            </style>
        """, unsafe_allow_html=True)

    def render_main_summary(self):
        st.markdown("<h1 style='text-align: center;'>📑 WRS Accessibility Dashboard</h2>", unsafe_allow_html=True)
        if self.job_info.exists():
            try:
                with open(self.job_info, "r", encoding="utf-8") as f:
                    job_data = json.load(f)
                st.markdown(
                    f"""
                    <div style="text-align:center; font-size:16px; margin-top:-10px; margin-bottom:20px; color: #666;">
                        <b>App Version:</b> {job_data.get('appVersion', 'N/A')} &nbsp;|&nbsp;
                        <b>Device OS:</b> {job_data.get('deviceOS', 'N/A')} &nbsp;|&nbsp;
                        <b>Device Model:</b> {job_data.get('workflow', 'N/A')} &nbsp;|&nbsp;
                        <b>Report ID:</b> {job_data.get('reportId', 'N/A')} &nbsp;|&nbsp;
                        <b>Run Date:</b> {job_data.get('runDate', 'N/A')}
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            except Exception as e:
                st.warning(f"Failed to load job info: {e}")
        st.write("---")
        col1, spacer, col2 = st.columns([12, 1.5,8])
        with col1:
            self.render_md_summary()
        with col2:
            self.render_db_summary()

    def run(self):
        self.apply_style()
        page = self.query_params.get("page", ["home"])[0]
        if page == "md_detail":
            self.render_md_detail()
        elif page == "db_detail":
            self.render_db_detail()
        else:
            self.render_main_summary()
            self.render_chart()

    def check_chromium(self):
        try:
            chromium_path = p.chromium.executable_path
        except Exception:
            chromium_path = None
        if chromium_path is None or not Path(chromium_path).exists():
            print("Chromium not found. Installing Chromium...")
            subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])
            print("Chromium installed successfully.")

if __name__ == "__main__":
    dashboard = ComplianceDashboard()
    dashboard.run()

    url = "http://localhost:8501"
    output_pdf = dashboard.output_path / "dashboard.pdf"
    output_png = dashboard.output_path / "dashboard.png"
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, wait_until="networkidle")
        page.wait_for_selector("div.js-plotly-plot", timeout=5000)
        page.pdf(
            path=str(output_pdf),
            print_background=True,
            margin={"top": "1cm", "bottom": "1cm", "left": "1cm", "right": "1cm"},
            format="A2"
        )
        browser.close()
    
    pdf_page = browser.new_page(viewport={"width": 1920, "height": 1080})
    pdf_page.goto(f"file://{output_pdf.resolve()}", wait_until="networkidle")
    dimensions = pdf_page.evaluate("""
        () => {
            const body = document.body;
            return { width: body.scrollWidth || 1920, height: body.scrollHeight || 1080 };
        }
    """)
    pdf_page.set_viewport_size({"width": dimensions["width"], "height": dimensions["height"]})
    pdf_page.screenshot(path=output_png, full_page=True)
  

    # with sync_playwright() as p:
    #     browser = p.chromium.launch(headless=True)
    #     page = browser.new_page()
    #     page.goto("http://localhost:8501", wait_until="networkidle")
    #     html_content = page.content()
    #     output_file.write_text(html_content, encoding="utf-8")
    #     browser.close()

