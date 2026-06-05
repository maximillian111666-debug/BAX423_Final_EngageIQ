"""
BAX-423 Technique: Multi-Stage Ranking Pipeline.
Stage 1 — Candidate Generation: ANN retrieval via FAISS (top-200).
Stage 2 — Scoring: Composite engagement score per candidate.
Stage 3 — Re-ranking: Combine composite score with domain bandit boost + diversity penalty.

Evaluation metric: nDCG@10 (computed against simulated relevance labels).
"""
import math
import numpy as np
from engine.scorer import score_candidates
from engine.embeddings import retrieve_candidates


def _ndcg_at_k(ranked_scores: list[float], k: int = 10) -> float:
    dcg = sum((2 ** rel - 1) / math.log2(i + 2)
              for i, rel in enumerate(ranked_scores[:k]))
    ideal = sorted(ranked_scores, reverse=True)[:k]
    idcg = sum((2 ** rel - 1) / math.log2(i + 2) for i, rel in enumerate(ideal))
    return dcg / idcg if idcg > 0 else 0.0


def _diversity_penalty(current: dict, already_selected: list[dict]) -> float:
    if not already_selected:
        return 0.0
    same_source = sum(1 for s in already_selected if s.get("source") == current.get("source"))
    same_domain = sum(1 for s in already_selected if s.get("domain") == current.get("domain"))
    return min(0.3, same_source * 0.05 + same_domain * 0.03)


def rerank(scored_items: list[dict], top_n: int = 50,
           diversity: bool = True) -> tuple[list[dict], float]:
    sorted_items = sorted(scored_items, key=lambda x: x.get("composite", 0), reverse=True)

    if not diversity:
        final = sorted_items[:top_n]
    else:
        final: list[dict] = []
        for item in sorted_items:
            penalty = _diversity_penalty(item, final)
            item["final_score"] = max(0.0, item.get("composite", 0) - penalty)
            final.append(item)
        final = sorted(final, key=lambda x: x.get("final_score", 0), reverse=True)[:top_n]

    for rank, item in enumerate(final, 1):
        item["rank"] = rank

    relevance_labels = [min(3, round(item.get("composite", 0) * 3)) for item in final]
    ndcg = _ndcg_at_k(relevance_labels, k=min(10, len(final)))

    return final, ndcg


def full_pipeline(profile_vec: np.ndarray, faiss_index, opp_ids: list[int],
                  opps_by_id: dict, opp_vecs_by_id: dict,
                  domain_boosts: dict[str, float] | None = None,
                  top_k_retrieve: int = 200, top_n_final: int = 50) -> tuple[list[dict], float]:
    candidates = retrieve_candidates(profile_vec, faiss_index, opp_ids, top_k=top_k_retrieve)
    scored = score_candidates(candidates, opps_by_id, profile_vec, opp_vecs_by_id, domain_boosts)
    ranked, ndcg = rerank(scored, top_n=top_n_final)
    return ranked, ndcg


def explain_ranking(item: dict) -> str:
    lines = []
    rel = item.get("relevance", 0)
    health = item.get("community_health", 0)
    vis = item.get("visibility", 0)
    effort = item.get("effort", 0)
    composite = item.get("composite", 0)

    lines.append(f"**Overall Score: {composite:.0%}**")
    lines.append(f"- Relevance to your profile: {rel:.0%}")
    lines.append(f"- Community health (stars/forks/comments): {health:.0%}")
    lines.append(f"- Visibility potential: {vis:.0%}")
    lines.append(f"- Engagement effort (lower = easier): {1 - effort:.0%}")

    if rel > 0.7:
        lines.append("\nStrong match with your stated interests.")
    if item.get("stars", 0) > 1000:
        lines.append(f"High-signal repo with {item['stars']:,} stars.")
    tags = item.get("tags", [])
    if isinstance(tags, str):
        import json
        try:
            tags = json.loads(tags)
        except Exception:
            tags = []
    if "good first issue" in [t.lower() for t in tags]:
        lines.append("Tagged 'good first issue' — beginner friendly.")
    if item.get("source") == "hackernews":
        lines.append("Trending on Hacker News — high visibility opportunity.")
    return "\n".join(lines)
