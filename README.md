# EngageIQ — Smart Engagement Opportunity Scorer

**BAX-423 Final Project · Spring 2026**

> Discover, rank, and act on high-value online engagement opportunities across GitHub and Hacker News — powered by Sentence-BERT embeddings, FAISS ANN retrieval, and Thompson Sampling adaptive ranking.

---

## Quick Start (5 minutes)

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure API keys
```bash
cp .env.example .env
# Edit .env — add your LLM_API_KEY (DeepSeek/Qwen/Moonshot)
# Optional: add GITHUB_TOKEN for live data refresh
```

### 3. Seed the offline database
```bash
python setup_data.py
```
This generates a **synthetic offline demo dataset** of 10,500+ records across all 15 technical domains — seeded from public-source-inspired GitHub/HN templates. Takes ~30 seconds. No internet required after this step.

### 4. Launch the app
```bash
streamlit run app.py
```
Open http://localhost:8501

---

## Architecture

```
Data Sources
  GitHub REST API v3 ──┐
  GH Archive           ├──► Streaming Pipeline (threading + queue)
  Hacker News API ─────┘         │
                                 ▼
                      MinHash Deduplication (Sketching)
                                 │
                                 ▼
                         SQLite Database (10k+ records)
                                 │
                    ┌────────────┴────────────┐
                    ▼                         ▼
        Sentence-BERT Embeddings      Batch Analytics
        (all-MiniLM-L6-v2)           (trends.py)
                    │
                    ▼
           FAISS HNSW Index (ANN)
                    │
                    ▼
         Multi-Stage Ranking Pipeline
         Stage 1: ANN Retrieve (top-200)
         Stage 2: Composite Scoring
                  (relevance 40% + community 25%
                  + visibility 20% + effort 15%)
         Stage 3: Re-rank with diversity + bandit boost
                    │
                    ▼
        Thompson Sampling Bandit (adaptive learning)
        Beta(alpha, beta) per domain, updated on feedback
                    │
                    ▼
             Streamlit Dashboard
        Feed · Analytics · Learning · Export
```

## BAX-423 Techniques

| Technique | Implementation | File |
|-----------|---------------|------|
| **Sketching** | MinHash (128 hash functions, LSH banding) for near-duplicate detection | `scraper/minhash_dedup.py` |
| **Embeddings** | Sentence-BERT all-MiniLM-L6-v2 + FAISS HNSW ANN index | `engine/embeddings.py` |
| **Ranking** | Candidate generation → composite scoring → diversity re-ranking; nDCG@10 metric | `engine/ranker.py` |
| **Adaptive Learning** | Thompson Sampling contextual bandit, Beta posteriors per domain | `engine/learner.py` |
| **Streaming** | Producer/consumer threading pipeline with bounded queue | `scraper/pipeline.py` |

## File Structure

```
code/
├── app.py              Main Streamlit application
├── config.py           API keys, domain definitions
├── setup_data.py       Offline dataset generator (10,500 records)
├── requirements.txt
├── .env.example
├── db/database.py      SQLite schema + CRUD
├── scraper/
│   ├── minhash_dedup.py    MinHash sketching
│   ├── github_scraper.py   GitHub API
│   ├── hackernews_scraper.py
│   └── pipeline.py         Streaming orchestrator
├── engine/
│   ├── embeddings.py   Sentence-BERT + FAISS
│   ├── scorer.py       Composite engagement scoring
│   ├── ranker.py       Multi-stage ranking + nDCG
│   └── learner.py      Thompson Sampling bandit
├── analytics/trends.py Batch trend analytics
├── llm/advisor.py      LLM explain + suggest actions
└── utils/export.py     CSV / PDF brief generator
```

## Deployment (Streamlit Cloud)

1. Push `code/` to a GitHub repo
2. Go to [share.streamlit.io](https://share.streamlit.io), connect the repo, set main file to `app.py`
3. Add env vars from `.env` in Streamlit Cloud Secrets settings

## Evaluation Metric

**nDCG@10** is computed on every ranking call:
- Relevance labels are **self-evaluated proxies** derived from composite scores (0–3 scale), not human-labeled ground truth
- Reported in the Feed tab and Personas tab

## Data Sources

- **Synthetic offline demo dataset** — 10,500+ records in `data/engageiq.db`, seeded from public-source-inspired GitHub/HN templates (real repo names/metadata used as seeds)
- **GitHub REST API v3** — available for live refresh via Admin tab (requires `GITHUB_TOKEN`)
- **Hacker News Firebase API** — available for live refresh via Admin tab (no auth required)
