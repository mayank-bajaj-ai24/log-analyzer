"""
parser.py — Stage 2: Structured log parsing using Drain3.

Converts unstructured log lines into structured templates and
assigns each entry a cluster ID.
"""

import re
from drain3 import TemplateMiner
from drain3.template_miner_config import TemplateMinerConfig

# Pre-compiled masking patterns (same as drain3.ini) for fast pre-grouping
_MASK_PATTERNS = [
    (re.compile(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}"), "<TIMESTAMP>"),
    (re.compile(r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b"), "<IP>"),
    (re.compile(r"\b[0-9]+\b"), "<NUM>"),
]


def _fast_mask(line: str) -> str:
    """Apply the same masking as Drain3 config to produce a grouping key."""
    for pattern, replacement in _MASK_PATTERNS:
        line = pattern.sub(replacement, line)
    return line


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


def parse_chunk(
    miner: TemplateMiner,
    chunk: list[str],
    _parse_cache: dict | None = None,
) -> list[dict]:
    """
    Parse a chunk of raw log lines.

    Uses pre-masking to group identical lines and only calls Drain3
    once per unique masked pattern. This dramatically reduces Drain3
    calls when many lines share the same structure (e.g. 200K lines
    with only ~600 unique patterns).

    Args:
        miner: Drain3 TemplateMiner instance.
        chunk: List of raw log line strings.
        _parse_cache: (internal) Cache of masked_line -> (template, cluster_id, parameters).

    Returns:
        List of parsed log dicts, each with keys:
        raw, template, cluster_id, parameters.
    """
    if not chunk:
        return []

    cache = _parse_cache if _parse_cache is not None else {}
    results = []

    for line in chunk:
        # Fast pre-mask to get grouping key
        masked = _fast_mask(line)

        if masked in cache:
            # Reuse cached Drain3 result — skip expensive parsing
            template, cluster_id, parameters = cache[masked]
            results.append({
                "raw":        line,
                "template":   template,
                "cluster_id": cluster_id,
                "parameters": parameters,
            })
        else:
            # First time seeing this pattern — call Drain3
            result = miner.add_log_message(line)
            template = result["template_mined"]
            cluster_id = result["cluster_id"]
            parameters = result.get("parameters", [])
            cache[masked] = (template, cluster_id, parameters)
            results.append({
                "raw":        line,
                "template":   template,
                "cluster_id": cluster_id,
                "parameters": parameters,
            })

    return results