create
name: create_start_a_calling_with_vbg
account: bwc.sha+138
area: calling
steps:
  - 1: start a call, dial_number: "8339"
  - 2: answer a call, agent_node: "calling_agent_8339"
  - 3: AI verify the current state and call success