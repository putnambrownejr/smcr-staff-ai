import os
import socket
import subprocess
from pathlib import Path

import pytest
from _pytest.capture import CaptureFixture
from _pytest.monkeypatch import MonkeyPatch

from app.startup_preflight import (
    EXIT_AVAILABLE,
    EXIT_INVALID_PORT,
    EXIT_OCCUPIED,
    LOOPBACK_HOST,
    main,
    parse_port,
)

REPO_ROOT = Path(__file__).resolve().parents[1]


def _run_launcher(
    tmp_path: Path,
    *,
    port: str | None,
    preflight_exit: int = 0,
) -> tuple[subprocess.CompletedProcess[str], list[str]]:
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    log_path = tmp_path / "uv.log"
    fake_uv = fake_bin / "uv"
    fake_uv.write_text(
        "#!/usr/bin/env sh\n"
        'printf \'%s\\n\' "$*" >> "$UV_LOG"\n'
        'if [ "$1" = "run" ] && [ "$2" = "python" ] '
        '&& [ "$3" = "-m" ] && [ "$4" = "app.startup_preflight" ]; then\n'
        '  exit "$PREFLIGHT_EXIT"\n'
        "fi\n"
        "exit 0\n",
        encoding="utf-8",
    )
    fake_uv.chmod(0o755)
    command = [str(REPO_ROOT / "start.sh")]

    environment = os.environ.copy()
    environment["PATH"] = f"{fake_bin}{os.pathsep}{environment.get('PATH', '')}"
    environment["UV_LOG"] = str(log_path)
    environment["PREFLIGHT_EXIT"] = str(preflight_exit)
    if port is None:
        environment.pop("SMCR_PORT", None)
    else:
        environment["SMCR_PORT"] = port

    completed = subprocess.run(
        command,
        cwd=REPO_ROOT,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    calls = [line.strip().replace('"', "") for line in log_path.read_text(encoding="utf-8").splitlines()]
    return completed, calls


def test_occupied_port_reports_checkout_and_leaves_listener_running(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
    capsys: CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)
    with socket.create_server((LOOPBACK_HOST, 0)) as listener:
        port = int(listener.getsockname()[1])

        result = main(["--port", str(port)])

        assert result == EXIT_OCCUPIED
        assert listener.fileno() >= 0

    captured = capsys.readouterr()
    assert captured.out == ""
    assert f"local port {port} is already in use" in captured.err
    assert f"Current checkout: {tmp_path.resolve()}" in captured.err
    assert "Another SMCR Staff AI checkout may already be running" in captured.err
    assert "SMCR_PORT" in captured.err
    assert 'set "SMCR_PORT=8001" && start.bat' in captured.err


def test_available_port_exits_silently(capsys: CaptureFixture[str]) -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as reservation:
        reservation.bind((LOOPBACK_HOST, 0))
        port = int(reservation.getsockname()[1])

    result = main(["--port", str(port)])

    assert result == EXIT_AVAILABLE
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""


@pytest.mark.parametrize(
    ("value", "expected"),
    [("1", 1), ("65535", 65_535), ("08000", 8_000)],
)
def test_valid_port_values_are_parsed_as_decimal(value: str, expected: int) -> None:
    assert parse_port(value) == expected


@pytest.mark.skipif(os.name == "nt", reason="POSIX launcher behavior is exercised in Linux CI.")
def test_posix_launcher_uses_configured_smcr_port(tmp_path: Path) -> None:
    completed, calls = _run_launcher(tmp_path, port="8123")

    assert completed.returncode == 0, completed.stderr
    assert "http://localhost:8123" in completed.stdout
    assert calls == [
        "sync --frozen",
        "run python -m app.startup_preflight --port 8123",
        "run uvicorn app.main:app --host 127.0.0.1 --port 8123 --reload",
    ]


@pytest.mark.skipif(os.name == "nt", reason="POSIX launcher behavior is exercised in Linux CI.")
def test_posix_launcher_defaults_to_port_8000(tmp_path: Path) -> None:
    completed, calls = _run_launcher(tmp_path, port=None)

    assert completed.returncode == 0, completed.stderr
    assert "http://localhost:8000" in completed.stdout
    assert calls == [
        "sync --frozen",
        "run python -m app.startup_preflight --port 8000",
        "run uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload",
    ]


@pytest.mark.skipif(os.name == "nt", reason="POSIX launcher behavior is exercised in Linux CI.")
def test_posix_launcher_does_not_start_uvicorn_when_preflight_fails(tmp_path: Path) -> None:
    completed, calls = _run_launcher(tmp_path, port="8123", preflight_exit=1)

    assert completed.returncode != 0
    assert calls == [
        "sync --frozen",
        "run python -m app.startup_preflight --port 8123",
    ]


@pytest.mark.parametrize(
    ("launcher", "expected_fragments"),
    [
        (
            "start.bat",
            [
                'if not defined SMCR_PORT set "SMCR_PORT=8000"',
                "uv sync --frozen\nif errorlevel 1 exit /b 1",
                'uv run python -m app.startup_preflight --port "%SMCR_PORT%"',
                "if errorlevel 1 exit /b 1",
                "http://localhost:%SMCR_PORT%",
                'uv run uvicorn app.main:app --host 127.0.0.1 --port "%SMCR_PORT%" --reload',
            ],
        ),
        (
            "start.sh",
            [
                'SMCR_PORT="${SMCR_PORT:-8000}"',
                'if ! uv run python -m app.startup_preflight --port "$SMCR_PORT"; then',
                "http://localhost:${SMCR_PORT}",
                'exec uv run uvicorn app.main:app --host 127.0.0.1 --port "$SMCR_PORT" --reload',
            ],
        ),
    ],
)
def test_launchers_use_smcr_port_for_preflight_url_and_uvicorn(
    launcher: str,
    expected_fragments: list[str],
) -> None:
    script = (REPO_ROOT / launcher).read_text(encoding="utf-8")

    for fragment in expected_fragments:
        assert fragment in script


def test_posix_launcher_is_tracked_as_executable() -> None:
    completed = subprocess.run(
        ["git", "ls-files", "-s", "start.sh"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )

    assert completed.stdout.startswith("100755 ")


@pytest.mark.parametrize(
    "value",
    ["", "0", "65536", "not-a-port", " 8001", "+8001", "8001.0", "８００１"],
)
def test_invalid_port_reports_configuration_error(
    value: str,
    capsys: CaptureFixture[str],
) -> None:
    result = main(["--port", value])

    assert result == EXIT_INVALID_PORT
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == (
        "Cannot start SMCR Staff AI: "
        "SMCR_PORT must be a whole number from 1 through 65535.\n"
    )
