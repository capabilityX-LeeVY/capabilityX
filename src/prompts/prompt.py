
def prompts_template(test_scenario):

    handle_webex_app_path = "src/prompts/handle_webex_app.md"

    output_template_path = "src/prompts/output_template.md"

    try:
        with open(handle_webex_app_path, "r", encoding="utf-8") as file:
            handle_meeting_template = file.read()
    except FileNotFoundError:
        print("File not found:", handle_webex_app_path)
        return None

    try:
        with open(output_template_path, "r", encoding="utf-8") as file:
            output_template = file.read()
    except FileNotFoundError:
        print("File not found:", output_template_path)
        return None
    
    handle_meeting = handle_meeting_template.format(test_scenario=test_scenario)
    
    prompts_template = handle_meeting + "\n\n" + output_template
    
    return prompts_template
