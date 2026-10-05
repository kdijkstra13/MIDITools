# Xala Delta Music Markup Language (XDM)

Write music as text, then turn it into a MIDI file.

## Basic structure and notes

A score is a sequence of bracketed measures. Each measure contains beats
separated by `|`. In the default 4/4 meter, write four beats per measure:

```text
[@mf:~]
[C4|D4|E4|F4]
[G4|A4|B4|C5]
```

Each note has a name and an explicit octave: `C4`, `D4`, or `C5`.
C4 is middle C (MIDI pitch 60). One note in each position lasts one beat
in this example. Measures play in order.

The first bracket is a **header**. Here, `@mf` sets mezzo-forte velocity
and `:~` sets full sounding length. These defaults apply to every following
note until another header changes them. The default meter is 4/4 and the
default tempo is 120 BPM.

Use this common practice throughout a score:

- Write the octave on every melodic note, including every chord member.
- Set velocity and sounding length in headers instead of repeating them on notes.
- Use `^` for an occasional accent, such as `E4^`.
- Choose named dynamics and articulation symbols, or percentages, and keep
  that choice consistent within an example or passage.

The examples below introduce one feature at a time. Most use named dynamics
and articulation symbols; exact percentages appear in their own section.

## Save and play a score

Install from the repository root:

```sh
python -m pip install .
```

Save the basic score above as UTF-8 text in `example.xdm`, then generate MIDI:

```sh
xdmgen example.xdm
```

This writes `example.mid`. Open it in your MIDI player or DAW.
To choose an output file or check the score without writing MIDI:

```sh
xdmgen example.xdm -o performance.mid
xdmgen example.xdm --validate
```

You can also supply the score directly:

```sh
xdmgen --code '[@mf:~][C4|D4|E4|F4]' -o melody.mid
```

Quote literal text so the shell preserves its brackets and symbols.
File input and `--code` are mutually exclusive. Literal MIDI generation
requires `-o`; `--validate` and `-o` cannot be combined. Input and output
must differ. Validation prints `Valid XDM` and exits with status 0; invalid
XDM or I/O errors exit with status 1, and incorrect CLI arguments with 2.

You can also run `python -m genmidi.cli` from the repository root.
Validation works without MIDIUtil; generating MIDI requires it.

## Rhythm and silence

### Shorter notes

Commas divide a beat into equal positions. Two positions make two half-beat
notes; three positions make three equal notes:

```text
[@mf:~]
[C4,D4|E4|F4,G4|A4]
```

Only beats 1 and 3 are divided here. The measure still has four beats.

### Rests

Leave a beat or position empty for silence:

```text
[@mf:~]
[C4||E4|]
```

Beats 2 and 4 are rests. Within a divided beat, `C4,` means a note followed
by silence, and `,C4` means silence followed by a note.
`[]` is a whole silent measure in the current meter.

### Longer notes

Use `_` to continue the previous note without playing it again:

```text
[@mf:~]
[C4|_|E4|_]
```

Each note lasts two beats. A hold can continue across a measure boundary.
It extends the entire previous event, including all chord members or drum
hits. After a rest it continues silence; at the start of a voice it is invalid.

### Sounding length

The header's gate controls how much of a note's written duration sounds.
It does not move the next note. For a short, detached passage:

```text
[@mf:']
[C4|D4|E4|F4]
```

The staccatissimo setting `:'` sounds each note for one quarter of its
position. Full gate `:~` sounds the whole position. Holds extend the written
duration first, then the gate applies to that total.

## Notes and chords

Use uppercase note names. Sharps and flats come before the octave:

```text
[@mf:~]
[C4|F#4|Bb4|C5]
```

Supported pitch spellings are C, C#/Db, D, D#/Eb, E, F, F#/Gb, G, G#/Ab,
A, A#/Bb, and B. Alternatives such as Cb and E# are not implemented.
Octaves are single digits, and pitches must remain in MIDI range 0..127
(C0 through G9).

Join notes with `+` to play a chord in one position:

```text
[@mf:~]
[C4+E4+G4|_|C4+F4+A4|_]
```

Each chord lasts two beats. Every member uses the header's velocity and gate.

## Score header

Headers use prefixed fields in any order. Commas and spaces are optional.
Start with just the settings you need:

```text
[s96@mf:~]
[C4|D4|E4|F4]
```

This changes the tempo to 96 BPM. Unspecified settings use their defaults,
or inherit their previous values when a header appears later in the score.

| Prefix | Meaning | Initial default | Example |
|---|---|---|---|
| `t` | Meter: positive numerator / power-of-two denominator | `4/4` | `t3/4` |
| `s` | Tempo in quarter-note BPM, positive integer | `120` | `s96` |
| `m` | Melody MIDI channel, `1..16` | `1` | `m2` |
| `i` | Melody instrument, MIDI program `0..127` | Unspecified | `i60` |
| `b` | Beats MIDI channel, `1..16` | `10` | `b10` |
| `@` | Velocity: named dynamic or `0..100` percent | `79` percent | `@mf` |
| `:` | Gate: articulation symbol or `0..100` percent | Full length | `:~` |

Each field may occur only once in a header. Include at least one field and
follow the header with a measure or parallel group. Headers consume no time.
Positional fields and bare dynamics in headers are not supported; use `@mf`.

### Meter

A measure must have exactly the numerator's number of beats, including rests.
In 3/4, write three beats:

```text
[t3/4@mf:~]
[C4|D4|E4]
```

Each beat's duration comes from the denominator: a quarter note for /4,
an eighth note for /8, and a half note for /2. A 6/8 measure therefore has
six eighth-note beats and lasts three MIDI quarter-note units. Commas divide
these beats equally.

### Instrument

Use `i60` to select MIDI program 60 on the melody channel:

```text
[i60@mf:~]
[C4|D4|E4|F4]
```

Instrument numbers are zero-based. A new instrument setting sends a program
change at the start of its measure. Without an instrument setting, the score
leaves the instrument choice to your player.

### Changes between measures

Put a new header before a passage to change its defaults:

```text
[@p:~]
[C4|D4|E4|F4]
[@f]
[G4|A4|B4|C5]
```

The second measure is louder; its gate stays at full length. Omitted fields
retain their previous values. Prefer these passage-level changes to placing
a velocity and gate on every note.

## Dynamics and articulation

### Occasional accents

For a single emphasized note, use `^`:

```text
[@mf:~]
[C4|D4|E4^|F4]
```

Only E4 receives the marcato accent: its velocity increases by 20%, capped at
100%, and its gate becomes 70%. F4 returns to the header defaults.
Use this for occasional accents; it is not a general replacement for an
exact velocity or gate adjustment.

### Named settings

Use named dynamics in headers to set a passage's velocity:

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

Use articulation symbols after the header's colon to set sounding length:

| Symbol | Meaning | Gate (%) | Header |
|---|---|---:|---|
| `'` | Staccatissimo | 25 | `[@mf:']` |
| `.` | Staccato | 50 | `[@mf:.]` |
| `-` | Tenuto | 95 | `[@mf:-]` |
| `~` | Full gate | 100 | `[@mf:~]` |

Full gate does not add overlap or send a legato controller message.

### Exact percentages

When exact values matter, use percentages consistently for both settings:

```text
[@70:80]
[C4|D4|E4|F4]
```

Every note has 70% velocity and sounds for 80% of its written duration.
Readable velocity percentages are converted to MIDI's 0..127 scale.

### Local exceptions

Use note-level settings only when a particular event needs an exception.
For example, shorten just E4:

```text
[@mf:~]
[C4|D4|E4'|F4]
```

F4 returns to the header defaults. A note can also take a local dynamic,
such as `E4p` or `E4@p`. In percentage notation, `E4@50` sets its velocity
and `E4:60` its gate. Local modifiers apply to the complete event, including
chord members and holds, and do not change subsequent defaults.

Modifier order is note/chord, velocity, then articulation or gate.
Choose one ending: a bare articulation, a colon gate/articulation, or `^`.
Endings cannot be stacked; `C4:60.`, `C4:.^`, and `C4:^` are invalid.
Keep a note and its modifiers together. Standalone modifiers and modifiers
on holds or empty positions are invalid.

## Drum codes

Drum codes replace melodic notes and use the beats channel (10 by default).
Start with a simple bass drum and snare pattern:

```text
[@mf:~]
[BD|SD|BD|SD]
```

Drum codes do not take octaves. They support the same rhythm, holds, and
occasional accents as notes. Join hits with `+` when they should play together:

```text
[@mf:~]
[BD+CH|SD+CH|BD+CH|SD+CH]
```

Melodic notes can also be joined with drums, such as `C4+BD`.
Channels use human numbering 1..16; channel 10 is the standard General MIDI
percussion channel. Set `b` in a header for other routing.

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

## Parallel voices

Wrap two or more measures in an outer bracket to play them simultaneously.
Give melodic voices separate channels with `m`:

```text
[@mf:~]
[[m1][C4|D4|E4|F4][m2][C3|D3|E3|F3]]
```

Each inner measure is one voice. A header inside the group applies only to
the following voice. Instruments and expression defaults can differ by voice.
Tempo and meter are shared and must be changed with an outer header.

Consecutive groups play in order, retaining each voice's position and settings:

```text
[@mf:~]
[[m1][C4|D4|E4|F4][m2][C3|D3|E3|F3]]
[[G4|A4|B4|C5][G3|A3|B3|C4]]
```

Use `[]` to keep a voice's place when it is silent. Every group must keep the
same number of voices. Holds and ramps continue independently within each
voice. An outer header updates all voices; omitted settings retain each
voice's existing values.

Deeper nesting and mixing plain measures with parallel groups are unsupported.
Overlapping pitches in different voices on the same channel are rejected;
use separate channels when independent note endings are needed. All voices
are validated before MIDI events are written.

## Crescendo and diminuendo

Use ramps when velocity should change gradually within a passage.
Prefix a note with `<` to start a crescendo, then put the same marker after
a later note with the target dynamic:

```text
[@p:~]
[<C4|D4|E4|F4f<]
```

The passage grows from the header's piano level to forte. For a diminuendo,
use `>` at both ends:

```text
[@f:~]
[>G4|F4|E4|C4p>]
```

Velocity is interpolated over musical time. A crescendo must end at an equal
or higher velocity; a diminuendo at an equal or lower one. The opening note
may supply its own starting dynamic. A closing marker needs a target velocity
and comes after all note modifiers.

Close a ramp before starting another. Missing, mismatched, or nested markers
are errors. Ramps can cross measures in the same voice. Local velocities
inside a ramp override only their event; following notes continue the ramp.
After the ramp closes, unmarked notes resume the header defaults. Marcato's
boost is applied after interpolation.

## More examples

Complete scores are in the [examples directory](examples/README.md), including
[JustForYou.xdm](examples/JustForYou.xdm). These larger arrangements combine
the features introduced above.

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
add_notes(midi, 0, "[t3/4s96m1][C4|D4|E4]", time=8, debug=True)
```

Parsing is quiet by default. `debug=True` prints the parsed measures and events. When combining tracks, keep simultaneous tempo and meter settings consistent because MIDI treats them as score-wide metadata.

## Parse errors

The parser reports the errors below with `ValueError`, including unsupported accidental spellings and pitches outside MIDI range `0..127`.

| Problem | Fix |
|---|---|
| Invalid header | Use prefixed fields such as `[m1t4/4s120]` |
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
