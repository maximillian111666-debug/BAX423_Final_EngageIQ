"""
BAX-423 Technique: Adaptive Learning via Thompson Sampling (Contextual Bandit).
Each domain has a Beta(alpha, beta) distribution representing engagement probability.
User feedback (engage/bookmark → reward=1, skip → reward=0) updates the posterior.
Domain boosts are sampled from these posteriors at ranking time.
"""
import numpy as np
from db.database import get_bandit_state, update_bandit, get_connection
from config import DOMAINS


ENGAGE_REWARD = 1.0
BOOKMARK_REWARD = 0.8
SKIP_REWARD = 0.0
ALPHA_INIT = 1.0
BETA_INIT = 1.0


def _load_state(conn, profile_id: int) -> dict[str, tuple[float, float]]:
    state = get_bandit_state(conn, profile_id)
    for domain in DOMAINS:
        if domain not in state:
            state[domain] = (ALPHA_INIT, BETA_INIT)
    return state


def record_feedback(conn, profile_id: int, domain: str, action: str):
    state = _load_state(conn, profile_id)
    alpha, beta = state.get(domain, (ALPHA_INIT, BETA_INIT))
    reward = {"engage": ENGAGE_REWARD, "bookmark": BOOKMARK_REWARD, "skip": SKIP_REWARD}.get(action, 0.0)
    alpha_new = alpha + reward
    beta_new = beta + (1.0 - reward)
    update_bandit(conn, profile_id, domain, alpha_new, beta_new)


def sample_domain_boosts(conn, profile_id: int, n_samples: int = 1000) -> dict[str, float]:
    state = _load_state(conn, profile_id)
    boosts: dict[str, float] = {}
    for domain, (alpha, beta) in state.items():
        sample = np.random.beta(alpha, beta, size=n_samples).mean()
        boosts[domain] = 0.7 + 0.6 * sample
    max_b = max(boosts.values()) if boosts else 1.0
    return {d: v / max_b for d, v in boosts.items()}


def simulate_feedback_rounds(conn, profile_id: int, n_rounds: int = 50) -> list[dict]:
    """Simulate n_rounds of feedback using an isolated in-memory state.
    Does NOT write to the real profile's bandit state."""
    rng = np.random.default_rng(42)
    history: list[dict] = []
    # Start from uniform priors — isolated from the real user profile
    state: dict[str, list[float]] = {d: [ALPHA_INIT, BETA_INIT] for d in DOMAINS}

    for round_i in range(n_rounds):
        domain = rng.choice(DOMAINS)
        action = rng.choice(["engage", "engage", "bookmark", "skip"],
                            p=[0.4, 0.25, 0.15, 0.20])
        reward = {"engage": ENGAGE_REWARD, "bookmark": BOOKMARK_REWARD,
                  "skip": SKIP_REWARD}.get(action, 0.0)
        state[domain][0] += reward
        state[domain][1] += 1.0 - reward

        avg_alpha = np.mean([ab[0] for ab in state.values()])
        boosts: dict[str, float] = {}
        for d, (a, b) in state.items():
            boosts[d] = 0.7 + 0.6 * np.random.beta(a, b, 1000).mean()
        max_b = max(boosts.values())
        boosts = {d: v / max_b for d, v in boosts.items()}
        history.append({
            "round": round_i + 1,
            "avg_alpha": round(avg_alpha, 3),
            "top_domain": max(boosts, key=boosts.get),
            "top_boost": round(boosts[max(boosts, key=boosts.get)], 3),
        })
    return history


def get_domain_preferences(conn, profile_id: int) -> list[dict]:
    state = _load_state(conn, profile_id)
    prefs = []
    for domain, (alpha, beta) in state.items():
        mean = alpha / (alpha + beta)
        prefs.append({
            "domain": domain,
            "alpha": round(alpha, 2),
            "beta": round(beta, 2),
            "engagement_rate": round(mean, 3),
            "confidence": round(alpha + beta, 1),
        })
    return sorted(prefs, key=lambda x: x["engagement_rate"], reverse=True)
