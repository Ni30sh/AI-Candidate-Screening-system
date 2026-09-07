import math
import pickle
import re
from collections import Counter
from pathlib import Path


def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-zA-Z][a-zA-Z0-9+#.-]{1,}", text.lower())


class LocalRetriever:
    def __init__(self, index_path: str):
        self.index_path = Path(index_path)
        self.documents: list[dict] = []
        self.idf: dict[str, float] = {}
        self.vectors: list[dict[str, float]] = []
        if self.index_path.exists():
            self._load()

    def _load(self) -> None:
        data = pickle.loads(self.index_path.read_bytes())
        self.documents, self.idf, self.vectors = data["documents"], data["idf"], data["vectors"]

    def build(self, documents: list[dict]) -> None:
        self.documents = documents
        document_terms = [set(tokenize(doc["text"])) for doc in documents]
        count = Counter(term for terms in document_terms for term in terms)
        total = len(documents) or 1
        self.idf = {term: math.log((1 + total) / (1 + frequency)) + 1 for term, frequency in count.items()}
        self.vectors = []
        for doc in documents:
            terms = Counter(tokenize(doc["text"]))
            scale = max(terms.values(), default=1)
            self.vectors.append({term: (frequency / scale) * self.idf.get(term, 1) for term, frequency in terms.items()})
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        self.index_path.write_bytes(pickle.dumps({"documents": self.documents, "idf": self.idf, "vectors": self.vectors}))

    def search(self, query: str, role: str, limit: int = 3) -> list[dict]:
        if not self.documents:
            return []
        query_terms = Counter(tokenize(query))
        scored = []
        for index, vector in enumerate(self.vectors):
            if self.documents[index].get("role") not in (role, "shared"):
                continue
            score = sum((query_terms[term] * self.idf.get(term, 1)) * value for term, value in vector.items())
            if score > 0:
                scored.append((score, self.documents[index]))
        return [dict(doc, score=round(score, 4)) for score, doc in sorted(scored, reverse=True, key=lambda item: item[0])[:limit]]
