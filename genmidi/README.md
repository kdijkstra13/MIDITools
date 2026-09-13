# Xala Delta's MIDI Markup Language (MML) Reference

Xala Delta's MML is the compact text notation used by `genmidi/main.py` in MIDITools to create MIDI notes and percussion.

Source implementation: <https://github.com/kdijkstra13/MIDITools/blob/main/genmidi/main.py>

## Quick start

Every score passed to `add_notes()` starts with a mandatory header:

```text
[4/4,192,4][C4|D4|E4|F4][G4|A4|B4|C5]
```

The first bracket is the score header:

```text
[time-signature, tempo, MIDI-channel]
```

So:

```text
[4/4,192,4]
```

means:

- time signature: **4/4**;
- tempo: **192 BPM**;
- melodic MIDI channel: **4**.

The brackets after the header are musical measures.

The most important symbols are:

| Syntax                 | Meaning |
|------------------------|---|
| `[4/4,192,4]`          | Mandatory score header: meter, BPM, melodic MIDI channel |
| `[ ... ]`              | Measure |
| `\|`                   | Next beat |
| `,`                    | Split one beat into equal subdivisions |
| `+`                    | Play events together |
| `_`                    | Carry/hold the complete previous event |
| `-`                    | Rest/silence when used by itself |
| `BD`, `SD`, `CH`, etc. | Two-letter drum names |
| `p`, `mf`, `f`, etc.   | Named velocity/dynamic |
| `@0..100`              | Exact numeric velocity percentage |
| `:0..100`              | Sounding-duration/gate percentage |
| `'`, `.`, `-`, `~`     | Articulation/gate presets |
| `>`                    | One-event marcato |
| `/`                    | Start crescendo |
| `\`                    | Start diminuendo |

A compact score using several features:

```text
[4/4,192,4][C4p.|D4,E4|/F4|G4+A4+C5][A4|B4|C5f>|C5+E5+G5-]
```

---

## 1. Score header

The header is always the first bracket in an MML score:

```text
[NUMERATOR/DENOMINATOR,TEMPO,CHANNEL]
```

Example:

```text
[4/4,192,4]
```

### Time signature

The first field is a normal human-readable time signature:

```text
4/4
3/4
6/8
12/8
```

The denominator must be a power of two: `1`, `2`, `4`, `8`, `16`, and so on.

MIDI stores a time-signature denominator as a power-of-two exponent. That conversion is performed internally by `_parse_header()` when metadata is written. You always write the familiar musical value such as `4` or `8` in MML.

For example:

```text
4/4 -> MIDIUtil denominator 2
6/8 -> MIDIUtil denominator 3
```

There is no denominator conversion in `create()` anymore.

### Tempo

The second field is BPM:

```text
[4/4,120,1]
[4/4,192,1]
[3/4,72,1]
```

Tempo must be at least 1 BPM.

### MIDI channel

The third field is the human MIDI channel number, from `1` through `16`:

```text
[4/4,192,1]
[4/4,192,4]
[4/4,192,16]
```

MIDIUtil uses zero-based channel numbers internally, so MML channel `4` is passed to MIDIUtil as channel `3`.

This channel applies to **melodic notes**. Drum codes always use General MIDI percussion channel 10.

```text
[4/4,192,4][C4+BD|D4+CH|E4+SD|F4+CH]
```

In that score:

- `C4`, `D4`, `E4`, `F4` use MIDI channel 4;
- `BD`, `CH`, `SD` use MIDI channel 10.

If you deliberately choose channel 10 in the header, melodic notes will also be sent on channel 10 and a General MIDI device may interpret their pitches as percussion.

### The header is mandatory

This is invalid:

```text
[C4|D4|E4|F4]
```

This is valid:

```text
[4/4,120,1][C4|D4|E4|F4]
```

---

## 2. Notes and octaves

Supported melodic note names are:

```text
C  C#  Db  D  D#  Eb  E  F  F#  Gb  G  G#  Ab  A  A#  Bb  B
```

Notes use uppercase letters. Sharps use `#`; flats use lowercase `b`.

Examples:

```text
C4
F#4
Bb3
Eb5
```

An octave is a single digit written directly after the note:

```text
C4
A3
F#5
Bb2
```

The parser starts in octave **4**. An explicitly written octave becomes the current octave and carries forward to later notes that omit it.

```text
[4/4,120,1][C4|D|E|F][G|A|B|C5]
```

Here `D` through `B` are in octave 4. After `C5`, later octave-less notes use octave 5.

Octave carry-over also happens inside chords:

```text
C4+E+G
```

means:

```text
C4+E4+G4
```

and:

```text
C4+E5+G
```

means:

```text
C4+E5+G5
```

---

## 3. Measures, beats, and subdivisions

After the header, each bracketed group is a measure:

```text
[4/4,120,1][C4|D4|E4|F4]
```

A field separated by `|` is one MML beat. Its duration comes from the time-signature denominator. MIDIUtil timing is measured in quarter-note units, so:

| Meter denominator | Duration of one `|` beat |
|---:|---:|
| `2` | `2.0` quarter-note units |
| `4` | `1.0` quarter-note unit |
| `8` | `0.5` quarter-note units |
| `16` | `0.25` quarter-note units |

For example, in 4/4:

```text
[4/4,120,1][C4|D4|E4|F4]
```

each event lasts one quarter note. In 6/8:

```text
[6/8,120,1][C4|D4|E4|F4|G4|A4]
```

each event lasts one eighth note, or `0.5` MIDIUtil quarter-note units. The complete measure therefore lasts `3.0` quarter-note units, as a 6/8 measure should.

Use commas to split one beat into equal subdivisions.

Two events per quarter-note beat in 4/4:

```text
[4/4,120,1][C4,D4|E4,F4|G4,A4|B4,C5]
```

Each gets half of the beat. In 6/8, the same comma split divides an eighth-note beat:

```text
[6/8,120,1][C4,D4|E4,F4|G4,A4|B4,C5|D5,E5|F5,G5]
```

Each comma-separated event there lasts one sixteenth note (`0.25` quarter-note units).

Subdivision duration is calculated as:

```text
(4 / denominator) / number_of_comma_separated_slots
```

The parser keeps the fractional value instead of rounding it to two decimal places, so tuplets do not accumulate avoidable timing drift.

The parser does **not** enforce the number of `|` fields inside a measure. Keep the textual measure layout consistent with the numerator in the header.

---

## 4. Carry and rest

Xala Delta's MML distinguishes holding from silence explicitly.

### Carry: `_`

Use `_` to extend the complete previous event through the current rhythmic slot:

```text
[4/4,120,1][C4|_|_|G4]
```

`C4` lasts through beats 1, 2, and 3. `G4` begins on beat 4.

Carry also works inside subdivisions:

```text
[4/4,120,1][C4,_|D4,-|E4,_|F4,-]
```

The `_` extends the preceding event by exactly one subdivision.

A carry must have a previous event. This is invalid:

```text
[4/4,120,1][_|C4|D4|E4]
```

### Rest: `-`

Use standalone `-` for silence:

```text
[4/4,120,1][C4|-|E4|-]
```

A rest consumes its slot but creates no MIDI note.

A rest does not reset octave carry:

```text
[4/4,120,1][C5|-|D|-]
```

The `D` is `D5`.

---

## 5. Chords and simultaneous events

Use `+` to play several events at the same time:

```text
C4+E4+G4
```

A chord occupies the same rhythmic slot as one note.

```text
[4/4,120,1][C4+E4+G4|F4+A4+C5|G4+B4+D5|C4+E4+G4]
```

Drums and melodic notes can be mixed in the same event:

```text
[4/4,120,4][C4+BD|D4+CH|E4+SD|F4+CH]
```

The melodic notes use channel 4; the drums use channel 10.

Modifiers apply to the complete chord/event:

```text
C4+E4+G4f
C4+E4+G4@72
C4+E4+G4mf:80
BD+CHf
```

---

## 6. Drums and percussion

Drums use two uppercase letters and are parsed directly by `add_notes()`.

| Code | Drum sound | GM note |
|---|---|---:|
| `BD` | Bass Drum 1 | 36 |
| `SS` | Side Stick | 37 |
| `SD` | Acoustic Snare | 38 |
| `CP` | Hand Clap | 39 |
| `CH` | Closed Hi-Hat | 42 |
| `PH` | Pedal Hi-Hat | 44 |
| `LT` | Low Tom | 45 |
| `OH` | Open Hi-Hat | 46 |
| `MT` | Low-Mid Tom | 47 |
| `CR` | Crash Cymbal 1 | 49 |
| `HT` | High Tom | 50 |
| `RD` | Ride Cymbal 1 | 51 |
| `RB` | Ride Bell | 53 |
| `TB` | Tambourine | 54 |
| `CB` | Cowbell | 56 |

Drum codes always use MIDI channel 10, independently of the melodic channel in the score header.

A simple pattern:

```text
[4/4,120,1][BD+CH,CH,CH,CH|SD+CH,CH,CH,CH|BD+CH,CH,BD+CH,CH|SD+CH,CH,CH,OH]
```

Carry and rest work exactly like they do for melodic notes:

```text
[4/4,120,1][BD,_,_,_|SD,-,-,-|BD+CH,_,_,_|SD+OH,-,-,-]
```

- `_` extends the complete previous drum event;
- `-` is a silent step.

The same dynamics and gate modifiers work on drums:

```text
SDf
BD@90
CHp
OH:80
SD>
```

---

## 7. Dynamics and velocity

Velocity can be written in two ways:

1. named musical dynamics, written directly after the event;
2. an exact percentage, written with `@`.

### Named dynamics: no `@`

| Dynamic | Internal level (0-100) |
|---|---:|
| `ppp` | 15 |
| `pp` | 25 |
| `p` | 35 |
| `mp` | 50 |
| `mf` | 65 |
| `f` | 80 |
| `ff` | 90 |
| `fff` | 100 |

Examples:

```text
C4p
C4mf
C4f
C4+E4+G4ff
SDmf
```

### Numeric velocity: `@`

Use `@0..100` for an exact velocity percentage:

```text
C4@42
C4@73
C4+E4+G4@90
BD@85
```

Named and numeric velocities are persistent until another explicit velocity appears:

```text
[4/4,120,1][C4p|D4|E4mf|F4][G4@73|A4|B4f|C5]
```

The default internal velocity is 79%, which maps to MIDI velocity 100.

---

## 8. Articulation and sounding duration

Articulation controls how much of the written rhythmic duration sounds.

| Suffix | Name | Gate |
|---|---|---:|
| `'` | Staccatissimo | 25% |
| `.` | Staccato | 50% |
| `-` | Tenuto | 95% |
| `~` | Legato | 100% |

Examples:

```text
C4'
D4.
E4-
F4~
```

Standalone `-` is a rest; trailing `-` is tenuto:

```text
-      rest
C4-    tenuto C4
SD-    tenuto snare event
```

Articulation settings are persistent:

```text
[4/4,120,1][C4.|D4|E4-|F4][G4~|A4|B4|C5]
```

### Exact gate percentage

Use `:0..100`:

```text
C4:60
C4+E4+G4:80
OH:50
```

`C4:60` means the MIDI note sounds for 60% of its notated duration.

Gate settings are persistent until changed.

Velocity and gate can be combined:

```text
C4@73:60
C4mf:60
SD@85:50
```

---

## 9. Marcato

Append `>` for a one-event marcato accent:

```text
C4>
C4+E4+G4>
C4mf>
SD@75>
```

Marcato:

- applies only to that event;
- uses a 70% gate;
- multiplies velocity by 1.20;
- caps velocity at 100%;
- does not replace the persistent velocity or gate afterward.

---

## 10. Crescendo and diminuendo

Use `/` before an event to start a crescendo:

```text
/C4
```

Use `\` before an event to start a diminuendo:

```text
\C4
```

A ramp ends at the next event with an explicit named or numeric velocity.

Crescendo:

```text
[4/4,120,1][C4p|/D4|E4|F4][G4|A4|B4|C5f]
```

Crescendo to an exact percentage:

```text
[4/4,120,1][C4p|/D4|E4|F4][G4|A4|B4|C5@72]
```

Diminuendo:

```text
[4/4,120,1][C5ff|\B4|A4|G4][F4|E4|D4|C4p]
```

Ramp rules:

- `/` must finish at the same or a higher velocity;
- `\` must finish at the same or a lower velocity;
- a ramp needs at least two different event positions;
- a second ramp cannot start before the first ends;
- an unfinished ramp raises an error;
- the target velocity remains active afterward.

Inside Python source, a raw string is convenient for diminuendo notation:

```python
notes = r"[4/4,120,1][C5ff|\B4|A4|G4][F4|E4|D4|C4p]"
```

---

## 11. Modifier order

An event has this general shape:

```text
[RAMP] CHORD [VELOCITY] [ENDING]
```

where:

```text
RAMP       = / or \
CHORD      = EVENT-NAME or EVENT-NAME+EVENT-NAME+...
VELOCITY   = ppp | pp | p | mp | mf | f | ff | fff | @0..100
ENDING     = ' | . | - | ~ | :0..100 | >
```

Examples:

```text
C4
C4mf
C4@73
C4mf.
C4@73:60
C4+E4+G4f-
SDmf
BD+CH@80
/C4
\C4
C4>
```

Do not reverse modifier order:

```text
C4f-      valid
C4-f      invalid
```

---

## 12. Cheat Sheet

```text
score       := header measure+
header      := "[" numerator "/" denominator "," tempo "," channel "]"
measure     := "[" beat ("|" beat)* "]"
beat        := slot ("," slot)*
slot        := event | carry
carry       := "_"
event       := [ramp] chord [velocity] [ending]
chord       := event_name ("+" event_name)*
event_name  := note | drum | rest
note        := A-G ["#" | "b"] [octave]
rest        := "-"
drum        := BD | SS | SD | CP | CH | PH | LT | OH | MT | CR | HT | RD | RB | TB | CB
octave      := one decimal digit
ramp        := "/" | "\\"
velocity    := dynamic | "@" percent
dynamic     := ppp | pp | p | mp | mf | f | ff | fff
ending      := "'" | "." | "-" | "~" | ":" percent | ">"
percent     := integer from 0 through 100
numerator   := positive integer
denominator := positive power of two
tempo       := positive integer BPM
channel     := integer from 1 through 16
```

---

## 13. Using MML from Python

Tempo and time signature no longer belong to `create()`. They are part of each MML header.

```python
import midiutil
from genmidi.main import create, add_notes

mf = create(
    sign=midiutil.SHARPS,
    scale=midiutil.MAJOR,
    track_names=["right_hand", "left_hand"],
)

right_hand = (
    "[4/4,192,1]"
    "[C4p|D|E|F]"
    "[Gmf|A|B|C5f]"
)

left_hand = (
    "[4/4,192,2]"
    "[C3+E3+G3|_|F3+A3+C4|_]"
    "[G3+B3+D4|_|C3+E3+G3|_]"
)

add_notes(mf, 0, right_hand)
add_notes(mf, 1, left_hand)

with open("example.mid", "wb") as f:
    mf.writeFile(f)
```

### `create()`

The current API is:

```python
create(sign, scale, track_names=None)
```

If `track_names` is omitted, the historical defaults are used:

```text
right_hand
left_hand
```

`create()` creates and names the tracks and writes key-signature metadata. It does **not** write tempo or time-signature metadata.

### `add_notes()`

The API remains:

```python
add_notes(mf, track, notes, time=0)
```

`add_notes()` reads tempo, time signature, and melodic MIDI channel from the MML header.

The optional `time=` argument offsets both the notes and the header metadata:

```python
add_notes(
    mf,
    0,
    "[3/4,96,1][C4|D4|E4]",
    time=8,
)
```

That can be used to introduce a later tempo or meter change by adding another MML section at a later time.

If multiple tracks start at the same time, their header tempo and time signature should normally agree. MIDI tempo/time-signature metadata is effectively score-wide even though MIDIUtil accepts a track argument for those events.

---

## 14. Meter-aware rhythmic behavior

The time-signature denominator controls the duration of every `|` beat:

```text
beat_duration = 4 / denominator
```

Therefore:

- `4/4` uses quarter-note beats (`1.0` MIDIUtil time unit each);
- `6/8` uses eighth-note beats (`0.5` each);
- `3/2` uses half-note beats (`2.0` each);
- `5/16` uses sixteenth-note beats (`0.25` each).

Commas subdivide that denominator-sized beat, and `_` extends the previous event by the same slot duration. This means a six-beat 6/8 measure now occupies exactly three quarter-note MIDI time units:

```text
[6/8,120,1][C4|D4|E4|F4|G4|A4]
```

The parser still does not enforce that each bracketed measure has exactly the numerator's number of `|` beats. That remains a notation/layout responsibility.

The BPM value is passed to MIDI as standard MIDI tempo (quarter notes per minute); the meter denominator changes note durations, not the MIDI tempo event itself.

---

## Quick reference card

| Goal                 | Syntax               | Example       |
|----------------------|----------------------|---------------|
| Score header         | `[meter,bpm,channel]` | `[4/4,192,4]` |
| Note                 | `NOTE[octave]`       | `C4`          |
| Sharp                | `#`                  | `F#4`         |
| Flat                 | `b`                  | `Bb3`         |
| Rest                 | standalone `-`       | `C4\|-\|D4`   |
| Carry previous event | `_`                  | `C4\|_\|D4`   |
| Drum                 | two-letter code      | `BD`          |
| Drum chord           | `+`                  | `BD+CH`       |
| Next beat            | `\|`                 | `C4\|D4`      |
| Subdivide beat       | `,`                  | `C4,D4`       |
| Chord                | `+`                  | `C4+E4+G4`    |
| Named dynamic        | `ppp..fff`           | `C4mf`        |
| Numeric velocity     | `@0..100`            | `C4@73`       |
| Staccatissimo        | `'`                  | `C4'`         |
| Staccato             | `.`                  | `C4.`         |
| Tenuto               | trailing `-`         | `C4-`         |
| Legato               | `~`                  | `C4~`         |
| Exact gate           | `:0..100`            | `C4:60`       |
| Velocity + gate      | `@V:G`               | `C4@73:60`    |
| Named dynamic + gate | `dynamic:G`          | `C4mf:60`     |
| Marcato              | `>`                  | `C4>`         |
| Crescendo start      | `/`                  | `/C4`         |
| Diminuendo start     | `\`                  | `\C4`         |

## Five rules to remember

1. Every score starts with a header such as `[4/4,192,4]` for meter, BPM, and melodic MIDI channel.
2. Use `[ ... ]` for measures, `|` for beats, commas for subdivisions, and `+` for simultaneous events.
3. Use `_` to carry the previous event and standalone `-` for silence; empty slots are invalid.
4. Write named dynamics directly (`C4mf`); use `@` only for numeric velocity (`C4@73`) and `:` for gate percentage (`C4:60`).
5. Drum codes always use MIDI channel 10; the header channel applies to melodic notes.
