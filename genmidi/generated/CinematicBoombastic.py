"""Cinematic 16-bar film-score cue for kdijkstra13/MIDITools/genmidi."""

import midiutil
from genmidi.main import create, add_notes

PERCUSSION = '[4/4,96,1][BD+CR@92,,,|,LT@54,,|BD@78,,,|,MT@58,,HT@64][BD@88,,,|,LT@58,,|BD@80,,MT@58,|HT@64,,MT@58,LT@54][BD+CR@94,,,|LT@56,,MT@60,|BD@82,,,|HT@66,,MT@60,LT@56][BD@92,,BD@74,|LT@58,MT@62,HT@66,|BD@84,,,|CR@88,HT@68,MT@62,LT@58][BD+CR@98,,BD@76,|LT@62,,MT@66,|BD@88,,BD@78,|HT@72,MT@66,LT@62,][BD@96,,BD@78,|LT@64,MT@68,HT@72,|BD@88,,,BD@76|CR@92,HT@74,MT@68,LT@64][BD+CR@100,,BD@80,|LT@66,MT@70,HT@74,|BD@90,,BD@82,|HT@76,MT@70,LT@66,][BD@98,BD@72,BD@80,|LT@66,MT@70,HT@76,|BD@92,,BD@82,BD@74|CR@96,HT@78,MT@72,LT@68][BD+CR@100,,BD@84,|LT@70,MT@74,HT@80,|BD@94,,BD@84,|HT@82,MT@76,LT@70,][BD@100,,BD@84,BD@76|LT@72,MT@76,HT@82,|BD@96,,BD@86,|CR@98,HT@84,MT@78,LT@72][BD+CR@100,,BD@86,|LT@74,MT@78,HT@84,|BD@98,BD@78,BD@88,|HT@86,MT@80,LT@74,][BD@100,BD@78,BD@88,|LT@74,MT@80,HT@86,|BD@100,,BD@90,BD@80|CR@100,HT@88,MT@82,LT@76][BD+CR@100,,BD@90,BD@82|LT@78,MT@84,HT@90,|BD@100,,BD@92,BD@84|HT@92,MT@86,LT@80,][BD@100,BD@82,BD@92,|LT@80,MT@86,HT@92,|BD@100,,BD@94,BD@84|CR@100,HT@94,MT@88,LT@82][BD+CR@100,BD@84,BD@94,|LT@82,MT@88,HT@94,|BD@100,BD@86,BD@96,|HT@96,MT@90,LT@84,CR@100][BD+CR@100,,,|CR@100,,,|BD@100,,,|BD+CR@100,,,]'
LOW_STRINGS = '[4/4,96,2][D2@82,A2|D2,A2|D2,A2|C2,A2][Bb1@82,F2|Bb1,F2|Bb1,F2|A1,F2][F2@84,C3|F2,C3|F2,C3|E2,C3][C2@84,G2|C2,G2|C2,G2|A1,G2][D2@88,A2|D2,A2|F2,A2|A2,F2][Bb1@88,F2|Bb1,F2|D2,F2|F2,D2][F2@90,C3|F2,C3|A2,C3|C3,A2][C2@90,G2|C2,G2|E2,G2|G2,E2][D2@94,A2|D2,A2|F2,A2|A2,D3][Bb1@94,F2|Bb1,F2|D2,F2|F2,Bb2][G1@94,D2|G1,D2|Bb1,D2|D2,G2][A1@96,E2|A1,E2|C#2,E2|E2,A2][D2@98,A2|D2,A2|F2,A2|A2,D3][Bb1@98,F2|Bb1,F2|D2,F2|F2,Bb2][C2@100,G2|C2,G2|E2,G2|G2,C3][D2@100,_|A1,_|D2,_|D1,_]'
BRASS = '[4/4,96,3][D3+F3+A3@66:94|_|_|_][Bb2+D3+F3@68:94|_|_|_][F3+A3+C4@70:94|_|_|_][C3+E3+G3@72:94|_|_|_][D3+F3+A3+D4@78:95|_|_|_][Bb2+D3+F3+Bb3@80:95|_|_|_][F3+A3+C4+F4@82:95|_|_|_][C3+E3+G3+C4@84:95|_|_|_][D3+F3+A3+D4@88:96|_|_|_][Bb2+D3+F3+Bb3@90:96|_|_|_][G2+Bb2+D3+G3@90:96|_|_|_][A2+C#3+E3+A3@94:96|_|_|_][D3+F3+A3+D4@98:97|_|_|_][Bb2+D3+F3+Bb3@100:97|_|_|_][C3+E3+G3+C4@100:97|_|_|_][D3+F3+A3+D4@100:100|_|_|_]'
HIGH_STRINGS = '[4/4,96,4][D4@56,F4|A4,F4|D4,F4|C4,F4][D4@58,F4|Bb4,F4|D4,F4|A3,F4][C4@58,F4|A4,F4|C5,A4|E4,A4][C4@60,E4|G4,E4|C5,G4|A4,G4][D4@64,F4|A4,D5|A4,F4|D5,A4][D4@66,F4|Bb4,D5|Bb4,F4|D5,Bb4][F4@68,A4|C5,F5|C5,A4|F5,C5][E4@70,G4|C5,E5|C5,G4|E5,C5][F4@72,A4|D5,F5|A4,D5|F5,A5][F4@74,Bb4|D5,F5|Bb4,D5|F5,Bb5][G4@76,Bb4|D5,G5|Bb4,D5|G5,Bb5][A4@78,C#5|E5,A5|C#5,E5|A5,C#6][D5@82,F5|A5,D6|A5,F5|D6,A5][D5@84,F5|Bb5,D6|Bb5,F5|D6,Bb5][E5@86,G5|C6,E6|G5,C6|E6,G6][D5@92,A5|D6,A5|F6,D6|D6,_]'
CHOIR = '[4/4,96,5][D3+F3+A3@46:100|_|_|_][Bb2+D3+F3@48:100|_|_|_][F3+A3+C4@50:100|_|_|_][C3+E3+G3@52:100|_|_|_][D3+F3+A3@56:100|_|_|_][Bb2+D3+F3@58:100|_|_|_][F3+A3+C4@60:100|_|_|_][C3+E3+G3@62:100|_|_|_][D3+F3+A3@68:100|_|_|_][Bb2+D3+F3@70:100|_|_|_][G2+Bb2+D3@72:100|_|_|_][A2+C#3+E3@76:100|_|_|_][D3+F3+A3+D4@82:100|_|_|_][Bb2+D3+F3+Bb3@84:100|_|_|_][C3+E3+G3+C4@88:100|_|_|_][D3+F3+A3+D4@98:100|_|_|_]'
HORN = '[4/4,96,1][D4@68|_|A4|_][F4@70|_|D4|_][C5@72|A4|F4|_][G4@70|E4|C4|_][D4@76|F4|A4|D5][Bb4@78|A4|F4|D4][F4@80|A4|C5|F5][E5@82|D5|C5|G4][A4@88|D5|F5|A5][Bb5@90|A5|F5|D5][G5@92|F5|D5|Bb4][E5@94|A5|C#6|A5][D5@98|F5|A5|D6][Bb5@100|D6|F6|D6][C6@100|G5|E5|G5][D6@100|_|A5|D6]'

mf = create(
    sign=midiutil.FLATS,
    scale=midiutil.MINOR,
    track_names=[
        "percussion",
        "low strings",
        "brass",
        "high strings",
        "choir",
        "french horn",
    ],
)

# MIDIUtil uses zero-based General MIDI program numbers.
# Positional args are used for compatibility: (tracknum, channel, time, program)
mf.addProgramChange(1, 1, 0, 48)  # String Ensemble 1
mf.addProgramChange(2, 2, 0, 61)  # Brass Section
mf.addProgramChange(3, 3, 0, 48)  # String Ensemble 1
mf.addProgramChange(4, 4, 0, 52)  # Choir Aahs
mf.addProgramChange(5, 0, 0, 60)  # French Horn

add_notes(mf, 0, PERCUSSION)
add_notes(mf, 1, LOW_STRINGS)
add_notes(mf, 2, BRASS)
add_notes(mf, 3, HIGH_STRINGS)
add_notes(mf, 4, CHOIR)
add_notes(mf, 5, HORN)

with open("cinematic_boombastic.mid", "wb") as f:
    mf.writeFile(f)
