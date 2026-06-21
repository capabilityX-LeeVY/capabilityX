
# test case

## sample 1: add test case with full workflow

/add-test-case Create "Show in floating window" test case.
account: allianz8
file directory: acc_regression meeting video
pre_conditions: start meeting, open video settings
steps:

  1. enable/check "Show in floating window"
  2. click save button, AI check prompt: "Verify that the Show in floating window effect is visually applied to the video. Output format: ✅Success or ❌Failed", reference: show_in_floating_window.jpg
post_conditions: end meeting, sign out

## sample 2: add test case with partial workflow and custom steps

/add-test-case-in-meetings Create "Show in floating window" test case

steps:
    1. open video settings
    2. enable/check "Show in floating window"
    3. save it and AI check prompt: "Verify that the Show in floating window effect is visually applied to the video. Output format: ✅Success or ❌Failed", reference: show_in_floating_window.jpg

## sample 3: join meeting

/add-test-case-join-meetings Create "guest join meeting" test case.

steps:
    1. guest join a meeting, meeting_link: <binbiwan@cisco.webex.com>, name: "tony"

## sample 4: join meeting and auto run test case

/add-test-case-join-meetings Create "guest join meeting" test case.

steps:
    1. guest join a meeting, meeting_link: <binbiwan@cisco.webex.com>, name: "tony"

after create the test case, run it automatically.

## sample 5: signed-in user join meeting (4-step composite workflow)

/add-test-case-join-meetings Create "user join meeting" test case.

steps:
    1. user allianz8 join a meeting with link, meeting_link: <binbiwan@cisco.webex.com>
