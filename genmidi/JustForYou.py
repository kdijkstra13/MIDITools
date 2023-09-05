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


drClass' MIDI Markup Language (MML)

1) Example
"""

import midiutil
from genmidi.main import create, add_notes

mf = create(num=4, den=4, tempo=60, sign=midiutil.FLATS, scale=midiutil.MAJOR)

add_notes(mf, 0, notes="[E5        |E, F, G   |E ,C       |         ]"
                       "[          |D, C      |Eb, Db     |C, Bb4   ]"
                       "[A         |A, Bb, C5 |G#4, A     |         ]"
                       "[Bb4       |A4, C5    |           |         ]"

                       "[E5        |E, F, G   |E ,C       |         ]"
                       "[          |D, C      |Eb, Db     |C, Bb4   ]"
                       "[A         |A, Bb, C5 |G#4, A     |G#, A    ]"
                       "[Bb4       |A4        |F          |         ]"

                       "[X         |G5, Gb    |F, E       |C, C#    ]"
                       "[D, F4     | , F      |           |         ]"
                       "[X         |G5, Gb5   |F, E       |C, C#    ]"
                       "[D         |          |           |         ]"

                       "[X         |D5, C     |F, Eb      |D, C     ]"
                       "[Bb4       |Bb, A     |C5,Bb4     |F4, G4   ]"
                       "[A         |          |           | , A     ]"
                       "[Bb        |A, C5     |           |         ]"
          )

Am7 = "G3+A3+C4+E4"
Am7a = "E3+G3+A3+C4"
Adim = "Eb3+Gb3+A3+C4"

Bes = "D3+F3+Bb3"
Besmaj7 = "D3+F3+A3"
Bes7 = "D3+F3+Ab3"
Bdim = "D3+F3+Ab3+B3"

C7 = "E3+G3+Bb3+C4"
C7a = "G3+Bb3+C4+E4"
Cm7 = "Eb3+G3+Bb3+C4"

Dm7 = "D3+F3+A3+C4"
Dm7a = "D3+F3+C4"
D7 = "D3+F#3+A3+C4"

Es7 = "Eb3+G3+Bb3+Db4"

Fmaj7 = "F3+A3+C4+E4"
F7 = "Eb3+F3+A3+C4"
Fisdim = "F#3+A3+C4+Eb4"
F6 = "F3+A3+C4+D4"

Gm7 = "F3+G3+Bb3+D4"
Gm7b = "G3+Bb3+D4+F4"
Gb7m5 = "F3+G3+Bb3+Db4"

add_notes(mf, 1, notes=f"[{Fmaj7}|{Fmaj7}|{Dm7}   |{Dm7}   ]"
                       f"[{Gm7}  |{Gm7}  |{C7}    |{C7}    ]"
                       f"[{Am7}  |{Am7}  |{Fisdim}|{Fisdim}]"
                       f"[{Gm7}  |{Gm7}  |{C7}    |{C7}    ]"
          
                       f"[{Fmaj7}|{Fmaj7}|{Dm7}   |{Dm7}   ]"
                       f"[{Gm7}  |{Gm7}  |{C7}    |{C7}    ]"
                       f"[{Am7}  |{Am7}  |{Fisdim}|{Fisdim}]"
                       f"[{Gm7b} |{C7a}  |{F6}    |        ]"

                       f"[{Cm7}  |{Cm7}     |{F7}   |{F7}   ]"
                       f"[{Dm7a} |{Dm7a}    |{Bes}  |{Bes}  ]"
                       f"[{Cm7}  |{Cm7}     |{F7}   |{F7}   ]"
                       f"[{Bes}  |{Besmaj7} |{Bes7} |{Bdim} ]"

                       f"[{Am7a} |{Am7a}    |{D7}   |{D7}   ]"
                       f"[{Gm7}  |{Gm7}     |{Es7}  |{Es7}  ]"
                       f"[{Am7a} |{Am7a}    |{Adim} |{Adim} ]"
                       f"[{Gb7m5}|{Gb7m5}   |{C7}   |{C7}   ]"
          )

with open("c:/projects/midi/Just for you.mid", 'wb') as f:
    mf.writeFile(f)
