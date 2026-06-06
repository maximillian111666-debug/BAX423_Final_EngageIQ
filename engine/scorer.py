"""
Engagement scoring: composite of relevance, community health,
visibility potential, and effort estimate.
"""
import math
import numpy as np
from engine.embeddings import cosine_similarity


def community_health_score(opp: dict) -> float:
    stars = opp.get("stars", 0)
    forks = opp.get("forks", 0)
    comments = opp.get("comments", 0)
    raw = math.log1p(stars) * 0.4 + math.log1p(forks) * 0.3 + math.log1p(comments) * 0.3
    return min(1.0, raw / 15.0)


def visibility_potential(opp: dict) -> float:
    stars = opp.get("stars", 0)
    source = opp.get("source", "")
    base = math.log1p(stars) / 15.0
    source_boost = {"github": 0.1, "hackernews": 0.15, "reddit": 0.12}.get(source, 0.0)
    return min(1.0, base + source_boost)


def effort_score(opp: dict) -> float:
    """Higher = easier to engage (more beginner-friendly)."""
    import json
    tags_raw = opp.get("tags") or []
    if isinstance(tags_raw, str):
        try:
            tags_raw = json.loads(tags_raw)
        except Exception:
            tags_raw = []
    tags = [t.lower() for t in tags_raw if isinstance(t, str)]
    beginner_tags = {"good first issue", "beginner", "easy", "help wanted", "starter", "first-timer"}
    has_beginner = bool(beginner_tags & set(tags))
    comments = opp.get("comments", 0)
    difficulty = 1.0 - min(1.0, comments / 50.0)
    return 0.7 * difficulty + 0.3 * (1.0 if has_beginner else 0.3)


def relevance_score(profile_vec: np.ndarray, opp_vec: np.ndarray) -> float:
    if profile_vec is None or opp_vec is None:
        return 0.5
    return max(0.0, cosine_similarity(profile_vec, opp_vec))


def composite_score(opp: dict, profile_vec: np.ndarray,
                    opp_vec: np.ndarray, domain_boost: float = 1.0) -> dict:
    rel = relevance_score(profile_vec, opp_vec)
    health = community_health_score(opp)
    visibility = visibility_potential(opp)
    effort = effort_score(opp)

    composite = (rel * 0.40 + health * 0.25 + visibility * 0.20 + effort * 0.15) * domain_boost

    return {
        "relevance": round(rel, 4),
        "community_health": round(health, 4),
        "visibility": round(visibility, 4),
        "effort": round(effort, 4),
        "composite": round(min(1.0, composite), 4),
    }


def score_candidates(candidates: list[tuple[int, float]], opps_by_id: dict,
                     profile_vec: np.ndarray, opp_vecs_by_id: dict,
                     domain_boosts: dict[str, float] | None = None) -> list[dict]:
    scored = []
    for opp_id, embedding_sim in candidates:
        opp = opps_by_id.get(opp_id)
        if not opp:
            continue
        domain = opp.get("domain", "")
        boost = 1.0
        if domain_boosts:
            boost = domain_boosts.get(domain, 1.0)
        opp_vec = opp_vecs_by_id.get(opp_id)
        scores = composite_score(opp, profile_vec, opp_vec, boost)
        scored.append({**opp, **scores, "embedding_sim": round(embedding_sim, 4)})
    return scored
