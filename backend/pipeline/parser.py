"""
parser.py — Stage 2: Structured log parsing using Drain3.

Converts unstructured log lines into structured templates and
assigns each entry a cluster ID.
"""

from drain3 import TemplateMiner
from drain3.template_miner_config import TemplateMinerConfig


def build_parser(config_path: str = "configs/drain3.ini") -> TemplateMiner:
    """
    Initialise and return a Drain3 TemplateMiner instance.

    Args:
        config_path: Path to the Drain3 config file.

    Returns:
        Configured TemplateMiner object.
    """
    config = TemplateMinerConfig()
    config.load(config_path)
    config.profiling_enabled = False
    return TemplateMiner(config=config)


def parse_line(miner: TemplateMiner, line: str) -> dict:
    """
    Parse a single log line and return structured output.

    Args:
        miner: Drain3 TemplateMiner instance.
        line:  Raw log line string.

    Returns:
        Dict with keys: raw (str), template (str),
                        cluster_id (int), parameters (list).
    """
    result = miner.add_log_message(line)
    return {
        "raw":        line,
        "template":   result["template_mined"],
        "cluster_id": result["cluster_id"],
        "parameters": result.get("parameters", []),
    }


def parse_chunk(miner: TemplateMiner, chunk: list[str]) -> list[dict]:
    """
    Parse a chunk of raw log lines.

    Args:
        miner: Drain3 TemplateMiner instance.
        chunk: List of raw log line strings.

    Returns:
        List of parsed log dicts, each with keys:
        raw, template, cluster_id, parameters.
    """
    parsed = [parse_line(miner, line) for line in chunk]

    unique_templates = len(set(r["template"] for r in parsed))
    print(f"[PARSER] {len(chunk)} lines -> {unique_templates} unique templates")

    return parsed