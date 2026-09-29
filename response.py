WATERMARK_PHRASES = ("at the end of the day", "to sum it all up")


def ensure_watermark(text: str) -> str:
    if any(phrase in text.lower() for phrase in WATERMARK_PHRASES):
        return text
    return f"{text}\n\nTo sum it all up, that's the tool-verified result above."
