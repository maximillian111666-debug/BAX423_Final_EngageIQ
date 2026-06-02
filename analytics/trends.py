"""
Batch analytics and trend detection across the full opportunity dataset.
Computes: trending topics, most active communities, engagement volume over time,
category distributions, velocity metrics.
"""
import json
import sqlite3
from collections import Counter, defaultdict
from datetime import datetime, timedelta
import numpy as np
from db.database import get_connection, get_domain_stats, get_time_series, get_opportunities


def domain_distribution(conn: sqlite3.Connection) -> list[dict]:
    return get_domain_stats(conn)


def source_distribution(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute("""
        SELECT source, COUNT(*) as count, AVG(activity_score) as avg_activity
        FROM opportunities GROUP BY source ORDER BY count DESC
    """).fetchall()
    return [dict(r) for r in rows]


def top_opportunities_by_domain(conn: sqlite3.Connection, limit_per_domain: int = 5) -> dict[str, list[dict]]:
    from config import DOMAINS
    result = {}
    for domain in DOMAINS:
        rows = conn.execute("""
            SELECT id, title, url, stars, comments, activity_score, source
            FROM opportunities WHERE domain=? ORDER BY activity_score DESC LIMIT ?
        """, (domain, limit_per_domain)).fetchall()
        result[domain] = [dict(r) for r in rows]
    return result


def trending_topics(conn: sqlite3.Connection, top_n: int = 20) -> list[dict]:
    rows = conn.execute(
        "SELECT tags FROM opportunities WHERE tags != '[]' AND tags != ''"
    ).fetchall()
    tag_counts: Counter = Counter()
    for row in rows:
        try:
            tags = json.loads(row[0])
            tag_counts.update(t.lower() for t in tags if isinstance(t, str) and len(t) > 2)
        except Exception:
            pass
    return [{"tag": tag, "count": cnt} for tag, cnt in tag_counts.most_common(top_n)]


def engagement_volume_over_time(conn: sqlite3.Connection) -> list[dict]:
    ts_data = get_time_series(conn)
    daily: dict[str, dict] = defaultdict(lambda: {"count": 0, "stars": 0})
    for row in ts_data:
        day = row.get("day", "")[:10]
        if day:
            daily[day]["count"] += row.get("count", 0)
            daily[day]["stars"] += row.get("stars", 0)
    return [{"date": d, **v} for d, v in sorted(daily.items())]


def fastest_growing_communities(conn: sqlite3.Connection, top_n: int = 10) -> list[dict]:
    rows = conn.execute("""
        SELECT domain, source,
               AVG(stars) as avg_stars,
               MAX(stars) as max_stars,
               COUNT(*) as count,
               AVG(activity_score) as avg_activity
        FROM opportunities
        GROUP BY domain, source
        HAVING count > 5
        ORDER BY avg_activity DESC
        LIMIT ?
    """, (top_n,)).fetchall()
    return [dict(r) for r in rows]


def weekly_engagement_summary(conn: sqlite3.Connection) -> dict:
    total = conn.execute("SELECT COUNT(*) FROM opportunities").fetchone()[0]
    by_source = source_distribution(conn)
    by_domain = domain_distribution(conn)
    top_tags = trending_topics(conn, top_n=10)
    top_opps = conn.execute("""
        SELECT title, url, stars, source, domain
        FROM opportunities ORDER BY activity_score DESC LIMIT 10
    """).fetchall()

    return {
        "total_opportunities": total,
        "by_source": by_source,
        "by_domain": by_domain[:10],
        "top_tags": top_tags,
        "top_opportunities": [dict(r) for r in top_opps],
        "generated_at": datetime.now().isoformat(),
    }


def persona_match_report(conn: sqlite3.Connection, persona_interests: list[str],
                         ranked_items: list[dict], persona_name: str) -> dict:
    interest_text = " ".join(persona_interests).lower()
    pass_criteria: dict[str, bool] = {}

    top10 = ranked_items[:10]
    domains_in_top10 = [i.get("domain", "") for i in top10]
    sources_in_top10 = [i.get("source", "") for i in top10]

    has_github = "github" in sources_in_top10
    has_hn = "hackernews" in sources_in_top10
    pass_criteria["multi_source_in_top10"] = has_github or has_hn

    avg_relevance = np.mean([i.get("relevance", 0) for i in top10]) if top10 else 0
    pass_criteria["avg_relevance_above_0.5"] = avg_relevance > 0.5

    pass_criteria["returned_10_results"] = len(ranked_items) >= 10

    has_explain = all("relevance" in i and "community_health" in i for i in top10)
    pass_criteria["explain_feature_present"] = has_explain

    return {
        "persona": persona_name,
        "total_results": len(ranked_items),
        "avg_relevance": round(avg_relevance, 3),
        "top_domains": list(set(domains_in_top10)),
        "pass_criteria": pass_criteria,
        "pass_rate": sum(pass_criteria.values()) / len(pass_criteria) if pass_criteria else 0,
    }
