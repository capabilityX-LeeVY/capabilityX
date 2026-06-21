create test case for turn on calling dock
name: turn_on_calling_dock
account: bwc.sha+138
area: calling
check_points: keyboard navigation, focus ring, screen reader
preconditions: uninstall, install, sign in, click emergency calling OK button, close AI Assistant, open calling settings, open call preferences, open calling dock
steps:
  - 1: click "Turn on Calling dock"
  - 2: capture fullscreen, then AI verify the calling dock is turned on successfully, and you can see the "calling dock" dialog displayed on the right side of the app