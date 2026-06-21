# Simple Text Extraction Prompt Template

Extract ONLY the literal visible text painted on this UI screenshot, preserving the
original top-to-bottom / left-to-right reading order.

INCLUDE:
1. All readable text, labels, headings, body copy, button captions, link text,
   placeholder text, and any other actual characters rendered on screen.
2. Preserve hierarchy and reading order (headings before body, etc.).

EXCLUDE — do NOT emit any of the following:
1. Icons, glyphs, or pictograms (e.g. warning triangles, info circles, app
   logos, status dots). Do NOT describe them with markdown image syntax such as
   `![Warning Icon]`, `![icon](...)`, or any `![...]` form. Skip them entirely.
2. Decorative shapes, borders, dividers, or background graphics.
3. Any meta-commentary about the screenshot itself — for example
   `*Layout and hierarchy preserved...*`, `*Original dialog shown above*`,
   "The image shows...", or any italic / parenthetical narrative footer.
4. Code fences (```), horizontal rules (`---`), or other markdown scaffolding
   that is not actually visible text in the image.
5. Quotation marks, brackets, or formatting characters that you add yourself
   to wrap text — output the text as it literally appears.

FORMATTING:
- You MAY use `**bold**` for visually-bold text and plain text for everything
  else. Do NOT add italic narrative or descriptive captions.
- One logical line per visible line of text. Use blank lines to separate
  visually distinct groups (heading vs. body vs. button row).

OUTPUT:
Return ONLY the transcribed visible text. No preamble, no summary, no closing
remarks, no code fence wrapping the whole response.
