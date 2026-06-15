import os
# Use cached model — no internet needed
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_DATASETS_OFFLINE"] = "1"
os.environ["HF_HUB_OFFLINE"] = "1"
import numpy as np
import faiss
import pickle
from sentence_transformers import SentenceTransformer
from rank_bm25 import BM25Okapi


# Load the embedding model once
model = SentenceTransformer('local_model/all-MiniLM-L6-v2')

def embed_chunks(chunks: list) -> np.ndarray:
    """Convert text chunks to vectors"""
    embeddings = model.encode(chunks, show_progress_bar=False)
    return np.array(embeddings).astype('float32')


def build_faiss_index(chunks: list, upload_id: int, index_folder: str) -> dict:
    """Build FAISS index and BM25 index from text chunks"""
    os.makedirs(index_folder, exist_ok=True)

    # ── FAISS Index ──────────────────────────────────────────
    embeddings = embed_chunks(chunks)
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings)

    # ── BM25 Index ───────────────────────────────────────────
    tokenized_chunks = [chunk.lower().split() for chunk in chunks]
    bm25 = BM25Okapi(tokenized_chunks)

    # ── Save everything ──────────────────────────────────────
    index_path  = os.path.join(index_folder, f"upload_{upload_id}.index")
    chunks_path = os.path.join(index_folder, f"upload_{upload_id}.chunks")
    bm25_path   = os.path.join(index_folder, f"upload_{upload_id}.bm25")

    faiss.write_index(index, index_path)

    with open(chunks_path, 'wb') as f:
        pickle.dump(chunks, f)

    with open(bm25_path, 'wb') as f:
        pickle.dump(bm25, f)

    return {
        "success": True,
        "num_vectors": index.ntotal,
        "dimension": dimension,
        "index_path": index_path
    }


def search_faiss_index(query: str, upload_id: int, index_folder: str, top_k: int = 5) -> list:
    """
    Hybrid search: FAISS semantic + BM25 keyword
    Combines both scores for better retrieval
    """
    index_path  = os.path.join(index_folder, f"upload_{upload_id}.index")
    chunks_path = os.path.join(index_folder, f"upload_{upload_id}.chunks")
    bm25_path   = os.path.join(index_folder, f"upload_{upload_id}.bm25")

    if not os.path.exists(index_path):
        return []

    # Load everything
    index = faiss.read_index(index_path)

    with open(chunks_path, 'rb') as f:
        chunks = pickle.load(f)

    # ── FAISS Semantic Search ─────────────────────────────────
    query_vector = model.encode([query]).astype('float32')
    distances, indices = index.search(query_vector, min(top_k * 2, len(chunks)))

    # Normalize FAISS scores (lower distance = better)
    faiss_scores = {}
    max_dist = max(distances[0]) if max(distances[0]) > 0 else 1
    for i, idx in enumerate(indices[0]):
        if idx < len(chunks):
            faiss_scores[idx] = 1 - (distances[0][i] / max_dist)

    # ── BM25 Keyword Search ───────────────────────────────────
    bm25_scores = {}
    if os.path.exists(bm25_path):
        with open(bm25_path, 'rb') as f:
            bm25 = pickle.load(f)

        tokenized_query = query.lower().split()
        scores = bm25.get_scores(tokenized_query)

        # Normalize BM25 scores
        max_score = max(scores) if max(scores) > 0 else 1
        for idx, score in enumerate(scores):
            bm25_scores[idx] = score / max_score

    # ── Hybrid Combination (60% FAISS + 40% BM25) ────────────
    all_indices = set(faiss_scores.keys()) | set(bm25_scores.keys())
    hybrid_scores = {}

    for idx in all_indices:
        faiss_s = faiss_scores.get(idx, 0)
        bm25_s  = bm25_scores.get(idx, 0)
        hybrid_scores[idx] = (0.6 * faiss_s) + (0.4 * bm25_s)

    # Sort by hybrid score and return top_k
    sorted_indices = sorted(hybrid_scores.keys(),
                           key=lambda x: hybrid_scores[x],
                           reverse=True)[:top_k]

    results = []
    for idx in sorted_indices:
        if idx < len(chunks):
            results.append({
                "chunk": chunks[idx],
                "score": hybrid_scores[idx],
                "faiss_score": faiss_scores.get(idx, 0),
                "bm25_score": bm25_scores.get(idx, 0)
            })

    return results