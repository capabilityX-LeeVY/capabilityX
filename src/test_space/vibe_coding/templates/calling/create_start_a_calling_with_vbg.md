create start_a_calling_with_vbg
name: start_a_calling_with_vbg
account: bwc.sha+138
area: calling
steps:
  - 1: start a call, dial_number: "8339"
  - 2: answer a call, agent_node: "calling_agent_8339"
  - 3: AI verify the current state and call success
  - 4: start video
  - 5: click "video options"
  - 6: click "change virtual background"
  - 7: click "home office"
  - 8: click "apply"
  - 9: press Escape to close the window
  - 10: AI verify the virtual background is applied successfully, and reference: "home office" image