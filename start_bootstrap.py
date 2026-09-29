import glob
import os
import platform
import shutil
import subprocess
import sys

if sys.platform == "win32":
    os.system("")
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = os.path.dirname(os.path.abspath(sys.argv[0] if getattr(sys, "frozen", False) else __file__))


def find_python():
    for candidate in ("python3", "python", "py"):
        path = shutil.which(candidate)
        if path:
            return path
    return None


def install_python():
    system = platform.system()
    if system == "Windows":
        if shutil.which("winget"):
            subprocess.run(
                ["winget", "install", "--id", "Python.Python.3.12", "-e",
                 "--source", "winget", "--accept-package-agreements", "--accept-source-agreements"],
                check=True,
            )
        else:
            print("winget isn't available. Install Python from https://python.org/downloads and re-run.")
            sys.exit(1)
    elif system == "Darwin":
        if shutil.which("brew"):
            subprocess.run(["brew", "install", "python"], check=True)
        else:
            print("Homebrew isn't available. Install Python from https://python.org/downloads and re-run.")
            sys.exit(1)
    elif system == "Linux":
        for manager, cmd in (
            ("apt-get", ["sudo", "apt-get", "install", "-y", "python3", "python3-pip"]),
            ("dnf", ["sudo", "dnf", "install", "-y", "python3", "python3-pip"]),
            ("pacman", ["sudo", "pacman", "-Sy", "--noconfirm", "python", "python-pip"]),
        ):
            if shutil.which(manager):
                subprocess.run(cmd, check=True)
                break
        else:
            print("No supported package manager found (apt/dnf/pacman). Install Python 3 manually and re-run.")
            sys.exit(1)
    else:
        print(f"Unrecognized OS '{system}'. Install Python 3 from https://python.org/downloads and re-run.")
        sys.exit(1)


def find_freshly_installed_python():
    local_app_data = os.environ.get("LOCALAPPDATA", "")
    pattern = os.path.join(local_app_data, "Programs", "Python", "Python3*", "python.exe")
    matches = sorted(glob.glob(pattern))
    return matches[-1] if matches else None


def main():
    print("Glisson Crawler -- bootstrap\n")

    python_bin = find_python()

    if not python_bin:
        print("Python not found on PATH -- installing it now.")
        install_python()
        python_bin = find_python() or find_freshly_installed_python()
        if not python_bin:
            print("\nPython just installed, but this terminal can't see it yet.")
            print("Close this window, open a new terminal, and run start again.")
            sys.exit(1)

    version = subprocess.run([python_bin, "--version"], capture_output=True, text=True).stdout.strip()
    print(f"Using Python: {version}\n")

    print("Installing requirements...")
    subprocess.run([python_bin, "-m", "pip", "install", "--quiet", "--no-warn-script-location",
                    "--upgrade", "pip"], check=True)
    subprocess.run([python_bin, "-m", "pip", "install", "--quiet", "--no-warn-script-location",
                    "-r", os.path.join(BASE_DIR, "requirements.txt")], check=True)

    env_path = os.path.join(BASE_DIR, ".env")
    if os.path.exists(env_path):
        print("\nExisting configuration found -- skipping setup, launching the app.\n")
        target = os.path.join(BASE_DIR, "app.py")
    else:
        print("\nLaunching setup...\n")
        target = os.path.join(BASE_DIR, "setup.py")

    result = subprocess.run([python_bin, target])
    if result.returncode != 0:
        print(f"\nGlisson Crawler exited with an error (code {result.returncode}).")
        input("Press Enter to close this window...")
    sys.exit(result.returncode)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nCancelled.")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"\nA step failed: {e}")
        sys.exit(1)
