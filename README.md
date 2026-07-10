# Memory-Efficient Log File Analyzer

**RV College of Engineering — Experiential Learning Project 2024-25**  
**Team 57 · Theme: SDG**

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-red.svg)](https://streamlit.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 📖 Overview

Modern IT systems generate massive log files (GB–TB/day) critical for monitoring, debugging, and security. Standard industry tools like ELK Stack and Splunk often require significant memory (10–20 GB RAM) and costly cloud infrastructure, making them inaccessible for smaller environments.

This project introduces a **lightweight, memory-efficient alternative** designed to process large-scale logs using **less than 200 MB of RAM**. It operates entirely locally without requiring a GPU, cloud infrastructure, or labeled data. This makes it highly suitable for student environments, small businesses, and IoT edge devices.

### Key Performance Results

| Metric | Our Tool | ELK Stack | Splunk |
|--------|----------|-----------|--------|
| **RAM Required** | **< 200 MB** | 10–20 GB | 8–16 GB |
| **Hardware** | **CPU Only** | GPU Optional | GPU Optional |
| **Infrastructure**| **Local / Edge** | Cloud Required | Cloud Required |
| **Data Deduplication** | **60–90% reduction** | — | — |
| **Data Compression** | **5–10× (Parquet)** | — | — |

---

## ✨ Key Features

- **Streaming Ingestion Engine:** Processes files of any size line-by-line, ensuring a constant memory footprint regardless of log volume.
- **Automated Parsing:** Utilizes the Drain3 algorithm to convert raw text logs into structured templates on the fly.
- **Intelligent Deduplication:** Implements MinHash and Local Sensitive Hashing (LSH) to identify and remove near-duplicate entries in sub-linear time.
- **Unsupervised Anomaly Detection:** Leverages Isolation Forests to flag anomalous log entries without requiring pre-labeled training data.
- **Interactive Dashboard:** Provides a rich, user-friendly Streamlit interface for exploring logs, analyzing performance metrics, and investigating anomalies.

---

## 🏗️ Architecture & Pipeline

### Project Structure

```text
log-analyzer/
├── backend/                        # Core processing engine
│   ├── pipeline/                   # 5-stage data processing pipeline
│   ├── configs/                    # Drain3 parsing configurations
│   ├── data/                       # Raw and processed datasets
│   ├── evaluation/                 # Benchmarking and metrics
│   ├── tests/                      # Unit testing suite
│   └── main.py                     # CLI entry point
├── frontend/                       # Interactive web application
│   ├── pages/                      # Dashboard views (Anomalies, Performance, etc.)
│   └── app.py                      # Streamlit entry point
├── requirements.txt                # Dependency list
└── README.md                       # Project documentation
```

### The 5-Stage Processing Pipeline

The system is designed around a strictly memory-bounded 5-stage pipeline:

1. **Streaming Ingestion**: Reads logs in chunks of 500 lines via a Python generator to keep memory usage flat.
2. **Drain3 Log Parsing**: Extracts static templates and dynamic variables from raw log text.
3. **MinHash + LSH Deduplication**: Compares and drops structurally identical log entries, immediately reducing the data volume by up to 90%.
4. **Feature Extraction & Isolation Forest**: Generates numerical vectors and assigns an anomaly score to each unique log entry.
5. **Parquet Storage**: Serializes the refined dataset into Apache Parquet format, compressing it by 5-10x for fast downstream querying.

> **Note on Memory Strategy:** Stages 1, 2, and 3 execute sequentially per chunk. Only the deduplicated, unique entries are retained in RAM to be processed by Stage 4.

---

## 🚀 Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/mayank-bajaj-ai24/LOG-FILE-ANALYZER.git
cd LOG-FILE-ANALYZER
```

### 2. Environment Setup

It is highly recommended to use a virtual environment.

```bash
python -m venv venv

# Windows Activation
venv\Scripts\activate

# Mac/Linux Activation
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 💻 Usage Instructions

### Running the Backend Pipeline

```bash
cd backend

# 1. Quick test using the bundled 20-line sample dataset
python main.py --input data/samples/sample.log --profile

# 2. Run without the memory profiler overhead
python main.py --input data/samples/sample.log

# 3. Process a full-scale dataset (e.g., BGL logs)
python main.py --input data/raw/BGL.log --output data/processed/ --profile
```

> **Windows Users:** The pipeline is fully optimized for Windows. If you encounter character rendering issues in PowerShell, enforce UTF-8 encoding:
> ```powershell
> $env:PYTHONIOENCODING="utf-8"
> ```

### Launching the Dashboard

In a new terminal window (from the project root):

```bash
streamlit run frontend/app.py
```

Navigate to **http://localhost:8501**. The dashboard will automatically detect processed data in `backend/data/processed/output.parquet`, or you can manually upload your own Parquet files.

---

## 🧪 Testing & Benchmarking

### Unit Tests
Ensure system stability by running the comprehensive test suite:
```bash
cd backend
python -m pytest tests/ -v
```

### Performance Benchmarks
Compare our streaming approach against traditional in-memory processing:
```bash
cd backend
python evaluation/benchmark.py --dataset data/samples/sample.log
```

---

## 📊 Recommended Datasets

For extensive testing, we recommend the public datasets from [LogHub](https://github.com/logpai/loghub). Place downloaded logs in the `backend/data/raw/` directory.

| Dataset | File Size | Recommended Use Case |
|---------|-----------|----------------------|
| **BGL** | ~700 MB | Anomaly detection validation (contains ground-truth labels). |
| **HDFS** | ~1.5 GB | Stress-testing the streaming ingestion engine. |
| **OpenStack** | ~500 MB | Evaluating Drain3 template extraction accuracy. |
| **Apache** | ~50 MB | Rapid development, testing, and debugging. |

---

## 🛠️ Technology Stack

| Category | Technology | Purpose |
|----------|------------|---------|
| **Language** | Python 3.10+ | Core logic and memory-efficient generators |
| **Parsing** | `drain3` | High-speed, fixed-depth log parsing |
| **Deduplication** | `datasketch` | Fast, probabilistic similarity search |
| **Machine Learning**| `scikit-learn` | Unsupervised anomaly scoring |
| **Data Storage** | `pyarrow` / Parquet | High-compression columnar storage |
| **Frontend UI** | `streamlit` & `plotly`| Interactive analytics and visualizations |

---

## 🌍 SDG Alignment

This project actively supports the United Nations Sustainable Development Goals:
- **SDG 9 (Industry, Innovation & Infrastructure):** Democratizes access to powerful log analytics by making it viable on low-end consumer hardware.
- **SDG 12 (Responsible Consumption):** Drastically reduces the storage arrays and compute power historically required for log management.
- **SDG 13 (Climate Action):** Lowers overall energy consumption in data centers, promoting a greener computing ecosystem.

---

## 📄 License

Distributed under the MIT License. See [LICENSE](LICENSE) for more information.
