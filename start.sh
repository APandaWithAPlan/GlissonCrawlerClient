#!/usr/bin/env bash
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Glisson Crawler -- bootstrap"
echo

find_python() {
    for candidate in python3 python py; do
        if command -v "$candidate" >/dev/null 2>&1; then
            echo "$candidate"
            return 0
        fi
    done
    return 1
}

PYTHON_BIN="$(find_python || true)"

if [ -z "$PYTHON_BIN" ]; then
    echo "Python not found on PATH -- installing it now."
    case "$(uname -s)" in
        MINGW*|MSYS*|CYGWIN*)
            if command -v winget >/dev/null 2>&1; then
                winget install --id Python.Python.3.12 -e --source winget --accept-package-agreements --accept-source-agreements
            else
                echo "winget isn't available. Install Python from https://python.org/downloads and re-run this script."
                exit 1
            fi
            ;;
        Darwin*)
            if command -v brew >/dev/null 2>&1; then
                brew install python
            else
                echo "Homebrew isn't available. Install Python from https://python.org/downloads and re-run this script."
                exit 1
            fi
            ;;
        Linux*)
            if command -v apt-get >/dev/null 2>&1; then
                sudo apt-get update && sudo apt-get install -y python3 python3-pip
            elif command -v dnf >/dev/null 2>&1; then
                sudo dnf install -y python3 python3-pip
            elif command -v pacman >/dev/null 2>&1; then
                sudo pacman -Sy --noconfirm python python-pip
            else
                echo "No supported package manager found (apt/dnf/pacman). Install Python 3 manually and re-run this script."
                exit 1
            fi
            ;;
        *)
            echo "Unrecognized OS. Install Python 3 from https://python.org/downloads and re-run this script."
            exit 1
            ;;
    esac

    PYTHON_BIN="$(find_python || true)"

    if [ -z "$PYTHON_BIN" ]; then
        NEWEST=$(ls -d "$LOCALAPPDATA/Programs/Python/Python3"*/python.exe 2>/dev/null | sort -V | tail -n 1)
        if [ -n "$NEWEST" ]; then
            PYTHON_BIN="$NEWEST"
        else
            echo
            echo "Python just installed, but this terminal can't see it yet."
            echo "Close this window, open a new terminal, and re-run start.sh."
            exit 1
        fi
    fi
fi

echo "Using Python: $("$PYTHON_BIN" --version)"
echo

echo "Installing requirements..."
"$PYTHON_BIN" -m pip install --quiet --no-warn-script-location --upgrade pip
"$PYTHON_BIN" -m pip install --quiet --no-warn-script-location -r "$DIR/requirements.txt"

if [ -f "$DIR/.env" ]; then
    echo
    echo "Existing configuration found -- skipping setup, launching the app."
    echo
    exec "$PYTHON_BIN" "$DIR/app.py"
fi

echo
echo "Launching setup..."
echo
exec "$PYTHON_BIN" "$DIR/setup.py"
