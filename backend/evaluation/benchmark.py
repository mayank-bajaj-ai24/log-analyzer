import argparse
import time
import tracemalloc
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pipeline.ingestion import stream_logs
from tabulate import tabulate

def measure_streaming(filepath):
    tracemalloc.start()
    start_time = time.time()
    total_lines = 0

    for chunk in stream_logs(filepath, chunk_size=500):
        total_lines += len(chunk)

    end_time = time.time()
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    return {
        "peak_ram_mb": round(peak / (1024 * 1024), 4),
        "time_sec": round(end_time - start_time, 4),
        "lines": total_lines
    }

def measure_bulk(filepath):
    tracemalloc.start()
    start_time = time.time()

    with open(filepath, 'r') as f:
        lines = f.readlines()

    end_time = time.time()
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    return {
        "peak_ram_mb": round(peak / (1024 * 1024), 4),
        "time_sec": round(end_time - start_time, 4),
        "lines": len(lines)
    }

def main():
    parser = argparse.ArgumentParser(description="Benchmark streaming vs bulk log loading")
    parser.add_argument('--dataset', required=True, help='Path to the log file')
    args = parser.parse_args()

    if not os.path.exists(args.dataset):
        print(f"Error: File not found — {args.dataset}")
        sys.exit(1)

    print(f"\nRunning benchmark on: {args.dataset}\n")

    print("Measuring streaming method...")
    stream_result = measure_streaming(args.dataset)

    print("Measuring bulk load method...")
    bulk_result = measure_bulk(args.dataset)

    # calculate savings
    ram_saving = round(
        ((bulk_result["peak_ram_mb"] - stream_result["peak_ram_mb"])
        / bulk_result["peak_ram_mb"]) * 100, 1
    ) if bulk_result["peak_ram_mb"] > 0 else 0

    table = [
        ["Peak RAM (MB)",    stream_result["peak_ram_mb"], bulk_result["peak_ram_mb"]],
        ["Time (seconds)",   stream_result["time_sec"],    bulk_result["time_sec"]],
        ["Lines Processed",  stream_result["lines"],       bulk_result["lines"]],
    ]

    headers = ["Metric", "Streaming", "Bulk Load"]

    print("\n" + "="*50)
    print("        BENCHMARK RESULTS")
    print("="*50)
    print(tabulate(table, headers=headers, tablefmt="grid"))
    print(f"\nRAM saved by streaming: {ram_saving}% less than bulk load")
    print("="*50 + "\n")

if __name__ == "__main__":
    main()