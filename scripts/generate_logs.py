"""
generate_logs.py — Synthetic log generator.

Reads a reference .log/.txt file, learns its message patterns (templates,
log levels, IPs, ports, numbers), and generates a much larger synthetic
log file with the same structure — for stress-testing the pipeline.

Usage:
    python scripts/generate_logs.py --reference data/samples/sample.log --lines 200000
    python scripts/generate_logs.py --reference data/samples/sample.log --lines 200000 --anomaly-rate 0.02
    python scripts/generate_logs.py --reference data/samples/sample.log --lines 200000 --output data/raw/stress_test_200k.log

Output is written to data/raw/ by default — the same folder main.py reads
real datasets from.
"""

import argparse
import random
import re
import os
from datetime import datetime, timedelta


# ── Step 1: Parse the reference file into reusable templates ──────────────

LEVEL_PATTERN = re.compile(r"\b(DEBUG|INFO|WARN|WARNING|ERROR|CRITICAL|FATAL)\b")
TIMESTAMP_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}")
IP_PATTERN = re.compile(r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b")
NUM_PATTERN = re.compile(r"\b\d+(?:\.\d+)?\b")


def load_reference_templates(reference_path: str) -> list[dict]:
    """
    Read the reference log file and extract a template per line:
    the line with timestamp, IPs, and numbers replaced by placeholders,
    plus its detected log level. Used as a pool to generate new lines from.

    Args:
        reference_path: Path to the reference .log or .txt file.

    Returns:
        List of dicts: {"template": str, "level": str}
    """
    if not os.path.exists(reference_path):
        raise FileNotFoundError(f"Reference file not found: {reference_path}")

    templates = []
    with open(reference_path, "r", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            level_match = LEVEL_PATTERN.search(line)
            level = level_match.group(1) if level_match else "INFO"

            # Strip the timestamp out — we regenerate it fresh per line
            template = TIMESTAMP_PATTERN.sub("{TIMESTAMP}", line, count=1)
            # Mark IPs and numbers as fillable slots
            template = IP_PATTERN.sub("{IP}", template)
            template = NUM_PATTERN.sub("{NUM}", template)

            templates.append({"template": template, "level": level})

    if not templates:
        raise ValueError(f"No usable lines found in reference file: {reference_path}")

    return templates


# ── Step 2: Fillers for placeholder slots ──────────────────────────────────

def random_ip() -> str:
    return f"{random.randint(10,192)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"


def random_num() -> int:
    return random.choice([
        random.randint(1, 99),
        random.randint(100, 9999),
        random.randint(1, 8),       # small counts (attempts, ports-ish)
        random.randint(1000, 65000) # port-like
    ])


def fill_template(template: str, timestamp: str) -> str:
    """Replace {TIMESTAMP}, {IP}, {NUM} placeholders with realistic, context-aware values."""
    line = template.replace("{TIMESTAMP}", timestamp, 1)
    while "{IP}" in line:
        line = line.replace("{IP}", random_ip(), 1)

    # Context-aware number filling: percentages and ratios need bounded values
    while "{NUM}" in line:
        idx = line.index("{NUM}")
        tail = line[idx:idx + 7]          # look just after the placeholder
        head = line[max(0, idx - 14):idx] # look just before the placeholder

        if tail.startswith("{NUM}%"):
            value = str(random.randint(50, 100))       # percentage — realistic high-usage range
        elif "ratio:" in head.lower():
            value = f"{random.uniform(0.10, 0.99):.2f}" # ratio — 0 to 1, 2 decimals
        elif "port" in head.lower():
            value = str(random.randint(1024, 65535))    # valid port range
        else:
            value = str(random_num())

        line = line.replace("{NUM}", value, 1)

    return line


# ── Step 3: Anomaly injection ──────────────────────────────────────────────

ANOMALY_MESSAGES = [
    "CRITICAL DISK USAGE EXCEEDED {NUM}% ON NODE worker-{NUM}",
    "CRITICAL OUT OF MEMORY on node worker-{NUM} process killed",
    "ERROR Database connection pool exhausted after {NUM} retries",
    "CRITICAL Kernel panic detected on host {IP}",
    "ERROR Unhandled exception in request handler: NullPointerException",
    "CRITICAL Security breach attempt detected from {IP}",
    "ERROR Replication lag exceeded {NUM}ms threshold on shard {NUM}",
]


def make_anomaly_line(timestamp: str) -> str:
    msg = random.choice(ANOMALY_MESSAGES)
    msg = fill_template(msg, timestamp="")
    return f"{timestamp} {msg}"


# ── Step 4: Main generation loop ───────────────────────────────────────────

def generate_logs(
    reference_path: str,
    output_path: str,
    total_lines: int,
    anomaly_rate: float = 0.01,
    start_time: datetime = None,
    seconds_per_line: float = 1.0,
) -> None:
    """
    Generate a synthetic log file based on patterns from a reference file.

    Args:
        reference_path: Path to the reference .log/.txt file to learn patterns from.
        output_path:    Path where the generated file will be written.
        total_lines:    Number of lines to generate.
        anomaly_rate:   Fraction of lines that should be anomalous (0.0–1.0).
        start_time:     Starting timestamp for the generated logs.
        seconds_per_line: Time gap between consecutive log lines.
    """
    templates = load_reference_templates(reference_path)
    print(f"[GEN] Loaded {len(templates)} templates from {reference_path}")

    if start_time is None:
        start_time = datetime(2024, 1, 15, 8, 0, 0)

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    anomaly_count = 0
    current_time = start_time

    with open(output_path, "w") as out:
        for i in range(total_lines):
            timestamp_str = current_time.strftime("%Y-%m-%d %H:%M:%S")

            if random.random() < anomaly_rate:
                line = make_anomaly_line(timestamp_str)
                anomaly_count += 1
            else:
                chosen = random.choice(templates)
                line = fill_template(chosen["template"], timestamp_str)

            out.write(line + "\n")
            current_time += timedelta(seconds=seconds_per_line)

            if (i + 1) % 20000 == 0:
                print(f"[GEN] {i + 1:,} / {total_lines:,} lines written...")

    file_size_mb = os.path.getsize(output_path) / 1024 / 1024

    print()
    print("=" * 60)
    print("  Log Generation Complete")
    print("=" * 60)
    print(f"  Reference file   : {reference_path}")
    print(f"  Output file      : {output_path}")
    print(f"  Total lines      : {total_lines:,}")
    print(f"  Anomalies seeded : {anomaly_count:,} ({anomaly_count/total_lines*100:.2f}%)")
    print(f"  File size        : {file_size_mb:.2f} MB")
    print("=" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate a synthetic log file from a reference log")
    parser.add_argument("--reference", required=True, help="Path to reference .log/.txt file")
    parser.add_argument("--lines", type=int, default=200_000, help="Number of lines to generate (default: 200000)")
    parser.add_argument("--output", default=None, help="Output file path (default: data/raw/generated_<lines>.log)")
    parser.add_argument("--anomaly-rate", type=float, default=0.01, help="Fraction of anomalous lines (default: 0.01 = 1%%)")
    parser.add_argument("--seconds-per-line", type=float, default=1.0, help="Seconds between log timestamps (default: 1.0)")
    args = parser.parse_args()

    output_path = args.output or f"data/raw/generated_{args.lines}.log"

    generate_logs(
        reference_path=args.reference,
        output_path=output_path,
        total_lines=args.lines,
        anomaly_rate=args.anomaly_rate,
        seconds_per_line=args.seconds_per_line,
    )