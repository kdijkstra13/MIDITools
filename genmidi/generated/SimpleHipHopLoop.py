"""Simple one-track hip-hop drum loop for kdijkstra13/MIDITools/genmidi.

No melody.
Velocity is fixed at 70.
Gate is fixed at 80.
"""

import midiutil
from genmidi.main import create, add_notes

LOOP = ('[4/4,90,1,@70:80]'
        '[BD+CH,CH,CH,CH|SD+CH,CH,BD+CH,CH|BD+CH,CH,CH,CH|SD+CH,CH,BD+CH,CH]'
        '[BD+CH,CH,BD+CH,CH|SD+CH,CH,CH,CH|BD+CH,CH,CH,CH|SD+CH,CH,BD+CH,CH]'
        '[BD+CH,CH,CH,CH|SD+CH,CH,BD+CH,CH|BD+CH,CH,BD+CH,CH|SD+CH,CH,CH,CH]'
        '[BD+CH,CH,BD+CH,CH|SD+CH,CH,CH,CH|BD+CH,CH,CH,CH|SD+CH,CH,BD+CH,CH]')

mf = create(
    sign=midiutil.SHARPS,
    scale=midiutil.MINOR,
    track_names=["hip hop drums"],
)

add_notes(mf, 0, LOOP)

with open("simple_hiphop_loop.mid", "wb") as f:
    mf.writeFile(f)

print("Wrote simple_hiphop_loop.mid")
