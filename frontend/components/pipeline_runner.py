"""
pipeline_runner.py — Runs the 5-stage backend pipeline from the frontend.
Uses absolute paths to avoid path resolution issues in Streamlit.
"""

import os
import sys
import time
import tempfile
import tracemalloc
import gc

# Resolve paths using absolute project root
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")

if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)


def get_sample_path():
    """Return the absolute path to the sample log file."""
    return os.path.join(BACKEND_DIR, "data", "samples", "sample.log")


def run_pipeline_with_metrics(log_lines: list[str], output_dir: str = None):
    """
    Run the full 5-stage pipeline on a list of raw log lines.

    Returns a dict with detailed metrics at every stage.
    """
    if output_dir is None:
        output_dir = tempfile.mkdtemp()

    tracemalloc.start()
    start_time = time.time()
    metrics = {"stages": []}

    # ── RAW INPUT STATS ────────────────────────────────────────────────
    raw_text = "\n".join(log_lines)
    raw_size_bytes = len(raw_text.encode("utf-8"))
    total_lines = len(log_lines)

    metrics["input"] = {
        "total_lines": total_lines,
        "raw_size_bytes": raw_size_bytes,
        "raw_size_mb": round(raw_size_bytes / (1024 * 1024), 4),
    }

    # ── STAGE 1: Ingestion (already done — lines are in memory) ────────
    _, mem_after_ingest = tracemalloc.get_traced_memory()
    metrics["stages"].append({
        "name": "Stage 1 — Streaming Ingestion",
        "description": "Read log file line-by-line using generators",
        "lines_in": total_lines,
        "lines_out": total_lines,
        "reduction_pct": 0.0,
        "ram_mb": round(mem_after_ingest / (1024 * 1024), 2),
        "data_loss": "None — every line preserved",
    })

    # ── STAGE 2: Parsing with Drain3 ───────────────────────────────────
    from pipeline.parser import build_parser, parse_line

    config_path = os.path.join(BACKEND_DIR, "configs", "drain3.ini")
    if os.path.exists(config_path):
        miner = build_parser(config_path)
    else:
        miner = build_parser()

    parsed = []
    for line in log_lines:
        parsed.append(parse_line(miner, line))

    unique_templates = len(set(p["template"] for p in parsed))
    _, mem_after_parse = tracemalloc.get_traced_memory()

    metrics["stages"].append({
        "name": "Stage 2 — Drain3 Parsing",
        "description": "Convert raw text -> structured templates + cluster IDs",
        "lines_in": total_lines,
        "lines_out": len(parsed),
        "unique_templates": unique_templates,
        "reduction_pct": 0.0,
        "ram_mb": round(mem_after_parse / (1024 * 1024), 2),
        "data_loss": "None — raw line preserved alongside template",
    })

    # ── STAGE 3: Deduplication ─────────────────────────────────────────
    from pipeline.deduplication import build_lsh, deduplicate_chunk

    lsh = build_lsh(threshold=0.8, num_perm=64)
    deduped = deduplicate_chunk(lsh, parsed, num_perm=64)
    _, mem_after_dedup = tracemalloc.get_traced_memory()

    entries_removed = len(parsed) - len(deduped)
    dedup_pct = (entries_removed / len(parsed) * 100) if parsed else 0

    deduped_text = "\n".join(d["raw"] for d in deduped)
    deduped_size_bytes = len(deduped_text.encode("utf-8"))

    metrics["stages"].append({
        "name": "Stage 3 — Deduplication (MinHash + LSH)",
        "description": "Remove near-duplicate entries using hashing",
        "lines_in": len(parsed),
        "lines_out": len(deduped),
        "entries_removed": entries_removed,
        "reduction_pct": round(dedup_pct, 1),
        "size_before_bytes": raw_size_bytes,
        "size_after_bytes": deduped_size_bytes,
        "ram_mb": round(mem_after_dedup / (1024 * 1024), 2),
        "data_loss": "Intentional — only redundant near-duplicates removed. Unique patterns preserved.",
    })

    # ── STAGE 4: Feature Extraction + Anomaly Detection ────────────────
    from pipeline.feature_extraction import build_features
    from pipeline.anomaly_detector import train_model, score_logs

    featured = build_features(deduped)
    feature_matrix = [log["features"] for log in featured]
    model = train_model(feature_matrix)
    results = score_logs(model, featured)
    _, mem_after_anomaly = tracemalloc.get_traced_memory()

    anomalies = [r for r in results if r.get("is_anomaly")]
    anomaly_count = len(anomalies)
    anomaly_pct = (anomaly_count / len(results) * 100) if results else 0

    metrics["stages"].append({
        "name": "Stage 4 — Anomaly Detection (Isolation Forest)",
        "description": "Extract features + flag anomalies using ML",
        "lines_in": len(deduped),
        "lines_out": len(results),
        "anomalies_found": anomaly_count,
        "anomaly_pct": round(anomaly_pct, 1),
        "reduction_pct": 0.0,
        "ram_mb": round(mem_after_anomaly / (1024 * 1024), 2),
        "data_loss": "None — only adds anomaly_score and is_anomaly fields",
    })

    # ── STAGE 5: Parquet Storage ───────────────────────────────────────
    from pipeline.storage import save_parquet

    out_path = save_parquet(results, output_dir)
    parquet_size_bytes = os.path.getsize(out_path)
    _, mem_after_storage = tracemalloc.get_traced_memory()

    compression_ratio = raw_size_bytes / parquet_size_bytes if parquet_size_bytes > 0 else 0

    metrics["stages"].append({
        "name": "Stage 5 — Parquet Compression",
        "description": "Save to columnar Parquet format with Snappy compression",
        "lines_in": len(results),
        "lines_out": len(results),
        "raw_size_bytes": raw_size_bytes,
        "parquet_size_bytes": parquet_size_bytes,
        "compression_ratio": round(compression_ratio, 1),
        "reduction_pct": round((1 - parquet_size_bytes / raw_size_bytes) * 100, 1) if raw_size_bytes > 0 else 0,
        "ram_mb": round(mem_after_storage / (1024 * 1024), 2),
        "data_loss": "None — lossless columnar compression",
    })

    # ── Final metrics ──────────────────────────────────────────────────
    elapsed = time.time() - start_time
    _, peak_mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    metrics["output"] = {
        "total_records": len(results),
        "anomaly_count": anomaly_count,
        "anomaly_pct": round(anomaly_pct, 1),
        "parquet_path": out_path,
        "raw_size_bytes": raw_size_bytes,
        "raw_size_mb": round(raw_size_bytes / (1024 * 1024), 4),
        "parquet_size_bytes": parquet_size_bytes,
        "parquet_size_mb": round(parquet_size_bytes / (1024 * 1024), 4),
        "compression_ratio": round(compression_ratio, 1),
        "dedup_reduction_pct": round(dedup_pct, 1),
        "peak_ram_mb": round(peak_mem / (1024 * 1024), 2),
        "elapsed_seconds": round(elapsed, 2),
    }
    metrics["results_df"] = results
    metrics["parquet_path"] = out_path

    gc.collect()
    return metrics
