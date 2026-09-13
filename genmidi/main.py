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

Xala Delta's MIDI Markup Language (Xala Delta's MML)

1) Create MIDI files for Synthesia using a MIDI markup language
"""
import re
from midiutil.MidiFile import MIDIFile
from typing import List, Tuple

NOTES = {"-": 0,  # rest
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

# Two-letter General MIDI percussion names. Percussion is written by add_notes()
# on MIDI channel 10 (zero-based channel 9); the score header selects the melodic channel.
DRUMS = {
    "BD": 36,  # Bass Drum 1
    "SS": 37,  # Side Stick
    "SD": 38,  # Acoustic Snare
    "CP": 39,  # Hand Clap
    "CH": 42,  # Closed Hi-Hat
    "PH": 44,  # Pedal Hi-Hat
    "LT": 45,  # Low Tom
    "OH": 46,  # Open Hi-Hat
    "MT": 47,  # Low-Mid Tom
    "CR": 49,  # Crash Cymbal 1
    "HT": 50,  # High Tom
    "RD": 51,  # Ride Cymbal 1
    "RB": 53,  # Ride Bell
    "TB": 54,  # Tambourine
    "CB": 56,  # Cowbell
}

PERCUSSION_CHANNEL = 9

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


def create_midi(track_names: List[str]) -> MIDIFile:
    """Create a MIDI file and name its tracks.

    Tempo and time signature are supplied by each MML score header in
    add_notes(), not here.
    """
    mf = MIDIFile(numTracks=len(track_names))
    for i, name in enumerate(track_names):
        mf.addTrackName(track=i, time=0, trackName=name)
    return mf


def note_to_pitch(note: str, oct=None) -> Tuple[int, int]:
    # A rest must not reset the carried octave.
    if note == "-":
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


def _midi_velocity(percent: float) -> int:
    """Convert the readable 0..100 scale to MIDI's 0..127 velocity."""
    return max(0, min(127, round(percent * 127 / 100)))


def _parse_header(notes: str):
    """Parse the mandatory MML score header.

    Existing form:
        [4/4,192,4]

    Extended forms with optional initial velocity and/or gate:
        [4/4,192,4,@68:80]
        [4/4,192,4,mf:80]
        [4/4,192,4,@68]
        [4/4,192,4,:80]

    Fields:
        4/4  -> time signature
        192  -> tempo in BPM
        4    -> melodic MIDI channel (human numbering 1..16)
        @68  -> optional initial velocity percentage (0..100)
        mf   -> optional named initial dynamic instead of @velocity
        :80  -> optional initial gate percentage (0..100)

    Header velocity and gate become the initial persistent values for the
    score. Note-level velocity, dynamic, gate, or articulation modifiers still
    override them from the point where they occur.

    MIDIUtil expects the time-signature denominator as log2(denominator), so
    the conversion happens here, at the boundary between human MML and MIDI.
    """
    match = re.match(
        r"^\[\s*(\d+)\s*/\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)"
        r"(?:\s*,\s*(?:(ppp|fff|pp|mp|mf|ff|p|f)|@(\d{1,3}))?"
        r"\s*(?::\s*(\d{1,3}))?)?\s*\]",
        notes,
    )
    if not match:
        raise ValueError(
            "MML must start with a header such as [4/4,192,4] "
            "or [4/4,192,4,@70:80]"
        )

    numerator = int(match.group(1))
    denominator = int(match.group(2))
    tempo = int(match.group(3))
    channel = int(match.group(4))

    dynamic_velocity = match.group(5)
    numeric_velocity = match.group(6)
    gate_value = match.group(7)

    velocity = DEFAULT_VELOCITY
    if dynamic_velocity is not None:
        velocity = DYNAMICS[dynamic_velocity]
    elif numeric_velocity is not None:
        velocity = _percentage(numeric_velocity, "velocity")

    gate = DEFAULT_GATE
    if gate_value is not None:
        gate = _percentage(gate_value, "gate")

    if numerator < 1:
        raise ValueError("Time-signature numerator must be at least 1")
    if denominator < 1 or denominator & (denominator - 1):
        raise ValueError("Time-signature denominator must be a power of two")
    if tempo < 1:
        raise ValueError("Tempo must be at least 1 BPM")
    if not 1 <= channel <= 16:
        raise ValueError("MIDI channel must be between 1 and 16")

    body = notes[match.end():].strip()
    if not body:
        raise ValueError("MML header must be followed by at least one measure")
    if not (body.startswith("[") and body.endswith("]")):
        raise ValueError("MML body must contain bracketed measures after the header")

    return {
        "numerator": numerator,
        "denominator": denominator,
        "midi_denominator": denominator.bit_length() - 1,
        "tempo": tempo,
        "channel": channel - 1,
        "velocity": velocity,
        "gate": gate,
        "body": body,
    }


def _parse_sequence_note(sequence_note: str):
    """Parse one comma-separated note/chord token.

    Grammar (modifiers apply to the whole chord):

        [RAMP] NOTE[+NOTE...][VELOCITY][ARTICULATION | :GATE | >]

    Examples:
        C4
        C4mf
        C4@73
        C4mf:60
        C4@73:60
        C4+E4+G4f-
        BD+CH
        SDf
        OH@73:60
        -             rest / silence
        /C4           start crescendo on C4
        \\C4          start diminuendo on C4
        C4>           marcato (one-note accent; does not carry)

    VELOCITY is either a named dynamic (ppp..fff), written directly without @,
    or a numeric percentage written as @0..100.
    GATE is a sounding-duration percentage written as :0..100.
    ARTICULATION is ', ., -, or ~ and carries forward.
    DRUM is one of the two-letter names in DRUMS and uses MIDI channel 10.
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

    # Parse the final duration/articulation modifier first, so forms such as
    # C4mf:60 and C4@73:60 leave the velocity suffix available to parse next.
    gate = None
    articulation = None
    marcato = False

    gate_match = re.search(r":(\d{1,3})$", token)
    if gate_match:
        gate = _percentage(gate_match.group(1), "gate")
        token = token[:gate_match.start()]
    elif token == "-":
        # A standalone '-' is the rest token. A trailing '-' on a note or
        # chord (for example C4-) remains the tenuto articulation.
        pass
    elif token and token[-1] in ARTICULATIONS:
        articulation = token[-1]
        token = token[:-1]
    elif token.endswith(">"):
        marcato = True
        token = token[:-1]

    velocity = None

    # Numeric velocity is explicitly marked with @.
    percentage_velocity_match = re.search(r"@(\d{1,3})$", token)
    if percentage_velocity_match:
        velocity = _percentage(percentage_velocity_match.group(1), "velocity")
        token = token[:percentage_velocity_match.start()]
    else:
        # Named dynamics are lowercase suffixes written directly after the
        # note/chord. Keep this case-sensitive: note names are uppercase.
        dynamic_match = re.search(r"(ppp|fff|pp|mp|mf|ff|p|f)$", token)
        if dynamic_match:
            velocity = DYNAMICS[dynamic_match.group(1)]
            token = token[:dynamic_match.start()]

    note_names = [part.strip() for part in token.split("+")]
    if not note_names or any(not note for note in note_names):
        raise ValueError(f"Invalid note/chord token: {sequence_note!r}")

    note_pattern = re.compile(r"^[A-G](?:#|b)?\d?$|^-$")
    for note in note_names:
        if note not in DRUMS and not note_pattern.match(note):
            raise ValueError(f"Invalid note/drum {note!r} in token {sequence_note!r}")

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
    """Add an MML score whose first bracket is a mandatory score header.

    Basic header syntax:
        [numerator/denominator,tempo,channel]

    Extended header syntax:
        [numerator/denominator,tempo,channel,velocity/gate settings]

    Examples:
        [4/4,192,4]
        [4/4,192,4,@68:80]
        [4/4,192,4,mf:80]
        [4/4,192,4,:80]

    Header velocity/gate are optional initial persistent settings. Note-level
    modifiers can still change them later.

    Each '|' beat has the duration of the time-signature denominator:
    quarter-note units for /4, eighth-note units for /8, half-note units for
    /2, and so on.

    Drum names from DRUMS always use General MIDI percussion channel 10
    (zero-based channel 9).

    Use '_' to carry/hold the complete previous event, including drum hits,
    and '-' for silence. Empty slots are invalid.
    """
    header = _parse_header(notes)
    melodic_channel = header["channel"]
    beat_duration = 4 / header["denominator"]
    notes = header["body"]

    mf.addTempo(track=track, time=time, tempo=header["tempo"])
    mf.addTimeSignature(
        track=track,
        time=time,
        numerator=header["numerator"],
        denominator=header["midi_denominator"],
        clocks_per_tick=32,
        notes_per_quarter=8,
    )

    p_list = []
    d_list = []
    t_list = []
    v_list = []
    g_list = []
    marcato_list = []
    channel_list = []

    tick = 0
    current_octave = 4
    current_velocity = header["velocity"]
    current_gate = header["gate"]
    previous_event_indices = []

    def extend_previous_event(duration):
        """Extend every member of the previous event by the given duration."""
        for index in previous_event_indices:
            d_list[index] += duration

    # A pending ramp is resolved by the next explicit named or numeric velocity.
    pending_ramp = None

    measures = notes[1:-1].split("][")
    for measure in measures:
        print(f"measure: {measure}")
        notes_per_measure = measure.split("|")

        for note_per_measure in notes_per_measure:
            print(f"notes: {note_per_measure}")
            sequence_notes = note_per_measure.split(",")

            if note_per_measure.strip():
                duration = beat_duration / len(sequence_notes)
                sub_tick = 0

                for sequence_note in sequence_notes:
                    print(f"note: {sequence_note}")
                    token = sequence_note.strip()

                    if not token:
                        raise ValueError(
                            "Empty subdivision is not valid MML; use '_' to carry "
                            "the previous event or '-' for a rest"
                        )

                    if token == "_":
                        if not previous_event_indices:
                            raise ValueError("Carry '_' has no previous event to extend")
                        extend_previous_event(duration)
                        sub_tick += duration
                        continue

                    parsed = _parse_sequence_note(sequence_note)
                    event_time = tick + sub_tick

                    if parsed["ramp"] is not None:
                        if pending_ramp is not None:
                            raise ValueError(
                                "A new dynamic ramp started before the previous one ended"
                            )
                        pending_ramp = {
                            "direction": parsed["ramp"],
                            "start_index": len(v_list),
                            "start_time": event_time,
                            "start_velocity": current_velocity,
                        }

                    # An explicit named or numeric velocity is persistent and also
                    # closes a pending ramp.
                    explicit_velocity = parsed["velocity"]
                    ramp_to_resolve = pending_ramp if (
                        explicit_velocity is not None
                        and pending_ramp is not None
                        and pending_ramp["start_time"] < event_time
                    ) else None

                    if explicit_velocity is not None:
                        current_velocity = explicit_velocity

                    # Gate/articulation settings are persistent for both melodic
                    # notes and drums.
                    if parsed["gate"] is not None:
                        current_gate = parsed["gate"]
                    elif parsed["articulation"] is not None:
                        current_gate = ARTICULATIONS[parsed["articulation"]]

                    event_indices = []

                    for note in parsed["notes"]:
                        print(f"note+: {note}")
                        is_drum = note in DRUMS

                        if is_drum:
                            pitch = DRUMS[note]
                            channel = PERCUSSION_CHANNEL
                            display_octave = "drum"
                        else:
                            pitch, current_octave = note_to_pitch(note, current_octave)
                            channel = melodic_channel
                            display_octave = current_octave

                        p_list.append(pitch)
                        d_list.append(duration)
                        t_list.append(event_time)
                        v_list.append(float(current_velocity))
                        g_list.append(
                            MARCATO_GATE if parsed["marcato"] else current_gate
                        )
                        marcato_list.append(parsed["marcato"])
                        channel_list.append(channel)
                        event_indices.append(len(p_list) - 1)

                        print(
                            f"note:{note} octave:{display_octave} len:{duration} "
                            f"time:{time + event_time} velocity:{current_velocity} "
                            f"gate:{g_list[-1]} channel:{channel + 1}"
                        )

                    previous_event_indices = event_indices

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
            else:
                raise ValueError(
                    "Empty beat is not valid MML; use '_' to carry the previous "
                    "event or '-' for a rest"
                )

            tick += beat_duration

    if pending_ramp is not None:
        direction = "crescendo" if pending_ramp["direction"] == "/" else "diminuendo"
        raise ValueError(
            f"Unfinished {direction}: add an explicit target velocity such as f, p, or @70"
        )

    for tick, pitch, duration, velocity, gate, marcato, channel in zip(
        t_list, p_list, d_list, v_list, g_list, marcato_list, channel_list
    ):
        if pitch != 0:  # rest
            if marcato:
                velocity = min(100, velocity * MARCATO_VELOCITY_FACTOR)

            mf.addNote(
                track=track,
                channel=channel,
                pitch=pitch,
                time=time + tick,
                duration=duration * gate / 100,
                volume=_midi_velocity(velocity),
            )


def create(sign, scale, track_names=None):
    """Create a MIDI file. Tempo and meter come from add_notes() headers.

    Key-signature metadata remains a file/track concern. By default the file
    contains the historical right_hand and left_hand tracks.
    """
    if track_names is None:
        track_names = ["right_hand", "left_hand"]

    mf = create_midi(track_names)

    for track in range(len(track_names)):
        mf.addKeySignature(
            track=track,
            time=0,
            accidentals=1,
            accidental_type=sign,
            mode=scale,
        )

    return mf
