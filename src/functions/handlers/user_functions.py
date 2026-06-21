def greet_user(name: str):
    """Greet the user with their name"""
    return {"greeting": f"Hello, {name}!"}

def who_are_you():
    """Answer the question 'Who are you?'"""
    return {
        "response": "I’m a Webex RegressShield AI assistant designed to help you with accessibility tasks. How can I assist you today?"
    }

def what_is_model():
    """Answer the question 'Who is model?'"""
    return {
        "response": "I am based on OpenAI's GPT-4 model, which is designed to assist with a wide range of validation accessibility tasks. How can I assist you today?"
    }

def what_can_you_do():
    """Answer the question 'What can you do?'"""
    return {
        "response": "I can assist with the following tasks:\n"
                    "- Starting or stopping a Webex meeting.\n"
                    "- Validating accessibility features for Webex meetings.\n"
                    "- Checking UI controls for accessibility compliance.\n"
                    "- Extracting and analyzing screen reader descriptions.\n"
                    "- Detecting focus rings and high contrast elements in images."
    }