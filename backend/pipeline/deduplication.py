"""
deduplication.py — Stage 3: Near-duplicate log removal using MinHash + LSH.

Uses Locality Sensitive Hashing to detect and remove near-identical
log templates without comparing all pairs (avoids O(n^2) cost).
"""

from datasketch import MinHash, MinHashLSH


def build_lsh(threshold: float = 0.8, num_perm: int = 64) -> MinHashLSH:
    """
    Create an LSH index for near-duplicate detection.

    Args:
        threshold: Jaccard similarity threshold (0.0–1.0).
                   Higher = stricter, fewer entries removed.
                   Lower  = more aggressive deduplication.
        num_perm:  Number of permutations for MinHash accuracy.

    Returns:
        Empty MinHashLSH index ready to insert into.
    """
    return MinHashLSH(threshold=threshold, num_perm=num_perm)


def make_minhash(text: str, num_perm: int = 64) -> MinHash:
    """
    Generate a MinHash signature for a log template string.

    Args:
        text:     Log template string (uses template, not raw line).
        num_perm: Must match the LSH index's num_perm.

    Returns:
        MinHash object representing the text.
    """
    m = MinHash(num_perm=num_perm)
    for token in text.lower().split():
        m.update(token.encode("utf8"))
    return m


def deduplicate_chunk(
    lsh: MinHashLSH,
    parsed_logs: list[dict],
    num_perm: int = 64,
    _minhash_cache: dict | None = None,
    _seen_templates: set | None = None,
) -> list[dict]:
    """
    Remove near-duplicate entries from a parsed log chunk.

    Operates on the 'template' key from each log dict (output of
    parse_chunk). The LSH index is shared across calls so duplicates
    are tracked across multiple chunks, not just within one chunk.

    Args:
        lsh:         MinHashLSH index (shared across chunks).
        parsed_logs: List of parsed log dicts from parser.py.
                     Each dict must have: raw, template, cluster_id, parameters.
        num_perm:    Must match the LSH index's num_perm.
        _minhash_cache: (internal) Cache of template -> MinHash for reuse.
        _seen_templates: (internal) Set of templates already processed.

    Returns:
        List of unique log dicts (near-duplicates removed).
        Each dict retains all original keys: raw, template, cluster_id, parameters.
    """
    before = len(parsed_logs)
    unique = []

    # Use shared caches if provided, otherwise use local ones
    mh_cache = _minhash_cache if _minhash_cache is not None else {}
    seen = _seen_templates if _seen_templates is not None else set()

    for i, log in enumerate(parsed_logs):
        template = log.get("template", log.get("raw", ""))

        # Fast path: if we've already seen this exact template, skip entirely
        if template in seen:
            continue

        # Get or compute MinHash (cache by template string)
        if template in mh_cache:
            mh = mh_cache[template]
        else:
            mh = make_minhash(template, num_perm)
            mh_cache[template] = mh

        key = f"{log.get('cluster_id', 'x')}_{id(log)}"

        if not lsh.query(mh):
            lsh.insert(key, mh)
            unique.append(log)

        # Mark this template as seen regardless of whether it was kept
        seen.add(template)

    after = len(unique)
    print(f"[DEDUP]  {before} -> {after} unique entries  ({before - after} removed)")
    return unique