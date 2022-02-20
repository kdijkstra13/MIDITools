"""
This file is part of the MIDITools distribution (https://github.com/kdijkstra13/MIDITools).
Copyright (c) 2022 Klaas Dijkstra

This program is free software: you can redistribute it and/or modify  
it under the terms of the GNU General Public License as published by  
the Free Software Foundation, version 3.

This program is distributed in the hope that it will be useful, but 
WITHOUT ANY WARRANTY; without even the implied warranty of 
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU 
General Public License for more details.

You should have received a copy of the GNU General Public License 
along with this program. If not, see <http://www.gnu.org/licenses/>.


drClass' MIDI Trancoder
Adds note velocity for the KORG Volca FM
"""

import jack
import struct
import time
import sys
import signal

def close(code, frame):
    print("Terminating.")
    sys.exit(0)

use_fm = False

if "FM" in sys.argv:
    use_fm = True

client = jack.Client('VolcaFM')
inport = client.midi_inports.register("in")
outport = client.midi_outports.register("out")

# First 4 bits of status byte:
NOTEON = 0x9
NOTEOFF = 0x8
CC = 0xb0
VEL = 41

@client.set_process_callback
def process(frames):
    outport.clear_buffer()
    for offset, indata in inport.incoming_midi_events():
        if len(indata) == 3:
            status, pitch, vel = struct.unpack("3B", indata)
            if status >> 4 == NOTEON and use_fm:
                outport.write_midi_event(offset, (CC, VEL, vel))
                print("{} {} {} -> {} {} {}".format(status, pitch, vel, CC, VEL, vel))
            if status >> 4 in (NOTEON, NOTEOFF):
                outport.write_midi_event(offset, indata)

client.activate()
signal.signal(signal.SIGTERM, close)
signal.signal(signal.SIGHUP, close)
signal.signal(signal.SIGINT, close)

print("Started drClass' MIDI Transcoder.")
print("use_fm = {}".format(use_fm))
print("Press [CTRL^C] to Stop.")
while True:
    time.sleep(10)
