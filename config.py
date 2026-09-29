import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def _load_dotenv(path: str) -> None:
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            value = value.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
                value = value[1:-1]
            os.environ.setdefault(key.strip(), value)


_load_dotenv(os.path.join(BASE_DIR, ".env"))

EVIDENCE_DIR = os.environ.get("EVIDENCE_DIR", os.path.join(BASE_DIR, "evidence"))

RECOVERY_DIR = os.path.join(EVIDENCE_DIR, "_recovered")

TSK_RECOVER_PATH = os.environ.get(
    "TSK_RECOVER_PATH",
    os.path.join(BASE_DIR, "tools", "sleuthkit", "sleuthkit-4.15.0-win32", "bin", "tsk_recover.exe"),
)

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")

OLLAMA_MODEL = os.environ.get("AGENT_MODEL", "")

GUI_HOST = os.environ.get("GUI_HOST", "0.0.0.0")
GUI_PORT = int(os.environ.get("GUI_PORT", "7860"))

GUI_CONCURRENCY_LIMIT = int(os.environ.get("GUI_CONCURRENCY_LIMIT", "10"))

MAX_PROMPT_CHARS = int(os.environ.get("MAX_PROMPT_CHARS", "4000"))
