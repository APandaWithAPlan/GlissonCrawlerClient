# GlissonCrawler - Client Setup

 - This is a local, tool-calling AI agent (running on Ollama) built for Glisson's Digital Forensics Class
 - Every answer the agent gives is backed by an actual tool call visible in the **Tool Activity Log** panel -- that transparency is the point of the exercise (comparing what the agent *did* to what it *claims*)

# Tech

  - Ollama for local (or remote, over the classroom LAN) tool-calling model inference
  - Gradio for the chat GUI
  - The Sleuth Kit (`tsk_recover`, bundled prebuilt for Windows) for file carving
  - Pillow / exifread for EXIF metadata reads

# What's here

  - `agent_tools/` -- the tools the agent can call: `hash_file`, `identify_file_signature` (magic-byte file type detection, independent of extension), `read_exif` (with strict calendar-date validation), and `run_tsk_recover` (wraps the bundled Sleuth Kit binary)
  - `agent.py` -- the Ollama tool-calling loop
  - `app.py` -- the Gradio chat GUI
  - `start.exe` / `start.sh` -- first-run bootstrap (installs Python/deps, then launches setup or, if already configured, the app directly). `start.exe` is compiled from `start_bootstrap.py` via PyInstaller
  - `setup.py` -- the interactive configuration wizard
  - `tools/sleuthkit/` -- The Sleuth Kit 4.15.0 for Windows (already extracted; `tsk_recover.exe` is at `tools/sleuthkit/sleuthkit-4.15.0-win32/bin/`)
  - `evidence/` -- put the lab's files here: `File_5`, `File_6`, `File_7`, `File_8`, `File_Image`, `Carving_1.dd`, `Carving_2.dd`. Recovered files from `tsk_recover` land in `evidence/_recovered/<image name>/`

# Prerequisites

  - Python
  - Ollama, (If running locally) **ensure you are only running the model provided**

# Building and running

### Windows

  - Double-click `start.exe`
  - It finds or installs Python, installs the pip requirements, then either launches the setup wizard (first run) or goes straight to the app if a `.env` from a previous run already exists

### Mac / Linux

  - Or on Windows, if you'd rather run it from a terminal:
  ```shell script
  bash start.sh
  ```

Either way, the wizard writes a `.env` file, so every run after the first skips straight to the app.

### First-run wizard

The wizard (`setup.py`) walks through 7 steps and writes the result to `.env`:

  1. **Where does Ollama run?** -- locally on this machine, or remotely on the Forensics Lab LAN
  2. Checks the connection, and won't let you continue with a broken one unless you say so
  3. Pick which pulled model to use 
  4. Where the lab evidence files live (`./evidence` by default)
  5. Confirms `tsk_recover.exe` is at the expected path
  6. Which port the GUI listens on
  7. Saves `.env` and offers to launch the GUI right away


# Configuration

Everything lives in `config.py` and can be overridden with environment variables (the wizard writes these to `.env` for you -- no need to edit code):

| Variable | Default | Purpose |
|---|---|---|
| `OLLAMA_HOST` | `http://127.0.0.1:11434` | Where the agent reaches Ollama -- local or your instructor's server |
| `AGENT_MODEL` | none -- chosen during setup | Any pulled Ollama model with tool-calling support |
| `EVIDENCE_DIR` | `./evidence` | Where lab files live |
| `TSK_RECOVER_PATH` | bundled `tsk_recover.exe` | Only change this if you moved the Sleuth Kit folder |
| `GUI_HOST` | `0.0.0.0` (local Ollama) / `127.0.0.1` (remote Ollama) | Set by the wizard based on step 1 |
| `GUI_PORT` | `7860` | Port the chat GUI listens on |
| `GUI_CONCURRENCY_LIMIT` | `10` | Maximum simultaneous chat turns accepted by Gradio |
| `MAX_PROMPT_CHARS` | `4000` | Maximum characters accepted in one user prompt |

