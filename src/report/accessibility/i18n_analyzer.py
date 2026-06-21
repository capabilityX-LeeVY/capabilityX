import os
import time
import pandas as pd

from pathlib import Path
from models.openai_client import OpenAIClient
from config.paths import LOCAL_REPORT_RESULT_PATH, PROMPTS_PATH
from common.utils.logger import LOGGER_INFO, LOGGER_ERROR


class I18nAnalyzer:
    def __init__(self) -> None:
        self.client = OpenAIClient()
        self.images_folder = self._get_images_folder()
        self.full_i18n_path = LOCAL_REPORT_RESULT_PATH

    def _load_i18n_prompt(self) -> str:
        template_path = PROMPTS_PATH / "template_i18n.md"
        try:
            with open(template_path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            LOGGER_ERROR(f"Prompt template not found: {template_path}")
            return ""

    def _get_images_folder(self) -> Path:
        current_dir = Path(__file__).resolve()
        while current_dir.name != "src" and current_dir.parent != current_dir:
            current_dir = current_dir.parent
        if current_dir.name == "src":
            return current_dir / "images"
        raise FileNotFoundError("Cannot find 'src' directory, check your project structure.")

    def get_image_files(self, user_image_path):
        user_image_path = Path(user_image_path)
        return [
            img for img in user_image_path.iterdir()
            if img.suffix.lower() in {'.png', '.jpg', '.jpeg', '.gif', '.bmp'}
        ]

    def analyze_images(self, user_image_path, output_path):
        image_files = self.get_image_files(user_image_path)
        LOGGER_INFO(f"Found {len(image_files)} images in {user_image_path}")

        os.makedirs(output_path, exist_ok=True)
        output_md_path = output_path / "result_gpt4_vision_message_temp.md"
        LOGGER_INFO(f"Output markdown path: {output_md_path}")

        batch_size = 10
        total_images = len(image_files)
        prompt = self._load_i18n_prompt()

        with open(output_md_path, 'w', encoding='utf-8') as f:
            for i in range(0, total_images, batch_size):
                batch = image_files[i:i + batch_size]
                LOGGER_INFO(
                    f"Processing batch {i // batch_size + 1} / "
                    f"{(total_images + batch_size - 1) // batch_size}"
                )
                time.sleep(2)

                for image_path in batch:
                    try:
                        message_content = self.client.chat_i18n(str(image_path), message=prompt)
                        if message_content:
                            relative_path = os.path.relpath(image_path, output_md_path.parent)
                            html_img_tag = (
                                f'<img src="{relative_path}" alt="{image_path.name}" '
                                f'style="max-width: 300px; height: auto;">'
                            )
                            message_content = message_content.replace("[Current Image]", html_img_tag)
                            f.write(message_content + "\n\n")
                        else:
                            LOGGER_ERROR(f"Empty response for {image_path}")
                    except Exception as e:
                        LOGGER_ERROR(f"Failed to analyze {image_path}, error={e}")

        return f"Analysis completed. Results saved to {output_md_path}"

    def get_response(self, user_image_path):
        prompt = self._load_i18n_prompt()
        result = self.client.chat_i18n(str(user_image_path), message=prompt)
        if not result:
            return "Analysis failed"

        output_md_path = self.images_folder / "l18n_report.md"
        image_name = os.path.basename(user_image_path)
        full_content = (
            "### Localization Analysis Report\n\n"
            f"![Analyzed Image]({image_name})\n\n"
            f"{result}"
        )
        with open(output_md_path, "w", encoding="utf-8") as md_file:
            md_file.write(full_content)
        return full_content

    def format_markdown_file(self, output_path):
        output_md_path = Path(output_path) / "result_gpt4_vision_message_temp.md"
        md_format_path = Path(output_path) / "raw_i18n_data.md"

        with open(output_md_path, 'r', encoding='utf-8') as file:
            markdown_content = file.readlines()

        tables = []
        current_table = []
        for line in markdown_content:
            if line.strip().startswith("|") and line.strip().endswith("|"):
                current_table.append(line.strip())
            elif current_table:
                tables.append(current_table)
                current_table = []
        if current_table:
            tables.append(current_table)

        merged_table = []
        for table in tables:
            header = table[0]
            separator = table[1]
            rows = table[2:]
            if not merged_table:
                merged_table.append(f"| No. | {header[1:]}")
                merged_table.append(f"|---|{separator[1:]}")
            merged_table.extend(rows)

        numbered_table = [
            f"| {i} | {row[1:]}"
            for i, row in enumerate(merged_table[2:], start=1)
        ]

        with open(md_format_path, 'w', encoding='utf-8') as output_file:
            output_file.write("\n".join(merged_table[:2] + numbered_table))

        LOGGER_INFO(f"Formatted Markdown saved to {md_format_path}")
        return md_format_path

    def remove_duplicate_rows(self, output_path):
        input_file = Path(output_path) / "raw_i18n_data.md"
        with open(input_file, "r", encoding="utf-8") as file:
            lines = file.readlines()

        header_line = lines[0].strip()
        columns = [col.strip() for col in header_line.split("|") if col.strip()]

        data_lines = [line.strip() for line in lines[2:] if line.strip()]
        data = []
        for line in data_lines:
            row = line.split("|")[1:-1]
            if len(row) < len(columns):
                row.extend([""] * (len(columns) - len(row)))
            elif len(row) > len(columns):
                row = row[:len(columns)]
            data.append(row)

        df = pd.DataFrame(data, columns=columns)
        df['key'] = df.iloc[:, 3].str.strip() + "_" + df.iloc[:, 4].str.strip()
        df_unique = df.drop_duplicates(subset='key').drop(columns=['key'])

        output_file = Path(output_path) / "public_i18n-report.md"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("| " + " | ".join(columns) + " |\n")
            f.write("|" + "|".join(["---"] * len(columns)) + "|\n")
            for _, row in df_unique.iterrows():
                f.write("| " + " | ".join(str(x).strip() if pd.notna(x) else "" for x in row) + " |\n")

        LOGGER_INFO(f"Deduplicated file saved to {output_file}")
        return output_file
