import os
from dotenv import load_dotenv

# Load .env from the same directory as this file (works both locally and on Streamlit Cloud)
_CODE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(_CODE_DIR, ".env"))

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.deepseek.com")
LLM_MODEL = os.getenv("LLM_MODEL", "deepseek-chat")

REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID", "")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET", "")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT", "EngageIQ/1.0 by BAX423")

DB_PATH = os.getenv("DB_PATH", os.path.join(_CODE_DIR, "data", "engageiq.db"))

EMBEDDING_MODEL = "all-MiniLM-L6-v2"
EMBEDDING_DIM = 384

DOMAINS = [
    "Machine Learning",
    "DevOps/K8s",
    "Trending Open-Source",
    "Developer Tools",
    "Cybersecurity",
    "Frontend (React/Web)",
    "B2B SaaS",
    "Blockchain",
    "Python Data Eng",
    "GameDev (C++)",
    "AI Research",
    "Embedded Systems (C/RTOS)",
    "Cloud APIs",
    "Mobile Dev (iOS/Flutter)",
    "Beginner Coding",
]

DOMAIN_QUERIES = {
    "Machine Learning": ["machine learning", "deep learning", "pytorch", "sklearn", "xgboost"],
    "DevOps/K8s": ["kubernetes", "docker", "terraform", "helm", "gitops"],
    "Trending Open-Source": ["awesome list", "open source framework", "trending library"],
    "Developer Tools": ["developer tools", "cli tool", "vscode extension", "linter", "formatter"],
    "Cybersecurity": ["security", "vulnerability", "penetration testing", "ctf", "cryptography"],
    "Frontend (React/Web)": ["react", "vue", "nextjs", "typescript", "tailwindcss"],
    "B2B SaaS": ["saas", "api platform", "enterprise", "multi-tenant"],
    "Blockchain": ["blockchain", "ethereum", "solidity", "web3", "defi"],
    "Python Data Eng": ["pandas", "apache spark", "airflow", "dbt", "data pipeline"],
    "GameDev (C++)": ["game engine", "unreal", "godot", "opengl", "game development"],
    "AI Research": ["llm", "transformer", "diffusion model", "reinforcement learning", "foundation model"],
    "Embedded Systems (C/RTOS)": ["embedded", "rtos", "microcontroller", "arduino", "firmware"],
    "Cloud APIs": ["aws", "azure", "google cloud", "serverless", "lambda"],
    "Mobile Dev (iOS/Flutter)": ["flutter", "swift", "kotlin", "react native", "ios development"],
    "Beginner Coding": ["beginner", "tutorial", "good first issue", "100daysofcode", "learn to code"],
}

HN_DOMAIN_KEYWORDS = {
    "Machine Learning": ["ml", "machine learning", "neural", "pytorch", "tensorflow", "sklearn"],
    "DevOps/K8s": ["kubernetes", "k8s", "docker", "devops", "terraform", "ci/cd"],
    "Trending Open-Source": ["open source", "github", "released", "new library", "framework"],
    "Developer Tools": ["tool", "cli", "editor", "plugin", "extension", "productivity"],
    "Cybersecurity": ["security", "vulnerability", "hack", "exploit", "breach", "encryption"],
    "Frontend (React/Web)": ["react", "vue", "angular", "frontend", "web", "css", "javascript"],
    "B2B SaaS": ["saas", "startup", "b2b", "enterprise", "api"],
    "Blockchain": ["blockchain", "crypto", "ethereum", "web3", "nft", "defi"],
    "Python Data Eng": ["python", "pandas", "spark", "data engineering", "etl", "pipeline"],
    "GameDev (C++)": ["game", "unity", "unreal", "godot", "gamedev", "c++"],
    "AI Research": ["gpt", "llm", "ai", "openai", "anthropic", "diffusion", "transformer"],
    "Embedded Systems (C/RTOS)": ["embedded", "iot", "raspberry pi", "arduino", "rtos", "firmware"],
    "Cloud APIs": ["aws", "azure", "gcp", "cloud", "serverless", "lambda"],
    "Mobile Dev (iOS/Flutter)": ["ios", "android", "flutter", "swift", "mobile", "app store"],
    "Beginner Coding": ["beginner", "learn", "tutorial", "course", "intro", "getting started"],
}
