
### **Image-Based Localization Compliance Analysis (Perception Phase)**  

To ensure a more structured and efficient evaluation, we will first **analyze localization issues** in the image for only the non-compliant controls. 

**Goal**: Identify localization issues directly from the image, without extracting control coordinates initially.  
**Actions**:  
- **Detect UI text elements** (auto detect).
- Auto-detect language ID (e.g., German (DE), French (FR) and so on) 
- Focus on the topmost window in the image to avoid irrelevant detections.
- If the topmost window is tree or tab structure, need to analyze the content and the label of info text of it.
- **Analyze localization issues**:
    - 1. **Translate**: Check if the text whether translate.
    - 2. **Text Truncation**: 
        - Text characters are visually cut off or missing, **or any part of a text label, checkbox, or other UI control is partially clipped by the container or window edge.** 
        - If available space is insufficient, **the text may wrap to the next line as long as words remain whole** (no mid-word breaks).
        - Ignore selection outlines, blue focus rectangles, or highlight boxes—they do **not** indicate truncation. 
        - If the screenshot shows UI elements that are very close to the window edge, zoom in and check pixel continuity of their borders. Even if the cutoff is 1–2 pixels, report it as `clipped_control`. Treat missing border pixels or incomplete outlines as truncation.
    - 3. **Element Overlap**: Any visible overlap or touching between labels, values, links, icons, checkboxes, inputs, or buttons.
        - Overlap with scrollbars or floating icons also counts if it **obscures content**.
        - **Exception**: Tooltip dialogs, popup menus, or overlay dialogs that appear on top of other UI elements are intentional design patterns and should NOT be flagged as overflow issues.
    - 4. **Clipped Control / Borders**:
        - Flag when any UI control (checkbox, button, input, dropdown) is **partially outside its container** or **visibly cropped by the dialog/window/tab edge**.
        - Include cases where only the control outline or right border is cut by the container.
    - 5. **Localization Accuracy**: Evaluate the correctness of the translation.  

## Hard Exclusions (NEVER flag as issues)
- Selection/focus outlines (blue/gray rectangles), hover/focus effects, shadows, glow.
- Tooltips/popovers intentionally overlaying content.
- Scrollbars, scroll positions, or content below the fold.
- Anti-aliasing artifacts; bold/weight rendering illusions.

## Decision Rules to reduce false positives
- **Truncation**: require visible glyph loss or ellipsis; do not flag "close to edge". 
- **Overlap**: require actual pixel intersection, not tight spacing.  
- **Mistranslation**: prefer high-precision flags; if uncertain, mark `confidence < 0.5`.  
- Prefer fewer but precise issues over speculative ones.

---

### **IMPORTANT INSTRUCTIONS**: 
- The `Image` column **MUST remain exactly as provided**, with the placeholder `[Current Image]`. **DO NOT** modify, replace, or assume its content. 
- **DO NOT** infer or generate image descriptions for the `Image` column. 
- **Only analyze UI text and localization issues**. 
- **Output should be a structured Markdown table**—NO extra explanations, NO additional text. 

---


#### **Expected Output Format**  
The Image column, please keep it as it is, it is my hard code string, **DO NOT** make assumptions.
The result should be returned in a **Markdown table format** for structured presentation, **only table, no others**.
If the suggestion is the same as the issue, just mark it as ✅ Compliant.
**Markdown Table Format:**
| Image | Control Name | Control Name(en_US) | Language: {{Language Id}} | Analysis Result | Compliance | Reference | Suggestion |
| [Current Image] | (Original control text) | (English text) | (Detected language) | (Issues identified) | (✅ Compliant or ❌ Non-compliant) | (WCAG/Standards) | (Suggestions for improvement) |

**Note**: Replace `{{Language Id}}` with the actual detected language (e.g., "German", "French", "Spanish", etc.) during analysis.

**Examples for Reference:**
| Image | Control Name | Control Name(en_US) | Language: {{Language Id}} | Analysis Result | Compliance | Reference | Suggestion |
|-------|--------------|---------------------|---------------------------|-----------------|------------|-----------|------------|
| [Current Image] | Invite and remind | Invite and remind | German | No translate | ❌ Non-compliant | **WCAG 3.1.2 Language of Parts (Level AA)** | The correct German translation of "Invite and remind" could be Einladen und Erinnern |
| [Current Image] | Start | Start | German | No translate | ❌ Non-compliant | **WCAG 3.1.2 Language of Parts (Level AA)** | Please provide a translation |
| [Current Image] | Cyfarfoddydd | Meetings | Welsh | N/A | ✅ Compliant | N/A | N/A |
| [Current Image] | Speichern | Save | German | N/A | ✅ Compliant | N/A | N/A |
| [Current Image] | Gwahoddiad i Alwad Grŵp | Group call notification | Welsh | N/A | ✅ Compliant | N/A | N/A |
| [Current Image] | Dyfeisiau | Devices | Welsh | N/A | ✅ Compliant | N/A | N/A |
| [Current Image] | Sain Clyfar | Smart Audio | Welsh | N/A | ✅ Compliant | N/A | N/A |
| [Current Image] | A I's meeting | A I's meeting | German | N/A | ✅ Compliant | N/A | This is a meeting name (proper noun) by design, and translation is not required |
| [Current Image] | tony's meeting | tony's meeting | German | N/A | ✅ Compliant | N/A | This is a meeting name (proper noun) by design, and translation is not required |
| [Current Image] | Warten auf Beitritt anderer Teilnehmer ... | Waiting for others to join... | German | N/A | ✅ Compliant | N/A | The translation is semantically complete and correctly retains the intended ellipsis ("...") |
| [Current Image] | Gosodiadau Fideo... | Video settings... | Welsh | N/A | ✅ Compliant | N/A | The translation is semantically complete and correctly retains the intended ellipsis ("...") |
| [Current Image] | Lleoliad hunan-olwg... | Adjust self-view... | Welsh | N/A | ✅ Compliant | N/A | The translation is semantically complete and correctly retains the intended ellipsis ("...") |
| [Current Image] | Nur ei... | Only... | German | Text Truncation | ❌ Non-compliant | **WCAG 1.3.1 Info and Relationships (Level A)** | This is semantically incomplete. The text "Nur ei..." appears truncated. Correct wording could not be fully extracted |
| [Current Image] | Slido starten (Umfragen und Frage-und-Antwort | Start Slido (polling and Q&A) | German | Truncated text | ❌ Non-compliant | **WCAG 1.3.1 Info and Relationships (Level A)** | Increase area/make the font size smaller to show the whole text or adjust the solution or replace with a more concise UI |