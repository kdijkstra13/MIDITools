# DrC's MML Language Reference

Xala Delta's MML is the compact music notation used by `genmidi/main.py` in the MIDITools project. It turns a text score into MIDI notes that can be used with tools such as Synthesia.

Source implementation: <https://github.com/kdijkstra13/MIDITools/blob/main/genmidi/main.py>

## 1. Learn the basic shape first

A simple two-measure melody in 4/4 can look like this:

```text
[C4|D|E|F][G|A|B|C5]
```

Read it like this:

```text
[ C4 | D | E | F ] [ G | A | B | C5 ]
  1    2   3   4     1   2   3   4
```

The important separators are:

| Syntax | Meaning |
|---|---|
| `[ ... ]` | Groups beats into a measure for readability |
| `|` | Moves to the next beat |
| `,` | Splits one beat into equal subdivisions |
| `+` | Plays notes at the same time as a chord |
| `X` | Rest / silence |
| blank beat | Extends the previously played note or chord |

A useful mental model is:

```text
[ beat | beat | beat | beat ]
```

For a 4/4 score, putting four beat fields inside each bracket is the natural layout.

---

## 2. Notes

Supported note names are:

```text
C  C#  Db  D  D#  Eb  E  F  F#  Gb  G  G#  Ab  A  A#  Bb  B
```

Notes must use uppercase letters. Accidentals use `#` for sharp or lowercase `b` for flat.

Examples:

```text
C4
F#4
Bb3
Eb5
```

### Octaves

An octave is a single digit written directly after the note:

```text
C4
A3
F#5
Bb2
```

The parser starts in octave **4**. Once an octave is written, that octave carries forward until another note changes it.

```text
[C4|D|E|F][G|A|B|C5]
```

Here `D`, `E`, `F`, `G`, `A`, and `B` all use octave 4. After `C5`, later notes without an octave use octave 5.

This also works inside chords:

```text
C4+E+G
```

which means `C4 + E4 + G4`.

If an octave changes inside a chord, it carries forward from that point:

```text
C4+E5+G
```

means `C4 + E5 + G5`.

---

## 3. Beats and subdivisions

Each field separated by `|` occupies one beat.

```text
[C4|D4|E4|F4]
```

Each of those notes occupies one full beat.

Use commas to divide a beat into equal parts.

### Two notes in a beat

```text
[C4,D4|E4,F4|G4,A4|B4,C5]
```

Each comma-separated note gets half a beat.

### Three notes in a beat

```text
[C4,D4,E4|F4,G4,A4|B4,C5,D5|E5,F5,G5]
```

Each note gets approximately one third of a beat.

### Four notes in a beat

```text
[C4,D4,E4,F4|G4,A4,B4,C5|D5,E5,F5,G5|A5,G5,F5,E5]
```

Each note gets one quarter of a beat.

The parser computes subdivision duration as:

```text
1 / number_of_comma_separated_slots
```

and rounds it to two decimal places. That means triplets are stored as `0.33` beats each rather than an exact `1/3`.

---

## 4. Chords

Use `+` to play notes simultaneously.

```text
C4+E4+G4
```

A chord occupies the same duration as a single note in the same position.

```text
[C4+E4+G4|F4+A4+C5|G4+B4+D5|C4+E4+G4]
```

Chords and subdivisions can be combined:

```text
[C4+E4+G4,D4+F4+A4|E4+G4+B4,F4+A4+C5|G4|C4+E4+G4]
```

Modifiers such as dynamics and articulation apply to the **whole chord**.

---

## 5. Rests

Use `X` for a rest.

```text
[C4|X|E4|X]
```

A rest consumes time but does not create a MIDI note.

A rest does **not** reset the current octave.

```text
[C5|X|D]
```

The final `D` is `D5`.

---

## 6. Holding / extending notes

A completely empty beat extends the previously played note or chord by one beat.

```text
[C4| | |G4]
```

This starts `C4` on beat 1 and holds it through beats 2 and 3. `G4` starts on beat 4.

The same works for a chord:

```text
[C4+E4+G4| | |F4+A4+C5]
```

All notes of the previous chord are extended together.

A field containing only spaces or dots is also considered empty by the parser:

```text
[C4|.| |G4]
```

For predictable ties, prefer a genuinely blank beat field such as `| |`.

### Caution: empty comma slots use legacy behavior

An empty subdivision such as this:

```text
[C4,|D4]
```

or this:

```text
[,C4|D4]
```

triggers the parser's legacy "extend previous note" logic. In the current implementation, the amount added is `1 / subdivision_duration`, which can be much longer than one subdivision. For example, in a two-slot beat the extension is **2 beats**, not `0.5` beat.

Because this is surprising, use empty **whole beat** fields for ordinary ties unless you specifically need the legacy behavior.

---

## 7. Dynamics / velocity

Velocity is written with `@` after a note or chord.

You can use traditional dynamic names:

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
C4@p
C4@mf
C4+E4+G4@f
```

You can also give a numeric value from `0` through `100`:

```text
C4@42
C4@73
C4+E4+G4@90
```

Dynamics are **persistent**. Once set, they remain active until another explicit velocity is encountered.

```text
[C4@p|D4|E4@mf|F4|G4@f|A4]
```

This means:

- `C4`, `D4` use `p`
- `E4`, `F4` use `mf`
- `G4`, `A4` use `f`

The default velocity is chosen so that it maps to MIDI velocity 100, matching the original implementation.

---

## 8. Articulation and gate length

Articulation changes the percentage of the written note duration that actually sounds.

| Suffix | Name | Gate |
|---|---|---:|
| `'` | staccatissimo | 25% |
| `.` | staccato | 50% |
| `-` | tenuto | 95% |
| `~` | legato | 100% |

Examples:

```text
C4'
D4.
E4-
F4~
```

Articulation settings are **persistent**.

```text
[C4.|D4|E4-|F4|G4~|A4]
```

Here:

- `C4` and `D4` use staccato
- `E4` and `F4` use tenuto
- `G4` and `A4` use legato

### Custom gate percentage

Instead of an articulation symbol, specify an exact gate percentage using `:0..100`.

```text
C4:60
C4+E4+G4:80
```

A gate of `60` means the MIDI note sounds for 60% of its notated duration.

Custom gate values are also persistent.

```text
[C4:70|D4|E4|F4]
```

All four notes use a 70% gate unless another gate or articulation appears.

---

## 9. Combining dynamics and articulation

Velocity comes before the final articulation or gate suffix.

Valid examples:

```text
C4@mf.
C4@f-
C4@73:60
C4+E4+G4@ff~
```

Read these as:

```text
C4@mf.          = C4, mezzo-forte, staccato
C4@f-           = C4, forte, tenuto
C4@73:60        = C4, velocity 73%, gate 60%
C4+E4+G4@ff~    = chord, fortissimo, legato
```

A token can have one final gate-style modifier: an articulation symbol, a numeric `:gate`, or marcato `>`.

---

## 10. Marcato

Append `>` for a one-event marcato accent.

```text
C4>
C4+E4+G4>
C4@mf>
```

Marcato is different from the persistent articulation settings:

- it applies only to that one note or chord
- its gate is 70%
- its velocity is multiplied by 1.20, capped at 100%

Afterward, the score returns to the previously active velocity and gate settings.

Example:

```text
[C4@mf|D4>|E4|F4]
```

Only `D4` gets the marcato accent.

---

## 11. Crescendo and diminuendo

Use `/` before a note or chord to begin a crescendo.

Use `\` before a note or chord to begin a diminuendo.

The ramp ends at the next note/chord with an explicit `@dynamic` or `@number`.

### Crescendo

```text
[C4@p|/D4|E4|F4][G4|A4|B4|C5@f]
```

The crescendo begins on `D4` at the current `p` level and rises linearly until `C5@f`.

### Diminuendo

```text
[C5@ff|\B4|A4|G4][F4|E4|D4|C4@p]
```

The diminuendo begins on `B4` and falls linearly until `C4@p`.

### Ramp rules

- `/` must end at the same or a higher velocity.
- `\` must end at the same or a lower velocity.
- A ramp needs notes at at least two different time positions.
- A second ramp cannot start before the first one ends.
- An unfinished ramp raises an error.
- The target dynamic remains active after the ramp because explicit dynamics are persistent.

For clarity, set the starting dynamic before the ramp marker rather than putting a new `@dynamic` on the same token that starts the ramp.

### Backslash in Python strings

If you write diminuendo notation inside Python source, a raw string is the clearest option:

```python
notes = r"[C5@ff|\B4|A4|G4][F4|E4|D4|C4@p]"
```

---

## 12. Modifier order

The parser accepts an event in this general shape:

```text
[RAMP] NOTES [@VELOCITY] [ENDING]
```

where:

```text
RAMP      = / or \
NOTES     = NOTE or NOTE+NOTE+...
VELOCITY  = ppp, pp, p, mp, mf, f, ff, fff, or 0..100
ENDING    = ', ., -, ~, :0..100, or >
```

Examples:

```text
/C4
C4@mf
C4@73:60
C4+E4+G4@f-
C4>
```

Do not write the modifiers in a different order. For example, use:

```text
C4@f-
```

not:

```text
C4-@f
```

---

## 13. Compact grammar

This is a human-oriented approximation of the parser grammar:

```text
score       := measure measure ...
measure     := "[" beat ("|" beat)* "]"
beat        := empty | event ("," event)*
event       := [ramp] chord [velocity] [ending]
chord       := note ("+" note)*
note        := A-G ["#" | "b"] [octave] | "X"
octave      := one decimal digit
ramp        := "/" | "\\"
velocity    := "@" dynamic | "@" 0..100
dynamic     := ppp | pp | p | mp | mf | f | ff | fff
ending      := "'" | "." | "-" | "~" | ":" 0..100 | ">"
```

Whitespace around notes is ignored, so formatting a score for readability is encouraged.

---

## 14. Worked examples

### A scale

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
[C4,D4|E4|X|G4,A4][B4|X|A4,G4|C5]
```

### Held chord

```text
[C4+E4+G4| | |F4+A4+C5]
```

### Dynamics and articulation

```text
[C4@p.|D4|E4@mf-|F4][G4@f>|A4|B4~|C5]
```

### Crescendo into a final chord

```text
[C4@p|/D4,E4|F4|G4][A4|B4|C5|C5+E5+G5@ff-]
```

---

## 15. Using the MML from Python

The repository's example creates a two-track MIDI file and writes separate right- and left-hand parts.

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

right_hand = "[C4|D|E|F][G|A|B|C5]"
left_hand = "[C3+E3+G3| |F3+A3+C4| ][G3+B3+D4| |C3+E3+G3| ]"

add_notes(mf, 0, right_hand)
add_notes(mf, 1, left_hand)

with open("example.mid", "wb") as f:
    mf.writeFile(f)
```

Track `0` is named `right_hand` and track `1` is named `left_hand` by `create()`.

The optional `time=` argument to `add_notes()` offsets the whole score:

```python
add_notes(mf, 0, "[C4|D4|E4|F4]", time=8)
```

This starts the passage 8 MIDI beat units later.

---

## 16. Time signature and key signature notes

`create()` writes time-signature and key-signature metadata to both MIDI tracks, but the MML parser does not automatically reshape the text to match that metadata.

In particular:

- the parser does not enforce the number of beats inside `[ ... ]`
- every `|` field advances time by one beat regardless of the time-signature denominator
- accidentals in the key signature do not automatically alter note names; write `F#`, `Bb`, etc. explicitly when that pitch is intended
- `create()` currently writes a key signature with one accidental and uses `sign`/`scale` to choose its type and mode

For straightforward results, make the number of `|`-separated fields in each bracket match the rhythmic layout you intend.

---

## 17. What this dialect does not support

Do not assume features from other MML languages. This parser currently has no syntax for:

- `O4` octave commands
- `L4` default note-length commands
- `T120` tempo changes inside the score
- loop/repeat commands
- lowercase note letters
- traditional dotted-duration notation
- a dedicated tie character
- automatic key-signature accidentals

Use the syntax documented in this file instead.

---

## 18. Quick reference card

| Goal | Syntax | Example |
|---|---|---|
| Note | `NOTE[octave]` | `C4` |
| Sharp | `#` | `F#4` |
| Flat | `b` | `Bb3` |
| Rest | `X` | `X` |
| Next beat | `|` | `C4|D4` |
| Subdivide beat | `,` | `C4,D4` |
| Chord | `+` | `C4+E4+G4` |
| Hold previous event | empty beat | `C4| |G4` |
| Dynamic | `@name` | `C4@mf` |
| Numeric velocity | `@0..100` | `C4@73` |
| Staccatissimo | `'` | `C4'` |
| Staccato | `.` | `C4.` |
| Tenuto | `-` | `C4-` |
| Legato | `~` | `C4~` |
| Custom gate | `:0..100` | `C4:60` |
| Marcato | `>` | `C4>` |
| Crescendo start | `/` | `/C4` |
| Diminuendo start | `\` | `\C4` |

---

## 19. A good way to write readable scores

Space does not affect normal note parsing, so line up beats visually:

```python
melody = (
    "[C4@p      |D4,E4     |F4         |G4        ]"
    "[A4        |/B4       |C5,D5      |E5@f      ]"
    "[F5.       |G5        |A5>        |C6-        ]"
)
```

For larger arrangements, defining chord names as Python strings can make the MML easier to read:

```python
Cmaj = "C3+E3+G3"
Fmaj = "F3+A3+C4"
Gmaj = "G3+B3+D4"

left_hand = (
    f"[{Cmaj}|{Cmaj}|{Fmaj}|{Fmaj}]"
    f"[{Gmaj}|{Gmaj}|{Cmaj}|{Cmaj}]"
)
```

This is the same style used by the repository's `JustForYou.py` example.

---

## 20. Summary

If you remember only five rules, remember these:

1. Write measures as `[ ... ]` and beats as `|`-separated fields.
2. Use commas for equal subdivisions of one beat.
3. Use `+` for simultaneous chord notes and `X` for rests.
4. Octaves, dynamics, and articulation settings carry forward until changed.
5. Use `@` for dynamics, articulation/gate suffixes for note length, and `/` or `\` for dynamic ramps.

A compact example using most of the language is:

```text
[C4@p.|D4,E4|/F4|G4+A4+C5][A4|B4|C5@f>|C5+E5+G5-]
```

Once the separators are familiar, DrC's MML reads much like a small piano-roll score written as text.
