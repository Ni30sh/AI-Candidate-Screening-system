import io
import re
from pathlib import Path
from pypdf import PdfReader


def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def extract_resume(filename: str, content: bytes) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix == ".txt":
        text = content.decode("utf-8", errors="strict")
    elif suffix == ".pdf":
        reader = PdfReader(io.BytesIO(content))
        text = " ".join(page.extract_text() or "" for page in reader.pages)
    else:
        raise ValueError("Only PDF and text resumes are supported")
    text = clean_text(text)
    if not text:
        raise ValueError("The resume contains no extractable text")
    return text
