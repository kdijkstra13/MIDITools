"""
This file is part of the MIDITools distribution (https://github.com/kdijkstra13/MIDITools).
Copyright (c) 2023 Klaas Dijkstra

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, version 3.
This program is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>.


drClass' MIDI Markup Language (DrC's MML)

1) Create MIDI files for Synthesia using a MIDI markup language
"""
import re
from midiutil.MidiFile import MIDIFile
from typing import List, Tuple

NOTES = {"X": 0,  # rest
         "C": 60,
         "C#": 61, "Db": 61,
         "D": 62,
         "D#": 63, "Eb": 63,
         "E": 64,
         "F": 65,
         "F#": 66, "Gb": 66,
         "G": 67,
         "G#": 68, "Ab": 68,
         "A": 69,
         "A#": 70, "Bb": 70,
         "B": 71}

# Human-readable 0..100 velocity scale. These values are intentionally
# simple presets rather than claims about absolute acoustic loudness.
DYNAMICS = {
    "ppp": 15,
    "pp": 25,
    "p": 35,
    "mp": 50,
    "mf": 65,
    "f": 80,
    "ff": 90,
    "fff": 100,
}

# Gate presets. Like octave and velocity, these carry forward until changed.
ARTICULATIONS = {
    "'": 25,   # staccatissimo
    ".": 50,   # staccato
    "-": 95,   # tenuto
    "~": 100,  # legato
}

DEFAULT_VELOCITY = 79  # maps back to MIDI velocity 100, matching the old default
DEFAULT_GATE = 100
MARCATO_GATE = 70
MARCATO_VELOCITY_FACTOR = 1.20


def create_midi(track_names: List[str], tempo=120) -> MIDIFile:
    mf = MIDIFile(numTracks=len(track_names))
    for i, name in enumerate(track_names):
        mf.addTrackName(track=i, time=0, trackName=name)
        mf.addTempo(track=i, time=0, tempo=tempo)
    return mf


def note_to_pitch(note: str, oct=None) -> Tuple[int, int]:
    # A rest must not reset the carried octave.
    if note == "X":
        return 0, oct

    if len(note) == 1 or (note[1] != "b" and note[1] != "#"):
        pitch = NOTES[note[:1]]
        if len(note) == 2:
            octave = int(note[1])
        else:
            octave = oct
        pitch = pitch + (octave - 4) * 12
    else:
        pitch = NOTES[note[:2]]
        if len(note) == 3:
            octave = int(note[2])
        else:
            octave = oct
        pitch = pitch + (octave - 4) * 12
    return pitch, octave


def _percentage(value: str, what: str) -> int:
    try:
        result = int(value)
    except ValueError as exc:
        raise ValueError(f"Invalid {what}: {value!r}") from exc
    if not 0 <= result <= 100:
        raise ValueError(f"{what.capitalize()} must be between 0 and 100, got {result}")
    return result


def _velocity(value: str) -> int:
    value = value.lower()
    if value in DYNAMICS:
        return DYNAMICS[value]
    return _percentage(value, "velocity")


def _midi_velocity(percent: float) -> int:
    """Convert the readable 0..100 scale to MIDI's 0..127 velocity."""
    return max(0, min(127, round(percent * 127 / 100)))


def _parse_sequence_note(sequence_note: str):
    """Parse one comma-separated note/chord token.

    Grammar (modifiers apply to the whole chord):

        [RAMP] NOTE[+NOTE...][@VELOCITY][ARTICULATION | :GATE]

    Examples:
        C4
        C4@mf
        C4@73:60
        C4+E4+G4@f-
        /C4          start crescendo on C4
        \\C4          start diminuendo on C4
        C4>          marcato (one-note accent; does not carry)

    VELOCITY is ppp..fff or 0..100.
    GATE is 0..100.
    ARTICULATION is ', ., -, or ~ and carries forward.
    """
    token = sequence_note.strip()
    if token == "":
        return None

    ramp = None
    if token[0] in ("/", "\\"):
        ramp = token[0]
        token = token[1:].strip()
        if not token:
            raise ValueError(
                "A ramp marker must be attached to its first note, e.g. /C4 or \\C4"
            )

    gate = None
    articulation = None
    marcato = False

    gate_match = re.search(r":(\d{1,3})$", token)
    if gate_match:
        gate = _percentage(gate_match.group(1), "gate")
        token = token[:gate_match.start()]
    elif token and token[-1] in ARTICULATIONS:
        articulation = token[-1]
        token = token[:-1]
    elif token.endswith(">"):
        marcato = True
        token = token[:-1]

    velocity = None
    velocity_match = re.search(r"@([A-Za-z]+|\d{1,3})$", token)
    if velocity_match:
        velocity = _velocity(velocity_match.group(1))
        token = token[:velocity_match.start()]

    note_names = [part.strip() for part in token.split("+")]
    if not note_names or any(not note for note in note_names):
        raise ValueError(f"Invalid note/chord token: {sequence_note!r}")

    note_pattern = re.compile(r"^[A-G](?:#|b)?\d?$|^X$")
    for note in note_names:
        if not note_pattern.match(note):
            raise ValueError(f"Invalid note {note!r} in token {sequence_note!r}")

    return {
        "notes": note_names,
        "ramp": ramp,
        "velocity": velocity,
        "gate": gate,
        "articulation": articulation,
        "marcato": marcato,
    }


def _resolve_ramp(v_list, t_list, start_index, start_time, start_velocity,
                  target_time, target_velocity, direction):
    if target_time <= start_time:
        raise ValueError("A dynamic ramp needs at least two different note positions")

    if direction == "/" and target_velocity < start_velocity:
        raise ValueError(
            f"Crescendo starts at {start_velocity} but ends lower at {target_velocity}"
        )
    if direction == "\\" and target_velocity > start_velocity:
        raise ValueError(
            f"Diminuendo starts at {start_velocity} but ends higher at {target_velocity}"
        )

    span = target_time - start_time
    for i in range(start_index, len(v_list)):
        if t_list[i] > target_time:
            break
        progress = (t_list[i] - start_time) / span
        progress = max(0.0, min(1.0, progress))
        v_list[i] = start_velocity + (target_velocity - start_velocity) * progress


def add_notes(mf: MIDIFile, track: int, notes: str, time=0):
    p_list = []
    d_list = []
    t_list = []
    v_list = []
    g_list = []
    marcato_list = []

    tick = 0
    current_octave = 4
    current_velocity = DEFAULT_VELOCITY
    current_gate = DEFAULT_GATE
    num_conc_notes = 0

    # A pending ramp is resolved when the next explicit @dynamic/@number occurs.
    pending_ramp = None

    measures = notes[1:-1].split("][")
    for measure in measures:
        print(f"measure: {measure}")
        notes_per_measure = measure.split("|")
        for note_per_measure in notes_per_measure:
            print(f"notes: {note_per_measure}")
            sequence_notes = note_per_measure.split(",")
            if len(note_per_measure.strip(". ")) > 0:
                duration = round(1 / len(sequence_notes), 2)
                sub_tick = 0

                for sequence_note in sequence_notes:
                    print(f"note: {sequence_note}")
                    stripped = sequence_note.strip()

                    # Preserve the original empty-token/tie behavior, including
                    # a lone "." which the old parser treated as an empty slot.
                    if sequence_note.strip(". ") == "":
                        for i in range(num_conc_notes):
                            d_list[-(i + 1)] += 1 / duration
                        sub_tick += duration
                        continue

                    parsed = _parse_sequence_note(sequence_note)
                    event_time = tick + sub_tick

                    if parsed["ramp"] is not None:
                        if pending_ramp is not None:
                            raise ValueError("A new dynamic ramp started before the previous one ended")
                        pending_ramp = {
                            "direction": parsed["ramp"],
                            "start_index": len(v_list),
                            "start_time": event_time,
                            "start_velocity": current_velocity,
                        }

                    # An explicit velocity is persistent and also closes a pending ramp.
                    explicit_velocity = parsed["velocity"]
                    ramp_to_resolve = pending_ramp if (
                        explicit_velocity is not None
                        and pending_ramp is not None
                        and pending_ramp["start_time"] < event_time
                    ) else None

                    if explicit_velocity is not None:
                        current_velocity = explicit_velocity

                    # Gate/articulation settings are persistent.
                    if parsed["gate"] is not None:
                        current_gate = parsed["gate"]
                    elif parsed["articulation"] is not None:
                        current_gate = ARTICULATIONS[parsed["articulation"]]

                    event_start_index = len(v_list)
                    for note in parsed["notes"]:
                        print(f"note+: {note}")
                        pitch, current_octave = note_to_pitch(note, current_octave)
                        p_list.append(pitch)
                        d_list.append(duration)
                        t_list.append(event_time)
                        v_list.append(float(current_velocity))
                        g_list.append(MARCATO_GATE if parsed["marcato"] else current_gate)
                        marcato_list.append(parsed["marcato"])
                        print(
                            f"note:{note} octave:{current_octave} len:{duration} "
                            f"time:{time + sub_tick} velocity:{current_velocity} gate:{g_list[-1]}"
                        )

                    num_conc_notes = len(parsed["notes"])

                    if ramp_to_resolve is not None:
                        _resolve_ramp(
                            v_list=v_list,
                            t_list=t_list,
                            start_index=ramp_to_resolve["start_index"],
                            start_time=ramp_to_resolve["start_time"],
                            start_velocity=ramp_to_resolve["start_velocity"],
                            target_time=event_time,
                            target_velocity=explicit_velocity,
                            direction=ramp_to_resolve["direction"],
                        )
                        pending_ramp = None

                    sub_tick += duration
            else:  # Empty measure connects the previous notes
                for i in range(num_conc_notes):
                    d_list[-(i + 1)] += 1
            tick += 1

    if pending_ramp is not None:
        direction = "crescendo" if pending_ramp["direction"] == "/" else "diminuendo"
        raise ValueError(
            f"Unfinished {direction}: add an explicit target dynamic such as @f or @p"
        )

    for tick, pitch, duration, velocity, gate, marcato in zip(
        t_list, p_list, d_list, v_list, g_list, marcato_list
    ):
        if pitch != 0:  # rest
            if marcato:
                velocity = min(100, velocity * MARCATO_VELOCITY_FACTOR)
            mf.addNote(
                track=track,
                channel=0,
                pitch=pitch,
                time=time + tick,
                duration=duration * gate / 100,
                volume=_midi_velocity(velocity),
            )


def create(num, den, sign, scale, tempo):
    translate = {2: 1, 4: 2, 8: 3, 16: 4}
    den = translate[den]
    mf = create_midi(["right_hand", "left_hand"], tempo=tempo)
    mf.addTimeSignature(track=0, time=0, numerator=num, denominator=den, clocks_per_tick=32, notes_per_quarter=8)
    mf.addKeySignature(track=0, time=0, accidentals=1, accidental_type=sign, mode=scale)
    mf.addTimeSignature(track=1, time=0, numerator=num, denominator=den, clocks_per_tick=32, notes_per_quarter=8)
    mf.addKeySignature(track=1, time=0, accidentals=1, accidental_type=sign, mode=scale)
    return mf
