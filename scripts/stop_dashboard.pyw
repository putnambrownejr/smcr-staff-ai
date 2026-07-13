"""Desktop-shortcut target: stop the running SMCR Staff AI server.

Run via pythonw.exe (no console window). Works whether the server was
started by this launcher, by the Startup-folder auto-start, or by an AI
assistant running start.bat.
"""

from _smcr_launch_lib import stop_server

if __name__ == "__main__":
    stop_server()
