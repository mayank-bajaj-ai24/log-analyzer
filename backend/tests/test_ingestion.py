import unittest
import tempfile
import os
import sys
import tracemalloc

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pipeline.ingestion import stream_logs

def create_temp_log(num_lines=10000):
    """Helper to create a temporary log file with num_lines lines."""
    tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False)
    for i in range(num_lines):
        tmp.write(f"[2024-01-01 00:00:{i:02d}] [INFO] Test log line number {i}\n")
    tmp.close()
    return tmp.name


class TestStreamLogs(unittest.TestCase):

    def setUp(self):
        """Create a temp log file before each test."""
        self.filepath = create_temp_log(10000)

    def tearDown(self):
        """Delete the temp log file after each test."""
        os.unlink(self.filepath)

    # --- Test 1: stream_logs yields lists ---
    def test_yields_lists(self):
        for chunk in stream_logs(self.filepath):
            self.assertIsInstance(chunk, list)
            break  # only need to check first chunk

    # --- Test 2: no chunk exceeds chunk_size ---
    def test_chunk_size_never_exceeded(self):
        for chunk in stream_logs(self.filepath, chunk_size=500):
            self.assertLessEqual(len(chunk), 500)

    # --- Test 3: total lines match file line count ---
    def test_total_lines_match(self):
        total = sum(len(chunk) for chunk in stream_logs(self.filepath))
        with open(self.filepath, 'r') as f:
            expected = sum(1 for _ in f)
        self.assertEqual(total, expected)

    # --- Test 4: KEY TEST — streaming uses less RAM than bulk load ---
    def test_streaming_uses_less_ram_than_bulk(self):

        # measure streaming peak RAM
        tracemalloc.start()
        for _ in stream_logs(self.filepath, chunk_size=500):
            pass
        _, stream_peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        # measure bulk load peak RAM
        tracemalloc.start()
        with open(self.filepath, 'r') as f:
            _ = f.readlines()
        _, bulk_peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        stream_mb = stream_peak / (1024 * 1024)
        bulk_mb = bulk_peak / (1024 * 1024)

        print(f"\n[RAM TEST] Streaming peak: {stream_mb:.4f} MB")
        print(f"[RAM TEST] Bulk load peak:  {bulk_mb:.4f} MB")

        # streaming must use less than 80% of bulk RAM
        self.assertLess(
            stream_mb,
            bulk_mb * 0.80,
            msg=f"Streaming ({stream_mb:.4f} MB) should be less than 80% of bulk ({bulk_mb:.4f} MB)"
        )

    # --- Test 5: works with custom chunk sizes ---
    def test_custom_chunk_size(self):
        for chunk in stream_logs(self.filepath, chunk_size=100):
            self.assertLessEqual(len(chunk), 100)


if __name__ == '__main__':
    unittest.main(verbosity=2)