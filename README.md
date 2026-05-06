# 🔍 Memory-Efficient Log File Analyzer

> **RV College of Engineering — Experiential Learning Project 2024-25**
> Team 57 · Theme: SDG

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-red.svg)](https://streamlit.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 📌 What Is This?

Modern systems generate **massive log files** (GB–TB/day) that are critical for monitoring, debugging, and security. Industry tools like **ELK Stack** and **Splunk** require **10–20 GB RAM** and costly cloud infrastructure.

This project is a **lightweight, memory-efficient alternative** that processes large-scale logs using **< 200 MB RAM** — no GPU, no cloud, no labeled data needed. Built for student laptops, small businesses, and IoT edge devices.

### Key Results

| Metric | Our Tool | ELK Stack | Splunk |
|--------|----------|-----------|--------|
| **RAM Required** | < 200 MB | 10–20 GB | 8–16 GB |
| **GPU Needed** | ❌ No | Optional | Optional |
| **Cloud Setup** | ❌ Not needed | ✅ Required | ✅ Required |
| **Cost** | Free | Free (self-hosted) | $$$ License |
| **Dedup Reduction** | 60–90% | — | — |
| **Compression** | 5–10× (Parquet) | — | — |

---

## 👥 Team

| # | USN | Name | Modules |
|---|-----|------|---------|
| 1 | 1RV24CS230 | Riya Aggarwal | `ingestion.py`, `test_ingestion.py` |
| 2 | 1RV24CS069 | Chinmayi Siddapur | `parser.py`, `deduplication.py`, `test_parser.py`, `test_dedup.py` |
| 3 | 1RV24CS235 | Roshan George | `feature_extraction.py`, `anomaly_detector.py`, `test_anomaly.py` |
| 4 | 1RV24CI066 | Mayank Bajaj | `storage.py`, `main.py`, `test_storage.py`, Frontend Dashboard |

**Mentors:** Dr. Anitha Sandeep (CS Dept) · Prof. Manasa M (AIML Dept)

---

## 🏗️ Project Structure

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
│   │   ├── test_ingestion.py
│   │   ├── test_parser.py
│   │   ├── test_dedup.py
│   │   ├── test_anomaly.py
│   │   └── test_storage.py         # 19 tests including 10-dict roundtrip
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

## 🔧 How It Works — 5-Stage Pipeline

```
Raw Log File (GB scale)
        │
        ▼
┌─────────────────────────────────────────┐
│ Stage 1 — Streaming Ingestion           │
│ Reads 500 lines at a time via generator │
│ RAM stays constant regardless of size   │
└────────────────────┬────────────────────┘
                     │  (chunk by chunk)
                     ▼
┌─────────────────────────────────────────┐
│ Stage 2 — Drain3 Log Parsing            │
│ Raw text → structured templates         │
│ "Connected to 10.0.0.5" → "... <IP>"   │
└────────────────────┬────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────┐
│ Stage 3 — Deduplication (MinHash + LSH) │
│ Removes 60–90% near-duplicate entries   │
│ Only unique patterns survive            │
└────────────────────┬────────────────────┘
                     │  (deduplicated set)
                     ▼
┌─────────────────────────────────────────┐
│ Stage 4 — Feature Extraction +          │
│           Isolation Forest              │
│ Anomaly score + is_anomaly flag         │
│ No labels, no GPU needed               │
└────────────────────┬────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────┐
│ Stage 5 — Parquet Storage               │
│ 5–10× compression with Snappy          │
│ Columnar format for fast queries        │
└─────────────────────────────────────────┘
```

**Memory strategy:** Stages 1→2→3 run per-chunk in a streaming loop. Only deduplicated entries accumulate in RAM (60–90% smaller than raw input). Stage 4 runs on the reduced set.

---

## 🚀 Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/chinn0329/log-analyzer.git
cd log-analyzer
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

## ▶️ Running the Pipeline (Backend)

```bash
cd backend

# Quick test on the 20-line sample
python main.py --input data/samples/sample.log --profile

# Run on a full dataset
python main.py --input data/raw/BGL.log --output data/processed/ --profile

# Without memory profiling
python main.py --input data/samples/sample.log
```

> **Windows Users:** This project is fully compatible with Windows. All Unicode characters have been optimized for standard CMD/PowerShell environments to prevent encoding errors.
> ```powershell
> # Optional: Ensure UTF-8 output in your terminal
> $env:PYTHONIOENCODING="utf-8"
> ```

### Expected Output

```
============================================================
  Log Analyzer — Run Complete
============================================================
  Input file      :  data/samples/sample.log
  Lines ingested  :  20
  After parsing   :  20 templates extracted
  After dedup     :  16 unique entries
  Dedup reduction :  20.0%
  Anomalies found :  1  (6.2%)
  Output saved    :  data/processed/output.parquet
  Peak RAM        :  80.6 MB
  Total time      :  3.50s
============================================================
```

---

## 📊 Running the Dashboard (Frontend)

```bash
# From the project root
streamlit run frontend/app.py
```

Open **http://localhost:8501** in your browser. The dashboard has 4 pages:

| Page | What It Shows |
|------|---------------|
| **📊 Overview** | Metric cards, log level donut chart, top templates bar chart, anomaly distribution |
| **🚨 Anomalies** | Anomaly table (sorted by score), score histogram, severity breakdown |
| **⚡ Performance** | RAM gauge, compression ratio, dedup impact, tool comparison vs ELK/Splunk |
| **🔎 Explore** | Searchable + filterable table of all log entries |

The dashboard auto-loads `backend/data/processed/output.parquet` if available, or you can upload any `.parquet` file via the sidebar.

---

## 🧪 Running Tests

```bash
cd backend

# Run all tests
python -m pytest tests/ -v

# Run only storage tests (Mayank's module)
python -m pytest tests/test_storage.py -v

# Run with coverage
python -m pytest tests/ --cov=pipeline
```

### Test Summary

| Module | Test File | Tests |
|--------|-----------|-------|
| `ingestion.py` | `test_ingestion.py` | Streaming, chunk sizes, memory |
| `parser.py` | `test_parser.py` | Template extraction, cluster IDs |
| `deduplication.py` | `test_dedup.py` | MinHash, LSH, duplicate removal |
| `anomaly_detector.py` | `test_anomaly.py` | Isolation Forest, scoring |
| `storage.py` | `test_storage.py` | **19 tests** — roundtrip, compression, edge cases |

---

## 📈 Running the Benchmark

```bash
cd backend
python evaluation/benchmark.py --dataset data/samples/sample.log
```

Compares streaming pipeline vs. naive baseline (load entire file into memory).

---

## 📦 Datasets

We use publicly available datasets from [LogHub](https://github.com/logpai/loghub):

| Dataset | Size | Best For |
|---------|------|----------|
| **BGL** | ~700 MB | Anomaly detection (has ground-truth labels) |
| **HDFS** | ~1.5 GB | High-volume streaming tests |
| **OpenStack** | ~500 MB | Template parsing tests |
| **Apache** | ~50 MB | Quick dev and testing |

> Download from [LogHub](https://github.com/logpai/loghub) and place in `backend/data/raw/`.

---

## 🛠️ Tech Stack

| Layer | Tool | Why |
|-------|------|-----|
| Language | Python 3.10+ | Native generator support for streaming |
| Parsing | `drain3` | Fixed-depth tree, streaming-compatible |
| Deduplication | `datasketch` | MinHash + LSH — sub-linear time |
| Anomaly Detection | `scikit-learn` Isolation Forest | No labels, CPU-only, lightweight |
| Storage | `pyarrow` + Parquet | Columnar compression, 5–10× smaller |
| Dashboard | `streamlit` + `plotly` | Interactive dark-mode dashboard |
| Profiling | `psutil`, `tracemalloc` | Real-time RAM measurement |
| Testing | `pytest` | Unit tests per pipeline module |

---

## 🌍 SDG Alignment

| SDG | Contribution |
|-----|-------------|
| **SDG 9 — Industry & Infrastructure** | Makes log analytics accessible on low-cost hardware (students, SMEs, IoT) |
| **SDG 12 — Responsible Consumption** | Reduces storage, compute, and energy vs. traditional tools |
| **SDG 13 — Climate Action** | Less energy = lower carbon emissions = green computing |

---

## 📜 License

MIT License — see [LICENSE](LICENSE) for details.