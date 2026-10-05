# XDM examples

These scores replace the former Python examples. Each `.xdm` file contains
the complete music, including simultaneous voices. From the repository root:

```sh
xdmgen genmidi/examples/HipHop.xdm --validate
xdmgen genmidi/examples/Cinematic2.xdm -o cinematic.mid
xdmgen genmidi/examples/JustForYou.xdm -o just-for-you.mid
```

| File | Measures | Voices |
|---|---:|---:|
| `Cinematic2.xdm` | 20 | 6 |
| `CinematicBoombastic.xdm` | 16 | 6 |
| `HipHop.xdm` | 8 | 5 |
| `SimpleHipHopLoop.xdm` | 4 | 1 |
| `SimpleJazzShuffle.xdm` | 4 | 1 |
| `JustForYou.xdm` | 16 | 2 |

Inherited velocity and gate changes from the old notation are written as
explicit local modifiers to preserve their effect. `Cinematic2.xdm` changes
from 96 to 132 BPM at measure 17. `JustForYou.xdm` uses channels 1 and 2 for
the right and left hands, avoiding ambiguous overlapping pitches.

The current XDM headers do not represent the old Python scripts' MIDI track
names, key-signature metadata, or program changes. The notes already contain
their accidentals, so omitting key-signature metadata does not change pitches.
To reproduce the cinematic instrumentation, select these General MIDI sounds
in your player or DAW:

| Channel | Sound | MIDI program (zero-based) |
|---|---|---:|
| 1 | French Horn | 60 |
| 2 | String Ensemble 1 | 48 |
| 3 | Brass Section | 61 |
| 4 | String Ensemble 1 | 48 |
| 5 | Choir Aahs | 52 |
| 10 | Percussion | — |
