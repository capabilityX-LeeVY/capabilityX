
def prompts_template(test_scenario, prompts_template_path):

    try:
        with open(prompts_template_path, "r", encoding="utf-8") as file:
            handle_meeting_template = file.read()
    except FileNotFoundError:
        print("File not found:", prompts_template_path)
        return None
    
    prompts_template_path = handle_meeting_template.format(test_scenario=test_scenario)
    
    return prompts_template_path
