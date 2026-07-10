"""
generate_hdfs_logs.py — Generate realistic HDFS block trace logs.

Produces data in the same format as hdfs_test_abnormal.txt:
    blk_<block_id>,<event_sequence>

Each line represents a block's lifecycle as a sequence of event codes.
Abnormal blocks have incomplete/unusual event sequences.

Usage:
    python scripts/generate_hdfs_logs.py --lines 140000
    python scripts/generate_hdfs_logs.py --lines 140000 --anomaly-rate 0.03
    python scripts/generate_hdfs_logs.py --lines 140000 --output data/raw/hdfs_140k.log
"""

import argparse
import random
import os

# ── HDFS Event Code Reference ─────────────────────────────────────────────
# These codes represent HDFS block lifecycle events observed in real traces:
#  2  = addStoredBlock          (block registered on DataNode)
#  3  = blockReport / heartbeat (periodic check)
#  4  = replicate               (scheduled replication)
#  5  = allocate / write        (block allocation, pipeline open)
#  6  = delete                  (block scheduled for deletion)
#  7  = invalidate              (block marked invalid)
#  9  = writeBlock              (data write to DataNode)
# 10  = readBlock error         (read failure)
# 11  = receiveBlock            (DataNode receives block)
# 13  = blockMap update         (NameNode block map sync)
# 14  = packet error            (write pipeline error)
# 16  = delete confirm          (block deleted from DataNode)
# 18  = recovery                (block recovery initiated)
# 20  = complete                (block completed successfully)
# 21  = close                   (block closed / finalized)
# 22  = serve                   (block served for read)
# 23  = commitBlock             (block committed to NameNode)
# 25  = under-replicated        (block below replication factor)
# 26  = scheduleReplication     (replication scheduled)
# 27  = excessReplica           (too many replicas)
# 28  = pendingReplication      (replication in progress)


# ── Normal Block Lifecycle Patterns ────────────────────────────────────────
# These templates represent healthy HDFS block lifecycles observed in real
# production traces. Each block follows a lifecycle:
#   allocate -> write -> receive -> replicate -> commit -> close

NORMAL_TEMPLATES = [
    # Standard 3-replica write, clean completion
    [5, 22, 5, 5, 11, 9, 11, 9, 11, 9, 26, 26, 26, 2, 2, 2, "{rep}", 23, 23, 23, 21, 21, 28, 26, 21],
    [5, 5, 22, 5, 11, 9, 11, 9, 11, 9, 26, 26, 26, 2, 2, 2, "{rep}", 23, 23, 23, 21, 21, 21, 20],
    [5, 5, 5, 22, 11, 9, 11, 9, 11, 9, 26, 26, 26, 2, 2, 2, "{rep}", 23, 23, 23, 21, 21, 28, 26, 21],
    [22, 5, 5, 5, 11, 9, 11, 9, 11, 9, 26, 26, 26, 2, 2, 2, "{rep}", 23, 23, 23, 21, 21, 21, 20],
    # 2-step commit patterns
    [5, 22, 5, 5, 11, 9, 11, 9, 11, 9, 26, 26, 26, 2, 2, "{rep2}", 23, 23, 23, 21, 21, 28, 26, 21],
    [5, 5, 22, 5, 11, 9, 11, 9, 26, 26, 11, 9, 26, 2, 2, "{rep2}", 23, 23, 23, 21, 21, 28, 26, 21],
    [22, 5, 5, 5, 11, 9, 11, 9, 26, 26, 11, 9, 26, 2, 2, "{rep2}", 23, 23, 23, 21, 21, 21, 20],
    [5, 5, 5, 22, 11, 9, 11, 9, 26, 11, 9, 26, 26, 2, 2, "{rep2}", 23, 23, 23, 21, 20, 21, 21],
    # Reordered receive/schedule patterns
    [5, 22, 5, 5, 11, 9, 11, 9, 26, 11, 9, 26, 26, 2, "{rep2}", 2, 23, 23, 23, 21, 21, 20, 21],
    [5, 5, 22, 5, 11, 9, 11, 9, 11, 9, 26, 26, 26, "{rep2}", 2, 2, 23, 23, 23, 21, 21, 20, 21],
    [22, 5, 5, 5, 26, 26, 11, 9, 11, 9, 11, 9, 26, "{rep2}", 2, 2, 23, 23, 23, 21, 21, 21, 20],
    [22, 5, 5, 5, 26, 26, 26, 11, 9, 11, 9, 11, 9, 2, "{rep2}", 2, 23, 23, 23, 21, 21, 28, 26, 21],
    # Heavy replication (many 4s or 3s — block reports)
    [5, 22, 5, 5, 11, 9, 11, 9, 11, 9, 26, 26, 26, 2, 2, 2, "{heavy_rep}", 23, 23, 23, 21, 21, 21, 20],
    [22, 5, 5, 5, 26, 26, 26, 11, 9, 11, 9, 11, 9, "{heavy_rep}", 2, 2, 23, 23, 23, 21, 21, 20, 21],
    # Recovery patterns (with 18, 25 — under-replicated recovery)
    [22, 5, 5, 5, 25, 26, 26, 26, 11, 9, 11, 9, 11, 9, 18, 5, 26, 6, 16, 21, 3, 2, 2, 23, 23, 23, 21, 21, 21],
    [22, 5, 5, 5, 26, 26, 11, 9, 11, 9, 11, 9, 25, 26, 18, 5, 26, 6, 16, 21, 3, 2, 2, 23, 23, 23, 21, 21, 21],
    [22, 5, 5, 5, 25, 26, 26, 11, 9, 11, 9, 11, 9, 26, 18, 5, 26, 16, 6, 21, 3, 2, 2, 23, 23, 23, 21, 21, 21],
    # Block map update patterns (with 13s)
    [22, 5, 5, 5, 26, 26, 26, 13, 11, 9, 13, 11, 9, 13, 11, 9, 3, 2, 2, 23, 23, 23, 21, 21, 21],
    [22, 5, 5, 5, 13, 13, 13, 26, 26, 26, 11, 9, 11, 9, 11, 9, 2, 3, 2, 23, 23, 23, 21, 21, 21],
    # Excess replica handling (with 27)
    [22, 5, 5, 5, 26, 11, 9, 11, 9, 26, 11, 9, 27, 26, "{rep2}", 2, 23, 23, 23, 21, 21, 21],
    [22, 5, 5, 5, 26, 26, 11, 9, 11, 9, 11, 9, 27, 26, "{rep2}", 2, 2, 23, 23, 23, 21, 21, 21],
]


# ── Abnormal Block Patterns ───────────────────────────────────────────────
# These represent blocks with incomplete lifecycles, failures, or issues.

ABNORMAL_TEMPLATES = [
    # Incomplete — block allocated but never written (orphan)
    [5, 22],
    [22, 5],
    # Write pipeline failure — invalidated
    [5, 22, 5, 7],
    [5, 5, 22, 7],
    [22, 5, 5, 7],
    [5, 22, 5, 7, 11, 10, 14, 7],
    [5, 5, 22, 7, 11, 10, 14, 7],
    [22, 5, 5, 7, 11, 10, 14, 7],
    # Read error during block lifecycle
    [22, 5, 5, 5, 11, 10, 14, 10, 14, 7, 7, 11, 14, 7, 8, 11, 15, 5, 15, 5],
    # Stuck replication — no commit/close
    [5, 22, 5, 5, 11, 9, 11, 9, 26, 26, 26],
    [22, 5, 5, 5, 11, 9, 26, 26, 11, 9, 11, 9],
]


def generate_block_id():
    """Generate a realistic HDFS block ID."""
    sign = random.choice(["", "-"])
    num = random.randint(100000000000000, 9999999999999999999)
    return f"blk_{sign}{num}"


def expand_replication(template):
    """Replace replication placeholders with realistic variable-length patterns."""
    result = []
    for item in template:
        if item == "{rep}":
            # Standard replication: 4,3 or 3,4 pattern with variable count
            count = random.randint(1, 4)
            rep_codes = random.choice([
                [4, 4, 3],
                [4, 3, 4],
                [3, 4, 4],
                [4, 4, 4, 3],
                [4, 3, 4, 4],
                [3, 4, 4, 4],
            ])
            for _ in range(count):
                result.extend(random.choice([
                    [4, 4, 3],
                    [4, 3, 4],
                    [3, 4, 4],
                    [4],
                    [3],
                ]))
        elif item == "{rep2}":
            # Shorter replication pattern
            pattern = random.choice([
                [4, 4, 3],
                [4, 3, 4],
                [3, 4, 4],
                [4, 3],
                [3, 4],
                [4, 4, 4, 3],
                [4, 3, 4, 2],
            ])
            result.extend(pattern)
        elif item == "{heavy_rep}":
            # Heavy block report / replication (many 3s or 4s)
            count = random.randint(10, 30)
            for _ in range(count):
                result.append(random.choice([3, 4, 4, 4]))
        else:
            result.append(item)
    return result


def generate_line(is_anomaly=False):
    """Generate a single HDFS log line."""
    block_id = generate_block_id()

    if is_anomaly:
        template = random.choice(ABNORMAL_TEMPLATES)
        events = list(template)  # abnormal templates are fixed
    else:
        template = random.choice(NORMAL_TEMPLATES)
        events = expand_replication(template)

    event_str = " ".join(str(e) for e in events)
    return f"{block_id},{event_str}"


def generate_hdfs_logs(output_path, total_lines, anomaly_rate=0.03):
    """
    Generate an HDFS-style block trace log file.

    Args:
        output_path:  Path to write the generated file.
        total_lines:  Number of block entries to generate.
        anomaly_rate: Fraction of abnormal blocks (default: 3%).
    """
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    anomaly_count = 0

    with open(output_path, "w") as f:
        for i in range(total_lines):
            is_anomaly = random.random() < anomaly_rate
            line = generate_line(is_anomaly)

            if is_anomaly:
                anomaly_count += 1

            f.write(line + "\n")

            if (i + 1) % 20000 == 0:
                print(f"[GEN] {i + 1:,} / {total_lines:,} blocks written...")

    file_size_mb = os.path.getsize(output_path) / 1024 / 1024

    print()
    print("=" * 60)
    print("  HDFS Block Trace Generation Complete")
    print("=" * 60)
    print(f"  Output file      : {output_path}")
    print(f"  Total blocks     : {total_lines:,}")
    print(f"  Normal blocks    : {total_lines - anomaly_count:,}")
    print(f"  Abnormal blocks  : {anomaly_count:,} ({anomaly_count/total_lines*100:.2f}%)")
    print(f"  File size        : {file_size_mb:.2f} MB")
    print("=" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate realistic HDFS block trace logs")
    parser.add_argument("--lines", type=int, default=140000, help="Number of block entries (default: 140000)")
    parser.add_argument("--output", default=None, help="Output path (default: data/raw/hdfs_140k.log)")
    parser.add_argument("--anomaly-rate", type=float, default=0.03, help="Fraction of abnormal blocks (default: 0.03 = 3%%)")
    args = parser.parse_args()

    output_path = args.output or f"data/raw/hdfs_{args.lines // 1000}k.log"

    generate_hdfs_logs(
        output_path=output_path,
        total_lines=args.lines,
        anomaly_rate=args.anomaly_rate,
    )
