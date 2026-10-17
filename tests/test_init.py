"""Smoke test for cyberpulse package."""

import unittest
import cyberpulse


class TestCyberpulseInit(unittest.TestCase):
    def test_version_defined(self):
        self.assertEqual(cyberpulse.__version__, "0.1.0")


if __name__ == "__main__":
    unittest.main()
