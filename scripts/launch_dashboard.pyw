"""Desktop-shortcut target: start SMCR Staff AI if needed, then open it.

Run via pythonw.exe (no console window). Installed as a Desktop shortcut by
scripts/create_desktop_shortcut.ps1 -- see that script, or ask your AI
assistant to "make me a desktop shortcut for this."
"""

from _smcr_launch_lib import ensure_server_running

if __name__ == "__main__":
    ensure_server_running(open_browser=True)
