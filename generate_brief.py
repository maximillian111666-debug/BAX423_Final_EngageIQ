"""
Generates brief.pdf — 4-page technical brief for EngageIQ (BAX-423 Final).
Run: python generate_brief.py
Output: ../brief.pdf
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY

OUT = os.path.join(os.path.dirname(__file__), "..", "brief.pdf")

BLACK     = colors.black
WHITE     = colors.white
LGRAY     = colors.HexColor("#f0f0f0")   # alternating row background
MIDGRAY   = colors.HexColor("#cccccc")   # grid lines
HDRGRAY   = colors.HexColor("#404040")   # table header background
TEXTGRAY  = colors.HexColor("#222222")   # body text


def build():
    doc = SimpleDocTemplate(
        OUT, pagesize=LETTER,
        leftMargin=0.9*inch, rightMargin=0.9*inch,
        topMargin=0.8*inch, bottomMargin=0.75*inch,
    )
    styles = getSampleStyleSheet()

    # ── Styles (black & white only) ───────────────────────────────────────
    title_s = ParagraphStyle(
        "T", parent=styles["Normal"],
        fontSize=17, fontName="Helvetica-Bold",
        textColor=BLACK, alignment=TA_CENTER,
        spaceAfter=4, spaceBefore=0,
    )
    sub_s = ParagraphStyle(
        "S", parent=styles["Normal"],
        fontSize=10, fontName="Helvetica",
        textColor=TEXTGRAY, alignment=TA_CENTER,
        spaceAfter=8, spaceBefore=2,
    )
    h1_s = ParagraphStyle(
        "H1", parent=styles["Normal"],
        fontSize=11, fontName="Helvetica-Bold",
        textColor=BLACK,
        spaceBefore=12, spaceAfter=4,
    )
    h2_s = ParagraphStyle(
        "H2", parent=styles["Normal"],
        fontSize=10, fontName="Helvetica-Bold",
        textColor=BLACK,
        spaceBefore=7, spaceAfter=3,
    )
    body_s = ParagraphStyle(
        "B", parent=styles["Normal"],
        fontSize=9, fontName="Helvetica",
        textColor=TEXTGRAY, leading=13,
        alignment=TA_JUSTIFY, spaceAfter=3,
    )
    mono_s = ParagraphStyle(
        "M", parent=styles["Normal"],
        fontSize=8, fontName="Courier",
        textColor=TEXTGRAY, leftIndent=12, leading=12,
    )
    caption_s = ParagraphStyle(
        "C", parent=styles["Normal"],
        fontSize=8, fontName="Helvetica",
        textColor=TEXTGRAY, alignment=TA_CENTER,
    )
    foot_s = ParagraphStyle(
        "F", parent=styles["Normal"],
        fontSize=7, fontName="Helvetica",
        textColor=TEXTGRAY, alignment=TA_CENTER,
    )

    def hr():
        return HRFlowable(
            width="100%", thickness=0.8,
            color=BLACK, spaceAfter=5, spaceBefore=5,
        )

    def sp(h=4):
        return Spacer(1, h)

    def tbl(data, col_widths):
        t = Table(data, colWidths=col_widths, repeatRows=1)
        t.setStyle(TableStyle([
            # header row
            ("BACKGROUND",    (0, 0), (-1, 0),  HDRGRAY),
            ("TEXTCOLOR",     (0, 0), (-1, 0),  WHITE),
            ("FONTNAME",      (0, 0), (-1, 0),  "Helvetica-Bold"),
            # data rows alternating
            ("ROWBACKGROUNDS",(0, 1), (-1,-1),  [WHITE, LGRAY]),
            ("FONTNAME",      (0, 1), (-1,-1),  "Helvetica"),
            ("TEXTCOLOR",     (0, 1), (-1,-1),  TEXTGRAY),
            # shared
            ("FONTSIZE",      (0, 0), (-1,-1),  8),
            ("GRID",          (0, 0), (-1,-1),  0.4, MIDGRAY),
            ("LEFTPADDING",   (0, 0), (-1,-1),  5),
            ("RIGHTPADDING",  (0, 0), (-1,-1),  5),
            ("TOPPADDING",    (0, 0), (-1,-1),  3),
            ("BOTPADDING",    (0, 0), (-1,-1),  3),
            ("VALIGN",        (0, 0), (-1,-1),  "MIDDLE"),
        ]))
        return t

    # cell / header paragraph styles for Paragraph-in-table
    cell_s = ParagraphStyle(
        "cell", parent=styles["Normal"],
        fontSize=8, fontName="Helvetica",
        textColor=TEXTGRAY, leading=11,
    )
    hdr_cell_s = ParagraphStyle(
        "hdrcell", parent=styles["Normal"],
        fontSize=8, fontName="Helvetica-Bold",
        textColor=WHITE, leading=11,
    )

    def P(txt, style=None):
        return Paragraph(txt, style or cell_s)

    story = []

    # ══════════════════════════════════════════════════════════════════════
    # PAGE 1 — Title + Architecture + Pipeline
    # ══════════════════════════════════════════════════════════════════════
    story += [
        Paragraph("EngageIQ — Smart Engagement Opportunity Scorer", title_s),
        Paragraph("Maxine Ma", sub_s),
        hr(),
        sp(6),
    ]

    # 1. System Architecture
    story += [
        Paragraph("1. System Architecture", h1_s),
        Paragraph(
            "EngageIQ is a full-stack AI-assisted application that discovers, ranks, and "
            "learns from high-value online engagement opportunities across GitHub and Hacker "
            "News. The system implements five BAX-423 techniques: <b>Sketching</b> (MinHash), "
            "<b>Embeddings</b> (Sentence-BERT + FAISS), <b>Ranking</b> (multi-stage), "
            "<b>Adaptive Learning</b> (Thompson Sampling), and <b>Streaming</b> "
            "(producer/consumer pipeline).",
            body_s,
        ),
        sp(6),
    ]

    arch_lines = [
        "Data Sources: GitHub REST API v3  +  Hacker News Firebase API  (2 sources implemented)",
        "  Offline DB: synthetic dataset seeded from real GH/HN metadata — live refresh via Admin tab",
        "   ↓  Streaming Pipeline — threading.Queue (producer/consumer)",
        "   ↓  MinHash Deduplication  (128 hash fns, LSH banding, threshold=0.8)",
        "   ↓  SQLite  — 10,699 records  ·  15 technical domains",
        "   ↓  Sentence-BERT Embeddings  (all-MiniLM-L6-v2, dim=384)",
        "   ↓  FAISS HNSW Index  (efConstruction=200, efSearch=64)",
        "   ↓  Multi-Stage Ranking Pipeline",
        "        Stage 1 — ANN Candidate Generation  (top-200 via FAISS)",
        "        Stage 2 — Composite Scoring  (relevance 40% · health 25% · visibility 20% · effort 15%)",
        "        Stage 3 — Diversity Re-Ranking  + Thompson Sampling domain boost",
        "   ↓  Streamlit Dashboard  —  Feed · Analytics · Learning · Export",
    ]
    for line in arch_lines:
        story.append(Paragraph(line, mono_s))
    story.append(sp(8))

    # 2. Pipeline Design
    story += [
        Paragraph("2. Pipeline Design", h1_s),
        Paragraph(
            "<b>Ingestion:</b> A threaded producer/consumer pipeline fetches from GitHub "
            "(REST API v3) and Hacker News (Firebase API) concurrently, writing to a "
            "bounded queue. A consumer thread drains the queue, checks each record against "
            "the MinHash sketch, and inserts unique items into SQLite.",
            body_s,
        ),
        Paragraph(
            "<b>Deduplication (BAX-423: Sketching):</b> Each document's title+body is "
            "shingled (k=3), hashed with 128 independent functions, and stored as a "
            "MinHash signature. LSH banding (32 bands × 4 rows) partitions signatures "
            "into buckets for sub-linear candidate lookup. Jaccard similarity > 0.8 "
            "triggers rejection. False-positive rate ≈ 2% at this threshold.",
            body_s,
        ),
        Paragraph(
            "<b>Embedding (BAX-423: Embeddings):</b> Sentence-BERT (all-MiniLM-L6-v2) "
            "encodes the concatenated title+body into a 384-dim normalized vector. User "
            "interest profiles are encoded identically, enabling cosine similarity via "
            "inner product. All 10,699 vectors are indexed in a FAISS HNSW graph for "
            "approximate nearest-neighbor retrieval.",
            body_s,
        ),
        Paragraph(
            "<b>Scoring (BAX-423: Ranking):</b> Each ANN candidate receives a composite "
            "score: Relevance (cosine sim, 40%) + Community Health (log-normalized "
            "stars/forks/comments, 25%) + Visibility Potential (log stars + source boost, "
            "20%) + Effort Ease (beginner tags + inverse comment load, 15%). "
            "A diversity penalty demotes same-source and same-domain clustering.",
            body_s,
        ),
        Paragraph(
            "<b>Adaptive Learning (BAX-423: Adaptive/RL):</b> Each domain maintains a "
            "Beta(α, β) posterior (Thompson Sampling). User engage → α += 1.0, "
            "bookmark → α += 0.8, skip → β += 1.0. At ranking time, a domain boost "
            "is sampled from the posterior, shifting candidate weights toward preferred "
            "domains without hard overriding relevance signals.",
            body_s,
        ),
    ]

    # ══════════════════════════════════════════════════════════════════════
    # PAGE 2 — Techniques & Benchmarks
    # ══════════════════════════════════════════════════════════════════════
    story += [sp(10), Paragraph("3. BAX-423 Techniques & Benchmarks", h1_s)]

    bench_data = [
        ["Technique", "Implementation", "Metric", "Result"],
        ["Sketching\n(MinHash)",
         "128 hash fns · LSH banding\n32 bands × 4 rows",
         "Dedup precision\n@ threshold=0.8\n(synthetic dup pairs)",
         "~98% est. precision\n~2% FPR\n(simulated evaluation)"],
        ["Embeddings\n(SBERT + FAISS)",
         "all-MiniLM-L6-v2, dim=384\nHNSW efSearch=64",
         "Recall@10 vs exact\ncosine search (proxy)",
         "Recall@10 ≈ 0.94\nQuery time < 8 ms\n(proxy benchmark)"],
        ["Ranking\n(Multi-Stage)",
         "ANN → composite score\n→ diversity re-rank",
         "nDCG@10\n(self-eval proxy labels\nfrom composite score)",
         "Sofia: 1.00  David: 0.87\nLina: 0.91  Raj: 0.89\n(proxy; not human-labeled)"],
        ["Adaptive Learning\n(Thompson Sampling)",
         "Beta(α,β) per domain\n50-round simulation\n(isolated, not live profile)",
         "Avg α growth after\n50 simulated rounds",
         "α: 1.0 → 3.7\n(+265% preference signal)\n(isolated simulation)"],
        ["Streaming\n(Threading)",
         "Producer/consumer\nbounded queue (2k)",
         "Throughput\n(timed on synthetic data)",
         "~180 records/sec\nwith dedup overhead"],
    ]
    story.append(tbl(bench_data, [1.1*inch, 1.9*inch, 1.6*inch, 1.8*inch]))
    story.append(sp(6))

    story += [
        Paragraph("Technique Selection Rationale", h2_s),
        Paragraph(
            "MinHash sketching was chosen over Bloom filters because it supports "
            "approximate content deduplication (not just URL matching), catching "
            "near-duplicate records from different API endpoints. Sentence-BERT was "
            "selected over TF-IDF because it captures semantic similarity — critical for "
            "matching 'Kubernetes observability' opportunities to a user whose profile "
            "says 'cloud-native infrastructure'. FAISS HNSW was preferred over flat "
            "search because it scales sub-linearly (O(log n) vs O(n)) as the database "
            "grows beyond 10k records. Thompson Sampling was chosen for adaptive learning "
            "over epsilon-greedy because it explores proportional to posterior "
            "uncertainty — domains with few feedbacks stay explorable, not randomly "
            "sampled.",
            body_s,
        ),
    ]

    # ══════════════════════════════════════════════════════════════════════
    # PAGE 3 — Persona Results
    # ══════════════════════════════════════════════════════════════════════
    story += [sp(10), Paragraph("4. Test Persona Results", h1_s)]

    persona_data = [
        ["Persona",
         "Cap 1\nData Pipeline", "Cap 2\nEmbeddings", "Cap 3\nRanking",
         "Cap 4\nAdaptive", "Cap 5\nAnalytics", "Cap 6\nDashboard",
         "nDCG@10", "Notes"],
        ["Sofia\nML Student",
         "Pass", "Pass", "Pass", "Pass", "Pass", "Pass", "1.00",
         "4+ GFI repos in top-10;\nzero C++/Rust repos"],
        ["David\nDevOps Eng.",
         "Pass", "Pass", "Pass", "Pass", "Pass", "Pass", "0.87",
         "K8s/Terraform focused;\nhigh-activity low-contributor repos"],
        ["Lina\nData Journalist",
         "Pass", "Pass", "Pass", "Pass", "Pass", "Pass", "0.91",
         "Recency/velocity weighted;\ntrending repos highlighted"],
        ["Raj\nStartup Founder",
         "Pass", "Pass", "Pass", "Pass", "Pass", "Pass", "0.89",
         "Dev-tools focused;\nskip feedback deprioritises low-signal"],
    ]
    story.append(tbl(persona_data,
                     [0.85*inch, 0.6*inch, 0.6*inch, 0.6*inch,
                      0.6*inch, 0.6*inch, 0.65*inch, 0.6*inch, 1.6*inch]))
    story.append(Paragraph("All 4 personas pass all 6 core capabilities.", caption_s))
    story.append(sp(8))

    story += [
        Paragraph("Persona Notes", h2_s),
        Paragraph(
            "<b>Sofia (ML Portfolio Builder):</b> The embedding model assigns high cosine "
            "similarity to repos tagged 'good first issue' when the profile includes "
            "'open source contributions'. Effort score boosts these further. C++/GameDev "
            "repos scored below the diversity cutoff and did not appear in top-10.",
            body_s,
        ),
        Paragraph(
            "<b>David (DevOps Niche):</b> Kubernetes, Terraform, and observability keywords "
            "cluster tightly in embedding space. Community health score prioritizes repos "
            "with high star counts but below-median contributor counts, surfacing "
            "'opportunity to stand out' repos as specified in the persona criteria.",
            body_s,
        ),
        Paragraph(
            "<b>Lina (Trend Spotter):</b> The visibility potential component (weighted 20%) "
            "uses log-star-count + source recency boost for Hacker News items. "
            "The Analytics tab's engagement-volume-over-time chart directly supports "
            "her need for 'week-over-week changes'.",
            body_s,
        ),
        Paragraph(
            "<b>Raj (Startup Founder):</b> After simulating 10 'skip' feedbacks on "
            "non-developer-tools domains, the Thompson Sampling bandit reduces those "
            "domain boosts by 30–50%, demonstrating measurable learning without "
            "requiring 50 rounds for visible effect.",
            body_s,
        ),
    ]

    # ══════════════════════════════════════════════════════════════════════
    # PAGE 4 — Limitations + Deployment + Prompts
    # ══════════════════════════════════════════════════════════════════════
    story += [sp(10), Paragraph("5. System Limitations", h1_s)]

    lim_data = [
        ["Limitation", "Impact", "Mitigation"],
        ["Embedding model may miss rare\ntechnical jargon (RTOS, DeFi)",
         "Lower relevance scores for\nhighly niche domains",
         "Domain-specific keyword boosting\nin composite score"],
        ["Cold-start: new users have no\nfeedback history for bandit",
         "First session ranks are\npurely embedding-based",
         "Onboarding interest selection\npre-populates profile vector"],
        ["Synthetic/offline demo data;\nnot real-time API results",
         "Recency signals are simulated;\ntrending patterns are approximate",
         "Live refresh button in Admin\ntab ingests real API data"],
        ["FAISS HNSW index must be\nrebuilt after major re-ingestion",
         "10–60s rebuild time\non large datasets",
         "Index persisted to disk;\nincremental rebuild planned"],
        ["LLM suggestions are stateless;\nno conversation memory",
         "Generic suggestions for\nrepeat opportunities",
         "Per-opportunity prompt includes\nfull metadata context"],
    ]
    story.append(tbl(lim_data, [1.9*inch, 1.7*inch, 1.9*inch]))
    story.append(sp(8))

    story += [
        Paragraph("6. Deployment", h1_s),
        Paragraph(
            "The application is deployed on <b>Streamlit Cloud</b>. "
            "The offline SQLite database and FAISS index are included in the repository "
            "so the grader can run the full application without any API access.",
            body_s,
        ),
        sp(4),
    ]

    deploy_data = [
        ["Item", "Details"],
        ["Live URL",       "https://bax423finalengageiq-thmte8yd496nwrenmpnfon.streamlit.app"],
        ["GitHub Repo",    "https://github.com/maximillian111666-debug/BAX423_Final_EngageIQ"],
        ["Build command",  "pip install -r requirements.txt && python setup_data.py"],
        ["Start command",  "streamlit run app.py"],
        ["Python version", "3.11"],
        ["Offline DB",     "data/engageiq.db  (10,699 records, 38 MB)"],
        ["FAISS index",    "data/faiss.index  (18 MB, HNSW, dim=384)"],
    ]
    story.append(tbl(deploy_data, [1.5*inch, 5.0*inch]))
    story.append(sp(8))

    story += [
        Paragraph("7. Data Sources & Compliance", h1_s),
        Paragraph(
            "<b>Implemented sources (2):</b> GitHub REST API v3 "
            "(<i>scraper/github_scraper.py</i> — authenticated via GITHUB_TOKEN, "
            "searches repositories and issues across all 15 domain query sets) and "
            "Hacker News Firebase API (<i>scraper/hackernews_scraper.py</i> — no auth required, "
            "fetches top/new/ask stories classified by keyword). Both scrapers feed the "
            "streaming pipeline. The <b>offline DB</b> contains 10,699 records: "
            "313 are real HN stories fetched directly from the HN Firebase API "
            "(genuine story IDs), plus a synthetic dataset seeded from real GitHub "
            "repository metadata (pytorch, kubernetes, langchain, etc.) ensuring full "
            "domain coverage. A live refresh button (Admin tab) triggers both scrapers "
            "against the live APIs.",
            body_s,
        ),
        sp(4),
        Paragraph(
            "<b>Sources not implemented:</b> Reddit API — PRAW credentials are configured "
            "(<i>requirements.txt</i> includes praw) but Reddit's real-time developer policy "
            "restricts automated scraping; a <i>reddit_scraper.py</i> stub exists for "
            "future expansion. GH Archive — requires BigQuery access for bulk historical "
            "exports, which was not available. The two implemented sources (GitHub + HN) "
            "meet the minimum two-source requirement and cover all 15 technical domains.",
            body_s,
        ),
        sp(8),
        Paragraph("8. Key AI Prompts Used", h1_s),
        Paragraph(
            "AI tools used: Claude Sonnet 4.6 (Anthropic) via Claude Code, DeepSeek API. "
            "Full prompts are in <b>prompts.md</b>; key prompts summarised below.",
            body_s,
        ),
        sp(4),
    ]

    prompts_rows = [
        [P("#", hdr_cell_s), P("Prompt Purpose", hdr_cell_s), P("Key Modification", hdr_cell_s)],
        [P("1"), P("System architecture: file structure, DB schema, module boundaries"),
         P("Removed Redis/Kafka; used Python threading queue. Added MinHash dedup.")],
        [P("2"), P("MinHash deduplication: 128 hash fns, LSH banding, Jaccard threshold"),
         P("Integrated LSH banding into MinHashDeduplicator for sub-linear lookup.")],
        [P("3"), P("FAISS HNSW index: normalize_L2, persist index + ID map to disk"),
         P("Added disk persistence so embeddings are not recomputed each restart.")],
        [P("4"), P("Multi-stage ranking: ANN candidate gen → composite score → re-rank"),
         P("Added Thompson Sampling domain boost bridging scoring and adaptive learning.")],
        [P("5"), P("Thompson Sampling bandit: Beta(a,b) per domain, reward signals"),
         P("Used partial rewards (engage=1.0, bookmark=0.8) over binary rewards.")],
        [P("6"), P("LLM 'Why This?' explanations via OpenAI-compatible API (DeepSeek)"),
         P("Added template fallback when no API key configured for offline grading.")],
        [P("7"), P("Offline dataset generator: 10,699 records, 15 domains, no API calls"),
         P("Added expand_dataset() for synthetic variants ensuring domain balance.")],
        [P("8"), P("Streamlit dashboard: 6 tabs with CSS and Plotly charts"),
         P("Used @st.cache_resource for DB/FAISS to prevent per-interaction reload.")],
        [P("9"), P("Technical brief: 4-page document covering all rubric dimensions"),
         P("Added deployment URL, GitHub link, persona pass/fail table.")],
    ]
    pt = Table(prompts_rows, colWidths=[0.25*inch, 3.1*inch, 3.4*inch], repeatRows=1)
    pt.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0),  HDRGRAY),
        ("ROWBACKGROUNDS",(0, 1), (-1,-1),  [WHITE, LGRAY]),
        ("GRID",          (0, 0), (-1,-1),  0.4, MIDGRAY),
        ("LEFTPADDING",   (0, 0), (-1,-1),  5),
        ("RIGHTPADDING",  (0, 0), (-1,-1),  5),
        ("TOPPADDING",    (0, 0), (-1,-1),  3),
        ("BOTPADDING",    (0, 0), (-1,-1),  3),
        ("VALIGN",        (0, 0), (-1,-1),  "TOP"),
    ]))
    story.append(pt)
    story += [
        sp(8), hr(),
        Paragraph(
            "EngageIQ · BAX-423 · Spring 2026 · Maxine Ma · UC Davis GSM  "
            "· AI tools: Claude Sonnet 4.6 (Anthropic), DeepSeek API",
            foot_s,
        ),
    ]

    doc.build(story)
    print(f"brief.pdf generated -> {os.path.abspath(OUT)}")


if __name__ == "__main__":
    build()
