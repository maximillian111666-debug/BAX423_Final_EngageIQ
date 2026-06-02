"""
Hacker News Firebase API scraper (no auth required).
Fetches top stories, new stories, and Ask HN posts.
"""
import time
import requests
from datetime import datetime, timezone
from config import HN_DOMAIN_KEYWORDS, DOMAINS


BASE = "https://hacker-news.firebaseio.com/v0"
SESSION = requests.Session()
SESSION.headers["Accept"] = "application/json"


def _classify_domain(title: str, text: str = "") -> str:
    combined = (title + " " + text).lower()
    scores: dict[str, int] = {}
    for domain, keywords in HN_DOMAIN_KEYWORDS.items():
        scores[domain] = sum(kw in combined for kw in keywords)
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else DOMAINS[2]


def _fetch_item(item_id: int) -> dict | None:
    try:
        resp = SESSION.get(f"{BASE}/item/{item_id}.json", timeout=8)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return None


def _story_to_opp(item: dict) -> dict | None:
    if not item or item.get("type") not in ("story", "ask", "show"):
        return None
    title = item.get("title", "")
    url = item.get("url") or f"https://news.ycombinator.com/item?id={item['id']}"
    body = item.get("text", "") or ""
    domain = _classify_domain(title, body)
    score = item.get("score", 0)
    comments = item.get("descendants", 0)
    ts = item.get("time", 0)
    created = datetime.fromtimestamp(ts, tz=timezone.utc).isoformat() if ts else ""
    activity = min(100.0, score * 0.3 + comments * 0.7)
    return {
        "source": "hackernews",
        "external_id": str(item["id"]),
        "url": url,
        "title": title[:500],
        "body": body[:1000],
        "domain": domain,
        "tags": [],
        "stars": score,
        "forks": 0,
        "comments": comments,
        "score": score,
        "activity_score": activity,
        "created_at": created,
    }


def fetch_top_stories(limit: int = 500) -> list[dict]:
    try:
        resp = SESSION.get(f"{BASE}/topstories.json", timeout=10)
        ids = resp.json()[:limit]
    except Exception:
        return []
    results = []
    for item_id in ids:
        item = _fetch_item(item_id)
        opp = _story_to_opp(item)
        if opp:
            results.append(opp)
        time.sleep(0.05)
    return results


def fetch_new_stories(limit: int = 300) -> list[dict]:
    try:
        resp = SESSION.get(f"{BASE}/newstories.json", timeout=10)
        ids = resp.json()[:limit]
    except Exception:
        return []
    results = []
    for item_id in ids:
        item = _fetch_item(item_id)
        opp = _story_to_opp(item)
        if opp:
            results.append(opp)
        time.sleep(0.05)
    return results


def fetch_ask_stories(limit: int = 200) -> list[dict]:
    try:
        resp = SESSION.get(f"{BASE}/askstories.json", timeout=10)
        ids = resp.json()[:limit]
    except Exception:
        return []
    results = []
    for item_id in ids:
        item = _fetch_item(item_id)
        opp = _story_to_opp(item)
        if opp:
            results.append(opp)
        time.sleep(0.05)
    return results


def scrape_all(limit: int = 800) -> list[dict]:
    items: list[dict] = []
    items.extend(fetch_top_stories(limit // 2))
    items.extend(fetch_new_stories(limit // 4))
    items.extend(fetch_ask_stories(limit // 4))
    return items
