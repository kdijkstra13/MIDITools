#!/bin/bash

# This file is part of the MIDITools distribution (https://github.com/kdijkstra13/MIDITools).
# Copyright (c) 2022 Klaas Dijkstra

# This program is free software: you can redistribute it and/or modify  
# it under the terms of the GNU General Public License as published by  
# the Free Software Foundation, version 3.

# This program is distributed in the hope that it will be useful, but 
# WITHOUT ANY WARRANTY; without even the implied warranty of 
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU 
# General Public License for more details.

# You should have received a copy of the GNU General Public License 
# along with this program. If not, see <http://www.gnu.org/licenses/>.


# drClass' MIDI Trancoder
# Adds note velocity for the KORG Volca FM
# Searches for MIDI Keyboard and the UM-ONE Jack devices and connects them through the VolcaFM transcoder.
# Note: There is a firmware update for the VolcaFM which adds velicity natively, that can be used instead of this.

/home/pi/miniconda3/envs/py35/bin/python /home/pi/software/bin/volcafm_velo.py FM &
pid=$!
sleep 2

#Find input device and output device (tested wih Roland EM22 and Roland UM-One under Ubuntu 12.04)
[ -z "$midi_input" ] && midi_input=`jack_lsp | egrep "a2j.*Keyboard.*(capture)" | head -1`
[ -z "$midi_output" ] && midi_output=`jack_lsp | egrep "UM-ONE.*(playback)" | head -1`
echo "midi_input=$midi_input"
echo "midi_output=$midi_output"

#Final check
[ -z "$midi_input" ] && echo "No suitable midi input found" && exit 1
[ -z "$midi_output" ] && echo "No suitable midi output found" && exit 1


source /home/pi/software/bin/find_midi_io.sh
jack_connect "$midi_input" "VolcaFM:in"
jack_connect "VolcaFM:out" "$midi_output"

wait $pid
