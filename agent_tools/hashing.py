import hashlib

from agent_tools.filesystem import resolve_evidence_path

_SUPPORTED = {"md5", "sha1", "sha256", "sha512"}


def hash_file(file_name: str, algorithm: str = "sha512") -> dict:
    algorithm = algorithm.lower()
    if algorithm not in _SUPPORTED:
        return {"error": f"unsupported algorithm '{algorithm}', use one of {sorted(_SUPPORTED)}"}

    path = resolve_evidence_path(file_name)
    hasher = hashlib.new(algorithm)
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            hasher.update(chunk)

    return {
        "file": file_name,
        "algorithm": algorithm,
        "hash": hasher.hexdigest(),
    }
