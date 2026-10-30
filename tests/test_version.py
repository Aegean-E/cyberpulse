"""Release metadata tests."""

import io
import re
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from cyberpulse import __version__
from cyberpulse.cli import main


class TestVersion(unittest.TestCase):
    def test_version_is_semver(self):
        self.assertRegex(__version__, r"^\d+\.\d+\.\d+$")

    def test_pyproject_version_matches_the_package(self):
        pyproject = Path(__file__).resolve().parent.parent / "pyproject.toml"
        text = pyproject.read_text(encoding="utf-8")
        match = re.search(r'^version = "([^"]+)"', text, re.MULTILINE)

        self.assertIsNotNone(match)
        self.assertEqual(match.group(1), __version__)

    def test_cli_version_flag_reports_the_package_version(self):
        output = io.StringIO()
        with self.assertRaises(SystemExit) as raised:
            with redirect_stdout(output):
                main(["--version"])

        self.assertEqual(raised.exception.code, 0)
        self.assertIn(__version__, output.getvalue())


if __name__ == "__main__":
    unittest.main()
