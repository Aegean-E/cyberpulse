"""Smoke test for cyberpulse package."""

import unittest
import cyberpulse


class TestCyberpulseInit(unittest.TestCase):
    def test_version_defined(self):
        self.assertRegex(cyberpulse.__version__, r"^\d+\.\d+\.\d+$")


if __name__ == "__main__":
    unittest.main()
