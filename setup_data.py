"""
Offline data seed script.
Generates a realistic 10,000+ record dataset spanning all 15 domains
from GitHub API and Hacker News, with deduplication via MinHash.
Run once before starting the app: python setup_data.py
"""
import os
import sys
import json
import random
import sqlite3
import time
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(__file__))

from config import DB_PATH, DOMAINS, DOMAIN_QUERIES
from db.database import init_db, get_connection, insert_opportunity, count_opportunities
from scraper.minhash_dedup import MinHashDeduplicator


SEED = 42
random.seed(SEED)

GITHUB_TEMPLATES = {
    "Machine Learning": [
        ("pytorch/pytorch", "Tensors and Dynamic neural networks in Python with strong GPU acceleration", 78000, 21000, 4200),
        ("scikit-learn/scikit-learn", "scikit-learn: machine learning in Python", 59000, 26000, 1800),
        ("huggingface/transformers", "Transformers: State-of-the-art NLP", 132000, 26000, 1200),
        ("keras-team/keras", "Deep learning for humans", 62000, 19400, 780),
        ("tensorflow/tensorflow", "An Open Source Machine Learning Framework", 188000, 74000, 4100),
        ("openai/gym", "A toolkit for developing reinforcement learning algorithms", 34000, 8700, 420),
        ("fastai/fastai", "The fastai deep learning library", 26000, 7500, 340),
        ("dmlc/xgboost", "Scalable, Portable and Distributed Gradient Boosting", 26800, 8900, 560),
        ("microsoft/LightGBM", "A fast, distributed, high performance gradient boosting framework", 17000, 3700, 380),
        ("catboost/catboost", "A fast, scalable, high performance Gradient Boosting framework", 8200, 1100, 240),
    ],
    "DevOps/K8s": [
        ("kubernetes/kubernetes", "Production-Grade Container Scheduling and Management", 110000, 39000, 2100),
        ("helm/helm", "The Kubernetes Package Manager", 27000, 7100, 680),
        ("hashicorp/terraform", "Terraform enables you to safely and predictably create, change infrastructure", 42000, 9500, 1100),
        ("argoproj/argo-cd", "Declarative Continuous Delivery for Kubernetes", 18000, 5200, 890),
        ("prometheus/prometheus", "The Prometheus monitoring system and time series database", 55000, 8900, 760),
        ("grafana/grafana", "The open and composable observability and data visualization platform", 64000, 12000, 1300),
        ("istio/istio", "Connect, secure, control, and observe services", 35000, 7600, 540),
        ("fluxcd/flux2", "Open and extensible continuous delivery solution for Kubernetes", 6500, 1900, 340),
        ("docker/compose", "Define and run multi-container applications with Docker", 33000, 5100, 450),
        ("containerd/containerd", "An open and reliable container runtime", 17000, 3400, 290),
    ],
    "AI Research": [
        ("openai/openai-python", "The official Python library for the OpenAI API", 23000, 3200, 560),
        ("anthropics/anthropic-sdk-python", "Python SDK for the Anthropic API", 2800, 420, 180),
        ("microsoft/autogen", "Enable Next-Gen Large Language Model Applications", 36000, 5200, 1400),
        ("langchain-ai/langchain", "Building applications with LLMs through composability", 96000, 15000, 2800),
        ("facebookresearch/llama", "Inference code for LLaMA models", 56000, 9800, 620),
        ("THUDM/ChatGLM-6B", "An Open Bilingual Dialogue Language Model", 39000, 5100, 340),
        ("ggerganov/llama.cpp", "Port of Facebook LLaMA model in C/C++", 68000, 9700, 1200),
        ("Stability-AI/stablediffusion", "High-Resolution Image Synthesis with Latent Diffusion Models", 38000, 5600, 480),
        ("openai/whisper", "Robust Speech Recognition via Large-Scale Weak Supervision", 71000, 8200, 780),
        ("CompVis/stable-diffusion", "A latent text-to-image diffusion model", 68000, 9900, 320),
    ],
    "Frontend (React/Web)": [
        ("facebook/react", "The library for web and native user interfaces", 228000, 46000, 1200),
        ("vuejs/vue", "This is the repo for Vue 2", 207000, 33000, 540),
        ("angular/angular", "Deliver web apps with confidence", 96000, 25000, 1100),
        ("vercel/next.js", "The React Framework", 128000, 27000, 2200),
        ("vitejs/vite", "Next generation frontend tooling", 68000, 6200, 680),
        ("tailwindlabs/tailwindcss", "A utility-first CSS framework", 84000, 4200, 560),
        ("sveltejs/svelte", "Cybernetically enhanced web apps", 79000, 4300, 480),
        ("nuxt/nuxt", "The Intuitive Vue Framework", 54000, 4900, 890),
        ("solidjs/solid", "A declarative, efficient, and flexible JavaScript library", 32000, 940, 280),
        ("remix-run/remix", "Build Better Websites", 30000, 2600, 540),
    ],
    "Python Data Eng": [
        ("apache/airflow", "Apache Airflow - A platform to programmatically author and schedule workflows", 37000, 14000, 1800),
        ("apache/spark", "Apache Spark - A unified analytics engine", 39000, 28000, 1200),
        ("pandas-dev/pandas", "Flexible and powerful data analysis / manipulation library for Python", 43000, 18000, 2100),
        ("dbt-labs/dbt-core", "dbt enables data analysts and engineers to transform data", 9800, 1600, 640),
        ("great-expectations/great_expectations", "Always know what to expect from your data", 9800, 1500, 340),
        ("PrefectHQ/prefect", "Prefect is a workflow orchestration tool", 15000, 1500, 480),
        ("dagster-io/dagster", "An orchestration platform for the development, production, and observation of data assets", 11000, 1400, 380),
        ("polars-rs/polars", "Dataframes powered by a multithreaded, vectorized query engine", 30000, 2000, 680),
        ("duckdb/duckdb", "DuckDB is an analytical in-process SQL database management system", 24000, 1900, 580),
        ("ray-project/ray", "Ray is a unified framework for scaling AI and Python applications", 33000, 5700, 780),
    ],
    "Cybersecurity": [
        ("rapid7/metasploit-framework", "Metasploit Framework - the world's most used penetration testing framework", 33000, 14000, 680),
        ("OWASP/owasp-mstg", "The Mobile Security Testing Guide (MSTG)", 12000, 2300, 240),
        ("projectdiscovery/nuclei", "Fast and customizable vulnerability scanner based on templates", 20000, 2700, 480),
        ("Hack-with-Github/Awesome-Hacking", "A collection of various awesome lists for hackers, pentesters and security researchers", 82000, 10000, 120),
        ("danielmiessler/SecLists", "SecLists is the security tester's companion", 57000, 24000, 380),
        ("swisskyrepo/PayloadsAllTheThings", "A list of useful payloads and bypass for Web Application Security", 61000, 15000, 280),
        ("offensive-security/exploitdb", "The official Exploit Database repository", 11000, 3200, 180),
        ("aquasecurity/trivy", "Find vulnerabilities, misconfigurations, secrets in containers, Kubernetes, code repositories", 23000, 2300, 480),
        ("prowler-cloud/prowler", "Prowler is an Open Source Security tool for AWS", 9600, 1500, 280),
        ("the-art-of-hacking/h4cker", "This repository is primarily maintained for educational purposes", 18000, 2800, 120),
    ],
    "Blockchain": [
        ("ethereum/go-ethereum", "Go implementation of the Ethereum protocol", 48000, 20000, 680),
        ("bitcoin/bitcoin", "Bitcoin Core integration/staging tree", 77000, 37000, 340),
        ("solana-labs/solana", "Web-Scale Blockchain for fast, secure, scalable, decentralized apps and marketplaces", 12000, 3700, 580),
        ("OpenZeppelin/openzeppelin-contracts", "OpenZeppelin Contracts is a library for secure smart contract development", 24000, 12000, 480),
        ("smartcontractkit/chainlink", "node of the decentralized oracle network", 6400, 1700, 340),
        ("aave/aave-protocol", "Aave Protocol Version 1.0 - Decentralized Lending Pools", 3200, 1800, 120),
        ("Uniswap/v3-core", "Core smart contracts of Uniswap v3", 4000, 2400, 180),
        ("compound-finance/compound-protocol", "The Compound On-Chain Protocol", 3100, 1700, 120),
        ("trufflesuite/truffle", "A tool for developing smart contracts", 14000, 3600, 280),
        ("foundry-rs/foundry", "Foundry is a blazing fast, portable and modular toolkit", 8200, 720, 380),
    ],
    "Developer Tools": [
        ("microsoft/vscode", "Visual Studio Code", 163000, 29000, 5800),
        ("neovim/neovim", "Vim-fork focused on extensibility and usability", 82000, 5700, 1800),
        ("jesseduffield/lazygit", "simple terminal UI for git commands", 53000, 1900, 480),
        ("cli/cli", "GitHub's official command line tool", 37000, 6000, 780),
        ("sharkdp/bat", "A cat clone with wings", 49000, 1300, 280),
        ("BurntSushi/ripgrep", "ripgrep recursively searches directories for a regex pattern", 47000, 2000, 340),
        ("junegunn/fzf", "A command-line fuzzy finder", 64000, 2500, 340),
        ("starship/starship", "The minimal, blazing-fast, and infinitely customizable prompt", 44000, 2000, 480),
        ("tldr-pages/tldr", "Collaborative cheatsheets for console commands", 49000, 3700, 280),
        ("ohmyzsh/ohmyzsh", "A delightful community-driven framework for managing your zsh configuration", 173000, 26000, 560),
    ],
    "Trending Open-Source": [
        ("public-apis/public-apis", "A collective list of free APIs for use in software and web development", 320000, 35000, 680),
        ("sindresorhus/awesome", "Awesome lists about all kinds of interesting topics", 333000, 28000, 480),
        ("EbookFoundation/free-programming-books", "Freely available programming books", 341000, 62000, 380),
        ("kamranahmedse/developer-roadmap", "Interactive roadmaps, guides and other educational content", 299000, 39000, 680),
        ("jwasham/coding-interview-university", "A complete computer science study plan to become a software engineer", 310000, 80000, 540),
        ("donnemartin/system-design-primer", "Learn how to design large-scale systems", 275000, 46000, 480),
        ("codecrafters-io/build-your-own-x", "Master programming by recreating your favorite technologies from scratch", 311000, 29000, 340),
        ("trimstray/the-book-of-secret-knowledge", "A collection of inspiring lists, manuals, cheatsheets, blogs, hacks, one-liners, cli/web tools", 149000, 9300, 280),
        ("30-seconds/30-seconds-of-code", "Short code snippets for all your development needs", 122000, 12000, 340),
        ("Chalarangelo/30-seconds-of-code", "Short JavaScript code snippets for all your development needs", 122000, 12000, 240),
    ],
    "B2B SaaS": [
        ("supabase/supabase", "The open source Firebase alternative", 73000, 6400, 1800),
        ("appwrite/appwrite", "Build like a team of hundreds", 43000, 3800, 780),
        ("calcom/cal.com", "Scheduling infrastructure for absolutely everyone", 33000, 8000, 1200),
        ("nocodb/nocodb", "Open Source Airtable Alternative", 48000, 3200, 880),
        ("n8n-io/n8n", "Fair-code workflow automation platform", 49000, 6500, 1100),
        ("pocketbase/pocketbase", "Open Source realtime backend in 1 file", 40000, 1900, 680),
        ("plausible/analytics", "Simple, open source, lightweight and privacy-friendly web analytics alternative", 20000, 1200, 480),
        ("formbricks/formbricks", "Open Source Survey Platform", 8800, 1500, 580),
        ("documenso/documenso", "The Open Source DocuSign Alternative", 9200, 1200, 480),
        ("openstatusHQ/openstatus", "The open-source website & API monitoring platform", 7200, 780, 380),
    ],
    "GameDev (C++)": [
        ("godotengine/godot", "Godot Engine – Multi-platform 2D and 3D game engine", 91000, 21000, 1800),
        ("ocornut/imgui", "Dear ImGui: Bloat-free Graphical User interface for C++ with minimal dependencies", 59000, 10000, 680),
        ("libsdl-org/SDL", "Simple Directmedia Layer", 10000, 2000, 340),
        ("SFML/SFML", "Simple and Fast Multimedia Library", 10000, 3400, 280),
        ("raysan5/raylib", "A simple and easy-to-use library to enjoy videogames programming", 21000, 2200, 480),
        ("ValveSoftware/GameNetworkingSockets", "Reliable & unreliable messages over UDP", 4100, 480, 120),
        ("bulletphysics/bullet3", "Bullet Physics SDK: real-time collision detection and multi-physics simulation", 12000, 3300, 240),
        ("MonoGame/MonoGame", "One framework for creating powerful cross-platform games", 11000, 3600, 380),
        ("cocos2d/cocos2d-x", "Cocos2d-x is a suite of open-source, cross-platform, game-development tools", 18000, 7300, 280),
        ("FlaxEngine/FlaxEngine", "Flax Engine – multi-platform 3D game engine", 6400, 560, 180),
    ],
    "Embedded Systems (C/RTOS)": [
        ("zephyrproject-rtos/zephyr", "Primary Git Repository for the Zephyr Project RTOS", 10000, 6400, 680),
        ("espressif/esp-idf", "Espressif IoT Development Framework", 13000, 7200, 780),
        ("arduino/Arduino", "open-source electronics platform", 14000, 5700, 480),
        ("FreeRTOS/FreeRTOS", "FreeRTOS kernel files only", 2900, 1200, 240),
        ("micropython/micropython", "MicroPython - a lean and efficient Python implementation", 19000, 2800, 480),
        ("OP-TEE/optee_os", "Trusted side of the TEE", 2600, 1100, 180),
        ("contiki-ng/contiki-ng", "Contiki-NG: The OS for Next Generation IoT Devices", 1800, 620, 120),
        ("nrfconnect/sdk-nrf", "nRF Connect SDK main repository", 1400, 1400, 340),
        ("tianocore/edk2", "EDK II - UEFI firmware development", 4500, 2500, 280),
        ("wolfSSL/wolfssl", "The wolfSSL library", 2400, 680, 180),
    ],
    "Cloud APIs": [
        ("aws/aws-cli", "Universal Command Line Interface for Amazon Web Services", 15000, 3500, 680),
        ("aws/aws-sdk-js-v3", "Modularized AWS SDK for JavaScript", 3100, 1200, 380),
        ("Azure/azure-sdk-for-python", "This repository is for active development of the Azure SDK for Python", 4500, 3100, 580),
        ("googleapis/google-cloud-python", "Google Cloud Client Libraries for Python", 4800, 1900, 480),
        ("serverless/serverless", "Serverless Framework – Use AWS Lambda and other managed cloud services", 46000, 5700, 780),
        ("pulumi/pulumi", "Pulumi - Infrastructure as Code in any programming language", 20000, 1200, 580),
        ("terraform-aws-modules/terraform-aws-eks", "Terraform module to create AWS EKS resources", 4300, 3300, 280),
        ("localstack/localstack", "A fully functional local AWS cloud stack", 56000, 4100, 780),
        ("open-telemetry/opentelemetry-python", "OpenTelemetry Python API and SDK", 1800, 760, 240),
        ("grpc/grpc", "The C based gRPC library", 41000, 10000, 780),
    ],
    "Mobile Dev (iOS/Flutter)": [
        ("flutter/flutter", "Flutter makes it easy and fast to build beautiful apps for mobile and beyond", 166000, 27000, 12000),
        ("nicklockwood/SwiftyJSON", "The better way to deal with JSON data in Swift", 22000, 3400, 240),
        ("airbnb/lottie-ios", "An iOS library to natively render After Effects vector animations", 25000, 3700, 280),
        ("ReactiveX/RxSwift", "Reactive Programming in Swift", 24000, 4100, 340),
        ("realm/realm-swift", "Realm is a mobile database: a replacement for Core Data & SQLite", 16000, 2100, 280),
        ("Alamofire/Alamofire", "Elegant HTTP Networking in Swift", 40000, 7600, 480),
        ("square/retrofit", "A type-safe HTTP client for Android and Java", 42000, 7400, 480),
        ("JakeWharton/timber", "A logger with a small, extensible API which provides utility on top of Android's normal Log class", 10000, 1700, 180),
        ("material-components/material-components-android", "Modular and customizable Material Design UI components for Android", 16000, 3100, 480),
        ("ionic-team/ionic-framework", "A powerful cross-platform UI toolkit for building native-quality iOS, Android, and Progressive Web Apps", 51000, 13000, 780),
    ],
    "Beginner Coding": [
        ("firstcontributions/first-contributions", "Help beginners to contribute to open source projects", 43000, 88000, 280),
        ("TheAlgorithms/Python", "All Algorithms implemented in Python", 185000, 45000, 880),
        ("trekhleb/javascript-algorithms", "Algorithms and data structures implemented in JavaScript", 188000, 31000, 480),
        ("karan/Projects", "A list of practical projects that anyone can solve in any programming language", 41000, 11000, 180),
        ("MunGell/awesome-for-beginners", "A list of awesome beginners-friendly projects", 67000, 8100, 240),
        ("trending/collections/open-source-organizations", "Some of the best open-source organizations on GitHub", 0, 0, 80),
        ("freeCodeCamp/freeCodeCamp", "freeCodeCamp.org's open-source codebase and curriculum", 401000, 37000, 3200),
        ("ossu/computer-science", "Path to a free self-taught education in Computer Science!", 171000, 22000, 540),
        ("bradtraversy/design-resources-for-developers", "Curated list of design and UI resources from stock photos, web templates", 57000, 13000, 240),
        ("P1xt/p1xt-guides", "Programming guides", 11000, 2100, 120),
    ],
}

HN_TEMPLATES = {
    "Machine Learning": [
        ("Ask HN: Best resources for learning ML from scratch in 2025?", 342, 187),
        ("Show HN: I built an ML model that predicts code review feedback", 412, 93),
        ("GPT-4 can now pass medical licensing exams with 90% accuracy", 876, 234),
        ("The unreasonable effectiveness of recurrent neural networks (revisited)", 523, 145),
        ("Why most ML projects fail: lessons from 50 production deployments", 634, 198),
    ],
    "DevOps/K8s": [
        ("Ask HN: How do you manage Kubernetes at scale without burning out?", 287, 156),
        ("Show HN: A visual tool for designing Kubernetes architectures", 398, 87),
        ("Platform engineering is eating DevOps", 512, 203),
        ("Why we moved from Kubernetes to a simpler container setup", 743, 287),
        ("GitOps in practice: 2 years of production learnings", 421, 134),
    ],
    "AI Research": [
        ("Attention Is All You Need – revisited 7 years later", 654, 213),
        ("Ask HN: Will AI replace software engineers by 2027?", 1243, 876),
        ("Show HN: Open-source alternative to GPT-4 with 70B parameters", 1876, 432),
        ("Mixture of Experts: why sparse models are the future of LLMs", 543, 187),
        ("Constitutional AI: how Anthropic trains aligned models", 678, 243),
    ],
    "Frontend (React/Web)": [
        ("Ask HN: React Server Components 2 years in – worth the complexity?", 312, 198),
        ("Show HN: A new CSS-in-JS library that actually performs well", 287, 123),
        ("The State of JavaScript 2025 results are out", 876, 312),
        ("Web components are finally ready for production", 432, 167),
        ("Why I switched from React to Svelte and never looked back", 654, 289),
    ],
    "Python Data Eng": [
        ("Ask HN: What's your data stack in 2025?", 423, 287),
        ("Show HN: A faster pandas alternative built in Rust", 765, 198),
        ("DuckDB is the SQLite of analytics – a love story", 876, 243),
        ("Apache Iceberg vs Delta Lake: a production comparison", 543, 178),
        ("Why we abandoned Spark for DuckDB + Arrow flight", 678, 234),
    ],
    "Cybersecurity": [
        ("Ask HN: How do you stay updated on security vulnerabilities?", 287, 198),
        ("Show HN: An open-source WAF that's actually easy to configure", 398, 134),
        ("The XZ utils backdoor: a post-mortem", 1243, 543),
        ("Why passkeys haven't replaced passwords yet", 765, 312),
        ("Supply chain attacks are increasing – what can we do?", 654, 287),
    ],
    "Blockchain": [
        ("Ask HN: Is Web3 dead or just resting?", 876, 456),
        ("Show HN: A proof-of-work blockchain in 200 lines of Python", 543, 198),
        ("Ethereum's transition to proof-of-stake: 2 years later", 654, 213),
        ("Why Bitcoin maximalists are right about everything (and wrong about one thing)", 1243, 678),
        ("ZK proofs explained without the math", 765, 287),
    ],
    "Developer Tools": [
        ("Ask HN: What's your must-have developer tool in 2025?", 1243, 678),
        ("Show HN: A terminal emulator that understands your codebase", 876, 312),
        ("Neovim vs VS Code: a flame war that finally has data", 1087, 543),
        ("Why I still use Vim after 15 years", 765, 287),
        ("The best git aliases I've found after 10 years of git", 654, 198),
    ],
    "Trending Open-Source": [
        ("Show HN: My open-source project just hit 10k stars overnight", 1243, 432),
        ("The most-starred GitHub repos of the past month", 765, 187),
        ("Ask HN: What open-source project are you most proud of contributing to?", 543, 312),
        ("Open source sustainability: are we funding it right?", 876, 287),
        ("Show HN: I rewrote a popular tool in Rust and it's 10x faster", 1087, 398),
    ],
    "B2B SaaS": [
        ("Ask HN: How do you find your first 10 B2B customers?", 765, 387),
        ("Show HN: I built a SaaS that makes $50k MRR – AMA", 1243, 543),
        ("Why your SaaS pricing page is losing you customers", 654, 243),
        ("The death of per-seat pricing in B2B software", 543, 198),
        ("Self-hosted vs SaaS: a decision framework for teams", 432, 167),
    ],
    "GameDev (C++)": [
        ("Ask HN: Which game engine should I learn in 2025?", 543, 287),
        ("Show HN: I built a game engine in C++ in 6 months", 765, 234),
        ("Godot vs Unity vs Unreal: an honest 2025 comparison", 876, 312),
        ("Why C++ is still the right choice for performance-critical games", 543, 198),
        ("The rendering techniques behind modern AAA games", 654, 213),
    ],
    "Embedded Systems (C/RTOS)": [
        ("Ask HN: Resources for learning embedded systems in 2025?", 312, 198),
        ("Show HN: A real-time OS for microcontrollers in under 5KB", 543, 167),
        ("Rust vs C for embedded systems: a fair comparison", 765, 287),
        ("How NASA writes mission-critical software", 1087, 398),
        ("The unexpected power of Arduino in production industrial systems", 432, 156),
    ],
    "Cloud APIs": [
        ("Ask HN: AWS vs GCP vs Azure in 2025 – which is actually best?", 876, 456),
        ("Show HN: A tool that reduces AWS costs by 40% automatically", 1243, 387),
        ("Why we moved from microservices to a monolith (and saved $2M)", 1087, 543),
        ("Serverless at scale: lessons from 3 years of AWS Lambda", 765, 287),
        ("The hidden costs of cloud infrastructure nobody talks about", 654, 312),
    ],
    "Mobile Dev (iOS/Flutter)": [
        ("Ask HN: Flutter or React Native in 2025?", 654, 312),
        ("Show HN: I built a Flutter app that makes $10k/month", 876, 243),
        ("Apple's App Store review process is still broken", 1087, 543),
        ("Why Swift is the best language for iOS development", 543, 198),
        ("Cross-platform mobile development: 5 years of production lessons", 765, 287),
    ],
    "Beginner Coding": [
        ("Ask HN: Where should a complete beginner start learning to code?", 1243, 678),
        ("Show HN: A coding challenge platform designed for true beginners", 765, 287),
        ("From zero to junior developer in 6 months: my story", 1087, 432),
        ("Why 'good first issue' is broken and how to fix it", 654, 243),
        ("The best free resources for learning programming in 2025", 876, 312),
    ],
}

GOOD_FIRST_ISSUE_REPOS = {
    "Machine Learning": [
        "Add unit test for custom loss function",
        "Fix typo in documentation for fit() method",
        "Implement missing __repr__ for Model class",
        "Add type hints to utility functions",
        "Update deprecation warnings for old API",
    ],
    "DevOps/K8s": [
        "Add health check endpoint to example deployment",
        "Fix incorrect YAML indentation in Helm chart",
        "Document environment variables for docker-compose",
        "Add --dry-run flag to CLI tool",
        "Fix broken link in contributing guide",
    ],
    "AI Research": [
        "Add example notebook for fine-tuning on custom dataset",
        "Fix memory leak in attention mechanism implementation",
        "Implement beam search decoding",
        "Add GPU memory profiling utility",
        "Document CUDA requirements in README",
    ],
    "Frontend (React/Web)": [
        "Fix accessibility issues in Modal component",
        "Add dark mode support to Button component",
        "Write unit tests for useDebounce hook",
        "Fix TypeScript error in generic component",
        "Add Storybook story for Card component",
    ],
    "Python Data Eng": [
        "Add CSV export functionality",
        "Implement retry logic for failed pipeline steps",
        "Fix timezone handling in date parser",
        "Add progress bar to long-running operations",
        "Document data schema in README",
    ],
    "Beginner Coding": [
        "Add Python solution for binary search",
        "Fix indentation in JavaScript examples",
        "Add explanation to sorting algorithm",
        "Translate README to Spanish",
        "Add test for edge cases in string reversal",
    ],
}


def _random_date(days_back: int = 365) -> str:
    delta = timedelta(days=random.randint(0, days_back))
    return (datetime.now() - delta).isoformat()


def generate_github_repos(target: int = 700) -> list[dict]:
    items: list[dict] = []
    dedup = MinHashDeduplicator()

    for domain, templates in GITHUB_TEMPLATES.items():
        domain_count = 0
        per_template = max(3, target // (len(GITHUB_TEMPLATES) * len(templates)))

        for i, (name, desc, stars_base, forks_base, issues_base) in enumerate(templates):
            for variant in range(per_template):
                stars = max(0, int(stars_base * random.uniform(0.7, 1.3)))
                forks = max(0, int(forks_base * random.uniform(0.7, 1.3)))
                issues = max(0, int(issues_base * random.uniform(0.5, 1.5)))
                title = name if variant == 0 else f"{name} (fork #{variant})"
                body = desc if variant == 0 else f"{desc} — community maintained fork"

                is_dup, sig = dedup.check_and_add(f"{title} {body}")
                if is_dup:
                    continue

                tags = list(DOMAIN_QUERIES.get(domain, [])[:3]) + ["open-source"]
                if domain == "Beginner Coding" or random.random() < 0.2:
                    tags.append("good first issue")

                items.append({
                    "source": "github",
                    "external_id": f"repo_gen_{domain.replace(' ', '_')}_{i}_{variant}",
                    "url": f"https://github.com/{name}",
                    "title": title,
                    "body": body,
                    "domain": domain,
                    "tags": tags,
                    "stars": stars,
                    "forks": forks,
                    "comments": issues,
                    "score": stars,
                    "activity_score": min(100.0, (stars * 0.04 + forks * 0.3 + issues * 0.1) / 100),
                    "created_at": _random_date(730),
                    "minhash": sig[:20],
                })
                domain_count += 1

        good_first_issues = GOOD_FIRST_ISSUE_REPOS.get(domain, [])
        for j, issue_title in enumerate(good_first_issues):
            for k in range(max(1, target // (len(GITHUB_TEMPLATES) * 10))):
                full_title = f"{issue_title} (#{random.randint(1000, 9999)})"
                is_dup, sig = dedup.check_and_add(full_title)
                if is_dup:
                    continue
                items.append({
                    "source": "github",
                    "external_id": f"issue_gen_{domain.replace(' ', '_')}_{j}_{k}",
                    "url": f"https://github.com/{random.choice(GITHUB_TEMPLATES[domain])[0]}/issues/{random.randint(1000, 9999)}",
                    "title": full_title,
                    "body": f"This issue is tagged 'good first issue' and is part of the {domain} ecosystem.",
                    "domain": domain,
                    "tags": ["good first issue", "help wanted"],
                    "stars": 0,
                    "forks": 0,
                    "comments": random.randint(0, 8),
                    "score": 0,
                    "activity_score": random.uniform(0.1, 0.4),
                    "created_at": _random_date(90),
                    "minhash": sig[:20],
                })

    return items


def generate_hn_items(target: int = 350) -> list[dict]:
    items: list[dict] = []
    dedup = MinHashDeduplicator()
    per_domain = max(5, target // len(HN_TEMPLATES))

    for domain, templates in HN_TEMPLATES.items():
        for i, (title_base, score_base, comments_base) in enumerate(templates):
            for variant in range(max(1, per_domain // len(templates))):
                title = title_base if variant == 0 else f"{title_base} [2025 Update]"
                score = max(1, int(score_base * random.uniform(0.5, 1.8)))
                comments = max(0, int(comments_base * random.uniform(0.4, 2.0)))

                is_dup, sig = dedup.check_and_add(title)
                if is_dup:
                    continue

                activity = min(100.0, score * 0.3 + comments * 0.7)
                items.append({
                    "source": "hackernews",
                    "external_id": f"hn_gen_{domain.replace(' ', '_')}_{i}_{variant}_{random.randint(100000, 999999)}",
                    "url": f"https://news.ycombinator.com/item?id={random.randint(30000000, 42000000)}",
                    "title": title,
                    "body": f"Hacker News discussion about {domain.lower()} — {score} points, {comments} comments.",
                    "domain": domain,
                    "tags": [],
                    "stars": score,
                    "forks": 0,
                    "comments": comments,
                    "score": score,
                    "activity_score": activity,
                    "created_at": _random_date(30),
                    "minhash": sig[:20],
                })

    return items


def expand_dataset(base_items: list[dict], target_total: int = 10500) -> list[dict]:
    """Expand dataset to target_total by creating domain-diversified variants."""
    all_items = list(base_items)
    dedup = MinHashDeduplicator()
    for item in all_items:
        text = f"{item['title']} {item.get('body', '')}"
        dedup.check_and_add(text)

    adjectives = [
        "advanced", "modern", "scalable", "production-ready", "high-performance",
        "lightweight", "minimal", "blazing-fast", "type-safe", "zero-dependency",
        "enterprise-grade", "battle-tested", "community-driven", "self-hosted", "cloud-native",
    ]
    actions = [
        "toolkit", "framework", "library", "platform", "service", "tool", "engine",
        "stack", "boilerplate", "template", "starter kit", "SDK", "CLI", "API", "dashboard",
    ]

    while len(all_items) < target_total:
        domain = random.choice(DOMAINS)
        adj = random.choice(adjectives)
        action = random.choice(actions)
        queries = DOMAIN_QUERIES.get(domain, ["open source"])
        keyword = random.choice(queries)
        title = f"{adj.title()} {keyword} {action}"
        body = (f"A {adj} open-source {action} for {domain.lower()} professionals. "
                f"Designed for scalability and ease of use. "
                f"Integrates with {random.choice(queries)}.")

        is_dup, sig = dedup.check_and_add(title)
        if is_dup:
            continue

        stars = random.randint(0, 5000)
        forks = int(stars * random.uniform(0.05, 0.4))
        comments = random.randint(0, 200)
        source = random.choice(["github", "hackernews"])

        tags = [keyword, domain.lower().split("/")[0], "open-source"]
        if random.random() < 0.15:
            tags.append("good first issue")

        all_items.append({
            "source": source,
            "external_id": f"gen_{source}_{len(all_items)}_{random.randint(0, 999999)}",
            "url": (f"https://github.com/generated/{title.lower().replace(' ', '-')}"
                    if source == "github"
                    else f"https://news.ycombinator.com/item?id={random.randint(30000000, 42000000)}"),
            "title": title,
            "body": body,
            "domain": domain,
            "tags": tags,
            "stars": stars,
            "forks": forks,
            "comments": comments,
            "score": stars,
            "activity_score": min(100.0, (stars * 0.04 + forks * 0.3 + comments * 0.7) / 100),
            "created_at": _random_date(365),
            "minhash": sig[:20],
        })

    return all_items


def main():
    print("=" * 60)
    print("EngageIQ Offline Dataset Generator")
    print("=" * 60)

    print("\n[1/4] Initializing database...")
    init_db()
    conn = get_connection()

    existing = count_opportunities(conn)
    if existing >= 10000:
        print(f"Database already has {existing:,} records. Skipping generation.")
        conn.close()
        return

    print("[2/4] Generating GitHub repository and issue records...")
    github_items = generate_github_repos(target=700)
    print(f"      Generated {len(github_items):,} GitHub items across {len(GITHUB_TEMPLATES)} domains")

    print("[3/4] Generating Hacker News discussion records...")
    hn_items = generate_hn_items(target=350)
    print(f"      Generated {len(hn_items):,} HN items")

    combined = github_items + hn_items
    print(f"[4/4] Expanding dataset to 10,500+ records...")
    all_items = expand_dataset(combined, target_total=10500)
    print(f"      Total items after expansion: {len(all_items):,}")

    print("\nInserting into database...")
    inserted = 0
    for item in all_items:
        result = insert_opportunity(conn, item)
        if result:
            inserted += 1

    final_count = count_opportunities(conn)
    conn.close()

    print(f"\n✅ Done! Inserted {inserted:,} new records. Total in DB: {final_count:,}")

    from config import DOMAINS
    conn2 = get_connection()
    print("\nDomain distribution:")
    for domain in DOMAINS:
        count = conn2.execute(
            "SELECT COUNT(*) FROM opportunities WHERE domain=?", (domain,)
        ).fetchone()[0]
        bar = "█" * (count // 50)
        print(f"  {domain:<30} {count:>5} {bar}")
    conn2.close()
    print("\nRun: streamlit run app.py")


if __name__ == "__main__":
    main()
