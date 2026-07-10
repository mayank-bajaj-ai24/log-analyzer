import tracemalloc
import psutil
import os

def log_memory(label):
    """Prints current RAM usage to terminal with a label."""
    process = psutil.Process(os.getpid())
    mem_mb = process.memory_info().rss / (1024 * 1024)
    print(f"[MEM] {label} — {mem_mb:.1f} MB")

def get_peak_memory_mb(func, *args, **kwargs):
    """
    Runs a function and returns its peak memory usage in MB.
    Usage: peak = get_peak_memory_mb(some_function, arg1, arg2)
    """
    tracemalloc.start()
    try:
        func(*args, **kwargs)
    finally:
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
    return peak / (1024 * 1024)

def get_peak_memory_for_generator(gen_func, *args, **kwargs):
    """
    Runs a generator function fully and returns peak memory in MB.
    Usage: peak = get_peak_memory_for_generator(stream_logs, filepath)
    """
    tracemalloc.start()
    try:
        for _ in gen_func(*args, **kwargs):
            pass
    finally:
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
    return peak / (1024 * 1024)