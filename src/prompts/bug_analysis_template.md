# Bug Classification and Accessibility Analysis

## Analysis Task
Please analyze the following bug data and classify it by meeting module and accessibility category.

## Input Data
- **Bug Description**: {column1_data}
- **Additional Details**: {column2_data}

## Classification Requirements
Based on the provided bug information, please classify the bug into the following categories:

### 1. Meeting Module Classification
Identify which Webex meeting module this bug belongs to:
- **Settings**: Configuration, preferences, account settings
- **Meeting Info**: Meeting link, meeting number, topic, copy meeting link
- **Audio**: Microphone, speakers, audio quality, mute/unmute
- **Video**: Camera, video quality, video sharing, backgrounds
- **Share**: Screen sharing, application sharing, whiteboard
- **Chat**: Text messaging, file sharing, chat features
- **Participants**: Participant list, roles, permissions, lobby
- **Apps**: The in meeting app panel, and apps like Miro
- **Recording**: Meeting recording, playback, storage
- **Reactions**: In meeting send reactions
- **Breakout Sessions**: Breakout Sessions creation, management, navigation
- **Sign language**: Sign language session start, end
- **Slido**: Polls, Q&A
- **General UI**: Overall interface, navigation, layout
- **Other**: If none of the above categories fit

### 2. Accessibility (ACC) Category Classification
Identify which accessibility category this bug falls under based on the following areas:

- **Writing**: Font, Character height, Icon, Image polarity
- **Color**: Color contrast, Color information, Color convention, Use of color
- **Scaling**: Adjustment via Zoom, Adjusting window size, Font graphics
- **Keyboard Operation**: Visible focus / Keyboard operation / Standard actions, Series / Keyboard shortcuts
- **Visual & Acoustic Barriers**: High contrast, Optical & acoustic effects
- **Screenreader**: Screen reader compatibility, Screen reader test, Screen reader for static text/label
- **Language**: Language settings, Localization, Translation
- **User Guidance**: Navigation elements / User control / Error prevention
- **Layout & Design**: Mask layout / Design of the form / UI element / Error message
- **Usability**: Self-help / Input assistance / Input verification / Other points
- **Braille**: Braille display output, Braille input keyboard, Braille translation accuracy, Refreshable Braille device compatibility

### 3. WCAG Standard Identification
Identify which WCAG 2.2 standards this bug violates. Please reference the appropriate WCAG 2.2 success criteria (Level A, AA, or AAA) that are not met.

## Expected Output Format
Please structure your response as follows:

```json
{
  "meeting_module": "Settings|Meeting info|Audio|Video|Share|Chat|Apps|Participants|Recording|Breakout Sessions|Reactions|Sign language|Slido|General UI|Other",
  
  "accessibility_category": "Writing|Color|Scaling|Keyboard Operation|Visual & Acoustic Barriers|Screenreader|Language|User Guidance|Layout & Design|Usability|Braille",
  
  "accessibility_subcategory": "Specific subcategory from the ACC area (e.g., 'Font', 'Color contrast', 'Visible focus', etc.)",
  
  "wcag_standard": "WCAG 2.2 AA 1.3.1, WCAG 2.2 AA 2.4.3",
  
  "complete_analysis": {
    "meeting_module": "Settings|Meeting info|Audio|Video|Share|Chat|Apps|Participants|Recording|Breakout Sessions|Reactions|Sign language|Slido|General UI|Other",
    "accessibility_category": "Writing|Color|Scaling|Keyboard Operation|Visual & Acoustic Barriers|Screenreader|Language|User Guidance|Layout & Design|Usability|Braille",
    "accessibility_subcategory": "Font|Character height|Icon|Image polarity|Color contrast|Color information|Color convention|Use of color|Adjustment via Zoom|Adjusting window size|Font graphics|Visible focus / Keyboard operation / Standard actions|Series / Keyboard shortcuts|High contrast|Optical & acoustic effects|Screen reader compatibility|Screen reader test|Screen reader for static text, label|Language|Navigation elements / User control / Error prevention|Mask layout / Design of the form / UI element / Error message|Self-help / Input assistance / Input verification / Other points|Braille display output|Braille input keyboard|Braille translation accuracy|Refreshable Braille device compatibility",
    "affected_user_groups": ["Screen reader users", "Keyboard-only users", "Users with motor disabilities", "etc."],
    "wcag_guidelines": ["WCAG 2.2 AA 1.3.1", "WCAG 2.2 AA 2.4.3", "etc."],
    "impact_description": "Description of how this affects users with disabilities"
  }
}
```

## Additional Context
- Focus on accurate module and accessibility category classification
- **Identify specific WCAG 2.2 standards that are violated** - this is crucial for compliance
- Consider the specific impact on users with disabilities
- Reference relevant WCAG 2.2 guidelines where applicable
- Provide confidence levels for your classifications
- Consider both obvious and subtle accessibility issues
- For wcag_standard field, list the most relevant WCAG guidelines as comma-separated values (e.g., "WCAG 2.2 AA 2.4.3, WCAG 2.2 AA 4.1.2")
