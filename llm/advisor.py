"""
LLM integration for:
1. "Why this?" explanations (summarise ranking reasons in natural language).
2. "Suggested Actions" (how to engage with a specific opportunity).
Supports any OpenAI-compatible API (DeepSeek, Qwen, Moonshot, etc.).
"""
import os
from openai import OpenAI
from config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL


def _get_client() -> OpenAI | None:
    if not LLM_API_KEY:
        return None
    return OpenAI(api_key=LLM_API_KEY, base_url=LLM_BASE_URL)


def _call_llm(prompt: str, max_tokens: int = 300) -> str:
    client = _get_client()
    if client is None:
        return _fallback_response(prompt)
    try:
        resp = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": (
                    "You are EngageIQ, a smart assistant that helps professionals "
                    "find high-value online engagement opportunities. Be concise, "
                    "actionable, and specific. Respond in English."
                )},
                {"role": "user", "content": prompt},
            ],
            max_tokens=max_tokens,
            temperature=0.7,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        return _fallback_response(prompt)


def _fallback_response(prompt: str) -> str:
    if "suggested" in prompt.lower() or "action" in prompt.lower():
        return (
            "**Suggested Actions:**\n"
            "1. Read through the repository README and open issues.\n"
            "2. Look for 'good first issue' labels to find beginner-friendly tasks.\n"
            "3. Join the community Discord/Slack if available.\n"
            "4. Leave a thoughtful comment or reaction to increase visibility.\n"
            "5. Star the repo to bookmark it and signal community interest."
        )
    return (
        "This opportunity was ranked highly because it closely matches your stated interests, "
        "has strong community engagement signals (stars, comments), and offers good visibility "
        "potential relative to the effort required to engage."
    )


def explain_opportunity(opp: dict, profile_interests: list[str], scores: dict) -> str:
    interests_str = ", ".join(profile_interests[:5]) if profile_interests else "your interests"
    prompt = f"""
Explain in 3-4 sentences why this engagement opportunity is a strong match for a professional interested in {interests_str}.

Opportunity:
- Title: {opp.get('title', '')}
- Source: {opp.get('source', '')}
- Domain: {opp.get('domain', '')}
- Stars: {opp.get('stars', 0):,}
- Comments: {opp.get('comments', 0)}
- Tags: {', '.join((opp.get('tags') or [])[:5]) if isinstance(opp.get('tags'), list) else ''}

Scores:
- Relevance to profile: {scores.get('relevance', 0):.0%}
- Community health: {scores.get('community_health', 0):.0%}
- Visibility potential: {scores.get('visibility', 0):.0%}

Keep it under 80 words. Be specific about WHY it matches.
"""
    return _call_llm(prompt, max_tokens=150)


def suggest_actions(opp: dict, profile_interests: list[str]) -> str:
    interests_str = ", ".join(profile_interests[:5]) if profile_interests else "technology"
    prompt = f"""
Suggest 3-5 specific, actionable ways to engage with this opportunity for someone interested in {interests_str}.

Opportunity:
- Title: {opp.get('title', '')}
- Source: {opp.get('source', '')}
- URL: {opp.get('url', '')}
- Domain: {opp.get('domain', '')}
- Stars: {opp.get('stars', 0):,}
- Description: {str(opp.get('body', ''))[:300]}

Format as a numbered list. Each action should be concrete (e.g., "Open an issue about X", "Post in r/Y", "Submit a PR that does Z").
Keep it under 150 words total.
"""
    return _call_llm(prompt, max_tokens=200)


def generate_weekly_brief_summary(stats: dict) -> str:
    prompt = f"""
Write a 3-paragraph executive summary for a weekly engagement brief.

Data:
- Total opportunities analyzed: {stats.get('total_opportunities', 0):,}
- Top domains: {', '.join([d['domain'] for d in stats.get('by_domain', [])[:5]])}
- Top tags: {', '.join([t['tag'] for t in stats.get('top_tags', [])[:8]])}
- Sources: {', '.join([s['source'] for s in stats.get('by_source', [])])}

Keep it professional, data-driven, and under 200 words.
Paragraph 1: Overview. Paragraph 2: Key trends. Paragraph 3: Recommended focus areas.
"""
    return _call_llm(prompt, max_tokens=300)
