"""Generate an 8-bar hip-hop beat with kdijkstra13/MIDITools/genmidi.

Run from the MIDITools repository root after installing its midiutil dependency.
"""
import midiutil
from genmidi.main import create, add_notes

DRUMS = '[4/4,90,1][BD@96,,,BD@72|SD+CP@94,,BD@78,|BD@92,,,BD@70|SD+CP@96,,,BD@78][BD@96,,BD@72,|SD+CP@94,,,BD@70|BD@90,,,BD@76|SD+CP@96,,BD@68,BD@82][BD@96,,,BD@72|SD+CP@94,,BD@76,|BD@90,,BD@68,|SD+CP@96,,,BD@80][BD@98,,BD@74,|SD+CP@96,,,|BD@92,,BD@72,BD@66|SD+CP@98,,LT@65,MT@72][BD@96,,,BD@70|SD+CP@94,,BD@78,|BD@94,,,BD@72|SD+CP@96,,BD@68,][BD@98,,BD@74,|SD+CP@95,,,BD@70|BD@92,,,BD@76|SD+CP@98,,,BD@82][BD@96,,,BD@70|SD+CP@94,,BD@72,|BD@90,,BD@68,|SD+CP@96,,BD@76,][BD@98,,BD@74,|SD+CP@96,,,BD@70|BD@94,,BD@74,BD@68|SD+CP@100,LT@62,MT@70,HT@78]'
HATS = '[4/4,90,1][CH@58,CH@34,CH@50,CH@38|CH@60,CH@36,CH@52,CH@40|CH@58,CH@34,CH@50,CH@38|CH@62,CH@38,CH@54,CH@42][CH@58,CH@34,CH@50,CH@38|CH@60,CH@36,CH@52,CH@40|CH@58,CH@34,CH@50,CH@38|CH@62,CH@40,OH@56,CH@38][CH@56,CH@32,CH@48,CH@36|CH@60,CH@34,CH@52,CH@38|CH@56,CH@32,CH@50,CH@36|CH@62,CH@38,CH@54,CH@40][CH@58,CH@34,CH@50,CH@38|CH@62,CH@36,CH@54,CH@40|CH@58,CH@34,CH@50,CH@38|CH@62,CH@40,OH@64,OH@48][CH@58,CH@34,CH@50,CH@38|CH@60,CH@36,CH@52,CH@40|CH@58,CH@34,CH@50,CH@38|CH@62,CH@38,CH@54,CH@42][CH@60,CH@34,CH@52,CH@38|CH@62,CH@36,CH@54,CH@40|CH@58,CH@34,CH@50,CH@38|CH@64,CH@40,OH@58,CH@38][CH@56,CH@32,CH@48,CH@36|CH@60,CH@34,CH@52,CH@38|CH@58,CH@32,CH@50,CH@36|CH@62,CH@38,CH@54,CH@40][CH@60,CH@34,CH@52,CH@38|CH@62,CH@36,CH@54,CH@40|CH@60,CH@36,CH@54,CH@42|CH@66,CH@42,OH@68,OH@50]'
BASS = '[4/4,90,2][E2@86:88,_|_,B1@72|D2@78,_|E2@90,_][C2@86,_|_,G1@72|B1@76,_|C2@88,_][G1@88,_|D2@74,_|F#2@80,|D2@76,_][F#1@86,_|A1@72,_|D2@82,|F#2@88,_][E2@88,_|_,B1@74|D2@80,_|G2@84,E2@90][C2@88,_|G1@72,_|B1@76,D2@78|E2@82,C2@88][A1@88,_|E2@74,_|G2@80,E2@74|A1@86,_][B1@90,_|F#2@76,_|A2@82,F#2@76|B1@92,_]'
RHODES = '[4/4,90,3][E3+G3+B3+D4+F#4@58:92|_|_|_][C3+E3+G3+B3+D4@56:92|_|_|_][G2+B2+D3+F#3@56:92|_|_|_][D3+F#3+A3+B3@58:92|_|_|_][E3+G3+B3+D4+F#4@60:92|_|_|_][C3+E3+G3+B3+D4@58:92|_|_|_][A2+C3+E3+G3@56:92|_|_|_][B2+D3+F#3+A3@58:92|_|_|_]'
LEAD = '[4/4,90,1][,B4@62:68|D5@68,E5@72|G5@76,F#5@66|E5@72,_][,G5@64|E5@70,D5@62|B4@66,D5@70|E5@74,_][B4@60,D5@66|G5@74,F#5@66|D5@64,B4@60|A4@58,_][F#5@70,E5@64|D5@70,B4@60|A4@58,B4@62|D5@70,_][,B4@64|D5@68,E5@74|G5@78,A5@72|B5@82,_][G5@72,E5@66|D5@62,E5@68|G5@74,B5@78|A5@70,_][E5@66,G5@72|A5@78,G5@70|E5@64,D5@60|C5@64,_][D5@66,F#5@72|A5@76,F#5@68|E5@64,D5@60|B4@58,]'

mf = create(
    sign=midiutil.SHARPS,
    scale=midiutil.MINOR,
    track_names=["drums", "hats", "bass", "rhodes", "lead"],
)

add_notes(mf, 0, DRUMS)
add_notes(mf, 1, HATS)
add_notes(mf, 2, BASS)
add_notes(mf, 3, RHODES)
add_notes(mf, 4, LEAD)

with open("hiphop_beat.mid", "wb") as f:
    mf.writeFile(f)
