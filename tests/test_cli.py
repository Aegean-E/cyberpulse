"""Integration tests for CyberPulse CLI."""

import io
import shutil
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from cyberpulse.cli import main


class TestCLI(unittest.TestCase):
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.temp_dir, ignore_errors=True)

    def run_cli(self, *args):
        stdout_buf = io.StringIO()
        cmd_args = ["--data-dir", str(self.temp_dir)] + list(args)
        exit_code = 0
        try:
            with redirect_stdout(stdout_buf):
                exit_code = main(cmd_args)
        except SystemExit as exc:
            exit_code = exc.code if isinstance(exc.code, int) else 0
        return exit_code, stdout_buf.getvalue()

    def test_cli_help(self):
        code, out = self.run_cli("--help")
        self.assertEqual(code, 0)
        self.assertIn("cyberpulse", out)

    def test_batch_infiltration_playthrough(self):
        # Scan, hack proxy a, move to proxy a, spoof trace, save game
        batch_cmds = "scan;hack node_proxy_a;move node_proxy_a;spoof;save"
        code, out = self.run_cli("--seed", "1337", "--auto-solve", "--exec", batch_cmds)
        self.assertEqual(code, 0)
        self.assertIn("Scanned", out)
        self.assertIn("breached", out)
        self.assertIn("Transferred terminal session", out)
        self.assertIn("IP Proxy bounced", out)
        self.assertIn("Infiltration progress saved", out)

        # Test loading the saved session
        code, out_load = self.run_cli("--seed", "1337", "--exec", "load;status")
        self.assertEqual(code, 0)
        self.assertIn("Loaded saved infiltration session", out_load)
        self.assertIn("Subnet Router Alpha", out_load)


if __name__ == "__main__":
    unittest.main()
