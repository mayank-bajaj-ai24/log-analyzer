"""
main.py — Entry point for the Memory Efficient Log File Analyzer pipeline.

Processes log files in a STREAMING, chunk-by-chunk fashion:
  - Stages 1–3 run per-chunk (constant RAM regardless of file size)
  - Only deduplicated results accumulate in memory (60–90% smaller)
  - Stage 4 runs on the reduced dataset (fits in RAM easily)
  - Stage 5 saves compressed Parquet output
  - Stage 6 (optional) uses an LLM to explain flagged anomalies

Usage:
    python main.py --input data/samples/sample.log
    python main.py --input data/raw/BGL.log --output data/processed/ --profile
    python main.py --input data/samples/sample.log --explain

Author: Mayank Bajaj (1RV24CI066)
"""

import argparse
import os
import time
import tracemalloc


def parse_args():
    parser = argparse.ArgumentParser(description="Memory Efficient Log Analyzer")
    parser.add_argument("--input", required=True, help="Path to input log file")
    parser.add_argument(
        "--output",
        default="data/processed/",
        help="Output directory for Parquet files",
    )
    parser.add_argument(
        "--profile", action="store_true", help="Enable memory profiling"
    )
    parser.add_argument("--explain", action="store_true", help="Use Gemini LLM to explain flagged anomalies")
    return parser.parse_args()


def run_pipeline(input_path: str, output_dir: str, profile: bool = False, explain: bool = False):
    """
    Execute the full log analysis pipeline.

    Memory strategy:
      - Stages 1->2->3 run per-chunk in a streaming loop.
        Each chunk is ingested, parsed, and deduplicated, then discarded.
        Only unique (deduplicated) entries accumulate.
      - After all chunks, the deduplicated set (60–90% smaller than raw)
        goes through Stage 4 (feature extraction + anomaly detection).
      - Stage 5 saves everything to compressed Parquet.
      - Stage 6 (optional, --explain) asks an LLM to explain flagged anomalies.

    This keeps peak RAM proportional to the DEDUPLICATED size,
    not the raw file size.
    """

    # ── memory profiling ───────────────────────────────────────────────
    if profile:
        tracemalloc.start()

    start = time.time()

    # ── Lazy imports (only load what's needed when it's needed) ────────
    from pipeline.ingestion import stream_logs
    from pipeline.parser import build_parser, parse_chunk
    from pipeline.deduplication import build_lsh, deduplicate_chunk
    from pipeline.feature_extraction import build_features
    from pipeline.anomaly_detector import train_model, score_logs, print_anomaly_summary
    from pipeline.storage import save_parquet
    from pipeline.llm_reasoning import explain_anomalies

    # ── Initialise shared state for streaming stages ───────────────────
    miner = build_parser()                          # Drain3 template miner
    lsh = build_lsh(threshold=0.8, num_perm=64)     # LSH index for dedup

    lines_ingested = 0
    templates_extracted = 0
    deduped_all: list[dict] = []   # only unique entries accumulate here

    # Shared caches for performance
    parse_cache: dict = {}      # masked_line -> (template, cluster_id, params)
    minhash_cache: dict = {}    # template -> MinHash object
    seen_templates: set = set() # templates already processed by dedup

    # ══════════════════════════════════════════════════════════════════
    #  STREAMING LOOP — Stages 1->2->3 per chunk
    #  RAM stays constant: only one chunk + deduped results in memory
    # ══════════════════════════════════════════════════════════════════
    print(f"[1–3/5] Streaming ingestion -> parsing -> dedup ...")
    print(f"        Reading from: {input_path}")
    print()

    t_stage123 = time.time()

    for chunk_num, chunk in enumerate(stream_logs(input_path), start=1):
        chunk_size = len(chunk)
        lines_ingested += chunk_size

        # Stage 2: Parse this chunk (cached — only new patterns hit Drain3)
        parsed = parse_chunk(miner, chunk, _parse_cache=parse_cache)
        templates_extracted += len(parsed)

        # Stage 3: Deduplicate against ALL previously seen entries
        unique = deduplicate_chunk(
            lsh, parsed, num_perm=64,
            _minhash_cache=minhash_cache,
            _seen_templates=seen_templates,
        )
        deduped_all.extend(unique)

        # chunk and parsed are now unreferenced -> eligible for GC

    t_stage123_end = time.time()

    unique_entries = len(deduped_all)
    print()
    print(f"        Total lines ingested : {lines_ingested}")
    print(f"        Templates extracted  : {templates_extracted}")
    print(f"        After dedup          : {unique_entries} unique entries")
    print(f"        Reduction            : {100*(1 - unique_entries/max(lines_ingested,1)):.1f}%")
    print(f"        Stages 1-3 time      : {t_stage123_end - t_stage123:.2f}s")
    print()

    # ══════════════════════════════════════════════════════════════════
    #  Stage 4: Feature extraction + Anomaly detection
    #  Runs on the DEDUPLICATED set (60–90% smaller than raw input)
    # ══════════════════════════════════════════════════════════════════
    print("[4/5] Running feature extraction & anomaly detection ...")
    t_stage4 = time.time()

    featured = build_features(deduped_all)
    feature_matrix = [log["features"] for log in featured]
    model = train_model(feature_matrix)
    results = score_logs(model, featured)

    t_stage4_end = time.time()

    anomalies = [r for r in results if r.get("is_anomaly")]
    anomaly_count = len(anomalies)
    anomaly_pct = (100.0 * anomaly_count / unique_entries) if unique_entries else 0.0
    print(f"      {anomaly_count} anomalies flagged ({anomaly_pct:.1f}%)")
    print(f"      Stage 4 time           : {t_stage4_end - t_stage4:.2f}s")
    print()

    print_anomaly_summary(results)
    print()

    # ══════════════════════════════════════════════════════════════════
    #  Stage 6 (optional): LLM explanation of flagged anomalies
    #  Only called on the small anomalous subset — not the full dataset.
    #  Safe no-op if no GEMINI_API_KEY is configured.
    # ══════════════════════════════════════════════════════════════════
    if explain:
        print("[6/6] Generating LLM explanations for anomalies ...")
        t_stage6 = time.time()
        results = explain_anomalies(results)
        t_stage6_end = time.time()
        print(f"      Stage 6 time           : {t_stage6_end - t_stage6:.2f}s")
        print()

    # ══════════════════════════════════════════════════════════════════
    #  Stage 5: Save to Parquet (compressed columnar format)
    # ══════════════════════════════════════════════════════════════════
    print("[5/5] Saving to Parquet ...")
    t_stage5 = time.time()
    out_path = save_parquet(results, output_dir)
    t_stage5_end = time.time()

    # ── Timing & memory ────────────────────────────────────────────────
    elapsed = time.time() - start

    peak_mb = 0.0
    if profile:
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        peak_mb = peak / 1024 / 1024
    else:
        try:
            import psutil
            peak_mb = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024
        except Exception:
            peak_mb = 0.0

    # ── Compression ratio ──────────────────────────────────────────────
    raw_size_mb = 0.0
    parquet_size_mb = 0.0
    compression_ratio = 0.0
    try:
        raw_size_mb = os.path.getsize(input_path) / 1024 / 1024
        parquet_size_mb = os.path.getsize(out_path) / 1024 / 1024
        if parquet_size_mb > 0:
            compression_ratio = raw_size_mb / parquet_size_mb
    except OSError:
        pass

    # ══════════════════════════════════════════════════════════════════
    #  Final summary
    # ══════════════════════════════════════════════════════════════════
    print()
    print("=" * 60)
    print("  Log Analyzer — Run Complete")
    print("=" * 60)
    print(f"  Input file      :  {input_path}")
    print(f"  Lines ingested  :  {lines_ingested:,}")
    print(f"  After parsing   :  {templates_extracted:,} templates extracted")
    print(f"  After dedup     :  {unique_entries:,} unique entries")
    print(f"  Dedup reduction :  {100*(1 - unique_entries/max(lines_ingested,1)):.1f}%")
    print(f"  Anomalies found :  {anomaly_count:,}  ({anomaly_pct:.1f}%)")
    if explain:
        explained_count = sum(1 for r in results if "llm_explanation" in r)
        print(f"  LLM explained   :  {explained_count:,} anomalies")
    print(f"  Output saved    :  {out_path}")
    if raw_size_mb > 0:
        print(f"  Raw file size   :  {raw_size_mb:.2f} MB")
        print(f"  Parquet size    :  {parquet_size_mb:.2f} MB  ({compression_ratio:.1f}x compression)")
    print(f"  Peak RAM        :  {peak_mb:.1f} MB")
    print(f"  -- Stage Timing --")
    print(f"  Stages 1-3      :  {t_stage123_end - t_stage123:.2f}s  (ingest + parse + dedup)")
    print(f"  Stage 4         :  {t_stage4_end - t_stage4:.2f}s  (features + anomaly)")
    if explain:
        print(f"  Stage 6         :  {t_stage6_end - t_stage6:.2f}s  (LLM explanations)")
    print(f"  Stage 5         :  {t_stage5_end - t_stage5:.2f}s  (Parquet save)")
    print(f"  Total time      :  {elapsed:.2f}s")
    print("=" * 60)


if __name__ == "__main__":
    args = parse_args()
    run_pipeline(args.input, args.output, args.profile, args.explain)