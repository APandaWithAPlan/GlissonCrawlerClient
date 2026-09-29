import datetime

import exifread

from agent_tools.filesystem import resolve_evidence_path
from agent_tools.signatures import identify_file_signature

_DATE_TAGS = ("EXIF DateTimeOriginal", "EXIF DateTimeDigitized", "Image DateTime")


def _validate_calendar_date(raw: str) -> dict:
    try:
        parsed = datetime.datetime.strptime(raw, "%Y:%m:%d %H:%M:%S")
        return {"raw_value": raw, "is_valid_calendar_date": True, "parsed": parsed.isoformat()}
    except ValueError as e:
        return {"raw_value": raw, "is_valid_calendar_date": False, "reason": str(e)}


def read_exif(file_name: str) -> dict:
    path = resolve_evidence_path(file_name)

    signature = identify_file_signature(file_name)

    with open(path, "rb") as f:
        tags = exifread.process_file(f, details=False)

    make = str(tags["Image Make"]) if "Image Make" in tags else None
    model = str(tags["Image Model"]) if "Image Model" in tags else None

    date_findings = {}
    for tag in _DATE_TAGS:
        if tag in tags:
            date_findings[tag] = _validate_calendar_date(str(tags[tag]))

    return {
        "file": file_name,
        "detected_file_type": signature["detected_type"],
        "extension_matches_detected_type": signature["extension_matches_detected_type"],
        "make": make,
        "model": model,
        "date_time_fields": date_findings or "no EXIF date/time tags present",
        "raw_tag_count": len(tags),
    }
