"""Transition tests: python -m unittest genmidi.test_syntax."""
import unittest

from genmidi.main import ARTICULATIONS, DRUMS, DYNAMICS, parse_xdm
from genmidi.syntax import bracket_groups, header_fields, parse_event, parse_measure


class SyntaxTests(unittest.TestCase):
    def event(self, text):
        return parse_event(text, DYNAMICS, ARTICULATIONS, DRUMS)

    def test_modifier_order_and_chord_scope(self):
        event = self.event("C4+Eb4+G4@mf:50")
        self.assertEqual(event.notes, ["C4", "Eb4", "G4"])
        self.assertEqual((event.velocity, event.gate), (65, 50))
        self.assertEqual(self.event("C4mf'").articulation, "'")
        self.assertEqual(self.event("BD+CHfff-").velocity, 100)

    def test_incomplete_and_forbidden_transitions(self):
        for text in ("C4+", "C4@", "C4:", "<", "C4'mf", "C4:60.",
                     "C4:.^", "C4:^", "C4@50@60", "_mf", "C4+ZZ",
                     "C4mf+E4", "<C4f<", "C4f<<"):
            with self.subTest(text=text), self.assertRaises(ValueError):
                self.event(text)

    def test_error_has_position_and_expectation(self):
        with self.assertRaisesRegex(ValueError, "Expected gate percentage or articulation at column 4"):
            self.event("C4:^")

    def test_delimiters_preserve_silent_positions(self):
        measure = parse_measure("C4,|_|,D4|", DYNAMICS, ARTICULATIONS, DRUMS)
        self.assertEqual([len(beat) for beat in measure.beats], [2, 1, 2, 1])
        self.assertIsNone(measure.beats[0][1])
        self.assertTrue(measure.beats[1][0].hold)
        self.assertIsNone(measure.beats[2][0])
        self.assertIsNone(measure.beats[3][0])

    def test_stack_rejects_stray_text_and_extra_depth(self):
        for text in ("[[][]junk]", "[junk[][]]", "[[[][]]]", "]", "[[]"):
            with self.subTest(text=text), self.assertRaises(ValueError):
                bracket_groups(text)
        self.assertEqual(len(bracket_groups("[[][]]")[0].children), 2)

    def test_header_states(self):
        self.assertEqual(header_fields("t 3 / 8, @mf :~ i60"),
                         {"t": "3/8", "@": "mf", ":": "~", "i": "60"})
        for text in ("t3", "t3/", "@", ":", "@mf@p", "m2/3"):
            with self.subTest(text=text), self.assertRaises(ValueError):
                header_fields(text)

    def test_local_settings_do_not_carry(self):
        calls = parse_xdm("[@20:80][C4mf'|D4|E4|F4]")
        notes = [values for method, values in calls if method == "addNote"]
        self.assertEqual([n["volume"] for n in notes], [83, 25, 25, 25])
        self.assertEqual([n["duration"] for n in notes], [0.25, 0.8, 0.8, 0.8])
