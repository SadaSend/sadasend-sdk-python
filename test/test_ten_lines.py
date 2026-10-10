import os
import subprocess
import sys
import unittest
from pathlib import Path


class TestTenLines(unittest.TestCase):
    def setUp(self):
        self.example_path = Path(__file__).resolve().parent.parent / "examples" / "ten_lines.py"

    def test_example_file_exists(self):
        self.assertTrue(self.example_path.exists())

    def test_example_is_ten_lines_or_fewer(self):
        lines = [
            line.strip()
            for line in self.example_path.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.strip().startswith("#")
        ]
        self.assertLessEqual(len(lines), 10, f"Expected 10 lines or fewer, found {len(lines)}")
        self.assertGreaterEqual(len(lines), 5)

    def test_example_imports_published_package(self):
        content = self.example_path.read_text(encoding="utf-8")
        self.assertIn("from sadasend import SadaSend", content)
        self.assertNotIn("from ..sadasend", content)
        self.assertNotIn("from .sadasend", content)


if __name__ == "__main__":
    unittest.main()
