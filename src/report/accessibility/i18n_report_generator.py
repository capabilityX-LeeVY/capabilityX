import re
import hashlib
import pandas as pd

from datetime import datetime
from pathlib import Path
from tools.Jira.Jira import TeamsJiraIssueReporter
from tools.markdownToDataframe import MarkdownToDataframe
from config.paths import SETTINGS_PATH, WINDOW_IMAGE_PATH
from config.mysql import ConnectToDB
from common.handler.settingsHandler import DynamicConfig


class I18nReportGenerator:
    def __init__(self, fullPath) -> None:
        self.fullPath = Path(fullPath) / "deduplicated_markdown.md"
        self.osInfo = None
        self.versionInfo = None
        self.jiraVersion = None
        self.qtVersion = None
        self.releaseVersion = None

    def _readConfigs(self):
        settings = DynamicConfig(SETTINGS_PATH)
        self.osInfo = settings.get('osInfo')
        self.versionInfo = settings.get('appVersion')
        self.qtVersion = settings.get('qtVersion')

        if self.versionInfo is not None:
            affectVersion = self.versionInfo.split('.')
            if len(affectVersion) >= 2:
                self.releaseVersion = ".".join(affectVersion[:2])
            self.jiraVersion = [{"name": f"WxRel-{self.releaseVersion}"}]

    def _formatJiraTitle(self, row: pd.Series, df: pd.DataFrame):
        col_control_name = df.columns[3]
        col_language = df.columns[5]
        title = f'[{row["Analysis Result"]}][{row[col_language]}][{row[col_control_name]}][{row["Compliance"]}][{row["Reference"]}]'
        if len(title) > 250:
            title = title[:250] + "..."
        return title

    def _formatJiraDescription(self, row: pd.Series):
        columns = list(row.index)
        if len(columns) > 1:
            del columns[1]
        description = f'h1. {{color:#172b4d}}WebEx APP UI issue Report{{color}}\r\n\r\n'
        description += "||" + "|| ".join(columns) + "||\r\n"
        row_str = ""
        for index, value in row.items():
            if index not in columns:
                continue
            display_value = str(value)
            index_str = str(index)
            if "Localization Compliance" in index_str:
                display_value = f'{{color:red}}{value}{{color}}'
            elif "Suggestions for Improvement" in index_str:
                display_value = f'*{str(value).strip()}*'
            row_str += " | " + display_value
        description += row_str + " | \r\n"
        return description

    def _fileJiraBug(self, row: pd.Series, df: pd.DataFrame):
        title = self._formatJiraTitle(row, df)
        description = self._formatJiraDescription(row)
        jira = TeamsJiraIssueReporter(title, description, self.jiraVersion)
        jira.labels = ["WebexRegressShield_localization"]
        jiraID = jira.creatBug()
        title = title.replace("'", "\\'").replace("#!", "\\'")
        return jiraID, title

    def _uploadImage(self, jiraID, image_paths):
        jira = TeamsJiraIssueReporter(None, None)
        jira.upload_image(jiraID, image_paths)

    def extract_alt_value(self, image_paths):
        match = re.search(r'alt="([^"]+)"', image_paths)
        if match:
            return match.group(1)
        return None

    def ParserReportAndFileBugs(self):
        self._readConfigs()
        dbConnection = ConnectToDB()
        df: pd.DataFrame = MarkdownToDataframe.MarkdownToDataframe(str(self.fullPath))
        mask = df["Compliance"].str.contains('Non-compliant')
        df = df[mask].reset_index(drop=True)  # type: ignore[assignment]
        jiraInfos = []
        maxCount = 50

        for _, row in df.iterrows():
            if maxCount <= 0:
                break
            col_image = df.columns[2]
            col_control_name = df.columns[3]
            hashString = row[col_control_name].replace("'", "\\'").replace("#!", "\\'")
            issue_hash = hashlib.sha256(hashString.encode("utf-8")).hexdigest()

            sql = f'SELECT * FROM `Localization`.`issueinfo` WHERE `hash` = "{issue_hash}" OR `hashString` = "{hashString}";'
            results, columns = dbConnection.Query(sql)

            if results:
                temp_df = pd.DataFrame(data=results, columns=columns)
                jiraID = temp_df["jiraID"].values[0]
                title = temp_df["title"].values[0]
                jiraInfos.append((jiraID, title))
                continue

            jiraID, title = self._fileJiraBug(row, df)
            if jiraID is not None:
                print(f"New Localization bug: https://jira-eng-gpk2.cisco.com/jira/browse/{jiraID}")
                maxCount -= 1
                date = datetime.today().date()
                sql_insert = (
                    f"INSERT INTO `Localization`.`issueinfo` "
                    f"(`jiraID`, `createDate`, `title`, `affectVersion`, `platform`, `hash`, `hashString`, `status`) "
                    f"VALUES ('{jiraID}', '{date}', '{title}', '{self.releaseVersion}', "
                    f"'{self.osInfo}', '{issue_hash}', '{hashString}', 'open');"
                )
                dbConnection.Execute(sql_insert)
                jiraInfos.append((jiraID, title))

                image_paths = row[col_image]
                alt_value = self.extract_alt_value(image_paths)
                image_paths = f"{WINDOW_IMAGE_PATH}/{alt_value}"
                self._uploadImage(jiraID, [image_paths])

        return jiraInfos

    def AddJiraInfoAndToHTML(self, htmlPath):
        dbConnection = ConnectToDB()
        df: pd.DataFrame = MarkdownToDataframe.MarkdownToDataframe(str(self.fullPath))
        df["References"] = df["References"].str.replace("**", "")
        df["Jira"] = ""

        for index, row in df.iterrows():
            description = row["EN"].replace("'", "\\'").replace("#!", "\\'")
            sql = f'SELECT jiraID FROM Localization.issueinfo WHERE hashString = "{description}";'
            data, _ = dbConnection.Query(sql)
            df.at[index, 'References'] = f'<b>{row["References"]}</b>'
            if data:
                df.at[index, 'Jira'] = (
                    f'<a href="https://jira-eng-gpk2.cisco.com/jira/browse/{data[0][0]}" '
                    f'target="_blank">{data[0][0]}</a>'
                )

        MarkdownToDataframe.DataframeToHTML(df, htmlPath)
