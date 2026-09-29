import os
import re
import subprocess

from config import RECOVERY_DIR, TSK_RECOVER_PATH
from agent_tools.filesystem import resolve_evidence_path

_SAFE_ID = re.compile(r"[^A-Za-z0-9_-]")


def run_tsk_recover(image_file: str, recover_unallocated: bool = True, session_id: str | None = None) -> dict:
    image_path = resolve_evidence_path(image_file)
    if not os.path.isfile(image_path):
        return {"error": f"'{image_file}' not found under the evidence directory"}

    session_dir = _SAFE_ID.sub("", session_id) if session_id else "shared"
    out_dir = os.path.join(RECOVERY_DIR, os.path.splitext(os.path.basename(image_file))[0], session_dir)
    os.makedirs(out_dir, exist_ok=True)

    args = [TSK_RECOVER_PATH]
    args.append("-e" if recover_unallocated else "-a")
    args += [image_path, out_dir]

    proc = subprocess.run(args, capture_output=True, text=True, timeout=600)

    recovered = []
    for root, _dirs, files in os.walk(out_dir):
        for fname in files:
            full = os.path.join(root, fname)
            recovered.append(
                {
                    "path_for_other_tools": os.path.relpath(full, os.path.dirname(RECOVERY_DIR)),
                    "name": fname,
                    "size_bytes": os.path.getsize(full),
                }
            )

    return {
        "image": image_file,
        "command": " ".join(args),
        "return_code": proc.returncode,
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip(),
        "recovered_file_count": len(recovered),
        "recovered_files": recovered,
        "output_directory": out_dir,
    }
