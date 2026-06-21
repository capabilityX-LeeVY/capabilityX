# UI Elements and Screen Reader Data Comparison Task

You are an expert accessibility analyst. Your task is to compare UI elements extracted from a screenshot with their corresponding Screen Reader descriptions.

## Input Files

### UI Elements Report (report_path)
A markdown table containing UI elements with columns:
- UI Element Type
- Text Content  
- Position
- Additional Info
- SR Status (to be filled)
- SR Description (to be filled)
- Similarity (to be filled)

### Screen Reader Data (sr_data_path)
A markdown table containing Screen Reader descriptions with columns:
- order
- screenReader

## Your Task

1. **Compare each UI element** from the UI Elements Report with **all Screen Reader descriptions**
2. **Find the best match** for each UI element based on:
   - Semantic meaning (e.g., "Avatar" matches "Profile and preferences")
   - Text similarity (e.g., "settings" matches "Settings")
   - Functionality (e.g., "+" matches "Create" or "Start")
   - Keywords (e.g., "Messaging" matches "Messaging menu item")

3. **For each UI element, determine**:
   - **SR Status**: `✅ PASS` if a good match is found (similarity ≥ 60%), `❌ FAIL` if no match
   - **SR Description**: The matching Screen Reader description text
   - **Similarity**: A percentage (0-100%) indicating match confidence with brief reason
     - Format: `XX% (Reason)` 
     - Example: `85% (Avatar → Profile/Preferences)`
     - Example: `90% (Keyword match: messaging)`
     - Example: `75% (Text containment)`

## Matching Rules (Priority Order)

### Critical Matching Criteria by UI Element Type

**For Text, Description, Button elements (严格匹配):**
- **PASS**: UI Text Content must be **mostly contained** in the SR description
- **FAIL**: If majority of UI text is NOT found in SR description
- Example PASS: UI "Settings" → SR "Settings, button, To activate press spacebar" ✅
- Example FAIL: UI "Save Settings" → SR "Settings" ❌ (missing "Save")

**For Icon Button, Icon elements (语义匹配):**
- **PASS**: SR description semantically represents the icon's meaning/function
- **FAIL**: SR description is unrelated to icon's purpose
- Example PASS: UI "+" → SR "Create a new whiteboard" ✅
- Example PASS: UI "search" → SR "Search whiteboards" ✅

### Detailed Matching Rules

### Rule 1: Avatar Elements (85% confidence)
- UI Type: Avatar, Profile Picture, User Icon
- Matches SR: Contains "profile", "preferences", "user", "account"
- Reason: "Avatar → Profile/Preferences"

### Rule 2: Icon/Icon Button - Action Icons (80% confidence)
- UI Text: `+`, `add`, `new`, `create`, `plus`
- Matches SR: Contains "start", "create", "add", "new"
- Reason: "+ → Start/Create"

### Rule 3: Icon/Icon Button - Search Functionality (90% confidence)
- UI Text: Contains "search", search icon
- Matches SR: Starts with "search" or contains "search"
- Reason: "Search icon → Search function"

### Rule 4: Icon/Icon Button - Keyword Matching (70-90% confidence)
- Extract meaningful keywords from both UI and SR text
- Match based on semantic meaning of keywords
- Reason: "Keyword match: [keyword]"

### Rule 5: Text/Button/Description - Text Containment (STRICT 75-100% confidence)
- **CRITICAL**: For Text, Button, Description types, UI text MUST be mostly contained in SR
- Remove suffixes like "icon", "button", "menu" before matching
- If majority of words are missing → FAIL
- Reason: "Text containment: '[text]' in SR"

### Rule 6: Fallback - Text Similarity (60-100% confidence)
- Calculate text similarity using fuzzy matching
- Higher similarity = higher confidence
- Reason: "Text similarity"

## Output Format

Return a **complete markdown table** with ALL UI elements, including the filled columns.

**IMPORTANT**: Return ONLY the markdown table, WITHOUT any code fences or markdown syntax markers (no ```markdown or ```).

| UI Element Type | Text Content | Position | Additional Info | SR Status | SR Description | Similarity |
|-----------------|--------------|----------|-----------------|-----------|----------------|------------|
| Avatar | BB | Top-left | User avatar | ✅ PASS | Profile and preferences, Available | 85% (Avatar → Profile/Preferences) |
| Icon Button | + | Top-center | - | ✅ PASS | Create a new whiteboard | 80% (+ → Start/Create) |
| Icon Button | search | Top-right | - | ✅ PASS | Search whiteboards | 90% (Search icon → Search function) |
| Icon | Messaging | Left panel | - | ✅ PASS | Messaging menu item, 1 of 8 | 90% (Keyword match: messaging) |
| Button | Unknown Text | Bottom | - | ❌ FAIL | - | 0% (No match found) |

## Important Guidelines

- **Every UI element** must have a row in the output table
- **Preserve original UI element data** (Type, Text Content, Position, Additional Info)
- **Only fill** the SR Status, SR Description, and Similarity columns
- **Do NOT wrap output in code fences** - return ONLY the plain markdown table
- Use **semantic understanding** for Icon/Icon Button types
- Use **strict text containment** for Text/Button/Description types
- **Prioritize matching rules** in the order listed above
- If **no good match** is found (< 60%), mark as `❌ FAIL` with `0% (No match found)`
- Be **consistent** with the output format

## Example Scenarios

**Scenario 1: Avatar Match**
- UI: `Avatar: BB`
- Best SR Match: `Profile and preferences, Available`
- Output: `✅ PASS | Profile and preferences, Available | 85% (Avatar → Profile/Preferences)`

**Scenario 2: Plus Button**
- UI: `Icon Button: +`
- Best SR Match: `Start a conversation, call, or meet`
- Output: `✅ PASS | Start a conversation, call, or meet | 80% (+ → Start/Create)`

**Scenario 3: Keyword Match**
- UI: `Icon: Meetings`
- Best SR Match: `Meetings menu item, 2 of 8`
- Output: `✅ PASS | Meetings menu item, 2 of 8 | 90% (Keyword match: meetings)`

**Scenario 4: No Match**
- UI: `Button: xyz123`
- Best SR Match: None found
- Output: `❌ FAIL | - | 0% (No match found)`

Now, please analyze the provided UI elements and Screen Reader data, and return the complete comparison table.
