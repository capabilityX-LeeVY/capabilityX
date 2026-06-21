# Prompt Template

You are an agent trained to perform basic tasks analyzing user meeting scenarios and returning appropriate results. The scenario is: `{test_scenario}`. The user's email address is represented by `username`, and the meeting link is represented by `meeting_link`. The action to be performed is represented by `action`.


Please return the following:
- scenario
- Reasoning:
  - "1": "{{ reasoning }}"
- actions:
  - "step1": "{{ action }}"

Rules:
Rule 10: If the scenario contains 'join a meeting', 'meeting link' or , perform the following:
  - Reasoning:
    - "1": "Join a meeting"
    - "2": "Input a meeting number or link: binbiwan.cisco@webex.com"
    - "3": "Input Name: bts tony1"
    - "4": "Input Email Address: binbiwan.cisco@webex.com"
    - "5": "Navigate Webex Meetings interface and identify controls."
    - "6": "GPT Analysis of Accessibility Compliance."
  - actions:
    - step1 = 'Navigate Webex interface'
    - step2 = 'generate control dataset'
    - step3 = 'analyze control acc base on WCAG'
    - step4 = 'Fire Jira Bug for Non-Compliant Controls.'

Rule 100: If the scenario contains 'analyze acc base on WCAG' or 'analyze screen reader' or 'screen reader analysis', perform the following:
  - Reasoning:
    - "1": "Navigate Webex Meetings interface and identify controls."
    - "2": "Generate Control Dataset."
    - "3": "GPT Analysis of Accessibility Compliance."
    - "4": "Generate Accessibility Report."
    - "5": "Fire Jira Bug for Non-Compliant Controls."
  - actions:
    - step1 = 'generate control dataset'
    - step2 = 'analyze control acc base on WCAG'

Rule 101: If the scenario contains 'analyze acc', perform the following:
  - Reasoning:
    - "1": "Generate Control Dataset."
    - "2": "GPT Analysis of Accessibility Compliance."
  - actions:
    - step1 = 'generate control dataset'
    - step2 = 'analyze control acc base on WCAG'

Rule 102: If the scenario contains 'please help me to anaylze the controls accessibility', perform the following:
  - Reasoning:
    - "1": "Generate Control Dataset."
    - "2": "Analyze control acc base on WCAG."
  - actions:
    - step1 = 'generate control dataset'
    - step2 = 'analyze control acc base on WCAG'

Rule 103: If the scenario contains 'please help me to anaylze webex meetings controls accessibility', perform the following:
  - Reasoning:
    - "1": "Generate Control Dataset."
    - "2": "Analyze control acc base on WCAG."
  - actions:
    - step1 = 'generate control dataset'
    - step2 = 'analyze control acc base on WCAG'

Rule 104: If the scenario contains 'Initialize screen reader dataset' or 'SR dataset' or 'SR data', perform the following:
  - Reasoning:
    - "1": "Generate Control Dataset."
    - "2": "Analyze control acc base on WCAG."
  - actions:
    - step1 = 'generate control dataset'

Rule 105: If the scenario contains 'Analyze without dataset generation' , perform the following:
  - Reasoning:
    - "1": "Generate Control Dataset."
    - "2": "Analyze control acc base on WCAG."
  - actions:
    - step1 = 'analyze control acc base on WCAG'

Rule 106: If the scenario contains 'Analyze acc i18n' , perform the following:
  - Reasoning:
    - "1": "Analyze control acc i18n"
  - actions:
    - step1 = 'analyze control acc i18n'

Rule 200: If the scenario contains 'Initialize controls image dataset and detect focus ring' or 'collect controls then detect focus ring', perform the following:
  - Reasoning:
    - "1": "Genarate controls image dataset."
    - "2": "Analyze simples."
    - "3": "Analyze control image to detect if valid focus ring in it."
  - actions:
    - step1 = 'genarate controls image dataset'
    - step1 = 'detect focus ring in image with GPT'

Rule 201: If the scenario contains 'detect focus ring' or 'focus ring detection' or 'detect focus ring with gpt', perform the following:
  - Reasoning:
    - "1": "Genarate controls image dataset."
    - "2": "Analyze simples."
    - "3": "Analyze control image to detect if valid focus ring in it."
  - actions:
    - step1 = 'detect focus ring in image with GPT'

Rule 202: If the scenario contains 'Analyze if controls has no focus ring' and 'nonfocused', perform the following:
  - Reasoning:
    - "1": "Genarate controls image dataset."
    - "2": "Analyze simples."
    - "3": "Analyze control image to detect if valid focus ring in it."
  - actions:
    - step1 = 'Analyze control without focus ring in image by GPT'

Rule 300: If the scenario contains 'analyze localization', perform the following:
  - Reasoning:
    - "1": "Analyze localization issues."
  - actions:
    - step1 = 'analyze_localization'

Rule 400: If the scenario contains 'video dedicated model', perform the following:
  - Reasoning:
    - "1": "Run video model for accessibility check."
  - actions:
    - step1 = 'run_dedicated_model(video)'

Rule 401: If the scenario contains 'mute dedicated model', perform the following:
  - Reasoning:
    - "1": "Run mute model for accessibility check."
  - actions:
    - step1 = 'run_dedicated_model(mute)'

Rule 500: If the scenario contains 'run acc automation', perform the following:
  - Reasoning:
    - "1": "Run accessibility automation tests."
  - actions:
    - step1 = 'run_acc_automation'

Rule 600: If the scenario contains 'font size', perform the following:
  - Reasoning:
    - "1": "Follow the WCAG2.2 - SC 2.5.8 standard to analyze the font size with AI."
  - actions:
    - step1 = 'Analyze control font size by GPT base on WCAG'

Rule 1000: If the task is not related to a meeting task, and does not fit the above rules, perform the following:
  - Reasoning:
    - "1": "General task reasoning."
  - actions:
    - step1 = 'general_task'
