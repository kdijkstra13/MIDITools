# Xala Delta Music Markup Language (XDM)

Write melodies, chords, and drum patterns as text, then turn them into MIDI files with Python.

## Getting started

Install from the repository root:

```sh
python -m pip install .
```

Save raw XDM text in a UTF-8 file named `example.xdm`:

```text
[m1b10t4/4s120@70]
[C4+BD|D4+CH|E4+SD|F4+CH]
[G4+BD|_|,E4+SD|C4+CH]
```

Generate `example.mid`, or validate without writing output:

```sh
xdmgen example.xdm
xdmgen example.xdm -o performance.mid
xdmgen example.xdm --validate
```

Literal XDM text can replace file input:

```sh
xdmgen --code '[t1/1][A+C+E]' -o chord.mid
xdmgen --code '[t1/1][[A][C][E]]' --validate
```

Quote literal text so the shell preserves brackets, spaces, and ramp markers.
File input and `--code` are mutually exclusive. Literal MIDI generation requires
`-o`; `--validate` and `-o` cannot be combined. Input and output must differ.
Validation reports `Valid XDM` and exits with status 0; invalid XDM or I/O errors
exit with status 1. Incorrect CLI arguments exit with status 2.

The CLI lives in [cli.py](cli.py); parsing and validation live in [main.py](main.py).
You can also run `python -m genmidi.cli` from the repository root. This form
supports validation without installing MIDIUtil; generating MIDI requires it.
Open generated MIDI files in your MIDI player or DAW.

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
- [Parallel voices](#parallel-voices)
- [Drum codes](#drum-codes)
- [Dynamics and articulation](#dynamics-and-articulation)
- [Examples](#examples)
- [Python API](#python-api)
- [Parse errors](#parse-errors)

## Score header

A score contains measures, each optionally preceded by a header. Without an initial header, the defaults below apply.

### Prefixed headers

Use letter prefixes to write settings in any order. Commas and spaces are
optional, so these headers are equivalent:

```text
[m2,b10,t4/4,s120,@mf,:-]
[m2b10t4/4s120@mf:-]
```

| Prefix | Meaning | Default | Examples |
|---|---|---|---|
| `m` | Melody channel, `1..16` | `1` | `m2` |
| `b` | Beats channel, `1..16` | `10` | `b10` |
| `t` | Time signature | `4/4` | `t4/4`, `t6/8`, `t12/8` |
| `s` | Speed in quarter-note BPM, positive integer | `120` | `s96` |
| `@` | Velocity percentage or dynamic | `79` | `@20`, `@mf` |
| `:` | Gate percentage or articulation | `100` | `:80`, `:-` |

Time signatures always require a slash: `t4/4`, `t6/8`, or `t12/8`.
Each prefix may occur only once. Unknown fields, duplicate fields, and
out-of-range settings are errors. Include at least one setting in a header.
A header must be followed by a measure. Omitted fields retain the previous
header settings; the first header uses the defaults above.

Headers may appear before any measure:

```text
[m2b10t4/4@20:80][C4@mf:-|D4|E4|F4]
[@70][G4|A4|B4|C5]
[s96t3/4][C4|E4|G4]
```

Only C4 in the first measure uses mezzo-forte and tenuto. D4, E4, and F4
use the header's velocity 20 and gate 80. The next header changes velocity
to 70; channel and gate remain unchanged. The final header changes tempo
and meter. Headers consume no musical time.

### Positional headers (also supported)

```text
[meter,tempo,melody-channel]
[meter,tempo,melody-channel,beats-channel]
[meter,tempo,melody-channel,beats-channel,velocity:gate]
```

The beats channel and velocity/gate settings are optional independently. Velocity and gate share one field: `@mf:80`, not `@mf,:80`. A gate-only field keeps its colon, as in `[4/4,120,1,:80]`. All header settings establish defaults, including a bare dynamic such as `mf`.

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

Each note-containing bracket is a measure; an outer bracket can group measures into parallel voices. A nonempty measure must contain **exactly the numerator's number of beats**, including empty beats. Use `|` between beats and commas to divide a beat into equal positions. `[]` supplies a whole silent measure automatically.

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
| `[]` | A full silent measure in the current meter |

A beat's duration comes from the meter denominator: quarter note in 4/4, eighth note in 6/8, half note in 3/2. In MIDI quarter-note units:

```text
position duration = (4 / denominator) / positions in the beat
```

For example, a 6/8 measure has six eighth-note beats and lasts three quarter-note units:

```text
[6/8,120,1][C4|D4|E4|F4|G4|A4]
```

`_` extends the entire previous event, including every chord member or drum hit. It can cross beat and measure boundaries within the same voice. After a rest, it continues the silence; at the very start of a voice, it is invalid.

Gate is applied to the event's total duration after carries are added. For example, `C4.,_` occupies one beat but sounds for half a beat. Carries do not retrigger notes or change their velocity.

Empty positions consume time without creating notes or resetting octave, velocity, or gate. Spaces around positions are ignored. A standalone `-` is invalid; a trailing `-` on a note means tenuto.

Leading whitespace and whitespace between headers and measures are allowed. Keep note names and their modifiers together, such as `C4@mf:~`. Settings and ramp markers must belong to a note or chord; standalone `@mf`, `:~`, `<`, and modifiers on `_` or empty positions are not supported.

## Parallel voices

Wrap two or more measures in an outer bracket to play independent voices
simultaneously. Consecutive outer groups play sequentially:

```text
[t4/4s120@mf]
[[m1][C4|D4|E4|F4][m2][C3|_|G3|_]]
[[G4|F4|E4|D4][F3|_|G3|_]]
```

All measures in a group start together and use the shared meter, so they
have the same written duration. Each child measure is one voice. A header
inside a group applies to the following voice only. Voice positions identify
the same voices in subsequent groups; their channels, velocity/gate defaults,
octaves, holds, and ramps remain independent and carry forward.

An outer header updates all voices; omitted channel and expression settings
retain each voice's existing values. Tempo and meter can change only through
an outer header. Local headers may repeat the shared tempo/meter but may not
conflict with them. Note modifiers still apply only to their own event.

Use `[]` for a full silent measure in a voice:

```text
[[][]][[][C4|D4|E4|F4]]
```

The first group is silent; the second plays notes in voice 2. Silence clears
that voice's previous event, so a subsequent `_` continues silence.

Ambiguous or unsupported structures raise `ValueError`: deeper nesting,
groups with fewer than two voices, changing the number of voices between
groups, mixing plain measures with parallel groups in one score, headers
without a following measure/group, and conflicting shared tempo or meter.
Use empty measures to retain a silent voice's position. Overlapping notes
in different voices with the same MIDI channel and pitch also raise an error;
assign separate channels when independent note endings are needed. All voices
are validated before MIDI events are written.

## Notes and chords

Use uppercase note names, an optional accidental, and an optional single-digit octave:

```text
C  C#  Db  D  D#  Eb  E  F  F#  Gb  G  G#  Ab  A  A#  Bb  B
```

Examples: `C4`, `F#5`, `Bb3`. The starting octave is **4**. An explicit octave carries forward, including inside chords: `C4+E5+G` means `C4+E5+G5`. Drum hits do not change the octave.

Use only the spellings listed above; alternatives such as `Cb` and `E#` are not implemented. C4 maps to MIDI pitch 60. Although the parser accepts single-digit octaves, MIDI output requires pitches in `0..127`; with this octave convention, stay between C0 and G9. The parser rejects pitches outside MIDI range `0..127`.

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
optional ramp start, then note/chord, then optional velocity, then optional articulation/gate, then optional ramp end
```

Only chord members are joined with `+`. For example, `<C4+E4+G4` starts a crescendo on a chord; `C4mf.` plays a mezzo-forte staccato note. Choose one ending: a bare articulation, a local `:` gate or articulation, or marcato. Endings cannot be stacked: `C4:60.` and `C4:.^` are invalid.

### Velocity

Use `@` for a local velocity: `C4@90` uses 90%, and `SD@mf` uses mezzo-forte. Bare dynamics such as `C4p` mean the same thing as `C4@p`. All affect only their own event; subsequent events use the header defaults unless they are inside a ramp. Numeric velocities require `@`.

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

Gate controls sounding duration without changing the position's timing or the start of the next event. Use `:` for an exact gate or articulation: `C4:60` uses a 60% gate, and `C4:~` uses full gate. These and bare articulation symbols affect only their event.

| Ending | Meaning | Gate | Example |
|---|---|---:|---|
| `'` | Staccatissimo | 25% | `C4'` |
| `.` | Staccato | 50% | `C4f.` |
| `-` | Tenuto | 95% | `C4-` |
| `~` | Full gate (legato preset) | 100% | `C4~` |
| `:0..100` | Local exact gate | Specified % | `C4@73:60` |
| `^` | Marcato, this event only | 70% | `SD@75^` |

Prefix any of `'`, `.`, `-`, or `~` with `:` as an alternative local spelling: `C4:'`, `C4:.`, `C4:-`, or `C4:~`. Marcato `^` is always incidental and also multiplies the event's velocity by 1.20, capped at 100%; `:^` is not supported.

`~` makes the note last its full written duration; it does not add overlap or send a legato controller message. Marcato's velocity boost is applied after ramp interpolation and does not change the header velocity.

### Header defaults and local overrides

Only headers change velocity and gate defaults. All modifiers inside a measure
apply to their own complete event, including chord members and carries.

```text
[@50:90][C4@mf:~|D4p.|E4|F4:60][G4|_|_|_]
```

C4 uses velocity 65 and gate 100. D4 uses velocity 35 and gate 50.
E4 returns to the header defaults, 50 and 90. F4 uses gate 60 only for
itself; G4 uses gate 90 for its complete held duration.

### Crescendo and diminuendo

Prefix an event with `<` to start a crescendo or `>` to start a diminuendo. Place the **same marker after** a later event and all its modifiers to end it, and include a target dynamic or numeric velocity on that closing event. Velocities are interpolated over musical time.

```text
[4/4,120,1][<C4p|D4|E4|F4f<][>G4@80|F4|E4|C4p>]
```

A dynamic on the opening event sets the starting level: `<C4p` starts at piano. If omitted, the header velocity is used. A crescendo must end at an equal or higher velocity; a diminuendo at an equal or lower velocity. Missing closing markers, closing markers without a target velocity, and mismatched markers raise `ValueError`. Close the current ramp before starting another on a separate event. A prefix always opens a ramp; a suffix always closes one. For example, `C4mf'>` closes a diminuendo on a mezzo-forte staccatissimo note. Closing markers without an open ramp and nested opening markers are errors.

Dynamics inside a ramp do not end it. They override their own event, and subsequent unmarked events continue along the ramp. For example, D4 is piano here, while E4 uses the interpolated velocity:

```text
[4/4,120,1][<C4@20|D4p|E4|F4@80<]
```

Opening and closing velocities are local to the ramp. After it closes, unmarked events resume the header velocity. `@` and bare dynamics have the same local scope; interior overrides never change header defaults.

## Examples

Save these scores as `.xdm` files and run `xdmgen`, or pass them to the Python `add_notes()` API.

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

Complete XDM examples are available in [JustForYou.xdm](JustForYou.xdm) and the [generated examples directory](generated/README.md). Those files replace the old Python music examples.

## Python API

Import these functions from `genmidi.main` when running from the repository root.

| Function | Purpose |
|---|---|
| `create_midi(track_names)` | Create a MIDI file with the named tracks |
| `create(sign, scale, track_names=None)` | Create named tracks and add key-signature metadata with one accidental; `sign` and `scale` use MIDIUtil constants |
| `add_notes(mf, track, notes, time=0, debug=False)` | Parse a score and add its notes, tempo, and meter |
| `parse_xdm(notes, track=0, time=0, debug=False)` | Validate and return MIDI event calls without writing them |
| `validate_xdm(notes)` | Validate XDM; raise `ValueError` on invalid input |

`create()` defaults to tracks named `right_hand` and `left_hand`. Neither creation function sets tempo or meter; these come from headers or the default 120 BPM and 4/4.

The `track` argument is **zero-based** and independent of MIDI channels. Use a separate `add_notes()` call for each track. The optional `time` offsets notes and header metadata in quarter-note units:

```python
add_notes(midi, 0, "[3/4,96,1][C4|D4|E4]", time=8, debug=True)
```

Parsing is quiet by default. `debug=True` prints the parsed measures and events. When combining tracks, keep simultaneous tempo and meter settings consistent because MIDI treats them as score-wide metadata.

## Parse errors

The parser reports the errors below with `ValueError`, including unsupported accidental spellings and pitches outside MIDI range `0..127`.

| Problem | Fix |
|---|---|
| Invalid header | Use prefixed fields such as `[m1t4/4s120]` or a legacy positional header |
| Wrong number of beats | Use exactly the meter numerator's number of beats separated by `\|`; commas subdivide each beat |
| Missing or nested measure brackets | Put each measure in its own `[ ... ]` group |
| Standalone `-` | Leave the position empty for a rest |
| `_` at the start of a score | Begin with a note, drum hit, or empty position |
| Old ramp or accent symbols | Use `<C4`, `>C4`, and `C4^` |
| Wrong modifier order, such as `C4-f` | Put velocity before the ending: `C4f-` |
| Unfinished or mismatched ramp | Suffix the opening marker after a later event with a target velocity, such as `F4f<` |
| Conflicting tempo or meter inside a parallel group | Put shared timing settings in an outer header |
| Changed number of parallel voices | Keep each voice's position; use `[]` for silent voices |
| Overlapping pitches on the same channel in different voices | Assign separate channels with voice headers |
| Deeper nesting or mixed plain measures and parallel groups | Use consecutive groups containing two or more measures |
| Values outside the accepted ranges | Check the [header](#score-header) and [dynamics](#dynamics-and-articulation) tables |

See [main.py](main.py) for the parser implementation.
