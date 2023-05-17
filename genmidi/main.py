import midiutil
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


def create_midi(track_names: List[str], tempo=120) -> MIDIFile:
    mf = MIDIFile(numTracks=len(track_names))
    for i, name in enumerate(track_names):
        mf.addTrackName(track=i, time=0, trackName=name)
        mf.addTempo(track=i, time=0, tempo=tempo)
    return mf


def note_to_pitch(note: str, oct=None) -> Tuple[int, int]:
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


def add_notes(mf: MIDIFile, track: int, notes: str, time=0):
    STRP = ". "
    p_list = []
    d_list = []
    t_list = []
    tick = 0
    current_octave = 0
    num_conc_notes = 0
    measures = notes[1:-1].split("][")
    for measure in measures:
        print(f"measure: {measure}")
        notes_per_measure = measure.split("|")
        for note_per_measure in notes_per_measure:
            print(f"notes: {note_per_measure}")
            sequence_notes = note_per_measure.split(",")
            if len(note_per_measure.strip(STRP)) > 0:
                duration = round(1/len(sequence_notes), 2)
                sub_tick = 0
                for sequence_note in sequence_notes:
                    print(f"note: {sequence_note}")
                    concurrent_notes = sequence_note.split("+")
                    for note in concurrent_notes:
                        print(f"note+: {note}")
                        note = note.strip(STRP)
                        if note == "":
                            for i in range(num_conc_notes):
                                d_list[-(i+1)] += 1/duration  # extend previous notes
                        else:
                            pitch, current_octave = note_to_pitch(note, current_octave)
                            p_list.append(pitch)
                            d_list.append(duration)
                            t_list.append(tick + sub_tick)
                            print(f"note:{note} octave:{current_octave} len:{duration} time:{time+sub_tick}")
                    num_conc_notes = len(concurrent_notes)
                    sub_tick += duration
            else:  # Empty measure connects the previous notes
                for i in range(num_conc_notes):
                    d_list[-(i+1)] += 1
            tick += 1
    for i, (tick, pitch, duration) in enumerate(zip(t_list, p_list, d_list)):
        mf.addNote(track=track, channel=0, pitch=pitch, time=tick, duration=duration, volume=100)


def create(num, den, sign, scale):
    translate = {2:1, 4:2, 8:3, 16:4}
    den = translate[den]
    mf = create_midi(["right_hand", "left_hand"], tempo=70)
    mf.addTimeSignature(track=0, time=0, numerator=num, denominator=den, clocks_per_tick=32, notes_per_quarter=8)
    mf.addKeySignature(track=0, time=0, accidentals=1, accidental_type=sign, mode=scale)
    mf.addTimeSignature(track=1, time=0, numerator=num, denominator=den, clocks_per_tick=32, notes_per_quarter=8)
    mf.addKeySignature(track=1, time=0, accidentals=1, accidental_type=sign, mode=scale)
    return mf

