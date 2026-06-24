#!/usr/bin/env bash

echo ""
echo "================================================"
echo " SMCR Staff AI - Setup Check"
echo "================================================"
echo ""

MISSING=0

# --- Git ---
if command -v git >/dev/null 2>&1; then
    echo "[OK]      Git: $(git --version)"
else
    echo "[MISSING] Git not found."
    echo ""
    echo "          Install options:"
    echo "            Mac:   brew install git"
    echo "            Linux: sudo apt install git  (or dnf/pacman equivalent)"
    echo "            Any:   https://git-scm.com/downloads"
    echo ""
    MISSING=1
fi

# --- Python ---
if command -v python3 >/dev/null 2>&1; then
    echo "[OK]      Python: $(python3 --version)  (3.12 or newer required)"
elif command -v python >/dev/null 2>&1; then
    echo "[OK]      Python: $(python --version)  (3.12 or newer required)"
else
    echo "[MISSING] Python not found."
    echo ""
    echo "          Install options:"
    echo "            Mac:   brew install python@3.12"
    echo "            Linux: sudo apt install python3.12"
    echo "            Any:   https://www.python.org/downloads/"
    echo ""
    MISSING=1
fi

# --- uv ---
if command -v uv >/dev/null 2>&1; then
    echo "[OK]      uv: $(uv --version)"
else
    echo "[MISSING] uv not found."
    echo ""
    echo "          Install options:"
    echo "            curl -LsSf https://astral.sh/uv/install.sh | sh"
    echo "            pip install uv"
    echo ""
    MISSING=1
fi

echo ""

if [ "$MISSING" -eq 1 ]; then
    echo "------------------------------------------------"
    echo " Install the missing items above, then re-run"
    echo " this script  OR  just run: ./start.sh"
    echo ""
    echo " TIP: Open Claude, Copilot, or another AI"
    echo " assistant in this folder and say:"
    echo ""
    echo "   'Help me install the prerequisites for"
    echo "    smcr-staff-ai - see QUICKSTART.md'"
    echo ""
    echo " It can walk you through each step."
    echo "------------------------------------------------"
else
    echo " All prerequisites found."
    echo ""
    printf "  Launch the server now? [Y/n]: "
    read -r LAUNCH
    case "${LAUNCH}" in
        [nN]*) exit 0 ;;
        *) exec ./start.sh ;;
    esac
fi

echo ""
