import re
import pandas as pd
from tools.Jira.Jira import TeamsJiraIssueReporter
from config.mysql import ConnectToDB
from datetime import datetime
import hashlib
from common.utils.logger import LOGGER_INFO
from tools.MessageBot.BotMessage import sendMessageToTeams

class CAccessibilityReport(object):
    def __init__(self,fullPath) -> None:
        self.fullPath = fullPath
        self.head = None
        self.reportTitle = None
        self.reportBody = None

        self.tableColumns = None
        self.tableStartLine = None
        self.tableItems = None
        self.osInfo = None
        self.versionInfo = None
        self.jiraVersion = None
        self.qtVersion = None
        self.releaseVersion = None

    def _parserHead(self):
        if self.head is None:
            return
        
        res = re.search('.*\s*\[(?P<osInfo>.*)\].*\s*\[Version:(?P<version>.*)\].*\s*\[qtVersion:(?P<QTversion>.*)\].*\s*',self.head)
        if res != None:
            resDict = res.groupdict()
            self.osInfo = resDict['osInfo'].strip(" ")
            self.versionInfo = resDict['version'].strip(" ")
            self.qtVersion = resDict['QTversion'].strip(" ")
            affectVersion = self.versionInfo.split('.')
            if len(affectVersion) >=2:
                self.releaseVersion = ".".join(affectVersion[:2])
            
            self.jiraVersion = [{ "name": f'''WxRel-{self.releaseVersion}'''},]

        
    def _parserReportTitle(self):
        LOGGER_INFO("CAccessibilityReport start to parser Report Title")
        if self.reportTitle is None:
            return
        
        res = re.search('.*\s*(?P<split>.*\|-+.*\|.*)',self.reportTitle)
        if res != None:
            resDict = res.groupdict()
            split = resDict['split']
            index = self.reportTitle.find(split)
            part1 = self.reportTitle[:index].strip('\n')
            self.tableStartLine = self.reportTitle[index:]
            self.head = part1.split("\n")[0]
            self._parserHead()
            self.tableColumns = part1.split("\n")[-1].strip("|").split("|")
            self.tableColumns = [item.strip(" ") for item in self.tableColumns]

        LOGGER_INFO("CAccessibilityReport parser Report Title Done.")

    def _parserReportBody(self):
        LOGGER_INFO("CAccessibilityReport start to parser Report Body")
        if self.reportBody is None:
            return
        
        lines = self.reportBody.strip("\n").split("\n")
        allDatas = []
        for line in lines:
            item = line.strip("|").split("|")
            allDatas.append(item)
        
        self.tableItems = pd.DataFrame(allDatas,columns=self.tableColumns)
        LOGGER_INFO("CAccessibilityReport parser Report Body Done.")

    def Parser(self):
        res = []
        LOGGER_INFO("CAccessibilityReport start to Parser markdown file...")
        with open(self.fullPath,"r", encoding='utf-8', errors='ignore') as f:
            content = f.read()
            res = re.search('.*\s*(?P<split>.*\d+.*\|.*\d+.*\|.*)',content)
            if res != None:
                resDict = res.groupdict()
                split = resDict['split']
                index = content.find(split)
                self.reportTitle = content[:index]
                self.reportBody = content[index:]
                if self.reportTitle is not None:
                    self._parserReportTitle()
                
                if self.reportBody is not None:
                    self._parserReportBody()

        LOGGER_INFO("CAccessibilityReport parser markdown file Done.")
        
    
    def _formatMarkdownAttachment(self,dataFrame:pd.DataFrame) -> str:
        LOGGER_INFO("CAccessibilityReport format Markdown Attachment Begin.")
        if self.reportTitle is None:
            return ""
        columns = ["Tab Order","Description","Control Localized Type","keyboard action","result"]
        df = pd.DataFrame(dataFrame,columns=columns)

        attachment = self.head + "\n"
        attachment = attachment + "|" + "| ".join(columns) + "|\n"
        attachment = attachment + "|-----------"*len(columns)+"|\n"
        for _, row in df.iterrows():
            rowStr = "|".join(list(row))
            attachment = attachment + "|" + rowStr + "|\n"
        
        # with open("/tmp/att.md","w+") as f:
        #     f.write(attachment)
        LOGGER_INFO("CAccessibilityReport format Markdown Attachment End.")
        return attachment
    
    def _foramtJiraDescription(self,dataFrame:pd.DataFrame) -> str:
        LOGGER_INFO("CAccessibilityReport foramt Jira Description Begin.")
        if self.reportTitle is None:
            return ""
        
        columns = ["Tab Order","Description","Control Localized Type","keyboard action","result"]
        df = pd.DataFrame(dataFrame,columns=columns)

        attachment = f'''h1. {{color:#172b4d}}{self.head.strip("#")}{{color}}\r\n\r\n'''
        attachment = attachment + "||" + "|| ".join(columns) + "||\r\n"
        for _, row in df.iterrows():
            reason = row["result"]
            res = re.search('.*\s*<span.*\s*(?P<failReason>Fail:.*)</.*\s',reason)
            if res != None:
                resDict = res.groupdict()
                row["result"] = f'''{{color:red}}{resDict['failReason'].strip()}{{color}}''' 

            rowStr = "|".join(list(row))

            attachment = attachment + "|" + rowStr + "|\r\n"
        
        LOGGER_INFO("CAccessibilityReport foramt Jira Description End.")
        # with open("/tmp/att1.md","w+") as f:
        #     f.write(attachment)
        return attachment
    
    def _formatIssueFormat(self,index,rowOfIssue):
        result = {}
        if self.tableItems is None:
            return result
        
        controlName = rowOfIssue["Description"].strip(" ").split(" ")
        if len(controlName) >=5:
            controlName = " ".join(controlName[:5]) + "..."
        else:
            controlName = " ".join(controlName).strip(" ")
        
        if len(controlName) == 0:
            controlName = "None"

        reason = rowOfIssue["result"]
        res = re.search('.*\s*<span.*\s*Fail:(?P<failReason>.*)</.*\s',reason)
        if res != None:
            resDict = res.groupdict()
            reason = resDict['failReason'].strip()

        title = f'''[Acc][{self.osInfo}][{controlName}][{reason}]'''
                
        startIndex = index - 4
        if startIndex <0:
            startIndex = 0

        attachmentDf = self.tableItems.iloc[startIndex:,:].head(6)
        description = self._foramtJiraDescription(attachmentDf)
        lastRowControlName = None
        if attachmentDf.shape[0] >=3:
            lastRowControlName = attachmentDf.iloc[-3]["Description"].strip(" ")
        
        hashStr = f'''{lastRowControlName} {rowOfIssue["Description"].strip(" ")} {reason}'''
        hashStr_new = f'''{lastRowControlName} {rowOfIssue["Description"].strip(" ")} {reason} {rowOfIssue["Control Localized Type"].strip(" ")}'''
        result["title"] = title
        result["description"] = description
        result["affectVersion"] = self.jiraVersion
        result["platform"] = self.osInfo
        result["issueHash"] = hashlib.sha256(hashStr_new.encode("utf-8")).hexdigest()
        result["issueHashString"] = hashStr
        result["issueHashString_new"] = hashStr_new
        result["releaseVersion"] = self.versionInfo
        return result

    def FindIssues(self):
        result = []
        if self.tableItems is None:
            return result

        issues = self.tableItems[self.tableItems["result"].str.contains("Fail")]
        for index,row in issues.iterrows():
            res = self._formatIssueFormat(index,row)
            result.append(res)
        
        return result

def FileNewJiraNotifition(JiraInfos):
    LOGGER_INFO("ready to File New Jira Notifition....")
    if len(JiraInfos) == 0:
        return
    
    message = "#### **New ACC Issue(s) found:**\n"
    for jiraInfo in JiraInfos:
        jiraID = jiraInfo[0]
        title = jiraInfo[1]
        newLine = f'''* **[{jiraID}](https://jira-eng-gpk2.cisco.com/jira/browse/{jiraID})** [{title}]\n'''
        message = message + newLine
    sendMessageToTeams(message,roomId="a48ab4a0-7d98-11f0-95e9-4735252c61fe")

def ParserMarkdownAndFileJira(fullPath:str) -> None:
    report = CAccessibilityReport(fullPath)
    report.Parser()
    issues = report.FindIssues()
    # if len(issues) > 10:
    #     issues = issues[:10]
    dbConnection = ConnectToDB()
    JiraInfos = []
    JiraIDs = []
    maxCount = 10
    for issue in issues:
        if maxCount <=0:
            break
        title = issue["title"].replace("'", "\\'").replace("#!", "\\'")
        description = issue["description"]
        affectVersion = issue["affectVersion"]
        platform = issue["platform"]
        IssueHash = issue["issueHash"]
        releaseVersion = issue["releaseVersion"]
        hashString = issue["issueHashString"].replace("'", "\\'").replace("#!", "\\'")
        hashString_new = issue["issueHashString_new"].replace("'", "\\'").replace("#!", "\\'")
        sql = f'''select * from `RegressShield`.`bugInfo` where `hash` = "{IssueHash}" or `hashString` = "{hashString}" or `hashString_new` = "{hashString_new}";'''
        results,_ = dbConnection.Query(sql)
        if len(results) > 0:
            message = f'''duplicate issue with hash:{IssueHash}, hashString:{hashString}'''
            LOGGER_INFO(message)
            continue
        jira = TeamsJiraIssueReporter(title,description,affectVersion)
        jiraID = jira.creatBug()
        if jiraID is not None:
            maxCount = maxCount -1
            newJira = [jiraID,issue["title"]]
            JiraInfos.append(newJira)
            date = datetime.today().date()
            sql1 = f'''INSERT INTO `RegressShield`.`bugInfo` (`jiraID`, `createDate`, `title`, `affectVersion`, `platform`, `hash`, `hashString`,`hashString_new`, `status`) VALUES ('{jiraID}', '{str(date)}', '{title}', '{releaseVersion}', '{platform}', '{IssueHash}', '{hashString}','{hashString_new}', 'open');'''
            dbConnection.Execute(sql1)
            JiraIDs.append(jiraID)

    return JiraIDs

if __name__ == "__main__":
    fullPath = "/Users/jianphu2/Downloads/fcc-report.md"
    ParserMarkdownAndFileJira(fullPath)