import os
import shutil
import socket
import subprocess
import sys

import pyfiglet

from config import (
    BASE_DIR,
    EVIDENCE_DIR,
    GUI_PORT,
    OLLAMA_HOST,
    OLLAMA_MODEL,
    TSK_RECOVER_PATH,
)

if sys.platform == "win32":
    os.system("")
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

GOLD = "\033[38;5;220m"
BURGUNDY = "\033[38;5;131m"
GREEN = "\033[38;5;71m"
RED = "\033[38;5;167m"
DIM = "\033[2m"
BOLD = "\033[1m"
RESET = "\033[0m"

TOTAL_STEPS = 7


def banner():
    print(GOLD + BOLD + pyfiglet.figlet_format("GLISSON CRAWLER", font="small") + RESET)
    print(DIM + "  an agentic forensics assistant -- setup wizard" + RESET + "\n")


def step(n, title):
    print(f"\n{BOLD}{BURGUNDY}[{n}/{TOTAL_STEPS}]{RESET} {BOLD}{title}{RESET}")


def ok(msg):
    print(f"  {GREEN}✓{RESET} {msg}")


def warn(msg):
    print(f"  {GOLD}!{RESET} {msg}")


def err(msg):
    print(f"  {RED}✗{RESET} {msg}")


def ask(prompt, default=None):
    suffix = f" {DIM}[{default}]{RESET}" if default else ""
    raw = input(f"  {prompt}{suffix}: ").strip()
    return raw or (default or "")


def _strip_quotes(path):
    if len(path) >= 2 and path[0] == path[-1] and path[0] in "\"'":
        return path[1:-1]
    return path


def ask_path(prompt, default=None):
    return _strip_quotes(ask(prompt, default))


def ask_choice(prompt, options, default_index=0):
    print(f"  {prompt}")
    for i, opt in enumerate(options, 1):
        marker = f"{GOLD}*{RESET}" if i - 1 == default_index else " "
        print(f"    {marker} {i}) {opt}")
    raw = input(f"  choose [1-{len(options)}] {DIM}[{default_index + 1}]{RESET}: ").strip()
    if not raw:
        return default_index
    try:
        idx = int(raw) - 1
        if 0 <= idx < len(options):
            return idx
    except ValueError:
        pass
    warn("Invalid choice, using default.")
    return default_index


def ask_yes_no(prompt, default=True):
    suffix = "Y/n" if default else "y/N"
    raw = input(f"  {prompt} [{suffix}]: ").strip().lower()
    return default if not raw else raw.startswith("y")


def resolve_ollama_connection():
    while True:
        step(1, "Where does Ollama run?")
        is_remote_default = 1 if not OLLAMA_HOST.startswith("http://127.0.0.1") else 0
        mode_idx = ask_choice(
            "How should this app reach Ollama?",
            [
                "Locally on this machine",
                "Remotely, over the network (e.g. the classroom's shared GPU computer)",
            ],
            is_remote_default,
        )

        if mode_idx == 0:
            ollama_host = "http://127.0.0.1:11434"
            ollama_bin = shutil.which("ollama")
            if ollama_bin:
                ok(f"Found Ollama executable at {ollama_bin}")
            else:
                warn("Ollama executable not found on PATH -- is it installed?")
        else:
            remote_addr = ""
            while not remote_addr:
                remote_addr = ask("IP address or hostname of the Ollama server (ask your instructor)")
                if not remote_addr:
                    warn("An address is required for remote mode.")
            remote_port = ask("Port Ollama is listening on", default="11434")
            ollama_host = f"http://{remote_addr}:{remote_port}"

        step(2, "Checking the Ollama connection")
        try:
            import ollama as ollama_pkg

            client = ollama_pkg.Client(host=ollama_host, timeout=5)
            models = [m.model for m in client.list().models]
            ok(f"Ollama server reachable at {ollama_host} ({len(models)} model(s) pulled)")
            return ollama_host, mode_idx, models
        except Exception as e:
            err(f"Could not reach Ollama at {ollama_host} ({e})")
            if mode_idx == 0:
                warn("Start it with `ollama serve`, then try again.")
            else:
                warn("Double-check the address/port and that the remote machine's firewall allows it.")
            if not ask_yes_no("Try again?", default=True):
                warn("Continuing without a confirmed Ollama connection.")
                return ollama_host, mode_idx, []


def main():
    banner()
    print(
        f"This walks through configuring {BOLD}Glisson Crawler{RESET} and writes your\n"
        f"choices to a {BOLD}.env{RESET} file so {BOLD}app.py{RESET} picks them up automatically.\n"
    )

    env = {}

    ollama_host, mode_idx, models = resolve_ollama_connection()
    env["OLLAMA_HOST"] = ollama_host

    step(3, "Choosing a model")
    if models:
        default_idx = models.index(OLLAMA_MODEL) if OLLAMA_MODEL in models else 0
        chosen_model = models[ask_choice("Which locally-pulled model should the agent use?", models, default_idx)]
    else:
        chosen_model = ""
        while not chosen_model:
            chosen_model = ask("No models detected -- type a model name to use anyway")
            if not chosen_model:
                warn("A model name is required.")
    ok(f"Using model {BOLD}{chosen_model}{RESET}")
    env["AGENT_MODEL"] = chosen_model

    step(4, "Evidence directory")
    evidence_dir = ask_path("Where do lab files (File_5, Carving_1.dd, ...) live?", default=EVIDENCE_DIR)
    os.makedirs(evidence_dir, exist_ok=True)
    file_count = len([f for f in os.listdir(evidence_dir) if os.path.isfile(os.path.join(evidence_dir, f))])
    ok(f"{evidence_dir} ready ({file_count} file(s) already there)")
    env["EVIDENCE_DIR"] = evidence_dir

    step(5, "Sleuth Kit (tsk_recover)")
    tsk_path = ask_path("Path to tsk_recover", default=TSK_RECOVER_PATH)
    if not os.path.isfile(tsk_path):
        err(f"No file at {tsk_path}")
        warn("Double-check the path -- if you tested this exe by hand at a command prompt "
             "and it printed a \"can't open file\" error, that's usually the *evidence* image "
             "path being unquoted, not this one. Any manual command with a folder name that "
             "has spaces in it (like this one) needs to be wrapped in quotes.")
    else:
        try:
            result = subprocess.run([tsk_path, "-V"], capture_output=True, text=True, timeout=10)
            ok(f"tsk_recover responds: {result.stdout.strip()}")
        except Exception as e:
            err(f"Couldn't run tsk_recover at that path ({e})")
    env["TSK_RECOVER_PATH"] = tsk_path

    step(6, "Network access")
    gui_host = "127.0.0.1" if mode_idx == 1 else "0.0.0.0"
    ok(f"GUI will be reachable on {'localhost only' if gui_host == '127.0.0.1' else 'the classroom LAN'} ({gui_host})")
    port_raw = ask("Port for the GUI", default=str(GUI_PORT))
    gui_port = int(port_raw) if port_raw.isdigit() else GUI_PORT

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        port_in_use = s.connect_ex(("127.0.0.1", gui_port)) == 0
    if port_in_use:
        warn(f"Something is already listening on port {gui_port} -- stop it before launching.")
    else:
        ok(f"Port {gui_port} is free")
    env["GUI_HOST"] = gui_host
    env["GUI_PORT"] = str(gui_port)

    step(7, "Saving configuration")
    env_path = os.path.join(BASE_DIR, ".env")
    with open(env_path, "w", encoding="utf-8") as f:
        for key, value in env.items():
            f.write(f"{key}={value}\n")
    ok(f"Wrote {env_path}")

    print(f"\n{BOLD}{GREEN}Setup complete.{RESET} Summary:\n")
    for key, value in env.items():
        print(f"  {DIM}{key}{RESET} = {value}")
    print()

    if ask_yes_no("Launch the GUI now?", default=True):
        print()
        result = subprocess.run([sys.executable, os.path.join(BASE_DIR, "app.py")])
        if result.returncode != 0:
            err(f"Glisson Crawler exited with an error (code {result.returncode}).")
            input("Press Enter to close this window...")
        sys.exit(result.returncode)
    else:
        print(f"\n  Run {BOLD}python app.py{RESET} whenever you're ready.\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nSetup cancelled.")
        sys.exit(1)
