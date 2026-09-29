import os

from agent_tools.filesystem import resolve_evidence_path

_SIGNATURES = [
    ("JPEG", True, lambda h: h[:3] == b"\xFF\xD8\xFF"),
    ("PNG", True, lambda h: h[:8] == b"\x89PNG\r\n\x1a\n"),
    ("GIF", True, lambda h: h[:6] in (b"GIF87a", b"GIF89a")),
    ("BMP", True, lambda h: h[:2] == b"BM"),
    ("TIFF", True, lambda h: h[:4] in (b"II*\x00", b"MM\x00*")),
    ("WEBP", True, lambda h: h[:4] == b"RIFF" and h[8:12] == b"WEBP"),
    ("PDF", False, lambda h: h[:5] == b"%PDF-"),
    ("ZIP/Office (docx/xlsx/pptx/zip)", False, lambda h: h[:4] == b"PK\x03\x04"),
    ("MP4/MOV", False, lambda h: h[4:8] == b"ftyp"),
    ("MP3", False, lambda h: h[:3] == b"ID3" or h[:2] in (b"\xFF\xFB", b"\xFF\xF3", b"\xFF\xF2")),
    ("WAV/AVI (RIFF)", False, lambda h: h[:4] == b"RIFF"),
    ("EXE/DLL", False, lambda h: h[:2] == b"MZ"),
    ("GZIP", False, lambda h: h[:2] == b"\x1f\x8b"),
    ("RAR", False, lambda h: h[:6] == b"Rar!\x1a\x07"),
    ("7Z", False, lambda h: h[:6] == b"7z\xbc\xaf\x27\x1c"),
]

_PICTURE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tif", ".tiff", ".webp"}


def identify_file_signature(file_name: str) -> dict:
    path = resolve_evidence_path(file_name)
    with open(path, "rb") as f:
        header = f.read(64)

    detected = None
    detected_is_picture = False
    for label, is_picture, matcher in _SIGNATURES:
        try:
            if matcher(header):
                detected = label
                detected_is_picture = is_picture
                break
        except Exception:
            continue

    claimed_ext = os.path.splitext(file_name)[1].lower()
    claimed_is_picture_ext = claimed_ext in _PICTURE_EXTENSIONS

    return {
        "file": file_name,
        "claimed_extension": claimed_ext or "(none)",
        "detected_type": detected or "unknown / no matching signature",
        "is_genuinely_a_picture": detected_is_picture,
        "extension_matches_detected_type": (detected is not None) and (claimed_is_picture_ext == detected_is_picture),
        "header_hex": header[:16].hex(),
    }
