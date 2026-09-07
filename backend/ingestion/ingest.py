import argparse
import re
from pathlib import Path
from pypdf import PdfReader
from app.core.config import get_settings
from app.services.retriever import LocalRetriever


def role_for(filename: str) -> str:
    name = filename.lower()
    if "python" in name or "brownlee" in name or "absolute" in name:
        return "data-science-applied-ml"
    return "ai-ml-engineer"


def ingest(source_dir: Path) -> int:
    documents = []
    for pdf_path in sorted(source_dir.glob("*.pdf")):
        reader = PdfReader(str(pdf_path))
        role = role_for(pdf_path.name)
        for page_number, page in enumerate(reader.pages, 1):
            text = re.sub(r"\s+", " ", page.extract_text() or "").strip()
            words = text.split()
            for offset in range(0, len(words), 180):
                chunk = " ".join(words[offset : offset + 240])
                if len(chunk) >= 80:
                    documents.append({"chunk_id": f"{pdf_path.stem[:24]}-{page_number}-{offset}", "text": chunk, "source": pdf_path.name, "role": role, "page": page_number, "section": None})
    LocalRetriever(get_settings().vector_db_path).build(documents)
    return len(documents)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path, default=Path("knowledge_base"), nargs="?")
    args = parser.parse_args()
    print(f"Indexed {ingest(args.source)} chunks")
