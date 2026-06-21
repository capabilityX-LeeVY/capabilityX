import pandas as pd
class MarkdownToDataframe(object):
    def __init__(self) -> None:
        pass

    @staticmethod
    def MarkdownToDataframe(path:str,startLine = 0) -> pd.DataFrame:
        from io import StringIO
        df = None
        with open(path,"r",encoding="utf-8",errors="ignore") as f:
            content = f.read()
            csv_data = "\n".join(line.strip('| ') for line in content.strip().split('\n')[startLine:])
            data = StringIO(csv_data)
            tmpDf = pd.read_csv(data, sep="|")
            tmpDf.columns = tmpDf.columns.str.strip()
            df = pd.DataFrame(tmpDf[1:])
            df.reset_index(drop=True, inplace=True)
            return df
        
        return df
    

    @staticmethod 
    def DataframeToHTML(df:pd.DataFrame,htmlPath):
        html = df.to_html(escape=False,index=False)
        styled_html = ""
        if len(html) != 0:
            styled_html = f"""
            <!DOCTYPE html> <html lang="zh">
            <head> <meta charset="UTF-8"> <style> 
                    table {{ border-collapse: collapse; width: 100%; }}
                    th, td {{ border: 1px solid black; padding: 8px; text-align: left; }}
                    th {{ background-color: #f2f2f2; }}
                    tr:nth-child(even) {{ background-color: #f9f9f9; }}
                    tr:nth-child(odd) {{ background-color: #ffffff; }}
                    </style>
            </head> 
            <body> {html} </body>
            </html>
            """
            with open(htmlPath,"w+",encoding="utf-8",errors="ignore") as f:
                f.write(styled_html)
    

if __name__ == "__main__":
    fullPath = "/Volumes/Data/Code/WebexRegressSheild/src/report/gpt-WCAG/WCAG_Screen_Reader_overall_report.md"
    df = MarkdownToDataframe.MarkdownToDataframe(fullPath)
    print(df.shape)
    df = df[df["Compliance"].str.contains('Non-compliant')]
    print(df)
    print(df["Compliance"])
    print(df.shape)
    html = df.to_html()
    styled_html = ""
    if len(html) != 0:
        styled_html = f"""
        <!DOCTYPE html> <html lang="zh">
        <head> <meta charset="UTF-8"> <style> 
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid black; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                tr:nth-child(even) {{ background-color: #f9f9f9; }}
                tr:nth-child(odd) {{ background-color: #ffffff; }}
                </style>
        </head> 
        <body> {html} </body>
        </html>
        """
        with open("/tmp/aa.html","w+",encoding="utf-8",errors="ignore") as f:
            f.write(styled_html)

