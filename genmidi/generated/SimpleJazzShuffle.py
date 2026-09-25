"""Simple one-track jazz shuffle for kdijkstra13/MIDITools/genmidi.

One drum track only.
No melody.
Velocity fixed at 68.
Gate fixed at 80.
"""

import midiutil
from genmidi.main import create, add_notes

LOOP = ('[4/4,120,1,@68:80]'
        '[BD+RD,,RD|,SS+RD,|BD+RD,,RD|,SS+RD,]'
        '[BD+RD,,RD|,SS+RD,|BD+RD,,RD|,SS+RD,]'
        '[BD+RD,,RD|,SS+RD,|BD+RD,,RD|,SS+RD,]'
        '[BD+RD,,RD|,SS+RD,|BD+RD,,RD|,SS+RD,]')

mf = create(
    sign=midiutil.SHARPS,
    scale=midiutil.MINOR,
    track_names=["jazz shuffle drums"],
)

add_notes(mf, 0, LOOP)

with open("simple_jazz_shuffle.mid", "wb") as f:
    mf.writeFile(f)
