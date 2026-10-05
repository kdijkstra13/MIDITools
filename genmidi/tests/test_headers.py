"""Run from the repository root: python -m unittest genmidi.tests.test_headers."""
import unittest

from genmidi.src.xdm import _parse_header, add_notes


class RecordingMIDI:
    def __init__(self):
        self.notes = []
        self.tempos = []
        self.meters = []
        self.programs = []

    def addProgramChange(self, **values):
        self.programs.append(values)

    def addNote(self, **values):
        self.notes.append(values)

    def addTempo(self, **values):
        self.tempos.append(values)

    def addTimeSignature(self, **values):
        self.meters.append(values)


class HeaderTests(unittest.TestCase):
    def parse(self, header, measure="[C4|D4|E4|F4]"):
        return _parse_header(header + measure)

    def test_equivalent_prefixed_spellings(self):
        expected = self.parse("[t4/4s120m2b10@mf:-]")
        for header in ("[m2,b10,t4/4,@mf,:-]", "[m2b10t4/4@mf:-]",
                       "[:- @mf s120 t4/4 b10 m2]"):
            with self.subTest(header=header):
                self.assertEqual(self.parse(header), expected)

    def test_positional_headers_are_rejected(self):
        for header in ("[4/4,120,2]", "[4/4,120,2,10]",
                       "[4/4,120,2,@mf:80]", "[4/4,120,2,:80]"):
            scores = (header + "[C4|D4|E4|F4]",
                      "[C4|D4|E4|F4]" + header + "[C4|D4|E4|F4]",
                      "[" + header + "[C4|D4|E4|F4][m3][C3|D3|E3|F3]]")
            for score in scores:
                midi = RecordingMIDI()
                with self.subTest(score=score), self.assertRaisesRegex(
                        ValueError, "prefixed fields"):
                    add_notes(midi, 0, score)
                self.assertEqual(midi.notes, [])
                self.assertEqual(midi.tempos, [])
                self.assertEqual(midi.programs, [])

    def test_numeric_expression(self):
        result = self.parse("[m2b10t4/4@20:80]")
        self.assertEqual((result["velocity"], result["gate"]), (20, 80))

    def test_defaults(self):
        result = self.parse("[m2]")
        self.assertEqual((result["numerator"], result["denominator"],
                          result["tempo"], result["channel"],
                          result["beats_channel"]), (4, 4, 120, 1, 9))

    def test_large_meter_and_speed(self):
        result = self.parse("[s96t12/8m16b1]", "[" + "|".join(["C4"] * 12) + "]")
        self.assertEqual((result["numerator"], result["denominator"],
                          result["tempo"], result["channel"],
                          result["beats_channel"]), (12, 8, 96, 15, 0))

    def test_invalid_fields(self):
        for header in ("[m2m3]", "[t4/4,t3/4]", "[m0]", "[b17]", "[s0]",
                       "[t44]", "[t4/3]", "[t128]", "[@101]", "[:101]", "[m2x3]",
                       "[m2junk]", "[mp]", "[sfast]", "[t4/4@mf@20]"):
            with self.subTest(header=header), self.assertRaises(ValueError):
                self.parse(header)

    def test_instruments(self):
        midi = RecordingMIDI()
        add_notes(midi, 2, "[i60m2][C4|D4|E4|F4]"
                  "[@70][C4|D4|E4|F4][i0m3][C4|D4|E4|F4]", time=3)
        self.assertEqual(midi.programs, [
            dict(track=2, channel=1, time=3, program=60),
            dict(track=2, channel=2, time=11, program=0),
        ])
        self.assertEqual(self.parse("[i127]")["instrument"], 127)
        self.assertEqual(self.parse("[m2,i60]")["instrument"], 60)

    def test_parallel_instruments(self):
        midi = RecordingMIDI()
        add_notes(midi, 0, "[[m1i60][C4|D4|E4|F4]"
                  "[m2i127][C3|D3|E3|F3]]")
        self.assertEqual([p["program"] for p in midi.programs], [60, 127])
        self.assertEqual([p["channel"] for p in midi.programs], [0, 1])

    def test_invalid_instruments(self):
        for header in ("[i128]", "[i-1]", "[i60i61]", "[imf]", "[i1/2]"):
            midi = RecordingMIDI()
            with self.subTest(header=header), self.assertRaises(ValueError):
                add_notes(midi, 0, header + "[C4|D4|E4|F4]")
            self.assertEqual(midi.programs, [])
            self.assertEqual(midi.notes, [])

    def test_measure_validation(self):
        with self.assertRaises(ValueError):
            self.parse("[t3/4]")

    def test_no_initial_header(self):
        result = _parse_header("  [C4|D4|E4|F4]  ")
        self.assertEqual((result["channel"], result["tempo"]), (0, 120))

    def test_headers_change_only_specified_defaults(self):
        midi = RecordingMIDI()
        add_notes(midi, 0, "[m2@20:80][C4|D4|E4|F4]"
                  "[@70][G4|A4|B4|C5]"
                  "[m3b11s96t3/8][C4|BD|E4]", time=2)
        self.assertEqual([n["volume"] for n in midi.notes], [25] * 4 + [89] * 7)
        self.assertEqual([n["channel"] for n in midi.notes], [1] * 8 + [2, 10, 2])
        self.assertEqual([n["time"] for n in midi.notes],
                         [2, 3, 4, 5, 6, 7, 8, 9, 10, 10.5, 11])
        self.assertEqual(midi.tempos, [dict(track=0, time=2, tempo=120),
                                       dict(track=0, time=10, tempo=96)])
        self.assertEqual(midi.meters[-1]["time"], 10)
        self.assertEqual(midi.meters[-1]["denominator"], 3)
        self.assertAlmostEqual(midi.notes[-1]["duration"], 0.4)

    def test_note_modifiers_are_local_including_carries(self):
        midi = RecordingMIDI()
        add_notes(midi, 0, "[@20:80][C4@mf:~|_|E4|F4:60][G4|A4@90|B4|C5]")
        self.assertEqual([n["volume"] for n in midi.notes],
                         [83, 25, 25, 25, 114, 25, 25])
        for note, duration in zip(midi.notes, [2, 0.8, 0.6, 0.8, 0.8, 0.8, 0.8]):
            self.assertAlmostEqual(note["duration"], duration)

    def test_header_requires_following_measure(self):
        for score in ("[m2]", "[m2][@20][C4|D4|E4|F4]",
                      "[C4|D4|E4|F4][@20]"):
            with self.subTest(score=score), self.assertRaises(ValueError):
                _parse_header(score)

    def test_ramps_open_before_and_close_after_event(self):
        midi = RecordingMIDI()
        add_notes(midi, 0, "[@50][<C4@20|D4|E4|F4@80<]"
                  "[>G4@80|F4|E4|C4@20'>][D4|_|_|_]")
        self.assertEqual([n["volume"] for n in midi.notes],
                         [25, 51, 76, 102, 102, 76, 51, 25, 64])
        self.assertAlmostEqual(midi.notes[7]["duration"], 0.25)

    def test_ramp_endpoint_after_chord_modifiers(self):
        midi = RecordingMIDI()
        add_notes(midi, 0, "[<C4p|D4|E4|F4+A4+C5f:50<]")
        self.assertEqual([n["volume"] for n in midi.notes[-3:]], [102] * 3)
        self.assertEqual([n["duration"] for n in midi.notes[-3:]], [0.5] * 3)

    def test_invalid_ramp_boundaries(self):
        for measure in ("[C4|D4|E4|F4f<]", "[<C4p|D4|E4|F4f>]",
                        "[<C4p|D4|E4|F4<]", "[<C4p|D4|E4|<F4f]",
                        "[<C4p<|D4|E4|F4]", "[>C4f|D4|E4|F4p]"):
            with self.subTest(measure=measure), self.assertRaises(ValueError):
                add_notes(RecordingMIDI(), 0, measure)

    def test_parallel_timing_state_and_holds(self):
        midi = RecordingMIDI()
        add_notes(midi, 0, "[@40][[m1][C5|_|_|_][m2@80][C3|D|E|F]]"
                  "[[_|_|D|E][G|A|B|C]]", time=3)
        upper = [n for n in midi.notes if n["channel"] == 0]
        lower = [n for n in midi.notes if n["channel"] == 1]
        self.assertEqual([n["time"] for n in upper], [3, 9, 10])
        self.assertEqual([n["pitch"] for n in upper], [72, 74, 76])
        self.assertEqual(upper[0]["duration"], 6)
        self.assertEqual([n["pitch"] for n in lower], [48, 50, 52, 53, 55, 57, 59, 48])
        self.assertEqual([n["volume"] for n in upper], [51] * 3)
        self.assertEqual([n["volume"] for n in lower], [102] * 8)
        self.assertEqual(len(midi.tempos), 1)

    def test_empty_measures_and_groups(self):
        midi = RecordingMIDI()
        add_notes(midi, 0, "[[][]][[][C4|D4|E4|F4]]")
        self.assertEqual([n["time"] for n in midi.notes], [4, 5, 6, 7])
        self.assertEqual(_parse_header("[]")["measures"], ["|||"])

    def test_outer_header_changes_all_voices(self):
        midi = RecordingMIDI()
        add_notes(midi, 0, "[[m1][C4|D4|E4|F4][m2][C3|D3|E3|F3]]"
                  "[t3/8s96@20][[G4|A4|B4][G3|A3|B3]]")
        self.assertEqual(len(midi.tempos), 2)
        self.assertEqual(midi.tempos[-1]["time"], 4)
        self.assertEqual(len(midi.meters), 2)
        self.assertEqual([n["volume"] for n in midi.notes if n["time"] >= 4], [25] * 6)

    def test_ambiguous_parallel_scores_fail_before_writing(self):
        for score in (
            "[[C4|D4|E4|F4]]", "[[[][]][]]", "[[][]][C4|D4|E4|F4]",
            "[[][]][[][][]]", "[[s96][C4|D4|E4|F4][]]",
            "[[t3/4][C4|D4|E4][]]", "[[][m2]]", "[[][]]junk",
            "[[][]", "[[C4|_|_|_][C4|_|_|_]]",
            "[[C4|_|_|_][_|D4|E4|F4]]",
        ):
            midi = RecordingMIDI()
            with self.subTest(score=score), self.assertRaises(ValueError):
                add_notes(midi, 0, score)
            self.assertEqual(midi.notes, [])
            self.assertEqual(midi.tempos, [])

    def test_parallel_ramps_are_independent(self):
        midi = RecordingMIDI()
        add_notes(midi, 0, "[[m1][<C4@20|D4|E4|F4@80<]"
                  "[m2][>C3@80|D3|E3|F3@20>]]")
        self.assertEqual([n["volume"] for n in midi.notes],
                         [25, 51, 76, 102, 102, 76, 51, 25])


if __name__ == "__main__":
    unittest.main()
