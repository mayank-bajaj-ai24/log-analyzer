# Memory-Efficient Log File Analyzer

**RV College of Engineering — Experiential Learning Project 2024-25**
Team 57 · Theme: SDG

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-red.svg)](https://streamlit.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## Overview

Modern systems generate massive log files (GB–TB/day) that are critical for monitoring, debugging, and security. Industry tools like ELK Stack and Splunk often require significant memory (10–20 GB RAM) and costly cloud infrastructure.

This project is a lightweight, memory-efficient alternative designed to process large-scale logs using less than 200 MB of RAM. It does not require a GPU, cloud infrastructure, or labeled data, making it ideal for student environments, small businesses, and IoT edge devices.

### Key Results

| Metric | Our Tool | ELK Stack | Splunk |
|--------|----------|-----------|--------|
| **RAM Required** | < 200 MB | 10–20 GB | 8–16 GB |
| **GPU Needed** | No | Optional | Optional |
| **Cloud Setup** | Not needed | Required | Required |
| **Cost** | Free | Free (self-hosted) | $$$ License |
| **Dedup Reduction** | 60–90% | — | — |
| **Compression** | 5–10× (Parquet) | — | — |

---

## Architecture

```
log-analyzer/
│
├── backend/                        # Pipeline & processing
│   ├── main.py                     # CLI entry point — runs full pipeline
│   ├── requirements.txt            # Python dependencies
│   ├── setup.cfg                   # Pytest configuration
│   ├── pipeline/                   # 5-stage processing pipeline
│   │   ├── ingestion.py            # Stage 1 — streaming line-by-line reader
│   │   ├── parser.py               # Stage 2 — Drain3 log parsing
│   │   ├── deduplication.py        # Stage 3 — MinHash + LSH deduplication
│   │   ├── feature_extraction.py   # Stage 4a — numerical feature vectors
│   │   ├── anomaly_detector.py     # Stage 4b — Isolation Forest scoring
│   │   ├── storage.py              # Stage 5 — PyArrow Parquet write/read
│   │   └── metrics.py              # Memory profiling utilities
│   ├── tests/                      # Unit tests for each module
│   ├── configs/
│   │   └── drain3.ini              # Drain3 config (depth, similarity)
│   ├── data/
│   │   ├── samples/sample.log      # 20-line sample for quick testing
│   │   └── processed/              # Parquet outputs after pipeline run
│   └── evaluation/
│       ├── benchmark.py            # Pipeline vs baseline comparison
│       └── metrics.py              # RAM tracker, F1 score, compression
│
├── frontend/                       # Streamlit Dashboard
│   ├── app.py                      # Entry point — Overview page
│   └── pages/
│       ├── 1_anomalies.py          # Anomaly detection results
│       ├── 2_performance.py        # RAM, compression, tool comparison
│       └── 3_explore.py            # Searchable/filterable log table
│
├── requirements.txt                # Root-level dependencies
├── README.md
├── CONTRIBUTING.md
└── .gitignore
```

---

## Pipeline Operation

The system processes data in a 5-stage pipeline:

1. **Streaming Ingestion**: Reads 500 lines at a time via generator. Memory remains constant regardless of file size.
2. **Drain3 Log Parsing**: Converts raw text into structured templates.
3. **Deduplication (MinHash + LSH)**: Removes 60–90% of near-duplicate entries, retaining unique patterns.
4. **Feature Extraction + Isolation Forest**: Calculates anomaly scores and flags without needing labels or a GPU.
5. **Parquet Storage**: Stores results with 5–10× compression using Snappy. Uses a columnar format for fast queries.

**Memory strategy:** Stages 1, 2, and 3 run per-chunk in a streaming loop. Only deduplicated entries accumulate in RAM. Stage 4 runs on this significantly reduced set.

---

## Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/mayank-bajaj-ai24/LOG-FILE-ANALYZER.git
cd LOG-FILE-ANALYZER
```

### 2. Create a Virtual Environment (recommended)

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

**Required packages:** `drain3`, `datasketch`, `scikit-learn`, `pyarrow`, `pandas`, `streamlit`, `plotly`, `psutil`, `memory-profiler`, `pytest`, `numpy`

---

## Running the Pipeline (Backend)

```bash
cd backend

# Quick test on the 20-line sample
python main.py --input data/samples/sample.log --profile

# Run on a full dataset
python main.py --input data/raw/BGL.log --output data/processed/ --profile

# Without memory profiling
python main.py --input data/samples/sample.log
```

> **Windows Users:** This project is fully compatible with Windows. All Unicode characters have been optimized for standard CMD/PowerShell environments to prevent encoding errors. You can optionally set UTF-8 encoding in your terminal:
> ```powershell
> $env:PYTHONIOENCODING="utf-8"
> ```

---

## Running the Dashboard (Frontend)

```bash
# From the project root
streamlit run frontend/app.py
```

Open **http://localhost:8501** in your browser. The dashboard includes sections for Overview, Anomalies, Performance, and Explore.

The dashboard automatically loads `backend/data/processed/output.parquet` if available, or you can upload any `.parquet` file via the sidebar.

---

## Running Tests

```bash
cd backend

# Run all tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=pipeline
```

---

## Running the Benchmark

```bash
cd backend
python evaluation/benchmark.py --dataset data/samples/sample.log
```

This compares the streaming pipeline against a naive baseline (loading the entire file into memory).

---

## Datasets

We use publicly available datasets from [LogHub](https://github.com/logpai/loghub). Download the desired datasets and place them in `backend/data/raw/`.

| Dataset | Size | Suggested Use |
|---------|------|---------------|
| **BGL** | ~700 MB | Anomaly detection (has ground-truth labels) |
| **HDFS** | ~1.5 GB | High-volume streaming tests |
| **OpenStack** | ~500 MB | Template parsing tests |
| **Apache** | ~50 MB | Quick development and testing |

---

## Tech Stack

| Component | Tool | Rationale |
|-------|------|-----|
| Language | Python 3.10+ | Generator support for streaming |
| Parsing | `drain3` | Fixed-depth tree, streaming-compatible |
| Deduplication | `datasketch` | MinHash + LSH — sub-linear time |
| Anomaly Detection | `scikit-learn` Isolation Forest | Unsupervised, CPU-only, lightweight |
| Storage | `pyarrow` + Parquet | Columnar compression |
| Dashboard | `streamlit` + `plotly` | Interactive dashboard |
| Profiling | `psutil`, `tracemalloc` | Real-time RAM measurement |
| Testing | `pytest` | Unit testing |

---

## SDG Alignment

- **SDG 9 — Industry & Infrastructure**: Makes log analytics accessible on low-cost hardware (students, SMEs, IoT).
- **SDG 12 — Responsible Consumption**: Reduces storage, compute, and energy vs. traditional tools.
- **SDG 13 — Climate Action**: Less energy consumption leads to green computing.

---

## License

MIT License — see [LICENSE](LICENSE) for details.
