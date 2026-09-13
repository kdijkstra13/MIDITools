# DrC's MIDI Markup Language (MML) Reference

DrC's MML is the compact text notation used by `genmidi/main.py` in MIDITools to create MIDI notes.

This is a project-specific MML dialect. It is **not** the common `O4 L4 CDEFG...` form of MML.

Source implementation: <https://github.com/kdijkstra13/MIDITools/blob/main/genmidi/main.py>

## Quick start

A simple two-measure melody:

```text
[C4|D|E|F][G|A|B|C5]
```

Read it as:

```text
[ C4 | D | E | F ][ G | A | B | C5 ]
   1    2   3   4     1   2   3   4
```

The most important symbols are:

| Syntax | Meaning |
|---|---|
| `[ ... ]` | Measure grouping |
| `|` | Next beat |
| `,` | Split a beat into equal subdivisions |
| `+` | Play notes together as a chord |
| `-` | Rest / silence when used by itself |
| `BD`, `SD`, `CH`, etc. | Two-letter drum/percussion names |
| `_` | Carry/hold the complete previous event, including drums |
| `p`, `mf`, `f`, etc. | Named velocity/dynamic |
| `@0..100` | Numeric velocity percentage |
| `:0..100` | Sounding-duration/gate percentage |
| `'`, `.`, `-`, `~` | Articulation/gate presets |
| `>` | One-note marcato |
| `/` | Start crescendo |
| `\` | Start diminuendo |

A compact example using several features:

```text
[C4p.|D4,E4|/F4|G4+A4+C5][A4|B4|C5f>|C5+E5+G5-]
```

---

## 1. Notes

`add_notes()` accepts both melodic notes and two-letter drum names. Melodic pitches are:

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

### Octaves

Write a single octave digit directly after a note:

```text
C4
A3
F#5
Bb2
```

The parser starts in octave **4**. An explicitly written octave becomes the current octave and carries forward to later notes that omit it.

```text
[C4|D|E|F][G|A|B|C5]
```

Here `D` through `B` are in octave 4. After `C5`, later notes without an octave are in octave 5.

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

## 2. Beats, measures, and subdivisions

A field separated by `|` is one beat:

```text
[C4|D4|E4|F4]
```

Each note above occupies one beat.

Use commas to divide one beat into equal slots.

Two notes per beat:

```text
[C4,D4|E4,F4|G4,A4|B4,C5]
```

Each note gets `1/2` beat.

Three notes per beat:

```text
[C4,D4,E4|F4,G4,A4]
```

Each note gets approximately `1/3` beat.

Four notes per beat:

```text
[C4,D4,E4,F4|G4,A4,B4,C5]
```

Each note gets `1/4` beat.

Internally, subdivision duration is calculated as:

```text
1 / number_of_comma_separated_slots
```

and rounded to two decimal places. For example, triplet slots are stored as `0.33` beats.

### Measures are mainly grouping

The parser does not enforce a particular number of beats inside `[ ... ]`. For conventional 4/4 notation, four `|`-separated fields per measure are natural:

```text
[C4|D4|E4|F4]
```

Adjacent measures are normally written directly next to each other:

```text
[C4|D4|E4|F4][G4|A4|B4|C5]
```

---

## 3. Chords

Use `+` to play several notes or drum hits at the same time:

```text
C4+E4+G4
```

A chord takes the same rhythmic slot as a single note. Drum hits can be combined with each other or with melodic notes.

```text
[C4+E4+G4|F4+A4+C5|G4+B4+D5|C4+E4+G4]
[BD+CH|CH|SD+CH|CH]
```

Chords and subdivisions can be combined:

```text
[C4+E4+G4,D4+F4+A4|E4+G4+B4,F4+A4+C5|G4|C4+E4+G4]
```

Velocity, gate, articulation, and marcato modifiers apply to the **whole chord**:

```text
C4+E4+G4f
C4+E4+G4@72
C4+E4+G4mf:80
```

---

## 4. Rests

Use a standalone `-` for a rest:

```text
[C4|-|E4|-]
```

`-` has two context-dependent meanings: by itself it is a rest, while after a note or chord it remains the tenuto articulation. For example, `-` is silence but `C4-` is a tenuto C4.

A rest consumes its rhythmic slot but does not create a MIDI note.

A rest does not reset the current octave:

```text
[C5|-|D]
```

The final `D` is `D5`.

---

## 5. Drums and percussion

Drums are written with **two uppercase letters** and are handled by the same `add_notes()` function as melodic notes. No separate drum function or drum syntax is needed.

`add_notes()` writes ordinary melodic notes on MIDI channel 1 and drum names on the General MIDI percussion channel, MIDI channel 10. (`midiutil` numbers channels from zero, so the implementation uses `channel=9` for drums.)

Supported drum names are:

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

The rhythm syntax is unchanged. `|` still means the next beat, commas still subdivide a beat, and `+` still means simultaneous events.

A simple four-on-the-floor style pattern:

```text
[BD+CH,CH,CH,CH|SD+CH,CH,CH,CH|BD+CH,CH,BD+CH,CH|SD+CH,CH,CH,OH]
```

The same modifiers used for notes also work on drums:

```text
SDf        # forte snare
BD@90      # exact 90% velocity
CHp        # piano closed hi-hat
OH:80      # 80% sounding duration/gate
SD>        # marcato/accented snare
```

Named dynamics still do **not** use `@`; `@` is only for numeric velocity.

Because melodic notes and drums share the same parser, they can even occur simultaneously:

```text
C4+BD
C4+E4+G4+CRf
```

Each melodic note is sent on channel 1; each drum hit is sent on channel 10.

### Holding drums and explicit silence

Use `_` to carry the complete previous event into the current rhythmic slot. This works identically for drums, melodic notes, and mixed chords.

```text
[BD,_,_,_|SD,_,_,_]
```

Each beat above is split into four sixteenth-note slots. `BD` starts on the first slot of beat 1 and each `_` extends it by one more slot, so it has a notated duration of one full beat. `SD` is held the same way on beat 2. Whether a drum module audibly responds to the longer MIDI note depends on that instrument, but the MML duration is still extended.

Use `-` when you want an explicitly silent step:

```text
[BD,-,-,-|SD,-,-,-]
```

Here `BD` and `SD` each occupy only their first sixteenth-note slot; every standalone `-` consumes one silent subdivision.

Mixed melodic/percussion events are held together:

```text
[C4+BD,_|D4]
```

The `_` in the second half of beat 1 extends both `C4` and `BD` by half a beat.

---

## 6. Holding and extending events

Use `_` to extend the complete previously started event by the current beat or subdivision. This applies to melodic notes, drums, and mixed chords:

```text
[C4|_|_|G4]
```

`C4` starts on beat 1 and continues through beats 2 and 3. `G4` starts on beat 4.

The same works for chords and drum events:

```text
[C4+E4+G4|_|_|F4+A4+C5]
[BD+CH|_|SD+CH|_]
```

If you want silence instead of a hold, write `-` explicitly:

```text
[BD|-|SD|-]
```

### Carrying through comma subdivisions

A `_` subdivision occupies exactly one subdivision and extends the complete previous event by exactly that slot's duration.

```text
[C4,_|D4]
```

The first beat has two half-beat slots. `C4` starts in the first slot and `_` extends it by another half beat, so `C4` lasts one complete beat. A drum event behaves the same way.

```text
[BD,_|SD]
```

Here `BD` also lasts one complete beat. To make the second half-beat silent instead, write `[BD,-|SD]`.

A carry must have a previous event. A leading `_` is therefore invalid:

```text
[_,C4|D4]   # invalid
```

Empty beats and empty subdivisions are also invalid. Write `_` for carry or `-` for rest explicitly. This catches accidental doubled separators such as `||` or `,,` instead of silently changing the rhythm.

A bare `.` is **not** a hold marker. `.` is only valid as an articulation suffix such as `C4.`.

---

## 7. Dynamics and velocity

Velocity can be written in two ways:

1. a named musical dynamic, written directly after the note/chord;
2. a numeric percentage, written with `@`.

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
```

Named dynamics are written directly after the note or chord. The `@` marker is reserved for numeric velocity percentages only.

### Numeric velocity: use `@`

Use `@0..100` when you want an exact velocity percentage:

```text
C4@42
C4@73
C4+E4+G4@90
```

`@` is therefore the marker for a **numeric velocity percentage**.

Both named and numeric velocities are persistent. Once changed, the current velocity remains active until another explicit velocity appears.

```text
[C4p|D4|E4mf|F4|G4@73|A4|B4f|C5]
```

This means:

- `C4`, `D4` use `p`;
- `E4`, `F4` use `mf`;
- `G4`, `A4` use numeric velocity 73%;
- `B4`, `C5` use `f`.

The default internal velocity is 79%, which maps to MIDI velocity 100.

---

## 8. Articulation and sounding duration

Articulation changes how much of the written rhythmic duration actually sounds.

| Suffix | Name | Gate |
|---|---|---:|
| `'` | staccatissimo | 25% |
| `.` | staccato | 50% |
| `-` | tenuto when used as a suffix | 95% |
| `~` | legato | 100% |

Examples:

```text
C4'
D4.
E4-
F4~
```

Articulation/gate settings are persistent:

```text
[C4.|D4|E4-|F4|G4~|A4]
```

Here `C4` and `D4` use staccato; `E4` and `F4` use tenuto; `G4` and `A4` use legato.

### Exact gate/duration percentage

Use `:0..100` for an exact sounding-duration percentage:

```text
C4:60
C4+E4+G4:80
```

`C4:60` means that the MIDI note sounds for 60% of its written rhythmic duration.

Custom gate values are also persistent:

```text
[C4:70|D4|E4|F4]
```

All four notes use a 70% gate unless another articulation or gate is specified.

This `:percentage` syntax is separate from velocity:

```text
C4@73:60
```

means:

- velocity = 73%;
- sounding duration/gate = 60%.

---

## 9. Combining velocity and duration modifiers

The general order is:

```text
NOTE-or-CHORD  VELOCITY  ENDING
```

Valid examples:

```text
C4mf.
C4f-
C4@73:60
C4mf:60
C4+E4+G4ff~
C4+E4+G4@85-
```

Read them as:

| Example | Meaning |
|---|---|
| `C4mf.` | C4, mezzo-forte, staccato |
| `C4f-` | C4, forte, tenuto |
| `C4@73:60` | C4, 73% velocity, 60% gate |
| `C4mf:60` | C4, mezzo-forte, 60% gate |
| `C4+E4+G4ff~` | chord, fortissimo, legato |

Do not reverse the modifier order. For example:

```text
C4f-      # valid
C4-f      # invalid
```

---

## 10. Marcato

Append `>` for a one-event marcato accent:

```text
C4>
C4+E4+G4>
C4mf>
C4@75>
```

Marcato:

- applies only to that one event;
- uses a 70% gate;
- multiplies its velocity by 1.20;
- caps velocity at 100%;
- does not replace the persistent velocity or gate setting afterward.

Example:

```text
[C4mf|D4>|E4|F4]
```

Only `D4` receives the marcato accent.

---

## 11. Crescendo and diminuendo

Use `/` before a note/chord to start a crescendo:

```text
/C4
```

Use `\` before a note/chord to start a diminuendo:

```text
\C4
```

A ramp ends at the next event with an explicit velocity. The target may be either a named dynamic or a numeric `@percentage`.

### Crescendo with named dynamics

```text
[C4p|/D4|E4|F4][G4|A4|B4|C5f]
```

The crescendo begins on `D4` at the current `p` level and rises to `f` at `C5`.

### Crescendo to an exact velocity

```text
[C4p|/D4|E4|F4][G4|A4|B4|C5@72]
```

### Diminuendo

```text
[C5ff|\B4|A4|G4][F4|E4|D4|C4p]
```

The diminuendo starts on `B4` and falls to `p` at the final `C4`.

Ramp rules:

- `/` must end at the same or a higher velocity;
- `\` must end at the same or a lower velocity;
- a ramp requires at least two different note positions;
- a second ramp cannot start before the first one ends;
- an unfinished ramp raises an error;
- the target velocity remains active after the ramp.

For the clearest behavior, set the starting velocity before the note carrying `/` or `\`.

### Backslash in Python strings

A raw string is convenient for diminuendo notation:

```python
notes = r"[C5ff|\B4|A4|G4][F4|E4|D4|C4p]"
```

---

## 12. Modifier grammar

A note/chord event has this general shape:

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
/C4
\C4
C4>
```

### Compact grammar

```text
score       := measure measure ...
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
```

---

## 13. Worked examples

### Scale

```text
[C4|D|E|F][G|A|B|C5]
```

### Eighth-note movement

```text
[C4,D|E,F|G,A|B,C5]
```

### Chord progression

```text
[C4+E4+G4|C4+E4+G4|F4+A4+C5|F4+A4+C5]
[G4+B4+D5|G4+B4+D5|C4+E4+G4|C4+E4+G4]
```

### Melody with rests

```text
[C4,D4|E4|-|G4,A4][B4|-|A4,G4|C5]
```

### Held chord

```text
[C4+E4+G4|_|_|F4+A4+C5]
```

### Named dynamics and articulation

```text
[C4p.|D4|E4mf-|F4][G4f>|A4|B4~|C5]
```

### Numeric velocity and exact gate

```text
[C4@35:50|D4|E4@65:95|F4][G4@80>|A4|B4:100|C5]
```

### Crescendo into a final chord

```text
[C4p|/D4,E4|F4|G4][A4|B4|C5|C5+E5+G5ff-]
```

### Drum pattern

```text
[BD+CH,CH,CH,CH|SD+CH,CH,CH,CH|BD+CH,CH,BD+CH,CH|SD+CH,CH,CH,OH]
```

### Melody and drums in one call

```text
[C4+BD|D4+CH|E4+SD|F4+CH]
```

---

## 14. Using MML from Python

```python
import midiutil
from genmidi.main import create, add_notes

mf = create(
    num=4,
    den=4,
    tempo=120,
    sign=midiutil.SHARPS,
    scale=midiutil.MAJOR,
)

right_hand = "[C4p|D|E|F][Gmf|A|B|C5f]"
left_hand = "[C3+E3+G3|_|F3+A3+C4|_][G3+B3+D4|_|C3+E3+G3|_]"

add_notes(mf, 0, right_hand)
add_notes(mf, 1, left_hand)

# add_notes() also accepts drums; they are emitted on MIDI channel 10.
drums = "[BD+CH,CH,CH,CH|SD+CH,CH,CH,OH]"
add_notes(mf, 1, drums)

with open("example.mid", "wb") as f:
    mf.writeFile(f)
```

The optional `time=` argument offsets an entire score:

```python
add_notes(mf, 0, "[C4|D4|E4|F4]", time=8)
```

---

## 15. Time signature and key signature behavior

`create()` writes time-signature and key-signature MIDI metadata, but MML rhythm and pitches are still explicit.

In particular:

- the parser does not enforce the number of beats in a measure;
- every `|` field advances by one beat;
- commas subdivide that beat equally;
- key-signature metadata does not automatically alter MML notes;
- write accidentals such as `F#` or `Bb` explicitly.
- 
---

## Quick reference card

| Goal                      | Syntax               | Example                    |
|---------------------------|----------------------|----------------------------|
| Note                      | `NOTE[octave]`       | `C4`                       |
| Sharp                     | `#`                  | `F#4`                      |
| Flat                      | `b`                  | `Bb3`                      |
| Rest                      | standalone `-`       | `C4`                        |-|D4` |
| Drum                      | two-letter drum code | `BD`                       |
| Drum chord                | `+`                  | `BD+CH`                    |
| Next beat                 | `\| `                | `C4\|D4` |
| Subdivide beat            | `,`                  | `C4,D4`                    |
| Chord                     | `+`                  | `C4+E4+G4`                 |
| Carry/hold previous event | `_`                  | `C4\|_\|G4` or `BD\|_\|SD` |
| Named dynamic             | `ppp..fff`           | `C4mf`                     |
| Numeric velocity          | `@0..100`            | `C4@73`                    |
| Staccatissimo             | `'`                  | `C4'`                      |
| Staccato                  | `.`                  | `C4.`                      |
| Tenuto                    | `-`                  | `C4-`                      |
| Legato                    | `~`                  | `C4~`                      |
| Exact gate/duration       | `:0..100`            | `C4:60`                    |
| Velocity + gate           | `@V:G`               | `C4@73:60`                 |
| Named dynamic + gate      | `dynamic:G`          | `C4mf:60`                  |
| Marcato                   | `>`                  | `C4>`                      |
| Crescendo start           | `/`                  | `/C4`                      |
| Diminuendo start          | `\`                  | `\C4`                      |

## Five rules to remember

1. Use `[ ... ]` for measures, `|` for beats, and commas for equal subdivisions.
2. Use `+` for simultaneous notes/drums, standalone `-` for rests, and two-letter names such as `BD`, `SD`, and `CH` for percussion.
3. Write named dynamics directly: `C4p`, `C4mf`, `C4ff`.
4. Use `@` only for numeric velocity percentages such as `C4@73`; use `:` for duration/gate percentages such as `C4:60`.
5. Use `_` to carry the previous event and standalone `-` for explicit silence; empty slots are invalid.
