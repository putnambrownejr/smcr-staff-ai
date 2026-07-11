import argparse
import socket
import sys
from collections.abc import Sequence
from pathlib import Path

LOOPBACK_HOST = "127.0.0.1"
CONNECT_TIMEOUT_SECONDS = 0.25
EXIT_AVAILABLE = 0
EXIT_OCCUPIED = 1
EXIT_INVALID_PORT = 2
_INVALID_PORT_MESSAGE = "SMCR_PORT must be a whole number from 1 through 65535."


def parse_port(value: str) -> int:
    if not value.isascii() or not value.isdecimal():
        raise ValueError(_INVALID_PORT_MESSAGE)
    port = int(value, 10)
    if not 1 <= port <= 65_535:
        raise ValueError(_INVALID_PORT_MESSAGE)
    return port


def is_loopback_port_accepting_connections(
    port: int,
    *,
    timeout: float = CONNECT_TIMEOUT_SECONDS,
) -> bool:
    try:
        with socket.create_connection((LOOPBACK_HOST, port), timeout=timeout):
            return True
    except OSError:
        return False


def occupied_port_message(port: int, checkout: Path) -> str:
    return "\n".join(
        [
            f"Cannot start SMCR Staff AI: local port {port} is already in use.",
            f"Current checkout: {checkout.resolve()}",
            "Another SMCR Staff AI checkout may already be running.",
            "Stop the other instance, or choose another local port:",
            '  PowerShell: $env:SMCR_PORT="8001"; .\\start.bat',
            '  Command Prompt: set "SMCR_PORT=8001" && start.bat',
            "  macOS/Linux: SMCR_PORT=8001 ./start.sh",
        ]
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check the local SMCR Staff AI startup port.")
    parser.add_argument("--port", required=True, metavar="PORT")
    args = parser.parse_args(argv)
    try:
        port = parse_port(str(args.port))
    except ValueError as exc:
        print(f"Cannot start SMCR Staff AI: {exc}", file=sys.stderr)
        return EXIT_INVALID_PORT
    if not is_loopback_port_accepting_connections(port):
        return EXIT_AVAILABLE
    print(occupied_port_message(port, Path.cwd()), file=sys.stderr)
    return EXIT_OCCUPIED


if __name__ == "__main__":
    raise SystemExit(main())
