def prompts_i18n_template():

    handle_webex_app_path = r"src/prompts/template_i18n.md"

    try:
        with open(handle_webex_app_path, "r", encoding="utf-8") as file:
            handle_meeting_template = file.read()
    except FileNotFoundError:
        print("File not found:", handle_webex_app_path)
        return None
    
    prompts_template = handle_meeting_template
    
    return prompts_template
