import markdown

class CConvertMarkdownToHTML(object):
    def __init__(self) -> None:
        pass

    def _readMarkdownFromFile(self,path:str) ->str:
        with open(path,"r",encoding="utf-8",errors="ignore") as f:
            markdown_text = f.read()
            html = markdown.markdown(markdown_text, extensions=['tables'])
            return html
        
        return ""
    
    @staticmethod
    def MarkdownToHTML(markdownPath:str,htmlPath:str):
        convert = CConvertMarkdownToHTML()
        convert.ConvertToHTML(markdownPath,htmlPath)

    def ConvertToHTML(self,markdownPath:str,htmlPath:str):
        html = self._readMarkdownFromFile(markdownPath)
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



if __name__ == '__main__':
    markdownPath = f'''/Users/jianphu2/Downloads/acc-navigation-report-QT5.15.2-44.12.0.30960.md'''
    htmlPath = f'''/Users/jianphu2/Downloads/acc-navigation-report-QT5.15.2-44.12.0.30960.md.html'''
    CConvertMarkdownToHTML.MarkdownToHTML(markdownPath,htmlPath)