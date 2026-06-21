import os
import sys

from dotenv import load_dotenv
load_dotenv()
pythonpath = os.getenv("PYTHONPATH")
if pythonpath:
    full_path = os.path.abspath(pythonpath)
    if full_path not in sys.path:
        sys.path.insert(0, full_path)
from tools.Jira.management.analyze.jira_db_handler import JiraDBHandler
handler = JiraDBHandler()
    
jira_id = "SPARK-692239"
steps = handler.get_steps_by_jira_id(jira_id)

if steps:
    print(f"Steps for {jira_id}:")
    
    # Create markdown content
    md_content = f"# Steps for {jira_id}\n\n"
    md_content += "| No. | step |\n"
    md_content += "|---|------|\n"
    
    for i, step in enumerate(steps, 1):
        # Handle case where step might be a list or other data type
        if isinstance(step, list):
            step_text = ", ".join(str(item) for item in step)
        else:
            step_text = str(step)
        
        # Remove the leading number and comma if present
        if step_text.startswith(f"{i}, "):
            clean_step = step_text[len(f"{i}, "):]
        else:
            clean_step = step_text
            
        print(f"  {i}. {clean_step}")
        # Escape pipe characters in step content to avoid breaking table format
        escaped_step = clean_step.replace("|", "\\|")
        md_content += f"| {i} | {escaped_step} |\n"
    
    # Write to markdown file
    output_file = f"{jira_id}_steps.md"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(md_content)
    
    print(f"\nSteps have been written to {output_file}")
    
bug_info = handler.get_bug_info_by_jira_id(jira_id)
if bug_info:
    print(f"\nBug summary: {bug_info.get('summary')}")
    print(f"Status: {bug_info.get('status')}")
    print(f"Steps count: {bug_info.get('steps_count')}")
        
