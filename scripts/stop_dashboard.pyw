"""Emergency fallback: stop the running SMCR Staff AI server from outside it.

The normal way to shut down is the power button inside the dashboard's top
bar (POST /dashboard/shutdown). Keep this script for the case where the
dashboard itself is unreachable (wedged server, broken page): run it via the
repo venv's pythonw.exe, no console window needed. It works whether the
server was started by the desktop launcher, the Startup-folder auto-start,
or an AI assistant running start.bat.
"""

from _smcr_launch_lib import stop_server

if __name__ == "__main__":
    stop_server()
