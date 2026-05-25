from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from utils.archiver import ArchiveMaster


class ArchiveMasterTests(unittest.TestCase):
    def test_store_uses_configured_report_title(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = ArchiveMaster.store(
                "content",
                output_dir=temp_dir,
                prefix="briefing",
                report_title="Daily Briefing",
            )

            archived = Path(path)
            self.assertTrue(archived.exists())
            self.assertIn("Daily Briefing", archived.read_text(encoding="utf-8").splitlines()[0])


if __name__ == "__main__":
    unittest.main()
