import sqlite3
import re
from config.paths import DB_PATH,CONTROL_NAVIGATOR_DATA_PATH

class NavigatorDataProcessor: 
    WCAG_MAPPING = {
        -1: "WCAG 2.1.1 Focus Lost",
        -2: "WCAG 2.1.1 Cannot Find Control", 
        -5: "WCAG 2.1.2 No Keyboard Trap",
        -8: "4.1.2 Name, Role, Value"
    }
    
    NON_COMPLIANT_VALUES = [-1, -2, -5, -8]
    EXCLUDED_CONTROL_TYPES = ["edit"]

    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self.navigator_data_path = CONTROL_NAVIGATOR_DATA_PATH

    def process_data(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
        SELECT * FROM (
            SELECT 
                "TabOrder",
                "Description",
                "ControlType",
                "ControlLocalizedType",
                "FromControl",
                is_validated,
                ROW_NUMBER() OVER (PARTITION BY "Description" ORDER BY "TabOrder") AS rn
            FROM "ControlINFO"
            )
            WHERE rn = 1
            ORDER BY "TabOrder", "Description";
        """)
        rows = cursor.fetchall()
        conn.close()

        rows = self.filter_redundant_failures(rows)
        md_content = self.generate_markdown_table(rows)

        output_path = self.navigator_data_path / "navigator-report.md"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(md_content)

        return output_path
    
    def generate_markdown_table(self, rows):
        md_lines = [
            "| No. | Control Name | ControlLocalizedType | FromControl | Analysis Result | Compliance | Reference |",
            "|-----|-------------|---------------------|-------------|------------------|------------|-----------|"
        ]
        # add data row (index: TabOrder=0, Description=1, ControlType=2, ControlLocalizedType=3, FromControl=4，is_validated=5)
        for index, row in enumerate(rows, 1):
            description = row[1] if row[1] else ""
            description = description.replace('\n', ' ').replace('\r', ' ')
            description = re.sub(r'\s+', ' ', description).strip()
            control_localized_type = row[3] if row[3] else ""
            from_control = row[4] if row[4] else ""
            from_control = from_control.replace('\n', ' ').replace('\r', ' ')
            from_control = re.sub(r'\s+', ' ', from_control).strip()
            is_validated = row[5] if row[5] else ""
            
            # format Compliance and Reference
            compliance, reference = self.format_compliance_and_reference(is_validated, control_localized_type)

            md_lines.append(f"| {index} | {description} | {control_localized_type} | {from_control} | {is_validated} | {compliance} | {reference} |")

        return "\n".join(md_lines)

    def format_compliance_and_reference(self, is_validated, control_localized_type):
        try:
            validated_value = int(is_validated) if is_validated != "" else 0
        except (ValueError, TypeError):
            validated_value = 0

        if (validated_value in self.NON_COMPLIANT_VALUES and 
            control_localized_type not in self.EXCLUDED_CONTROL_TYPES):
            return "❌ Non-compliant", self.WCAG_MAPPING.get(validated_value, "WCAG Issue")
        else:
            return "✅ Compliant", ""

    def filter_redundant_failures(self, rows):
        filtered_rows = []
        redundant_failure_count = 0
        
        for row in rows:
            is_validated = row[5] if row[5] else ""
            
            if is_validated == -2:
                redundant_failure_count += 1
                if redundant_failure_count == 1:
                    filtered_rows.append(row)
                elif redundant_failure_count == 3:
                    navigation_block_summary = (
                        row[0],  # TabOrder
                        f"[{redundant_failure_count}+ controls blocked after this point]",  # Description
                        "summary",  # ControlType
                        "Navigation Issue",  # ControlLocalizedType
                        -2,  # is_validated
                        row[4]  # FromControl
                    )
            else:
                redundant_failure_count = 0
                filtered_rows.append(row)
        
        return filtered_rows