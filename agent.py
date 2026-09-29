import json

import ollama

from config import OLLAMA_HOST, OLLAMA_MODEL
from agent_tools import carving, exif_tool, filesystem, hashing, signatures
from response import ensure_watermark

_client = ollama.Client(host=OLLAMA_HOST)

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "list_evidence_files",
            "description": "List files available in the evidence directory (optionally a subfolder, e.g. '_recovered/Carving_1').",
            "parameters": {
                "type": "object",
                "properties": {
                    "subdir": {"type": "string", "description": "Subfolder to list, relative to the evidence directory. Defaults to the top level."},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "hash_file",
            "description": "Compute a cryptographic hash of a file in the evidence directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_name": {"type": "string", "description": "File name/relative path under the evidence directory."},
                    "algorithm": {"type": "string", "description": "One of md5, sha1, sha256, sha512.", "default": "sha512"},
                },
                "required": ["file_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "identify_file_signature",
            "description": "Inspect a file's magic-number header to determine its real type, independent of its extension/name.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_name": {"type": "string", "description": "File name/relative path under the evidence directory."},
                },
                "required": ["file_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_exif",
            "description": "Read EXIF metadata (file type, make, model, date/time fields) from an image file, with strict date validation.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_name": {"type": "string", "description": "File name/relative path under the evidence directory."},
                },
                "required": ["file_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_tsk_recover",
            "description": "Run tsk_recover on a disk image (.dd) under the evidence directory to recover files, and list what was recovered.",
            "parameters": {
                "type": "object",
                "properties": {
                    "image_file": {"type": "string", "description": "Disk image file name/relative path under the evidence directory."},
                    "recover_unallocated": {"type": "boolean", "description": "Recover allocated AND unallocated (deleted) files. Defaults to true.", "default": True},
                },
                "required": ["image_file"],
            },
        },
    },
]

_DISPATCH = {
    "list_evidence_files": filesystem.list_evidence_files,
    "hash_file": hashing.hash_file,
    "identify_file_signature": signatures.identify_file_signature,
    "read_exif": exif_tool.read_exif,
    "run_tsk_recover": carving.run_tsk_recover,
}

_SESSION_SCOPED_TOOLS = {"run_tsk_recover"}

MAX_TOOL_ROUNDS = 30


def run_agent(user_message: str, history: list[dict], session_id: str | None = None):
    messages = history + [{"role": "user", "content": user_message}]

    for _round in range(MAX_TOOL_ROUNDS):
        response = _client.chat(model=OLLAMA_MODEL, messages=messages, tools=TOOLS)
        msg = response["message"]
        messages.append(msg)

        tool_calls = msg.get("tool_calls")
        if not tool_calls:
            yield ("final", ensure_watermark(msg.get("content", "")))
            return

        for call in tool_calls:
            name = call["function"]["name"]
            raw_args = call["function"]["arguments"]
            args = json.loads(raw_args) if isinstance(raw_args, str) else dict(raw_args)

            yield ("tool_call", {"name": name, "arguments": args})

            fn = _DISPATCH.get(name)
            if fn is None:
                result = {"error": f"unknown tool '{name}'"}
            else:
                call_args = dict(args)
                if name in _SESSION_SCOPED_TOOLS:
                    call_args["session_id"] = session_id
                try:
                    result = fn(**call_args)
                except Exception as e:
                    result = {"error": f"{type(e).__name__}: {e}"}

            yield ("tool_result", {"name": name, "result": result})
            messages.append({"role": "tool", "content": json.dumps(result, default=str)})

    yield ("final", "(stopped: too many tool-call rounds without a final answer -- ask a narrower question)")
