import re
import unicodedata


def slugify(text: str, sep: str = "-") -> str:
    """Make a URL-safe slug: lowercase, ascii, words joined by sep."""
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    text = text.lower()
    out = []
    for ch in text:
        if ch.isalnum():
            out.append(ch)
        elif out and out[-1] != sep:
            out.append(sep)
    return "".join(out).rstrip("-")
