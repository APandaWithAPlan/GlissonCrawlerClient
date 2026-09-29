import os

from config import EVIDENCE_DIR


class PathOutsideEvidenceDir(Exception):
    pass


def resolve_evidence_path(name: str) -> str:
    candidate = os.path.normpath(os.path.join(EVIDENCE_DIR, name))
    evidence_root = os.path.normpath(EVIDENCE_DIR)
    if not (candidate == evidence_root or candidate.startswith(evidence_root + os.sep)):
        raise PathOutsideEvidenceDir(f"'{name}' resolves outside the evidence directory")
    return candidate


def list_evidence_files(subdir: str = ".") -> list[dict]:
    target = resolve_evidence_path(subdir)
    if not os.path.isdir(target):
        return [{"error": f"'{subdir}' is not a directory under the evidence folder"}]

    results = []
    for root, _dirs, files in os.walk(target):
        for fname in files:
            full = os.path.join(root, fname)
            rel = os.path.relpath(full, EVIDENCE_DIR)
            results.append({"name": rel, "size_bytes": os.path.getsize(full)})
    return results
