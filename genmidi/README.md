# Xala Delta's MIDI Markup Language (MML)

Write melodies, chords, and drum patterns as text, then turn them into MIDI files with Python.

## Getting started

From the **MIDITools repository root** (the directory containing `genmidi`), install the dependency:

```sh
python -m pip install MIDIUtil
```

Save this as `example.py` in that same directory:

```python
from genmidi.main import create_midi, add_notes

midi = create_midi(["Melody and drums"])
score = (
    "[4/4,120,1,10,@70]"
    "[C4+BD|D4+CH|E4+SD|F4+CH]"
    "[G4+BD|_|,E4+SD|C4+CH]"
)
add_notes(midi, 0, score)

with open("example.mid", "wb") as output:
    midi.writeFile(output)
```

Run `python example.py`, then open `example.mid` in your MIDI player or DAW.

The header selects **4/4**, **120 BPM**, melody channel **1**, beats channel **10**, and velocity **70%**. Each following bracket is one measure:

- `|` separates beats; a 4/4 measure has four beats, each with one or more positions.
- `+` plays notes and drums together.
- `_` holds the previous event for another position.
- `,` splits a beat equally. In `,E4+SD`, the first half is silent.

Change the pitches, add another measure, or use the reference below to add expression.

## Contents

- [Score header](#score-header)
- [Rhythm and silence](#rhythm-and-silence)
- [Notes and chords](#notes-and-chords)
- [Drum codes](#drum-codes)
- [Dynamics and articulation](#dynamics-and-articulation)
- [Examples](#examples)
- [Python API](#python-api)
- [Parse errors](#parse-errors)

## Score header

Every score starts with a header followed by at least one measure.

```text
[meter,tempo,melody-channel]
[meter,tempo,melody-channel,beats-channel]
[meter,tempo,melody-channel,beats-channel,velocity:gate]
```

The beats channel and velocity/gate settings are optional independently. Velocity and gate share one field: `@mf:80`, not `@mf,:80`. A gate-only field keeps its colon, as in `[4/4,120,1,:80]`. All header settings establish persistent defaults, including a bare dynamic such as `mf`.

| Field | Accepted values | Default |
|---|---|---|
| Meter | Positive numerator / power-of-two denominator, such as `4/4` or `6/8` | Required |
| Tempo | Positive integer BPM, in quarter notes per minute | Required |
| Melody channel | `1..16` | Required |
| Beats channel | `1..16` | `10` |
| Velocity | `@0..100` or `@dynamic` (bare dynamics also accepted in headers) | `79` (MIDI velocity 100) |
| Gate | `:0..100` or a prefixed articulation such as `:~` | `100` |

Both channel fields use human numbering. Drum codes use the beats channel; notes use the melody channel. Channel 10 is the standard General MIDI percussion channel. Other channels allow custom routing.

| Header example | Meaning |
|---|---|
| `[4/4,120,2]` | Melody channel 2; default beats, velocity, and gate |
| `[4/4,120,2,16]` | Melody channel 2, beats channel 16 |
| `[4/4,120,2,@68]` | Initial velocity 68; default beats channel |
| `[4/4,120,2,:80]` | Initial gate 80 |
| `[4/4,120,2,10,@mf:~]` | Both channels, mezzo-forte velocity, and full gate |

## Rhythm and silence

Each bracket after the header is a measure. It must contain **exactly the numerator's number of beats**, including empty beats. Use `|` between beats and commas to divide a beat into equal positions.

| Notation | Meaning |
|---|---|
| `[C4\|D4\|E4\|F4]` | Four beats |
| `C4,D4` | Two equal positions within one beat |
| `C4,D4,E4` | Three equal positions within one beat |
| `C4,_` | One event occupying both halves; its gate determines how long it sounds |
| `C4,` | Note, then silence |
| `,C4` | Silence, then note |
| `[C4\|\|E4\|]` | Notes on beats 1 and 3; silence on beats 2 and 4 |
| `[\|\|\|]` | A silent four-beat measure |

A beat's duration comes from the meter denominator: quarter note in 4/4, eighth note in 6/8, half note in 3/2. In MIDI quarter-note units:

```text
position duration = (4 / denominator) / positions in the beat
```

For example, a 6/8 measure has six eighth-note beats and lasts three quarter-note units:

```text
[6/8,120,1][C4|D4|E4|F4|G4|A4]
```

`_` extends the entire previous event, including every chord member or drum hit. It can cross beat and measure boundaries. After a rest, it continues the silence; at the very start of a score, it is invalid.

Gate is applied to the event's total duration after carries are added. For example, `C4.,_` occupies one beat but sounds for half a beat. Carries do not retrigger notes or change their velocity.

Empty positions consume time without creating notes or resetting octave, velocity, or gate. Spaces around positions are ignored. A standalone `-` is invalid; a trailing `-` on a note means tenuto.

The header must begin at the first character of the score; leading whitespace before it is not accepted. Whitespace between measures is allowed. Keep note names and their modifiers together, such as `C4@mf:~`. Settings and ramp markers must belong to a note or chord; standalone `@mf`, `:~`, `<`, and modifiers on `_` or empty positions are not supported.

## Notes and chords

Use uppercase note names, an optional accidental, and an optional single-digit octave:

```text
C  C#  Db  D  D#  Eb  E  F  F#  Gb  G  G#  Ab  A  A#  Bb  B
```

Examples: `C4`, `F#5`, `Bb3`. The starting octave is **4**. An explicit octave carries forward, including inside chords: `C4+E5+G` means `C4+E5+G5`. Drum hits do not change the octave.

Use only the spellings listed above; alternatives such as `Cb` and `E#` are not implemented. C4 maps to MIDI pitch 60. Although the parser accepts single-digit octaves, MIDI output requires pitches in `0..127`; with this octave convention, stay between C0 and G9. Higher notes are not range-checked by the parser and can fail when the MIDI file is written.

Join notes or drum codes with `+` to play them simultaneously. A chord occupies one position, and its modifiers apply to every member:

```text
C4+E4+G4
C4+BD
C4+E4+G4mf:80
```

## Drum codes

Drum codes use the beats channel from the header. They support the same rhythm, dynamics, articulation, and carry notation as melodic notes.

| Code | Sound | MIDI pitch |
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

## Dynamics and articulation

Modifiers follow this order; each part except the note/chord is optional:

```text
optional ramp marker, then note/chord, then optional velocity, then optional ending
```

Only chord members are joined with `+`. For example, `<C4+E4+G4` starts a crescendo on a chord; `C4mf.` plays a mezzo-forte staccato note. Choose one ending: a bare articulation, a persistent `:` gate or articulation, or marcato. Endings cannot be stacked: `C4:60.` and `C4:.^` are invalid.

### Velocity

Use `@` for persistent velocity: `C4@90` sets 90%, and `SD@mf` sets mezzo-forte for this and subsequent events. A bare dynamic, such as `C4p` or `SDmf`, affects only that event. Afterward, the persistent velocity resumes outside a ramp; inside a ramp, unmarked events follow the interpolation described below. Numeric velocities always require `@` and are persistent.

| Dynamic | Velocity (%) |
|---|---:|
| `ppp` | 15 |
| `pp` | 25 |
| `p` | 35 |
| `mp` | 50 |
| `mf` | 65 |
| `f` | 80 |
| `ff` | 90 |
| `fff` | 100 |

### Gate and accents

Gate controls sounding duration without changing the position's timing or the start of the next event. Use `:` for persistence: `C4:60` sets a 60% gate, and `C4:~` sets full gate for this and subsequent events. Bare articulation symbols affect only their event.

| Ending | Meaning | Gate | Example |
|---|---|---:|---|
| `'` | Staccatissimo | 25% | `C4'` |
| `.` | Staccato | 50% | `C4f.` |
| `-` | Tenuto | 95% | `C4-` |
| `~` | Full gate (legato preset) | 100% | `C4~` |
| `:0..100` | Persistent exact gate | Specified % | `C4@73:60` |
| `^` | Marcato, this event only | 70% | `SD@75^` |

Prefix any of `'`, `.`, `-`, or `~` with `:` to make its gate persistent: `C4:'`, `C4:.`, `C4:-`, or `C4:~`. Marcato `^` is always incidental and also multiplies the event's velocity by 1.20, capped at 100%; `:^` is not supported.

`~` makes the note last its full written duration; it does not add overlap or send a legato controller message. Marcato's velocity boost is applied after ramp interpolation and does not change the persistent velocity.

### Settings carry forward

Header velocity and gate establish the starting values. Within the score, `@` updates persistent velocity and `:` updates persistent gate. Bare dynamics and articulations override only their own event, including all chord members and any carries of that event.

```text
[4/4,120,1,@50:90][C4@mf:~|D4p.|E4|F4:60][G4|_|_|_]
```

`C4@mf:~` sets persistent velocity 65 and gate 100. `D4p.` uses velocity 35 and gate 50 only for D4. E4 returns to 65 and 100. `F4:60` changes the persistent gate to 60, which G4 also uses. Octave, velocity, and gate state start fresh on each `add_notes()` call.

### Crescendo and diminuendo

Prefix an event with `<` to start a crescendo or `>` to start a diminuendo. Repeat the **same marker** on a later event to end it, and include a target dynamic or numeric velocity on that closing event. Velocities are interpolated over musical time.

```text
[4/4,120,1][<C4p|D4|E4|<F4f][>G4@80|F4|E4|>C4p]
```

A dynamic on the opening event sets the starting level: `<C4p` starts at piano. If omitted, the persistent velocity is used. A crescendo must end at an equal or higher velocity; a diminuendo at an equal or lower velocity. Missing closing markers, closing markers without a target velocity, and mismatched markers raise `ValueError`. Close the current ramp before starting another on a separate event.

Dynamics inside a ramp do not end it. They override their own event, and subsequent unmarked events continue along the ramp. For example, D4 is piano here, while E4 uses the interpolated velocity:

```text
[4/4,120,1][<C4@20|D4p|E4|<F4@80]
```

The persistence rules still apply. `<F4f` closes a crescendo, then later events resume the persistent velocity; `<F4@f` also keeps forte active afterward. Likewise, `<C4p` sets only the starting level, whereas `<C4@p` changes the persistent default too. A persistent dynamic inside a ramp overrides its event and updates the default used after the ramp; it does not change the interpolation of other ramp events.

## Examples

These are complete scores to pass to `add_notes()`. The getting-started Python script handles file creation and saving.

### Held chords

```text
[4/4,96,2,@60:95][C3+E3+G3|_|F3+A3+C4|_][G3+B3+D4|_|C3+E3+G3|_]
```

Each chord occupies two beats and sounds for 1.9 beats (95% of two beats).

### Jazz shuffle drums

```text
[4/4,120,1,10,@68:80][BD+RD,,RD|,SS+RD,|BD+RD,,RD|,SS+RD,]
```

Each beat has three equal positions. Empty positions provide the gaps in the shuffle.

Longer Python examples are available in [JustForYou.py](JustForYou.py) and the [generated examples directory](generated/).

## Python API

Import these functions from `genmidi.main` when running from the repository root.

| Function | Purpose |
|---|---|
| `create_midi(track_names)` | Create a MIDI file with the named tracks |
| `create(sign, scale, track_names=None)` | Create named tracks and add key-signature metadata with one accidental; `sign` and `scale` use MIDIUtil constants |
| `add_notes(mf, track, notes, time=0, debug=False)` | Parse a score and add its notes, tempo, and meter |

`create()` defaults to tracks named `right_hand` and `left_hand`. Neither creation function sets tempo or meter; these come from score headers.

The `track` argument is **zero-based** and independent of MIDI channels. Use a separate `add_notes()` call for each track. The optional `time` offsets notes and header metadata in quarter-note units:

```python
add_notes(midi, 0, "[3/4,96,1][C4|D4|E4]", time=8, debug=True)
```

Parsing is quiet by default. `debug=True` prints the parsed measures and events. When combining tracks, keep simultaneous tempo and meter settings consistent because MIDI treats them as score-wide metadata.

## Parse errors

The parser reports the errors below with `ValueError`. It does not validate every MIDI limit or accidental spelling; unsupported spellings such as `Cb` currently raise `KeyError`, and some out-of-range values fail during MIDI serialization.

| Problem | Fix |
|---|---|
| Missing header | Start with a header such as `[4/4,120,1]` |
| Wrong number of beats | Use exactly the meter numerator's number of beats separated by `\|`; commas subdivide each beat |
| Missing or nested measure brackets | Put each measure in its own `[ ... ]` group |
| Standalone `-` | Leave the position empty for a rest |
| `_` at the start of a score | Begin with a note, drum hit, or empty position |
| Old ramp or accent symbols | Use `<C4`, `>C4`, and `C4^` |
| Wrong modifier order, such as `C4-f` | Put velocity before the ending: `C4f-` |
| Unfinished or mismatched ramp | Repeat the opening marker on a later event with a target velocity, such as `<F4f` |
| Values outside the accepted ranges | Check the [header](#score-header) and [dynamics](#dynamics-and-articulation) tables |

See [main.py](main.py) for the parser implementation.
