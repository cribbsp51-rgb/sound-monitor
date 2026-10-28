import csv
import os

class CSVExporter:
    def __init__(self, path):
        self.path = path
        self._ensure_header()

    def _ensure_header(self):
        if not os.path.exists(self.path):
            with open(self.path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["ts", "spl"])

    def write(self, ts, spl):
        with open(self.path, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([ts, spl])
