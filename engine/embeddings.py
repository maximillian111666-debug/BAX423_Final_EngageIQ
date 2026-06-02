"""
BAX-423 Technique: Embeddings + Approximate Nearest-Neighbor Search.
Uses Sentence-BERT (all-MiniLM-L6-v2) to embed opportunity text and
user interest profiles. FAISS HNSW index enables sub-linear ANN retrieval.
"""
import os
import pickle
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from config import EMBEDDING_MODEL, EMBEDDING_DIM

_model: SentenceTransformer | None = None
_CODE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX_PATH = os.path.join(_CODE_DIR, "data", "faiss.index")
ID_MAP_PATH = os.path.join(_CODE_DIR, "data", "faiss_ids.pkl")


def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBEDDING_MODEL)
    return _model


def embed_texts(texts: list[str]) -> np.ndarray:
    model = get_model()
    vectors = model.encode(texts, batch_size=64, show_progress_bar=False,
                           normalize_embeddings=True)
    return vectors.astype(np.float32)


def embed_single(text: str) -> np.ndarray:
    return embed_texts([text])[0]


def build_faiss_index(vectors: np.ndarray, opp_ids: list[int],
                      index_path: str = INDEX_PATH,
                      id_map_path: str = ID_MAP_PATH) -> faiss.IndexHNSWFlat:
    dim = vectors.shape[1]
    index = faiss.IndexHNSWFlat(dim, 32)
    index.hnsw.efConstruction = 200
    index.hnsw.efSearch = 64
    faiss.normalize_L2(vectors)
    index.add(vectors)
    os.makedirs(os.path.dirname(os.path.abspath(index_path)), exist_ok=True)
    faiss.write_index(index, index_path)
    with open(id_map_path, "wb") as f:
        pickle.dump(opp_ids, f)
    return index


def load_faiss_index(index_path: str = INDEX_PATH,
                     id_map_path: str = ID_MAP_PATH) -> tuple[faiss.IndexHNSWFlat, list[int]] | tuple[None, None]:
    if not os.path.exists(index_path) or not os.path.exists(id_map_path):
        return None, None
    index = faiss.read_index(index_path)
    with open(id_map_path, "rb") as f:
        opp_ids = pickle.load(f)
    return index, opp_ids


def retrieve_candidates(query_vector: np.ndarray, index: faiss.IndexHNSWFlat,
                        opp_ids: list[int], top_k: int = 200) -> list[tuple[int, float]]:
    q = query_vector.reshape(1, -1).astype(np.float32)
    faiss.normalize_L2(q)
    distances, indices = index.search(q, min(top_k, len(opp_ids)))
    results = []
    for dist, idx in zip(distances[0], indices[0]):
        if idx < 0 or idx >= len(opp_ids):
            continue
        results.append((opp_ids[idx], float(dist)))
    return results


def build_index_from_db(conn, index_path: str = INDEX_PATH,
                        id_map_path: str = ID_MAP_PATH,
                        progress_callback=None) -> tuple[faiss.IndexHNSWFlat, list[int]]:
    from db.database import get_opportunities, save_embedding
    rows = get_opportunities(conn, limit=50000)
    if not rows:
        return None, []

    texts = [f"{r['title']} {r['body']}" for r in rows]
    opp_ids = [r["id"] for r in rows]

    batch = 256
    all_vecs = []
    for i in range(0, len(texts), batch):
        chunk = embed_texts(texts[i: i + batch])
        all_vecs.append(chunk)
        for j, vec in enumerate(chunk):
            save_embedding(conn, opp_ids[i + j], vec)
        if progress_callback:
            progress_callback(i + len(chunk), len(texts))

    vectors = np.vstack(all_vecs)
    return build_faiss_index(vectors, opp_ids, index_path, id_map_path), opp_ids


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    na = np.linalg.norm(a)
    nb = np.linalg.norm(b)
    if na == 0 or nb == 0:
        return 0.0
    return float(np.dot(a, b) / (na * nb))
