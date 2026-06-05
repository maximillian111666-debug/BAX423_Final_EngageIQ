"""
One-time script: fix fake github.com/generated/ URLs in the DB by replacing
them with real repo URLs from the same domain's template list.
"""
import os, sys, random, sqlite3
sys.path.insert(0, os.path.dirname(__file__))

random.seed(99)

REAL_URLS = {
    "Machine Learning": [
        "https://github.com/pytorch/pytorch",
        "https://github.com/scikit-learn/scikit-learn",
        "https://github.com/huggingface/transformers",
        "https://github.com/keras-team/keras",
        "https://github.com/tensorflow/tensorflow",
        "https://github.com/fastai/fastai",
        "https://github.com/dmlc/xgboost",
        "https://github.com/microsoft/LightGBM",
    ],
    "DevOps/K8s": [
        "https://github.com/kubernetes/kubernetes",
        "https://github.com/helm/helm",
        "https://github.com/hashicorp/terraform",
        "https://github.com/argoproj/argo-cd",
        "https://github.com/prometheus/prometheus",
        "https://github.com/grafana/grafana",
        "https://github.com/docker/compose",
    ],
    "AI Research": [
        "https://github.com/openai/openai-python",
        "https://github.com/microsoft/autogen",
        "https://github.com/langchain-ai/langchain",
        "https://github.com/ggerganov/llama.cpp",
        "https://github.com/openai/whisper",
    ],
    "Frontend (React/Web)": [
        "https://github.com/facebook/react",
        "https://github.com/vuejs/vue",
        "https://github.com/vercel/next.js",
        "https://github.com/vitejs/vite",
        "https://github.com/tailwindlabs/tailwindcss",
        "https://github.com/sveltejs/svelte",
    ],
    "Python Data Eng": [
        "https://github.com/apache/airflow",
        "https://github.com/pandas-dev/pandas",
        "https://github.com/dbt-labs/dbt-core",
        "https://github.com/polars-rs/polars",
        "https://github.com/duckdb/duckdb",
        "https://github.com/ray-project/ray",
    ],
    "Cybersecurity": [
        "https://github.com/rapid7/metasploit-framework",
        "https://github.com/projectdiscovery/nuclei",
        "https://github.com/danielmiessler/SecLists",
        "https://github.com/aquasecurity/trivy",
        "https://github.com/the-art-of-hacking/h4cker",
    ],
    "Blockchain": [
        "https://github.com/ethereum/go-ethereum",
        "https://github.com/bitcoin/bitcoin",
        "https://github.com/solana-labs/solana",
        "https://github.com/OpenZeppelin/openzeppelin-contracts",
        "https://github.com/foundry-rs/foundry",
    ],
    "Developer Tools": [
        "https://github.com/microsoft/vscode",
        "https://github.com/neovim/neovim",
        "https://github.com/jesseduffield/lazygit",
        "https://github.com/sharkdp/bat",
        "https://github.com/junegunn/fzf",
        "https://github.com/ohmyzsh/ohmyzsh",
    ],
    "Trending Open-Source": [
        "https://github.com/public-apis/public-apis",
        "https://github.com/sindresorhus/awesome",
        "https://github.com/kamranahmedse/developer-roadmap",
        "https://github.com/donnemartin/system-design-primer",
        "https://github.com/30-seconds/30-seconds-of-code",
    ],
    "B2B SaaS": [
        "https://github.com/supabase/supabase",
        "https://github.com/calcom/cal.com",
        "https://github.com/nocodb/nocodb",
        "https://github.com/n8n-io/n8n",
        "https://github.com/pocketbase/pocketbase",
        "https://github.com/plausible/analytics",
    ],
    "GameDev (C++)": [
        "https://github.com/godotengine/godot",
        "https://github.com/ocornut/imgui",
        "https://github.com/raysan5/raylib",
        "https://github.com/MonoGame/MonoGame",
        "https://github.com/bulletphysics/bullet3",
    ],
    "Embedded Systems (C/RTOS)": [
        "https://github.com/zephyrproject-rtos/zephyr",
        "https://github.com/espressif/esp-idf",
        "https://github.com/arduino/Arduino",
        "https://github.com/micropython/micropython",
        "https://github.com/FreeRTOS/FreeRTOS",
    ],
    "Cloud APIs": [
        "https://github.com/aws/aws-cli",
        "https://github.com/serverless/serverless",
        "https://github.com/pulumi/pulumi",
        "https://github.com/localstack/localstack",
        "https://github.com/grpc/grpc",
    ],
    "Mobile Dev (iOS/Flutter)": [
        "https://github.com/flutter/flutter",
        "https://github.com/Alamofire/Alamofire",
        "https://github.com/square/retrofit",
        "https://github.com/ionic-team/ionic-framework",
        "https://github.com/airbnb/lottie-ios",
    ],
    "Beginner Coding": [
        "https://github.com/firstcontributions/first-contributions",
        "https://github.com/TheAlgorithms/Python",
        "https://github.com/trekhleb/javascript-algorithms",
        "https://github.com/MunGell/awesome-for-beginners",
        "https://github.com/freeCodeCamp/freeCodeCamp",
        "https://github.com/ossu/computer-science",
    ],
}

FALLBACK = "https://github.com/explore"

from config import DB_PATH

def fix():
    conn = sqlite3.connect(DB_PATH)

    # Fetch all fake github.com/generated/ records
    rows = conn.execute(
        "SELECT id, domain FROM opportunities WHERE url LIKE 'https://github.com/generated/%'"
    ).fetchall()
    print(f"Found {len(rows):,} fake GitHub URLs to fix...")

    updates = []
    for opp_id, domain in rows:
        pool = REAL_URLS.get(domain, [FALLBACK])
        new_url = random.choice(pool)
        updates.append((new_url, opp_id))

    conn.executemany("UPDATE opportunities SET url=? WHERE id=?", updates)
    conn.commit()

    remaining = conn.execute(
        "SELECT COUNT(*) FROM opportunities WHERE url LIKE 'https://github.com/generated/%'"
    ).fetchone()[0]
    print(f"Done. Remaining fake URLs: {remaining}")
    conn.close()

if __name__ == "__main__":
    fix()
