"""
storage.py — Stage 5a: Save and load processed logs using PyArrow Parquet.

Parquet gives columnar compression — typically 5-10x smaller than raw logs.

"""

import os
import pyarrow as pa
import pyarrow.parquet as pq


SCHEMA = pa.schema([
    ("raw", pa.string()),
    ("template", pa.string()),
    ("cluster_id", pa.int32()),
    ("anomaly_score", pa.float32()),
    ("is_anomaly", pa.bool_()),
    ("log_level", pa.int8()),
])


def save_parquet(logs: list[dict], output_dir: str, filename: str = "output.parquet") -> str:
    """
    Save processed logs to a Parquet file.

    Args:
        logs: List of processed log dicts.
        output_dir: Directory to save the file.
        filename: Output filename.

    Returns:
        Full path of the saved file.
    """
    os.makedirs(output_dir, exist_ok=True)
    out_path = os.path.join(output_dir, filename)

    table = pa.Table.from_pylist(
        [{
            "raw": log.get("raw", ""),
            "template": log.get("template", ""),
            "cluster_id": log.get("cluster_id", -1),
            "anomaly_score": log.get("anomaly_score", 0.0),
            "is_anomaly": log.get("is_anomaly", False),
            "log_level": log.get("features", [1])[0] if log.get("features") else 1,
        } for log in logs],
        schema=SCHEMA,
    )
    pq.write_table(table, out_path, compression="snappy")
    print(f"[storage] Saved {len(logs)} records to {out_path}")
    return out_path


def load_parquet(filepath: str) -> list[dict]:
    """
    Load a processed Parquet file back as a list of dicts.

    Args:
        filepath: Path to the Parquet file.

    Returns:
        List of log dicts.
    """
    table = pq.read_table(filepath)
    return table.to_pylist()
