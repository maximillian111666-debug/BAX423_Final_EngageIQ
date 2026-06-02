"""
GitHub REST API v3 scraper.
Fetches repositories and issues across all 15 technical domains.
"""
import time
import requests
from datetime import datetime
from config import GITHUB_TOKEN, DOMAIN_QUERIES, DOMAINS


SESSION = requests.Session()
SESSION.headers.update({
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
})
if GITHUB_TOKEN:
    SESSION.headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"


def _classify_domain(text: str) -> str:
    text_lower = text.lower()
    for domain, keywords in DOMAIN_QUERIES.items():
        if any(kw in text_lower for kw in keywords):
            return domain
    return DOMAINS[0]


def _rate_limit_wait(resp: requests.Response):
    remaining = int(resp.headers.get("X-RateLimit-Remaining", 1))
    if remaining < 5:
        reset_at = int(resp.headers.get("X-RateLimit-Reset", time.time() + 60))
        wait = max(0, reset_at - time.time()) + 1
        time.sleep(min(wait, 30))


def search_repos(query: str, domain: str, per_page: int = 30, max_pages: int = 3) -> list[dict]:
    results = []
    for page in range(1, max_pages + 1):
        try:
            resp = SESSION.get(
                "https://api.github.com/search/repositories",
                params={"q": query, "sort": "stars", "order": "desc",
                        "per_page": per_page, "page": page},
                timeout=15,
            )
            _rate_limit_wait(resp)
            if resp.status_code != 200:
                break
            items = resp.json().get("items", [])
            if not items:
                break
            for item in items:
                results.append({
                    "source": "github",
                    "external_id": f"repo_{item['id']}",
                    "url": item["html_url"],
                    "title": item["full_name"],
                    "body": (item.get("description") or "")[:1000],
                    "domain": domain,
                    "tags": item.get("topics", [])[:10],
                    "stars": item.get("stargazers_count", 0),
                    "forks": item.get("forks_count", 0),
                    "comments": item.get("open_issues_count", 0),
                    "score": item.get("stargazers_count", 0),
                    "activity_score": _repo_activity(item),
                    "created_at": item.get("created_at", ""),
                })
            time.sleep(0.5)
        except Exception:
            break
    return results


def search_issues(query: str, domain: str, per_page: int = 30, max_pages: int = 2) -> list[dict]:
    results = []
    for page in range(1, max_pages + 1):
        try:
            resp = SESSION.get(
                "https://api.github.com/search/issues",
                params={
                    "q": f"{query} label:\"good first issue\" is:open is:issue",
                    "sort": "updated", "order": "desc",
                    "per_page": per_page, "page": page,
                },
                timeout=15,
            )
            _rate_limit_wait(resp)
            if resp.status_code != 200:
                break
            items = resp.json().get("items", [])
            if not items:
                break
            for item in items:
                results.append({
                    "source": "github",
                    "external_id": f"issue_{item['id']}",
                    "url": item["html_url"],
                    "title": item["title"],
                    "body": (item.get("body") or "")[:1000],
                    "domain": domain,
                    "tags": [l["name"] for l in item.get("labels", [])],
                    "stars": 0,
                    "forks": 0,
                    "comments": item.get("comments", 0),
                    "score": item.get("comments", 0),
                    "activity_score": item.get("comments", 0) * 0.5,
                    "created_at": item.get("created_at", ""),
                })
            time.sleep(0.5)
        except Exception:
            break
    return results


def _repo_activity(item: dict) -> float:
    stars = item.get("stargazers_count", 0)
    forks = item.get("forks_count", 0)
    issues = item.get("open_issues_count", 0)
    return min(100.0, (stars * 0.04 + forks * 0.3 + issues * 0.1))


def scrape_all_domains(target_per_domain: int = 50) -> list[dict]:
    all_items: list[dict] = []
    for domain, queries in DOMAIN_QUERIES.items():
        domain_items: list[dict] = []
        for q in queries[:2]:
            repos = search_repos(q, domain, per_page=30, max_pages=2)
            domain_items.extend(repos)
            issues = search_issues(q, domain, per_page=20, max_pages=1)
            domain_items.extend(issues)
            if len(domain_items) >= target_per_domain:
                break
        all_items.extend(domain_items[:target_per_domain])
    return all_items
