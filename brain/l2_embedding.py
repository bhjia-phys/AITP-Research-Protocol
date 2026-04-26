"""Vector embedding for L2 concept semantic search.

Pure numpy implementation — no model download, works offline, instant.
Character n-grams + physics alias expansion for technical terminology.

For L2 scale (hundreds of concepts), character n-grams capture subword
patterns that token-based approaches miss: "RPA" matches "Random Phase
Approximation" via "rp" + "pa" bigram overlap.
"""

from __future__ import annotations

import base64
import hashlib
from typing import Any

import numpy as np

_DIM = 256
_FITTED_VOCAB: dict[str, int] | None = None

_PHYSICS_ALIASES: dict[str, list[str]] = {
    "rpa": ["random phase approximation", "dielectric response", "screening", "ring diagram"],
    "gw": ["g0w0", "gw approximation", "hedin", "many-body perturbation", "quasiparticle"],
    "qsgw": ["quasiparticle self-consistent gw", "self-consistent gw"],
    "bse": ["bethe-salpeter equation", "exciton", "electron-hole", "optical absorption"],
    "dft": ["density functional theory", "kohn-sham", "hohenberg-kohn"],
    "lda": ["local density approximation", "uniform electron gas"],
    "gga": ["generalized gradient approximation", "pbe", "semi-local"],
    "dyson": ["dyson equation", "green function", "self-energy", "propagator"],
    "self-energy": ["self energy", "sigma", "correlation", "many-body"],
    "greens-function": ["green function", "propagator", "single-particle", "spectral"],
    "screening": ["dielectric function", "dielectric response", "polarization", "epsilon"],
    "vertex": ["vertex correction", "electron-hole interaction", "beyond-gw", "gamma"],
    "hedin": ["hedin equations", "gw approximation", "many-body perturbation theory"],
    "eft": ["effective field theory", "wilsonian", "rg flow", "renormalization group"],
    "topological": ["topology", "chern", "berry", "edge state", "surface state", "bulk-boundary"],
    "hubbard": ["hubbard model", "mott", "strongly correlated", "mott insulator"],
    "ads-cft": ["ads/cft", "holography", "gauge-gravity duality", "maldacena"],
    "cft": ["conformal field theory", "scaling", "critical", "operator product expansion"],
    "superconductivity": ["superconductor", "bcs", "cooper pair", "meissner"],
    "path-integral": ["path integral", "feynman", "functional integral", "partition function"],
}


def _expand_query(text: str) -> str:
    """Expand a query with physics aliases for better matching."""
    tokens = text.lower().replace("-", " ").replace("/", " ").replace("(", " ").replace(")", " ").split()
    expanded = set(tokens)
    for token in tokens:
        if token in _PHYSICS_ALIASES:
            for alias in _PHYSICS_ALIASES[token]:
                expanded.update(alias.split())
    return " ".join(sorted(expanded))


def _char_ngrams(text: str, n_min: int = 2, n_max: int = 4) -> list[str]:
    """Extract character n-grams from text. Captures subword patterns."""
    clean = text.lower().strip()
    ngrams = []
    for n in range(n_min, n_max + 1):
        for i in range(len(clean) - n + 1):
            ngrams.append(clean[i:i + n])
    return ngrams


def _hash_to_index(token: str, dim: int = _DIM) -> int:
    """Hash a token to a stable dimension index using sha256."""
    h = hashlib.sha256(token.encode()).digest()
    return int.from_bytes(h[:4], "big") % dim


def _build_vocab(documents: list[str], dim: int = _DIM):
    """Build a fixed-size vocabulary from TF-like token frequencies."""
    global _FITTED_VOCAB
    token_freq: dict[str, float] = {}
    n_docs = len(documents)

    for doc in documents:
        expanded = _expand_query(doc)
        tokens = _char_ngrams(expanded)
        seen = set()
        for t in tokens:
            if t not in seen:
                token_freq[t] = token_freq.get(t, 0.0) + 1.0
                seen.add(t)

    # Keep top-N by document frequency
    sorted_tokens = sorted(token_freq.items(), key=lambda x: -x[1])[:dim * 4]
    total_docs = max(n_docs, 1)

    # Compute IDF-like weights
    _FITTED_VOCAB = {}
    for i, (token, df) in enumerate(sorted_tokens):
        if i >= dim:
            break
        idf = np.log((total_docs + 1) / (df + 1)) + 1
        idx = _hash_to_index(token, dim)
        _FITTED_VOCAB[token] = idx


def embed_concept(
    title: str,
    physical_meaning: str = "",
    all_existing: list[str] | None = None,
) -> np.ndarray:
    """Embed a concept → 256-dim sparse TF-IDF-like vector (normalized)."""
    text = title
    if physical_meaning:
        text += " " + physical_meaning

    if all_existing and _FITTED_VOCAB is None:
        _build_vocab(all_existing, _DIM)

    expanded = _expand_query(text)
    tokens = _char_ngrams(expanded)

    # Term frequency with sublinear scaling
    vec = np.zeros(_DIM, dtype=np.float32)
    token_counts: dict[int, float] = {}
    for t in tokens:
        idx = _hash_to_index(t, _DIM)
        token_counts[idx] = token_counts.get(idx, 0.0) + 1.0

    for idx, count in token_counts.items():
        vec[idx] = np.log(1.0 + count)

    norm = np.linalg.norm(vec)
    if norm > 0:
        vec = vec / norm
    return vec.astype(np.float32)


def encode_vector(vec: np.ndarray) -> str:
    """Encode a float32 vector as a compact base64 string."""
    return base64.b64encode(vec.tobytes()).decode("ascii")


def decode_vector(encoded: str) -> np.ndarray | None:
    """Decode a base64-encoded vector back to numpy array."""
    try:
        data = base64.b64decode(encoded)
        arr = np.frombuffer(data, dtype=np.float32)
        if len(arr) == _DIM:
            return arr
        return None
    except Exception:
        return None


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Cosine similarity between two vectors."""
    if len(a) != len(b):
        return 0.0
    return float(np.dot(a, b))


def find_similar(
    query_vec: np.ndarray,
    candidates: list[dict[str, Any]],
    top_k: int = 5,
    threshold: float = 0.10,
) -> list[dict[str, Any]]:
    """Find top_k most similar concepts to query_vec from candidates."""
    results = []
    for c in candidates:
        emb_str = c.get("_embedding", "")
        if not emb_str:
            continue
        emb = decode_vector(emb_str)
        if emb is None:
            continue
        sim = cosine_similarity(query_vec, emb)
        if sim >= threshold:
            results.append({
                "node_id": c["node_id"],
                "title": c.get("title", ""),
                "domain": c.get("domain", ""),
                "type": c.get("type", ""),
                "similarity": round(sim, 3),
            })

    results.sort(key=lambda x: x["similarity"], reverse=True)
    return results[:top_k]
