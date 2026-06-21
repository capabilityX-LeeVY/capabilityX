# UI Elements Extraction Prompt Template

Analyze this UI screenshot and extract ALL UI elements (both with text and icon-only).

IMPORTANT: Extract EVERY visible UI element as a COMPLETE unit.

UI ELEMENT IDENTIFICATION:
1. **Text-based elements**: Buttons, links, labels with text
2. **Icon-only elements**: Buttons with only icons (+, ×, search, menu, etc.)
3. **Composite elements**: Text + icon combinations (must be ONE row)
4. **Input fields**: Text fields with labels, placeholders, and shortcuts
5. **Informational text**: Descriptions, help text, instructions, empty state messages
6. **Status messages**: Notifications, alerts, status indicators
7. **Avatar/Profile elements**: User avatars with initials or profile pictures

⚠️ **SPECIAL ATTENTION - AVATARS/USER INITIALS**:
- **MUST look for AVATAR elements** (usually circular or rounded square)
- Avatars often contain **USER INITIALS** (e.g., "BB" for "bts1 bts", "JD" for "John Doe")
- Common locations: Top-left corner, next to user name, in headers, profile sections
- Avatar text is usually **1-3 capital letters** in a colored circle/square
- **Examples**: "BB", "JD", "AB", "XY"
- Even if small or subtle, **MUST extract** the initials/letters inside avatars!

⚠️ **SPECIAL ATTENTION - LOW CONTRAST TEXT**:
- **MUST carefully look for text with LOW CONTRAST** (light gray, faded, dim text)
- These are often secondary labels, captions, metadata, or disabled states
- Common locations: near icons, below headings, in sidebars, status bars
- **Examples**: "Call settings", "Last updated", "Not available", timestamps
- **DO NOT SKIP** low contrast text - it's just as important as high contrast text!

CRITICAL FORMATTING RULES:

1. **INPUT FIELDS WITH SHORTCUTS**:
   - Combine the field text AND shortcut in Text Content
   - Format: 'Field text Shortcut'
   - Example: If you see search field 'Search, meet, and call' with 'Ctrl+F'
     Text Content: 'Search, meet, and call Ctrl+F'
     Additional Info: Only note if has icon like 'Has search icon'

2. **ICON-ONLY BUTTONS**:
   - Text Content: Just the icon name/function (NO 'icon' suffix)
   - Examples:
     * '+' button → Text Content: '+'
     * Search icon → Text Content: 'search'
     * Calendar icon → Text Content: 'calendar'
     * Settings icon → Text Content: 'settings'
   - Additional Info: Leave as '-' (no need to repeat 'Icon button')

3. **TEXT + ICON BUTTONS**:
   - Text Content: The text only (remove icon symbol)
   - Additional Info: Note the icon
   - Example: '+ Create a new whiteboard'
     Text Content: 'Create a new whiteboard'
     Additional Info: 'Has + icon'

4. **DROPDOWN INDICATORS**:
   - Text Content: The text without ▼
   - Additional Info: 'Dropdown'
   - Example: 'Sort by: Last edited ▼'
     Text Content: 'Sort by: Last edited'
     Additional Info: 'Dropdown'

5. **DESCRIPTION TEXT / HELP TEXT**:
   - Type: 'Description' or 'Help Text'
   - Text Content: Full description text (can be long, keep it on one line)
   - Examples:
     * Empty state message: "Find all of your whiteboards here, including..."
     * Help text: "Use a whiteboard to write out and sketch ideas..."
     * Instructions: "Click here to get started..."
   - Additional Info: Context like 'Empty state', 'Help message', or '-'

6. **AVATAR / USER INITIALS**:
   - Type: 'Avatar'
   - Text Content: The initials/letters visible inside the avatar (e.g., 'BB', 'JD', 'AB')
   - Examples:
     * User 'bts1 bts' → Avatar shows 'BB' → Text Content: 'BB'
     * User 'John Doe' → Avatar shows 'JD' → Text Content: 'JD'
     * User 'Alice Brown' → Avatar shows 'AB' → Text Content: 'AB'
   - Additional Info: 'User avatar' or 'Profile picture with initials'
   - NOTE: Avatar is usually a small circular or rounded square element with 1-3 capital letters

COMPLETE EXAMPLES:

| UI Element Type | Text Content | Position | Additional Info |
|-----------------|-------------|----------|-----------------|
| Text Field | Search, meet, and call Ctrl+F | Top-center | Has search icon |
| Icon Button | + | Top-right | - |
| Button | Create a new whiteboard | Middle-center | Has + icon |
| Dropdown | Sort by: Last edited | Top-right | Dropdown |
| Icon Button | search | Top-right | - |
| Icon Button | calendar | Left-side | - |
| Icon Button | settings | Bottom-left | - |
| Tab | All boards | Top-left | Selected |
| Link | Open Settings | Bottom-left | - |
| Label | Call settings | Bottom-left | Low contrast/faded text |
| Avatar | BB | Top-left | User avatar with initials |
| Description | Find all of your whiteboards here, including whiteboards that are shared with you or that are from your spaces. Use a whiteboard to write out and sketch ideas with others. | Middle-center | Empty state message |

UI ELEMENT TYPES TO INCLUDE:
- **Interactive**: Button, Icon Button, Text Field, Link, Tab, Dropdown, Checkbox, Radio Button
- **Informational**: Label, Title, Description, Help Text, Status, Notification
- **Structural**: Heading, Subheading, Section Title
- **User Identity**: Avatar (with user initials or profile picture)

WHAT TO EXTRACT:
✅ ALL interactive elements (buttons, links, inputs)
✅ ALL text labels and titles
✅ ALL descriptions and help text (even if long)
✅ ALL status messages and notifications
✅ ALL icon-only buttons
✅ ALL tabs and navigation items
✅ Empty state messages and instructions
✅ **LOW CONTRAST TEXT** (light gray, faded, or dim text - MUST INCLUDE!)
✅ Secondary labels, captions, metadata, timestamps
✅ Text near icons or in status bars
✅ **AVATAR/USER INITIALS** (e.g., 'BB', 'JD' in circular/rounded elements - MUST INCLUDE!)
✅ Profile pictures with visible letters/initials

OUTPUT FORMAT:
Return ONLY a markdown table with these exact columns:
| UI Element Type | Text Content | Position | Additional Info |

Rules:
- NO explanations before or after the table
- NO line breaks in Text Content (keep long text on ONE line)
- Position: Top-left, Top-center, Top-right, Middle-left, Middle-center, Middle-right, Bottom-left, Bottom-center, Bottom-right
- Additional Info: Use '-' when nothing special to note
- MUST include ALL visible text, including descriptions and help text
- MUST include ALL visible UI elements, no omissions
- **CRITICAL**: Include low contrast/faded/light gray text (e.g., "Call settings", secondary labels)
- If text is hard to read due to low contrast, look MORE carefully - don't skip it!
- **CRITICAL**: Include AVATAR/USER INITIALS (e.g., "BB", "JD" in circular elements) - these are usually small but important!
- Avatars are often in corners or near user name - look for circular/rounded elements with 1-3 capital letters
