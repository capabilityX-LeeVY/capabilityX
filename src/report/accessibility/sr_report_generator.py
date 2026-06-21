import os
import pandas as pd

from pathlib import Path
from models.openai_client import OpenAIClient
from prompts.prompts_acc import prompts_template
from common.handler.fileHandler import write_to_file
from config.paths import SETTINGS_PATH, CONTROL_SCREEN_READER_DATA_PATH, SCREEN_READER_RESULT_PATH, PROMPTS_PATH
from common.handler.settingsHandler import DynamicConfig
from common.utils.logger import LOGGER_INFO, LOGGER_ERROR
from tools.markdownToDataframe import MarkdownToDataframe as MarkdownToDataframeUtil


class SrReportGenerator:
    def __init__(self) -> None:
        self.client = OpenAIClient()
        self.full_sr_path = Path(SCREEN_READER_RESULT_PATH)

    def _ask(self, lines, prompts_template_path: str) -> str:
        message = prompts_template(lines, prompts_template_path)
        if message is None:
            LOGGER_ERROR(f"Failed to build prompt from template: {prompts_template_path}", "RED")
            return ""
        result = self.client.chat(message)
        return result or ""

    @staticmethod
    def _remove_pipes_in_cells(answer: str) -> str:
        lines = answer.splitlines()
        new_lines = []
        header_cols = None
        for i, line in enumerate(lines, start=1):
            stripped_line = line.strip()
            if stripped_line.startswith("|---"):
                new_lines.append(line)
                continue
            if stripped_line.startswith("|"):
                parts = [p.strip() for p in stripped_line.strip("|").split("|")]
                if header_cols is None:
                    header_cols = len(parts)
                cleaned_parts = [p.replace("|", "") for p in parts]
                if len(cleaned_parts) != header_cols:
                    print(f"⚠ Line {i} has {len(cleaned_parts)} columns (expected {header_cols}): {line.strip()}")
                if len(cleaned_parts) < header_cols:
                    cleaned_parts += [""] * (header_cols - len(cleaned_parts))
                elif len(cleaned_parts) > header_cols:
                    cleaned_parts = cleaned_parts[:header_cols]
                new_line = "| " + " | ".join(cleaned_parts) + " |"
                new_lines.append(new_line)
            else:
                new_lines.append(line)
        return "\n".join(new_lines)

    def run(self) -> Path:
        settings = DynamicConfig(SETTINGS_PATH)
        app_version = settings.get("appVersion")
        qt_version = settings.get("installOptions", "qtversion")

        raw_data = CONTROL_SCREEN_READER_DATA_PATH / "raw-data"
        analyzed = CONTROL_SCREEN_READER_DATA_PATH / "analyzed"
        output_path = SCREEN_READER_RESULT_PATH

        os.makedirs(output_path, exist_ok=True)
        os.makedirs(analyzed, exist_ok=True)

        file_paths = [
            os.path.join(raw_data, f).replace(os.sep, "/")
            for f in os.listdir(raw_data)
            if f.endswith(".md")
        ]

        summary_file = self.full_sr_path / f"public_sr-report_{app_version}.md"
        summary_df = pd.DataFrame()

        for i, file_path in enumerate(file_paths, start=1):
            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            LOGGER_INFO(f">>> [{i}] Calling AI to generate report for {file_path}", "WHITE")
            prompts_template_path = PROMPTS_PATH / "sr_template.md"
            answer = self._ask(lines, prompts_template_path=str(prompts_template_path))
            cleaned_answer = self._remove_pipes_in_cells(answer)

            base_name = os.path.basename(file_path)
            if "windows" in base_name:
                filename = f"SR_report_with_gpt4o_{app_version}_QT{qt_version}_{base_name}"
            else:
                filename = f"SR_report_with_gpt4o_{app_version}_{base_name}"

            report_path = SCREEN_READER_RESULT_PATH
            os.makedirs(report_path, exist_ok=True)
            filepath = os.path.join(report_path, filename)
            write_to_file(cleaned_answer, filepath)

            output_file = output_path / filename
            write_to_file(cleaned_answer, output_file)

            df = MarkdownToDataframeUtil.MarkdownToDataframe(filepath)
            if "No." in df.columns:
                df = df.drop(columns=["No."])
            summary_df = pd.concat([summary_df, df], ignore_index=True)

            stem = Path(file_path).stem
            if "windows" in Path(file_path).name:
                dest_name = f"{stem}_{app_version}_QT{qt_version}.md"
            else:
                dest_name = f"{stem}_{app_version}.md"
            dest_path = analyzed / dest_name
            if dest_path.exists():
                dest_path.unlink()
            Path(file_path).rename(dest_path)

            LOGGER_INFO(f">>> [{i}] Saved accessibility report to {output_file}", "GREEN")

        summary_df.insert(0, "No.", range(1, len(summary_df) + 1))
        with open(summary_file, "w", encoding="utf-8") as f:
            f.write("| " + " | ".join(summary_df.columns) + " |\n")
            f.write("|" + "|".join(["---"] * len(summary_df.columns)) + "|\n")
            for _, row in summary_df.iterrows():
                f.write("| " + " | ".join(str(x) for x in row) + " |\n")

        return summary_file
