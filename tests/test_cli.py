import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout

from hyprtk_calc.cli import main


class CliTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="hyprtk-calc-cli-")
        self.saved = {key: os.environ.get(key) for key in ("HYPRTK_CALC_CONFIG_DIR", "HYPRTK_CALC_HISTORY")}
        os.environ["HYPRTK_CALC_CONFIG_DIR"] = self.dir
        os.environ["HYPRTK_CALC_HISTORY"] = os.path.join(self.dir, "history.jsonl")
        # A piped stdin would otherwise make main() think it has work to do.
        self.stdin = os.dup(0)
        self.devnull = os.open(os.devnull, os.O_RDONLY)
        os.dup2(self.devnull, 0)

    def tearDown(self):
        os.dup2(self.stdin, 0)
        os.close(self.stdin)
        os.close(self.devnull)
        for key, value in self.saved.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        for name in os.listdir(self.dir):
            path = os.path.join(self.dir, name)
            if os.path.isfile(path):
                os.remove(path)
        os.rmdir(self.dir)

    def run_cli(self, *args):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            status = main(list(args))
        return status, out.getvalue(), err.getvalue()

    def test_expression(self):
        status, out, err = self.run_cli("2+2*3")
        self.assertEqual(status, 0)
        self.assertEqual(out.strip(), "8")
        self.assertEqual(err, "")

    def test_multiple_arguments_are_one_expression(self):
        status, out, _ = self.run_cli("2", "+", "3")
        self.assertEqual(out.strip(), "5")

    def test_precision_flag(self):
        _, out, _ = self.run_cli("-p", "20", "1/3")
        self.assertEqual(out.strip(), "0.33333333333333333333")

    def test_angle_flag(self):
        _, out, _ = self.run_cli("-a", "rad", "sin(pi/2)")
        self.assertEqual(out.strip(), "1")

    def test_base_flag(self):
        _, out, _ = self.run_cli("-b", "16", "255")
        self.assertEqual(out.strip(), "0xFF")

    def test_grouping_flag(self):
        _, out, _ = self.run_cli("-g", "comma", "1234567")
        self.assertEqual(out.strip(), "1,234,567")

    def test_all_bases(self):
        _, out, _ = self.run_cli("--all-bases", "255")
        self.assertIn("0xFF", out)
        self.assertIn("0b11111111", out)

    def test_json(self):
        _, out, _ = self.run_cli("--json", "1/4")
        record = json.loads(out)
        self.assertEqual(record["expression"], "1/4")
        self.assertEqual(record["result"], "0.25")
        self.assertTrue(record["ok"])

    def test_error_sets_status_and_writes_stderr(self):
        status, out, err = self.run_cli("1/0")
        self.assertEqual(status, 1)
        self.assertEqual(out, "")
        self.assertIn("division by zero", err)

    def test_json_error(self):
        status, out, _ = self.run_cli("--json", "nope")
        record = json.loads(out)
        self.assertFalse(record["ok"])
        self.assertIn("not defined", record["error"])
        self.assertEqual(status, 1)

    def test_history_flows_between_invocations(self):
        # The CLI does not record, but --history must still read the file the
        # GUI writes, so a shared store keeps both useful.
        from hyprtk_calc.history import History

        History().add("6*7", "42")
        status, out, _ = self.run_cli("--history")
        self.assertEqual(status, 0)
        self.assertIn("6*7", out)
        self.assertIn("42", out)

    def test_clear_history(self):
        from hyprtk_calc.history import History

        History().add("6*7", "42")
        status, out, _ = self.run_cli("--clear-history")
        self.assertEqual(status, 0)
        self.assertIn("cleared 1", out)
        self.assertEqual(len(History()), 0)

    def test_version(self):
        with self.assertRaises(SystemExit) as caught:
            self.run_cli("--version")
        self.assertEqual(caught.exception.code, 0)


class StdinTest(unittest.TestCase):
    def test_piped_lines_are_evaluated_in_order(self):
        import sys

        saved_dir = os.environ.get("HYPRTK_CALC_CONFIG_DIR")
        os.environ["HYPRTK_CALC_CONFIG_DIR"] = tempfile.mkdtemp(prefix="hyprtk-calc-stdin-")
        source = "1+1\n12*12\n"
        fake = type("Fake", (), {"isatty": lambda self: False, "read": lambda self: source})()
        original = sys.stdin
        sys.stdin = fake
        try:
            out = io.StringIO()
            with redirect_stdout(out):
                status = main(["-"])
        finally:
            sys.stdin = original
            if saved_dir is None:
                os.environ.pop("HYPRTK_CALC_CONFIG_DIR", None)
            else:
                os.environ["HYPRTK_CALC_CONFIG_DIR"] = saved_dir
        self.assertEqual(status, 0)
        self.assertEqual(out.getvalue().split(), ["2", "144"])


if __name__ == "__main__":
    unittest.main()
