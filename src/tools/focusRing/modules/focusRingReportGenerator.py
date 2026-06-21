#Detects the focus ring in the images by openCV, and generates a report in HTML format.

from acc.handler import accFocusRing

output_html_path = "src/report/focus_ring/focusRing_results.html"

pre_controls_image_path = 'src/datasets/img/local/focus_ring/preControls'
pre_controls_image_column = "Pre-controls images result"

focus_controls_image_path = 'src/datasets/img/local/focus_ring/currentControls'
focus_controls_image_column = "Focus controls images result"

def getFocusRingReport():
      pre_controls_results = accFocusRing.getFocusRing(pre_controls_image_path)
      accFocusRing.focusRingResultToHTML(pre_controls_results, pre_controls_image_column, output_html_path)
      focus_controls_results = accFocusRing.getFocusRing(focus_controls_image_path)
      accFocusRing.focusRingResultToHTML(focus_controls_results, focus_controls_image_column, output_html_path)