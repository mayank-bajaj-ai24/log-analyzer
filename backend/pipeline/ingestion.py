import gc
import psutil
import os

def log_memory(label):
    process = psutil.Process(os.getpid())
    mem_mb = process.memory_info().rss / (1024 * 1024)
    print(f"[MEM] {label} — {mem_mb:.1f} MB")

def stream_logs(filepath, chunk_size=500):
    chunk = []
    chunk_number = 0

    with open(filepath, 'r') as f:
        for line in f:
            chunk.append(line.rstrip('\n'))

            if len(chunk) == chunk_size:
                chunk_number += 1
                yield chunk
                chunk = []
                gc.collect()
                log_memory(f"Chunk {chunk_number}")

        # yield any remaining lines at end of file
        if chunk:
            chunk_number += 1
            yield chunk
            gc.collect()
            log_memory(f"Chunk {chunk_number} (final)")