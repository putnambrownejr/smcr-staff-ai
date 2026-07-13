"""Login auto-start target: start SMCR Staff AI silently, no browser.

Installed as a shortcut in the Windows Startup folder by
scripts/create_desktop_shortcut.ps1 -Autostart -- so the server is already
warm by the time you click the desktop icon. Deliberately does not open a
browser tab; being logged in should not pop windows you didn't ask for.
"""

from _smcr_launch_lib import ensure_server_running

if __name__ == "__main__":
    ensure_server_running(open_browser=False)
