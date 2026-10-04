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

Xala Delta Music Markup Language (XDM)

1) Create MIDI files for Synthesia using a MIDI markup language
"""
import re
from typing import TYPE_CHECKING, List, Tuple

if TYPE_CHECKING:
    from midiutil import MIDIFile

NOTES = {"C": 60,
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
# on the beats channel selected by the score header (default: channel 10).
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

# Gate presets. Headers set defaults; note modifiers are local.
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


def create_midi(track_names: List[str]) -> "MIDIFile":
    """Create a MIDI file and name its tracks.

    Tempo and time signature are supplied by headers or defaults in
    add_notes(), not here.
    """
    from midiutil import MIDIFile

    mf = MIDIFile(numTracks=len(track_names))
    for i, name in enumerate(track_names):
        mf.addTrackName(track=i, time=0, trackName=name)
    return mf


def note_to_pitch(note: str, oct=None) -> Tuple[int, int]:
    spelling = re.match(r"[A-G](?:#|b)?", note).group()
    if spelling not in NOTES:
        raise ValueError(f"Unsupported note spelling: {spelling!r}")
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
    if not 0 <= pitch <= 127:
        raise ValueError(f"Note {note!r} is outside MIDI pitch range 0..127")
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


def _parse_prefixed_header(header: str, defaults=None):
    """Read unordered, optionally comma-separated header fields."""
    token = re.compile(
        r"(?P<field>[mbts@:])\s*(?P<value>"
        r"\d+\s*/\s*\d+|ppp|fff|pp|mp|mf|ff|p|f|\d+|['.~-])"
    )
    fields = {}
    position = 0
    while position < len(header):
        separator = re.match(r"[\s,]*", header[position:])
        position += separator.end()
        if position == len(header):
            break
        match = token.match(header, position)
        if match is None:
            raise ValueError(f"Invalid header field at {header[position:]!r}")
        field, value = match.group("field", "value")
        value = re.sub(r"\s+", "", value)
        if field in fields:
            raise ValueError(f"Duplicate header field {field!r}")
        if field == "t":
            if "/" in value:
                parts = value.split("/")
            else:
                raise ValueError("Timing needs a fraction, e.g. t4/4 or t12/8")
            fields[field] = tuple(map(int, parts))
        elif field in "mbs":
            if not value.isdigit():
                raise ValueError(f"Header field {field!r} needs an integer")
            fields[field] = int(value)
        elif field == "@":
            fields[field] = (DYNAMICS[value] if value in DYNAMICS
                             else _percentage(value, "velocity"))
        else:
            fields[field] = (ARTICULATIONS[value] if value in ARTICULATIONS
                             else _percentage(value, "gate"))
        position = match.end()
    if not fields:
        raise ValueError("Header must contain at least one setting")
    defaults = defaults or {
        "numerator": 4, "denominator": 4, "tempo": 120,
        "channel": 0, "beats_channel": 9,
        "velocity": DEFAULT_VELOCITY, "gate": DEFAULT_GATE,
    }
    numerator, denominator = fields.get(
        "t", (defaults["numerator"], defaults["denominator"])
    )
    return (numerator, denominator, fields.get("s", defaults["tempo"]),
            fields.get("m", defaults["channel"] + 1),
            fields.get("b", defaults["beats_channel"] + 1),
            fields.get("@", defaults["velocity"]), fields.get(":", defaults["gate"]))


def _parse_single_header(notes: str, defaults=None):
    """Parse one MML settings header.

    Channels: [4/4,192,4,10,@68:80] selects melody 4 and beats 10.
    The optional beats channel defaults to 10.

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

    Header velocity and gate become the default values for the
    score. All note-level modifiers override only their own event.

    MIDIUtil expects the time-signature denominator as log2(denominator), so
    the conversion happens here, at the boundary between human MML and MIDI.
    """
    match = re.match(
        r"^\[\s*(\d+)\s*/\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)"
        r"(?:\s*,\s*(\d+))?"
        r"(?:\s*,\s*(?:@?(ppp|fff|pp|mp|mf|ff|p|f)|@(\d{1,3}))?"
        r"\s*(?::\s*(\d{1,3}|['.~-]))?)?\s*\]",
        notes,
    )
    prefixed = None
    if not match:
        prefixed = re.match(r"^\[\s*([mbts@:][^\[\]]*)\]", notes)
    if not match and not prefixed:
        raise ValueError(
            "MML must start with a header such as [4/4,192,4] "
            "or [4/4,192,4,@70:80]"
        )

    if prefixed:
        numerator, denominator, tempo, channel, beats_channel, velocity, gate = (
            _parse_prefixed_header(prefixed.group(1), defaults)
        )
        header_end = prefixed.end()
    else:
        numerator = int(match.group(1))
        denominator = int(match.group(2))
        tempo = int(match.group(3))
        channel = int(match.group(4))
        beats_channel = int(match.group(5)) if match.group(5) else 10
        dynamic_velocity = match.group(6)
        numeric_velocity = match.group(7)
        gate_value = match.group(8)
        velocity = DEFAULT_VELOCITY
        if dynamic_velocity is not None:
            velocity = DYNAMICS[dynamic_velocity]
        elif numeric_velocity is not None:
            velocity = _percentage(numeric_velocity, "velocity")
        gate = DEFAULT_GATE
        if gate_value is not None:
            gate = (ARTICULATIONS[gate_value] if gate_value in ARTICULATIONS
                    else _percentage(gate_value, "gate"))
        header_end = match.end()

    if numerator < 1:
        raise ValueError("Time-signature numerator must be at least 1")
    if denominator < 1 or denominator & (denominator - 1):
        raise ValueError("Time-signature denominator must be a power of two")
    if tempo < 1:
        raise ValueError("Tempo must be at least 1 BPM")
    if not 1 <= channel <= 16:
        raise ValueError("MIDI channel must be between 1 and 16")
    if not 1 <= beats_channel <= 16:
        raise ValueError("Beats MIDI channel must be between 1 and 16")

    body = notes[header_end:].strip()
    measures = re.findall(r"\[([^\[\]]*)\]", body)

    return {
        "numerator": numerator,
        "denominator": denominator,
        "midi_denominator": denominator.bit_length() - 1,
        "tempo": tempo,
        "channel": channel - 1,
        "beats_channel": beats_channel - 1,
        "velocity": velocity,
        "gate": gate,
        "body": body,
        "measures": measures,
    }


def _bracket_groups(text):
    """Read balanced groups without silently discarding intervening text."""
    groups = []
    position = 0
    while position < len(text):
        if text[position].isspace():
            position += 1
            continue
        if text[position] != "[":
            raise ValueError("Expected a bracketed header, measure, or parallel group")
        begin = position + 1
        depth = 1
        position += 1
        while position < len(text) and depth:
            if text[position] == "[":
                depth += 1
            elif text[position] == "]":
                depth -= 1
            position += 1
        if depth:
            raise ValueError("Unclosed bracket")
        groups.append(text[begin:position - 1])
    return groups


def _is_header(group):
    return re.match(r"\s*(?:[mbts@:]|\d+\s*/)", group) is not None


def _measure(group, settings):
    if not group.strip():
        group = "|" * (settings["numerator"] - 1)
    beats = len(group.split("|"))
    if beats != settings["numerator"]:
        raise ValueError(
            f"Measure has {beats} beats; expected {settings['numerator']} "
            f"for time signature {settings['numerator']}/{settings['denominator']}"
        )
    return group


def _voice_score(measures, headers):
    result = headers[0].copy()
    result.update(measures=measures, measure_headers=headers)
    return result


def _parse_header(notes: str):
    """Parse sequential measures or sequential groups of parallel measures."""
    groups = _bracket_groups(notes)
    parallel = any("[" in group for group in groups)
    current = _parse_single_header("[m1]")
    voices = []
    states = []
    awaiting_measure = False
    group_count = 0
    for group in groups:
        if "[" not in group and _is_header(group):
            if awaiting_measure:
                raise ValueError("Each header must be followed by a measure or group")
            current = _parse_single_header("[" + group + "]", current)
            states = [_parse_single_header("[" + group + "]", state) for state in states]
            awaiting_measure = True
            continue
        if parallel:
            if "[" not in group:
                raise ValueError("Cannot mix plain measures and parallel groups in one score")
            children = _bracket_groups(group)
            if any("[" in child for child in children):
                raise ValueError("Parallel groups cannot be nested")
            entries = []
            pending = None
            for child in children:
                if _is_header(child):
                    if pending is not None:
                        raise ValueError("Each voice header must be followed by a measure")
                    pending = child
                else:
                    entries.append((pending, child))
                    pending = None
            if pending is not None:
                raise ValueError("Voice header has no following measure")
            if len(entries) < 2:
                raise ValueError("A parallel group must contain at least two voices")
            if group_count and len(entries) != len(voices):
                raise ValueError("Parallel groups must keep the same number of voices; use [] for silence")
        else:
            entries = [(None, group)]
        if not voices:
            voices = [([], []) for _ in entries]
            states = [current.copy() for _ in entries]
        for index, (local_header, measure) in enumerate(entries):
            state = states[index].copy()
            # Tempo and meter are shared; outer headers control their changes.
            for field in ("tempo", "numerator", "denominator", "midi_denominator"):
                state[field] = current[field]
            if local_header is not None:
                state = _parse_single_header("[" + local_header + "]", state)
                if any(state[field] != current[field]
                       for field in ("tempo", "numerator", "denominator")):
                    raise ValueError("Voice headers cannot conflict with shared tempo or meter; use an outer header")
            voices[index][0].append(_measure(measure, state))
            voices[index][1].append(state.copy())
            states[index] = state
        group_count += 1
        awaiting_measure = False
    if not voices or awaiting_measure:
        raise ValueError("A header must be followed by a measure or parallel group")
    scores = [_voice_score(measures, headers) for measures, headers in voices]
    result = scores[0].copy()
    result["voices"] = scores
    return result



def _parse_sequence_note(sequence_note: str):
    """Parse one comma-separated note/chord token.

    Grammar (modifiers apply to the whole chord):

        [RAMP_START] NOTE[+NOTE...][VELOCITY][ARTICULATION | :GATE | ^][RAMP_END]

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
        (empty)       rest / silence
        <C4           start crescendo on C4
        >C4          start diminuendo on C4
        C4^           marcato (one-note accent; does not carry)

    @0..100, @dynamic, and bare dynamics set local velocity.
    :0..100 and :articulation set local gate. Bare ', ., -, and ~
    apply only to this event. Marcato ^ is always local.
    Suffix the same ramp marker on a later event with a target velocity to
    close the ramp, e.g. <C4p ... F4f<. Interior dynamics override only their event
    within the interpolation; none update the header defaults.
    DRUM is one of the two-letter names in DRUMS and uses the header beats channel.
    """
    token = sequence_note.strip()
    if token == "":
        return None

    ramp = None
    ramp_end = None
    if token[0] in ("<", ">"):
        ramp = token[0]
        token = token[1:].strip()
        if not token:
            raise ValueError(
                "A ramp marker must be attached to its first note, e.g. <C4 or >C4"
            )

    if token[-1] in ("<", ">"):
        ramp_end = token[-1]
        token = token[:-1].strip()
        if not token:
            raise ValueError("A ramp endpoint must be attached to a note, e.g. C4p>")
        if ramp is not None:
            raise ValueError("An event cannot both start and end a ramp")

    # Parse the final duration/articulation modifier first, so forms such as
    # C4mf:60 and C4@73:60 leave the velocity suffix available to parse next.
    gate = None
    articulation = None
    marcato = False

    gate_match = re.search(r":(\d{1,3}|['.~-])$", token)
    if gate_match:
        value = gate_match.group(1)
        gate = (ARTICULATIONS[value] if value in ARTICULATIONS
                else _percentage(value, "gate"))
        token = token[:gate_match.start()]
    elif token and token[-1] in ARTICULATIONS:
        articulation = token[-1]
        token = token[:-1]
    elif token.endswith("^"):
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
        dynamic_match = re.search(r"(@?)(ppp|fff|pp|mp|mf|ff|p|f)$", token)
        if dynamic_match:
            velocity = DYNAMICS[dynamic_match.group(2)]
            token = token[:dynamic_match.start()]

    note_names = [part.strip() for part in token.split("+")]
    if not note_names or any(not note for note in note_names):
        raise ValueError(f"Invalid note/chord token: {sequence_note!r}")

    note_pattern = re.compile(r"^[A-G](?:#|b)?\d?$")
    for note in note_names:
        if note not in DRUMS and not note_pattern.match(note):
            raise ValueError(f"Invalid note/drum {note!r} in token {sequence_note!r}")

    return {
        "notes": note_names,
        "ramp": ramp,
        "ramp_end": ramp_end,
        "velocity": velocity,
        "gate": gate,
        "articulation": articulation,
        "marcato": marcato,
    }


def _resolve_ramp(v_list, t_list, start_index, start_time, start_velocity,
                  target_time, target_velocity, direction, explicit_velocities):
    if target_time <= start_time:
        raise ValueError("A dynamic ramp needs at least two different note positions")

    if direction == "<" and target_velocity < start_velocity:
        raise ValueError(
            f"Crescendo starts at {start_velocity} but ends lower at {target_velocity}"
        )

    if direction == ">" and target_velocity > start_velocity:
        raise ValueError(
            f"Diminuendo starts at {start_velocity} but ends higher at {target_velocity}"
        )

    span = target_time - start_time
    for i in range(start_index, len(v_list)):
        if t_list[i] > target_time:
            break
        if start_time < t_list[i] < target_time and explicit_velocities[i]:
            continue
        progress = (t_list[i] - start_time) / span
        progress = max(0.0, min(1.0, progress))
        v_list[i] = start_velocity + (target_velocity - start_velocity) * progress


def _add_voice(mf, track, header, time=0, debug=False):
    """Add an MML score with optional setting headers before measures.

    Basic header syntax:
        [numerator/denominator,tempo,channel]

    Extended header syntax:
        [numerator/denominator,tempo,channel,velocity/gate settings]

    Examples:
        [4/4,192,4]
        [4/4,192,4,@68:80]
        [4/4,192,4,mf:80]
        [4/4,192,4,:80]

    Optional headers before measures change defaults. Note-level modifiers
    apply only to the complete event, including carries.

    Each '|' beat has the duration of the time-signature denominator:
    quarter-note units for /4, eighth-note units for /8, half-note units for
    /2, and so on.

    An optional beats channel follows the melodic channel, e.g.
    [4/4,120,1,10,@68:80]. Both channels use human numbering 1..16.
    Omitted beats channels default to 10.

    Use '_' to carry/hold the complete previous event, including drum hits,
    and empty slots for silence. Each measure must have exactly numerator
    beats. Set debug=True to print parsing diagnostics.
    """
    melodic_channel = header["channel"]
    beat_duration = 4 / header["denominator"]

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
    explicit_velocities = []
    g_list = []
    marcato_list = []
    channel_list = []

    tick = 0
    current_octave = 4
    current_velocity = header["velocity"]
    current_gate = header["gate"]
    previous_event_indices = None

    def extend_previous_event(duration):
        """Extend every member of the previous event by the given duration."""
        for index in previous_event_indices:
            d_list[index] += duration

    # Prefix opens a ramp; a matching suffix closes it on a later event.
    pending_ramp = None

    measures = header["measures"]
    previous_header = None
    for measure, header in zip(measures, header["measure_headers"]):
        melodic_channel = header["channel"]
        beat_duration = 4 / header["denominator"]
        current_velocity = header["velocity"]
        current_gate = header["gate"]
        if previous_header is not None:
            if header["tempo"] != previous_header["tempo"]:
                mf.addTempo(track=track, time=time + tick, tempo=header["tempo"])
            if (header["numerator"], header["denominator"]) != (
                previous_header["numerator"], previous_header["denominator"]
            ):
                mf.addTimeSignature(
                    track=track, time=time + tick, numerator=header["numerator"],
                    denominator=header["midi_denominator"],
                    clocks_per_tick=32, notes_per_quarter=8,
                )
        previous_header = header
        if debug:
            print(f"measure: {measure}")
        notes_per_measure = measure.split("|")

        for note_per_measure in notes_per_measure:
            if debug:
                print(f"notes: {note_per_measure}")
            sequence_notes = note_per_measure.split(",")

            duration = beat_duration / len(sequence_notes)
            sub_tick = 0

            for sequence_note in sequence_notes:
                if debug:
                    print(f"note: {sequence_note}")
                token = sequence_note.strip()

                if not token:
                    previous_event_indices = []
                    sub_tick += duration
                    continue

                if token == "_":
                    if previous_event_indices is None:
                        raise ValueError("Carry '_' has no previous event to extend")
                    extend_previous_event(duration)
                    sub_tick += duration
                    continue

                parsed = _parse_sequence_note(sequence_note)
                event_time = tick + sub_tick
                explicit_velocity = parsed["velocity"]

                ramp_to_resolve = None
                if parsed["ramp"] is not None:
                    if pending_ramp is not None:
                        raise ValueError("A ramp is already open; close it with a suffix first")
                    else:
                        pending_ramp = {
                            "direction": parsed["ramp"],
                            "start_index": len(v_list),
                            "start_time": event_time,
                            "start_velocity": (
                                explicit_velocity if explicit_velocity is not None
                                else current_velocity
                            ),
                        }

                if parsed["ramp_end"] is not None:
                    if pending_ramp is None:
                        raise ValueError("A ramp endpoint has no open ramp")
                    if parsed["ramp_end"] != pending_ramp["direction"]:
                        raise ValueError(
                            f"Mismatched ramp endpoint: expected "
                            f"{pending_ramp['direction']!r}, got {parsed['ramp_end']!r}"
                        )
                    if explicit_velocity is None:
                        raise ValueError(
                            "A ramp endpoint needs an explicit target velocity, "
                            "e.g. F4f< or C4@p>"
                        )
                    ramp_to_resolve = pending_ramp

                event_velocity = (
                    explicit_velocity if explicit_velocity is not None
                    else current_velocity
                )

                event_gate = (
                    ARTICULATIONS[parsed["articulation"]]
                    if parsed["articulation"] is not None else (
                        parsed["gate"] if parsed["gate"] is not None else current_gate
                    )
                )

                event_indices = []

                for note in parsed["notes"]:
                    if debug:
                        print(f"note+: {note}")
                    is_drum = note in DRUMS

                    if is_drum:
                        pitch = DRUMS[note]
                        channel = header["beats_channel"]
                        display_octave = "drum"
                    else:
                        pitch, current_octave = note_to_pitch(note, current_octave)
                        channel = melodic_channel
                        display_octave = current_octave

                    p_list.append(pitch)
                    d_list.append(duration)
                    t_list.append(event_time)
                    v_list.append(float(event_velocity))
                    explicit_velocities.append(explicit_velocity is not None)
                    g_list.append(
                        MARCATO_GATE if parsed["marcato"] else event_gate
                    )
                    marcato_list.append(parsed["marcato"])
                    channel_list.append(channel)
                    event_indices.append(len(p_list) - 1)

                    if debug:
                        print(
                            f"note:{note} octave:{display_octave} len:{duration} "
                            f"time:{time + event_time} velocity:{event_velocity} "
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
                        explicit_velocities=explicit_velocities,
                    )
                    pending_ramp = None

                sub_tick += duration

            tick += beat_duration

    if pending_ramp is not None:
        direction = "crescendo" if pending_ramp["direction"] == "<" else "diminuendo"
        raise ValueError(
            f"Unfinished {direction}: suffix {pending_ramp['direction']!r} "
            "after a later note's modifiers with a target velocity"
        )

    for tick, pitch, duration, velocity, gate, marcato, channel in zip(
        t_list, p_list, d_list, v_list, g_list, marcato_list, channel_list
    ):
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


def parse_xdm(notes: str, track=0, time=0, debug=False):
    """Validate XDM and return MIDI event calls, without requiring MIDIUtil."""
    score = _parse_header(notes)

    class Events:
        def __init__(self):
            self.calls = []

        def addTempo(self, **values):
            self.calls.append(("addTempo", values))

        def addTimeSignature(self, **values):
            self.calls.append(("addTimeSignature", values))

        def addNote(self, **values):
            self.calls.append(("addNote", values))

    all_calls = []
    previous_notes = {}
    for voice_index, voice in enumerate(score["voices"]):
        events = Events()
        _add_voice(events, track, voice, time, debug)
        voice_notes = {}
        for method, values in events.calls:
            if method == "addNote":
                key = (values["channel"], values["pitch"])
                begin = values["time"]
                end = begin + values["duration"]
                for other_begin, other_end in previous_notes.get(key, []):
                    if max(begin, other_begin) < min(end, other_end):
                        raise ValueError(
                            "Parallel voices overlap on the same channel and pitch; "
                            "use separate melody or beats channels"
                        )
                voice_notes.setdefault(key, []).append((begin, end))
            if voice_index == 0 or method == "addNote":
                all_calls.append((method, values))
        for key, intervals in voice_notes.items():
            previous_notes.setdefault(key, []).extend(intervals)
    return all_calls


def validate_xdm(notes: str):
    """Validate syntax, musical structure, and MIDI pitch ranges."""
    parse_xdm(notes)


def add_notes(mf: "MIDIFile", track: int, notes: str, time=0, debug=False):
    """Add a score, validating all voices before writing MIDI events."""
    for method, values in parse_xdm(notes, track, time, debug):
        getattr(mf, method)(**values)


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
