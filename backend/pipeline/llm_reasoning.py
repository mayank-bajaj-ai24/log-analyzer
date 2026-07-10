"""
llm_reasoning.py — Stage 6 (optional): LLM-based anomaly explanation.

Takes the small set of entries flagged as anomalous by Stage 4
(Isolation Forest) and asks an LLM to explain, in one plain-English
sentence, why each one is likely a problem.

This stage is deliberately OPTIONAL and called only on the (usually
small) subset of flagged anomalies — never on the full log stream.
This keeps the core pipeline's memory-efficiency claim untouched;
the LLM call is a value-add layer on top, not a dependency.

Uses Groq's free API (LPU hardware — much faster than typical GPU-based
free tiers, well suited for short explanation tasks like this).
Get a free key at: https://console.groq.com/keys

Setup:
    pip install groq python-dotenv
    Add to .env in project root:  GROQ_API_KEY="your-key-here"

Usage:
    python main.py --input data/samples/sample.log --explain
"""

import os
import time
import json

try:
    from dotenv import load_dotenv
    load_dotenv()  # reads .env file in project root, if present
except ImportError:
    pass  # dotenv not installed — GROQ_API_KEY must be set another way


DEFAULT_MODEL = "llama-3.1-8b-instant"
MAX_RAW_CHARS = 200  # truncate long log lines before sending to the LLM

EXPLANATION_PROMPT = """You are a site reliability engineer reviewing a flagged log entry from an
automated anomaly detector. In exactly ONE short sentence (under 25 words), explain what about
this entry's pattern is statistically unusual compared to normal logs, based only on what is
shown below. Do NOT guess at security causes (e.g. SQL injection, brute force, intrusion) unless
the log text explicitly names them — most anomalies are operational, not malicious. No preamble.

Log entry (truncated if long): {raw}
Detected pattern: {template}
Anomaly score: {score} (more negative = more statistically unusual)

One-sentence explanation:"""

BATCH_EXPLANATION_PROMPT = """You are a site reliability engineer reviewing flagged log entries from an automated anomaly detector.
For each log entry below, explain in exactly ONE short sentence (under 25 words) why it is statistically unusual.
Do NOT guess at security causes (e.g. SQL injection, brute force, intrusion) unless the log text explicitly names them.

You MUST return your response as a JSON object containing a list of strings under the key "explanations", like this:
{{
  "explanations": [
    "Explanation for log 0...",
    "Explanation for log 1..."
  ]
}}

Log entries to explain:
{logs_formatted}
"""


def truncate_raw(raw: str, max_chars: int = MAX_RAW_CHARS) -> str:
    """
    Truncate a long log line so it stays within a safe token budget.
    Some datasets (e.g. BGL) have lines with hundreds of repeated values.

    Args:
        raw:       The original raw log line.
        max_chars: Maximum characters to keep.

    Returns:
        Truncated string, with a marker if truncation occurred.
    """
    if len(raw) <= max_chars:
        return raw
    return raw[:max_chars] + " ...[truncated]"


def get_client():
    """
    Build a Groq API client from the GROQ_API_KEY environment variable.
    Imports groq lazily so installing it mid-session works without restart.

    Returns:
        A configured Groq client, or None if the key is missing or the
        groq package is not installed.
    """
    try:
        from groq import Groq
    except ImportError:
        print("[LLM] groq package not installed — skipping explanations.")
        print("[LLM] Install with: pip install groq")
        return None

    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        # Retry loading .env in case it was created after first import
        try:
            from dotenv import load_dotenv
            load_dotenv(override=True)
            api_key = os.environ.get("GROQ_API_KEY")
        except ImportError:
            pass

    if not api_key:
        print("[LLM] GROQ_API_KEY not set — skipping explanations.")
        print("[LLM] Get a free key at https://console.groq.com/keys")
        return None

    try:
        return Groq(api_key=api_key)
    except Exception as e:
        print(f"[LLM] Failed to create client: {e}")
        return None


def explain_one(client: "Groq", log: dict, model: str = DEFAULT_MODEL, max_retries: int = 3) -> str:
    """
    Get a one-sentence LLM explanation for a single anomalous log entry.
    Retries with increasing backoff if a rate limit is hit.

    Args:
        client:      An initialised Groq client.
        log:         A scored log dict with 'raw', 'template', 'anomaly_score' keys.
        model:       Groq model name to use.
        max_retries: How many times to retry on a 429 rate-limit error.

    Returns:
        A short explanation string, or a fallback message on failure.
    """
    prompt = EXPLANATION_PROMPT.format(
        raw=truncate_raw(log.get("raw", "")),
        template=truncate_raw(log.get("template", "")),
        score=log.get("anomaly_score", "N/A"),
    )

    for attempt in range(max_retries + 1):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=60,
            )
            text = (response.choices[0].message.content or "").strip()
            return text if text else "No explanation generated."
        except Exception as e:
            error_str = str(e)
            is_rate_limit = "429" in error_str or "rate_limit_exceeded" in error_str
            is_too_large = "context_length_exceeded" in error_str or "413" in error_str

            if is_too_large:
                # Truncation should prevent this, but if it still happens,
                # don't waste retries — fail immediately with a clear message.
                return "[explanation unavailable: log entry too large even after truncation]"

            if is_rate_limit and attempt < max_retries:
                wait = 10 * (attempt + 1)  # 10s, 20s, 30s
                print(f"      [rate limited — waiting {wait}s before retry {attempt + 1}/{max_retries}]")
                time.sleep(wait)
                continue

            return f"[explanation unavailable: {e}]"

    return "[explanation unavailable: max retries exceeded]"


def explain_batch(client: "Groq", logs: list[dict], model: str = DEFAULT_MODEL) -> list[str] | None:
    """
    Get one-sentence LLM explanations for a batch of anomalous log entries in a single call.

    Args:
        client: An initialised Groq client.
        logs:   List of scored log dicts with 'raw', 'template', 'anomaly_score' keys.
        model:  Groq model name to use.

    Returns:
        List of explanation strings matching the input list size, or None on failure/mismatch.
    """
    if not logs:
        return []

    logs_formatted = ""
    for idx, log in enumerate(logs):
        logs_formatted += f"[{idx}] Log: {truncate_raw(log.get('raw', ''))}\n"
        logs_formatted += f"Pattern: {truncate_raw(log.get('template', ''))}\n"
        logs_formatted += f"Score: {log.get('anomaly_score', 'N/A')}\n\n"

    prompt = BATCH_EXPLANATION_PROMPT.format(logs_formatted=logs_formatted)

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            response_format={"type": "json_object"},
        )
        text = (response.choices[0].message.content or "").strip()
        if not text:
            return None

        parsed = json.loads(text)
        explanations = parsed.get("explanations", [])

        if len(explanations) == len(logs):
            return [str(e).strip() for e in explanations]
        else:
            print(f"[LLM] Mismatch in batch explanation count: expected {len(logs)}, got {len(explanations)}")
            return None
    except Exception as e:
        print(f"[LLM] Batch explanation failed: {e}")
        return None


def explain_anomalies(
    logs: list[dict],
    model: str = DEFAULT_MODEL,
    max_explanations: int = 20,
    delay_seconds: float = 0.3,
) -> list[dict]:
    """
    Add an 'llm_explanation' key to each anomalous entry in logs.

    Only calls the LLM on entries where is_anomaly is True, and caps
    the total number of calls. Non-anomalous entries are left untouched.
    If no API key is configured, this function is a safe no-op — the
    pipeline continues normally.

    Args:
        logs:             List of scored log dicts (output of anomaly_detector.score_logs).
        model:            Groq model name to use.
        max_explanations: Maximum number of anomalies to explain (default 20).
        delay_seconds:    Pause between calls (default 0.3s — Groq is fast).

    Returns:
        The same list, with 'llm_explanation' added to explained entries.
    """
    client = get_client()
    if client is None:
        return logs

    anomalies = [l for l in logs if l.get("is_anomaly")]
    to_explain = anomalies[:max_explanations]

    if not anomalies:
        print("[LLM] No anomalies to explain.")
        return logs

    if len(anomalies) > max_explanations:
        print(f"[LLM] {len(anomalies)} anomalies found — explaining top {max_explanations} only "
              f"(use --max-explanations to change this).")

    print(f"[LLM] Requesting explanations for {len(to_explain)} anomalies via {model} (Groq)...")

    start = time.time()

    # Try batch explanation first
    batch_explanations = explain_batch(client, to_explain, model=model)
    if batch_explanations is not None:
        for log, explanation in zip(to_explain, batch_explanations):
            log["llm_explanation"] = explanation
        elapsed = time.time() - start
        print(f"[LLM] Done (batch mode). {len(to_explain)} explanations generated in {elapsed:.1f}s.")
        return logs

    # Fallback to sequential mode if batching failed or returned None
    print("[LLM] Falling back to sequential explanations...")
    for i, log in enumerate(to_explain):
        explanation = explain_one(client, log, model=model)
        log["llm_explanation"] = explanation
        print(f"  [{i+1}/{len(to_explain)}] {log['raw'][:60]}...")
        print(f"      -> {explanation}")

        if i < len(to_explain) - 1:
            time.sleep(delay_seconds)

    elapsed = time.time() - start
    print(f"[LLM] Done (sequential fallback). {len(to_explain)} explanations generated in {elapsed:.1f}s.")
    return logs