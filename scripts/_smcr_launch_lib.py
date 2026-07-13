"""Shared logic for the desktop-shortcut launcher scripts (Windows only).

Used by launch_dashboard.pyw (open-on-click), start_server_hidden.pyw (silent
login auto-start), and stop_dashboard.pyw. Deliberately standalone -- it does
not import the `app` package, so it works even before `uv sync` has been run
once (in which case it shows a plain-language dialog instead of a traceback).

Not part of the running app; only touched by a user double-clicking a
desktop/Startup-folder shortcut, so it talks in message boxes, not stdout.
"""

from __future__ import annotations

import ctypes
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
VENV_PYTHON = REPO_ROOT / ".venv" / "Scripts" / "python.exe"

APP_TITLE = "SMCR Staff AI"
MB_OK = 0x0
MB_ICONINFORMATION = 0x40
MB_ICONERROR = 0x10
POLL_SECONDS = 0.5
POLL_ATTEMPTS = 60  # 30s total, matching the patience of a normal app launch

# These scripts run under pythonw.exe (no console). A child console program
# (netstat, taskkill, powershell) would otherwise flash a console window open.
_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)

# Health checks must hit 127.0.0.1 directly. A plain urlopen() honors
# http_proxy/https_proxy environment variables -- common on government
# machines -- and a proxy will not route to this machine's loopback.
_DIRECT_OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))


def _local_state_root() -> Path:
    # Mirrors default_local_state_root() in app/core/config.py, duplicated
    # here (not imported) so this launcher works even without `uv sync`.
    explicit_home = os.environ.get("SMCR_STAFF_AI_HOME")
    if explicit_home:
        return Path(explicit_home).expanduser()
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        return Path(local_app_data) / "smcr-staff-ai"
    return Path.home() / "AppData" / "Local" / "smcr-staff-ai"


LAUNCHER_DIR = _local_state_root() / "launcher"
PID_FILE = LAUNCHER_DIR / "server.pid"
LOG_FILE = LAUNCHER_DIR / "server.log"


def get_port() -> int:
    raw = os.environ.get("SMCR_PORT", "8000")
    try:
        port = int(raw)
        if 1 <= port <= 65535:
            return port
    except ValueError:
        pass
    show_message(
        f"SMCR_PORT={raw!r} is not a valid port; using 8000 instead.",
        icon=MB_ICONINFORMATION,
    )
    return 8000


def health_url(port: int) -> str:
    return f"http://127.0.0.1:{port}/health"


def dashboard_url(port: int) -> str:
    return f"http://127.0.0.1:{port}/dashboard"


def show_message(text: str, *, icon: int = MB_ICONINFORMATION) -> None:
    if sys.platform != "win32":
        print(text)
        return
    ctypes.windll.user32.MessageBoxW(0, text, APP_TITLE, MB_OK | icon)


def is_healthy(port: int) -> bool:
    try:
        with _DIRECT_OPENER.open(health_url(port), timeout=1.5) as resp:
            return resp.status == 200
    except (urllib.error.URLError, OSError, TimeoutError):
        return False


def _spawn_server(port: int) -> subprocess.Popen | None:
    if not VENV_PYTHON.exists():
        show_message(
            "SMCR Staff AI isn't set up yet on this machine.\n\n"
            "Open the smcr-staff-ai folder and run start.bat once to finish "
            "setup, then try this shortcut again.",
            icon=MB_ICONERROR,
        )
        return None

    LAUNCHER_DIR.mkdir(parents=True, exist_ok=True)
    creationflags = _NO_WINDOW | getattr(subprocess, "DETACHED_PROCESS", 0)
    with open(LOG_FILE, "a", encoding="utf-8") as log:
        log.write(f"\n--- launched {time.strftime('%Y-%m-%d %H:%M:%S')} on port {port} ---\n")
        log.flush()
        process = subprocess.Popen(
            [str(VENV_PYTHON), "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", str(port)],
            cwd=str(REPO_ROOT),
            stdout=log,
            stderr=subprocess.STDOUT,
            creationflags=creationflags,
            close_fds=True,
        )
    PID_FILE.write_text(str(process.pid), encoding="utf-8")
    return process


def ensure_server_running(*, open_browser: bool) -> bool:
    """Start the server if needed, wait for it, optionally open the dashboard.

    Returns True if the server ended up healthy, False otherwise (a message
    box has already explained why in the False case).
    """
    port = get_port()
    if is_healthy(port):
        if open_browser:
            webbrowser.open(dashboard_url(port))
        return True

    process = _spawn_server(port)
    if process is None:
        return False

    for _ in range(POLL_ATTEMPTS):
        # Health first: if two launches raced (double double-click, or login
        # auto-start finishing just as the user clicks the icon), the loser's
        # uvicorn dies on port-bind -- but the dashboard IS up, which is what
        # the user actually asked for.
        if is_healthy(port):
            if open_browser:
                webbrowser.open(dashboard_url(port))
            return True
        if process.poll() is not None:
            time.sleep(POLL_SECONDS)
            if is_healthy(port):
                if open_browser:
                    webbrowser.open(dashboard_url(port))
                return True
            show_message(
                "SMCR Staff AI stopped unexpectedly while starting.\n\n"
                f"Check the log for details:\n{LOG_FILE}",
                icon=MB_ICONERROR,
            )
            return False
        time.sleep(POLL_SECONDS)

    show_message(
        "SMCR Staff AI didn't start within 30 seconds.\n\n"
        f"Check the log for details:\n{LOG_FILE}",
        icon=MB_ICONERROR,
    )
    return False


def _pid_from_port(port: int) -> int | None:
    """Find the PID listening on `port` via netstat.

    Authoritative for "who actually holds the port" -- unlike the PID file,
    which can go stale (server restarted some other way, PID reused).
    """
    try:
        result = subprocess.run(
            ["netstat", "-ano"], capture_output=True, text=True, timeout=5, creationflags=_NO_WINDOW
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    needle = f"127.0.0.1:{port}"
    for line in result.stdout.splitlines():
        parts = line.split()
        if len(parts) >= 5 and parts[0] == "TCP" and parts[1] == needle and parts[3] == "LISTENING":
            try:
                return int(parts[4])
            except ValueError:
                return None
    return None


def _pid_from_file() -> int | None:
    if not PID_FILE.exists():
        return None
    try:
        return int(PID_FILE.read_text(encoding="utf-8").strip())
    except ValueError:
        return None


def _process_table() -> dict[int, tuple[int | None, str, str]]:
    """pid -> (parent_pid, executable_path, command_line) for every process."""
    try:
        result = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                'Get-CimInstance Win32_Process | ForEach-Object { "$($_.ProcessId)|$($_.ParentProcessId)|$($_.ExecutablePath)|$($_.CommandLine)" }',
            ],
            capture_output=True,
            text=True,
            timeout=15,
            creationflags=_NO_WINDOW,
        )
    except (OSError, subprocess.TimeoutExpired):
        return {}
    table: dict[int, tuple[int | None, str, str]] = {}
    for line in result.stdout.splitlines():
        # Command line goes last because it can itself contain "|"; the pid,
        # ppid, and exe path fields cannot.
        pid_raw, _, rest = line.partition("|")
        ppid_raw, _, rest = rest.partition("|")
        exe, _, cmdline = rest.partition("|")
        try:
            pid = int(pid_raw)
        except ValueError:
            continue
        try:
            ppid: int | None = int(ppid_raw)
        except ValueError:
            ppid = None
        table[pid] = (ppid, exe.strip(), cmdline.strip())
    return table


def _is_our_server(pid: int, table: dict[int, tuple[int | None, str, str]]) -> bool:
    """True when the process is part of this repo's server.

    Judged by COMMAND LINE, not executable path: uv-created venvs use a
    trampoline, so the interpreter that actually binds the port reports the
    base Python install (outside the repo) as its executable -- but its
    command line still carries the repo's venv path and/or the app module.
    """
    info = table.get(pid)
    if info is None:
        return False
    cmdline = info[2].lower()
    if not cmdline:
        return False
    repo_marker = str(REPO_ROOT).lower()
    return repo_marker in cmdline or ("uvicorn" in cmdline and "app.main:app" in cmdline)


def _root_server_pid(pid: int, table: dict[int, tuple[int | None, str, str]]) -> int:
    """Climb from the port-holding process to the root of its server family.

    `start.bat` runs `uv run uvicorn ... --reload`: uv.exe -> venv python
    (reload supervisor) -> venv python (the process that binds the port).
    Killing only the bound child makes the supervisor restart it, so Stop
    must target the top of that chain. Climb while the parent is also part
    of this repo's server (venv python, or the uv.exe that launched it);
    stop at anything else (explorer, cmd, terminal, an AI assistant).
    """
    def is_server_family(candidate: int) -> bool:
        info = table.get(candidate)
        if info is None:
            return False
        exe = info[1].lower()
        if exe.endswith(os.sep + "uv.exe"):
            return True
        return _is_our_server(candidate, table)

    current = pid
    for _ in range(10):  # defensive bound; real chains are 2-3 deep
        info = table.get(current)
        parent = info[0] if info else None
        if parent and parent != current and is_server_family(parent):
            current = parent
        else:
            break
    return current


def stop_server() -> None:
    port = get_port()
    if not is_healthy(port):
        PID_FILE.unlink(missing_ok=True)
        show_message("SMCR Staff AI isn't running.")
        return

    pid = _pid_from_port(port) or _pid_from_file()
    if pid is None:
        show_message(
            "SMCR Staff AI is running, but this shortcut couldn't identify its "
            "process to stop it. Close its terminal window if you started it "
            "with start.bat, or restart your computer to clear it."
        )
        return

    table = _process_table()
    if table and not _is_our_server(pid, table):
        show_message(
            f"Something is answering on port {port}, but it doesn't look like "
            "SMCR Staff AI from this folder. Nothing was stopped.",
            icon=MB_ICONERROR,
        )
        return
    target = _root_server_pid(pid, table) if table else pid

    subprocess.run(
        ["taskkill", "/PID", str(target), "/T", "/F"], capture_output=True, creationflags=_NO_WINDOW
    )
    PID_FILE.unlink(missing_ok=True)
    # A --reload supervisor that survived would resurrect the server within a
    # couple of seconds; poll long enough to catch that instead of declaring
    # victory on a momentary gap.
    for _ in range(6):
        time.sleep(0.5)
        if is_healthy(port):
            break
    if is_healthy(port):
        show_message("Could not stop SMCR Staff AI. Try again, or restart your computer.", icon=MB_ICONERROR)
    else:
        show_message("SMCR Staff AI stopped.")
