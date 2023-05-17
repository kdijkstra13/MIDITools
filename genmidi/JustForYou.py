import midiutil
from genmidi.main import create, add_notes

mf = create(num=4, den=4, sign=midiutil.FLATS, scale=midiutil.MAJOR)

add_notes(mf, 0, notes="[E5        |E, F, G   |E ,C       |         ]"
                       "[          |D, C      |Eb, Db     |C, Bb4   ]"
                       "[A         |A, Bb, C5 |G#4, A     |         ]"
                       "[Bb4       |A4, C5    |           |         ]"

                       "[E5        |E, F, G   |E ,C       |         ]"
                       "[          |D, C      |Eb, Db     |C, Bb4   ]"
                       "[A         |A, Bb, C5 |G#4, A     |G#, A    ]"
                       "[Bb4       |A4        |F          |         ]"
          )

Fmaj7 = "F3+A3+C4+E4"
Dm7 = "D3+F3+A3+C4"
Gm7 = "F3+G3+Bb3+D4"
Gm7b = "G3+Bb3+D4+F4"
C7 = "E3+G3+Bb3+C4"
C7a = "G3+Bb3+C4+E4"
Am7 = "G3+A3+C4+E4"
Fisdim = "F#3+A3+C4+Eb4"
F6 = "F3+A3+C4+D4"

add_notes(mf, 1, notes=f"[{Fmaj7}|{Fmaj7}|{Dm7}   |{Dm7}   ]"
                       f"[{Gm7}  |{Gm7}  |{C7}    |{C7}    ]"
                       f"[{Am7}  |{Am7}  |{Fisdim}|{Fisdim}]"
                       f"[{Gm7}  |{Gm7}  |{C7}    |{C7}    ]"
          
                       f"[{Fmaj7}|{Fmaj7}|{Dm7}   |{Dm7}   ]"
                       f"[{Gm7}  |{Gm7}  |{C7}    |{C7}    ]"
                       f"[{Am7}  |{Am7}  |{Fisdim}|{Fisdim}]"
                       f"[{Gm7b} |{C7a}  |{F6}    |        ]"
          )


with open("c:/projects/midi/Just for you.mid", 'wb') as f:
    mf.writeFile(f)
