"""CLI checks: python -m unittest genmidi.tests.test_cli."""
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from genmidi.xdmgen import main
from genmidi.src.xdm import validate_xdm


class CLITests(unittest.TestCase):
    def run_cli(self, arguments):
        stdout, stderr = StringIO(), StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            result = main(arguments)
        return result, stdout.getvalue(), stderr.getvalue()

    def test_validate_literal_without_midi_dependency(self):
        with patch("genmidi.xdmgen.create_midi", side_effect=AssertionError("must not create MIDI")):
            result, stdout, stderr = self.run_cli(["--code", "[t1/1][A+C+E]", "--validate"])
        self.assertEqual(result, 0)
        self.assertIn("Valid XDM", stdout)
        self.assertEqual(stderr, "")

    def test_validate_file_creates_no_output(self):
        with TemporaryDirectory() as directory:
            source = Path(directory) / "song.xdm"
            source.write_text("[[][]][[][C4|D4|E4|F4]]", encoding="utf-8")
            self.assertEqual(self.run_cli([str(source), "--validate"])[0], 0)
            self.assertFalse(source.with_suffix(".mid").exists())

    def test_generate_from_file_and_literal(self):
        with TemporaryDirectory() as directory:
            source = Path(directory) / "song.xdm"
            source.write_text("[t1/1][A+C+E]", encoding="utf-8")
            self.assertEqual(self.run_cli([str(source)])[0], 0)
            generated = source.with_suffix(".mid").read_bytes()
            self.assertEqual(generated[:4], b"MThd")
            self.assertIn(b"MTrk", generated)
            output = Path(directory) / "literal.mid"
            self.assertEqual(self.run_cli(["--code", "[t1/1][A+C+E]", "-o", str(output)])[0], 0)
            self.assertEqual(output.read_bytes()[:4], b"MThd")

    def test_invalid_input_does_not_replace_output(self):
        with TemporaryDirectory() as directory:
            output = Path(directory) / "existing.mid"
            output.write_bytes(b"existing")
            for score in ("[t44][C4|D4|E4|F4]", "[C9|D9|E9|A9]",
                          "[Cb4|D4|E4|F4]", "[[C4|_|_|_][C4|_|_|_]]"):
                result, stdout, stderr = self.run_cli(["--code", score, "-o", str(output)])
                self.assertEqual(result, 1)
                self.assertEqual(stdout, "")
                self.assertIn("xdmgen:", stderr)
                self.assertEqual(output.read_bytes(), b"existing")

    def test_missing_input_file(self):
        with TemporaryDirectory() as directory:
            self.assertEqual(self.run_cli([str(Path(directory) / "missing.xdm"), "--validate"])[0], 1)

    def test_invalid_argument_combinations(self):
        for arguments in ([], ["--code", "[]"],
                          ["song.xdm", "--code", "[]", "--validate"],
                          ["song.xdm", "--validate", "-o", "song.mid"],
                          ["song.xdm", "-o", "song.xdm"]):
            with self.subTest(arguments=arguments), redirect_stderr(StringIO()), self.assertRaises(SystemExit) as error:
                main(arguments)
            self.assertEqual(error.exception.code, 2)

    def test_all_xdm_examples(self):
        for path in Path(__file__).parents[1].rglob("*.xdm"):
            with self.subTest(path=path):
                validate_xdm(path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
