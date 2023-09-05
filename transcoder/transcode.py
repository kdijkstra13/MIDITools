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


drClass' MIDI Transcoder

1) View incoming MIDI messages
2) Transcode incoming messages to other messages
3) Transcode Guitar Hero Drums to Korg Volca Beats
4) Transcode Guitar Hero Drums to Electron Model Cycles
"""
import sys
import time
from typing import Dict, List, Any

import pygame.midi as midi

from transcoder.utils.midi import get_midi_input, get_midi_output, choose_device_by_name, choose_device, encode_message, \
    decode_note_message, NOTE_ON, NOTE_OFF, decode_message, full_note_to_number, friendly_message

# Band hero drums
BH_CHANNEL = 9
BH_BASS = 16
BH_RED_TOM = 38
BH_BLUE_TOM = 48
BH_GREEN_TOM = 45
BH_YELLOW_HI = 46
BH_ORANGE_HI = 49

# Volca Beats
VB_CHANNEL = 9
VB_KICK = 36
VB_SNARE = 38
VB_LO_TOM = 43
VB_HI_TOM = 50
VB_CL_HAT = 42
VB_OP_HAT = 46
VB_CLAP = 39


def transcode_message(message, conv):
    timestamp, channel, cmd, note, velo = decode_message(message)
    result = message
    if cmd in [NOTE_ON, NOTE_OFF]:
        for channel_from, note_from, channel_to, note_to in conv:
            if note == note_from and channel == channel_from:
                result = encode_message(timestamp, channel_to, cmd, note_to, velo)
    return result


def message_transcode_loop(midi_input, midi_output, conv):
    while True:
        if midi_input.poll():
            in_message = midi_input.read(1)[0]
            out_message = transcode_message(in_message, conv)
            midi_output.write([out_message])
            print(f"{friendly_message(in_message)} -> {friendly_message(out_message)}")


def message_copy_loop(midi_input, midi_output):
    while True:
        if midi_input.poll():
            message = midi_input.read(1)[0]
            midi_output.write([message])
            print(f"{friendly_message(message)}")

def band_hero_to_volca_beats(midi_input, midi_output):
    conv = [[BH_CHANNEL, BH_BASS,      VB_CHANNEL, VB_KICK],
            [BH_CHANNEL, BH_RED_TOM,   VB_CHANNEL, VB_SNARE],
            [BH_CHANNEL, BH_BLUE_TOM,  VB_CHANNEL, VB_HI_TOM],
            [BH_CHANNEL, BH_GREEN_TOM, VB_CHANNEL, VB_LO_TOM],
            [BH_CHANNEL, BH_YELLOW_HI, VB_CHANNEL, VB_CL_HAT],
            [BH_CHANNEL, BH_ORANGE_HI, VB_CHANNEL, VB_OP_HAT]]
    message_transcode_loop(midi_input, midi_output, conv)


def band_hero_to_electron_cycles(midi_input, midi_output):
    conv = [[BH_CHANNEL, BH_BASS,      0, full_note_to_number("C5")],
            [BH_CHANNEL, BH_RED_TOM,   1, full_note_to_number("C5")],
            [BH_CHANNEL, BH_BLUE_TOM,  2, full_note_to_number("C5")],
            [BH_CHANNEL, BH_GREEN_TOM, 3, full_note_to_number("C5")],
            [BH_CHANNEL, BH_YELLOW_HI, 4, full_note_to_number("C5")],
            [BH_CHANNEL, BH_ORANGE_HI, 5, full_note_to_number("C5")]]
    message_transcode_loop(midi_input, midi_output, conv)


def round_robin_notes(midi_input, midi_output, in_channel, out_channels, echo_other=True):
    idx = 0
    note_state = {}
    while True:
        if midi_input.poll():
            in_message = midi_input.read(1)[0]
            timestamp, chan, cmd, byte1, byte2 = decode_message(in_message)
            if chan == in_channel and cmd in [NOTE_ON, NOTE_OFF]:
                if cmd == NOTE_ON:
                    out_message = encode_message(timestamp, out_channels[idx], cmd, byte1, byte2)
                    state, oct, note, _ = decode_note_message(cmd, byte1, byte2)
                    note_state[f"{note}{oct}"] = out_channels[idx]  # remember which channel to note belongs to
                    idx = (idx + 1 if idx < len(out_channels) - 1 else 0)
                else:
                    state, oct, note, _ = decode_note_message(cmd, byte1, byte2)
                    out_channel = note_state[f"{note}{oct}"]
                    out_message = encode_message(timestamp, out_channel, cmd, byte1, byte2)
                    del note_state[f"{note}{oct}"]

                midi_output.write([out_message])
                print(f"{friendly_message(in_message)} -> {friendly_message(out_message)}")
                print(note_state)
            elif echo_other:
                midi_output.write([in_message])

if __name__ == "__main__":
    midi.init()
    input_devices = get_midi_input()
    output_devices = get_midi_output()
    if len(sys.argv) == 3:
        input_device_name = sys.argv[1]
        output_device_name = sys.argv[2]
        input_device = choose_device_by_name(input_devices, sys.argv[1])
        output_device = choose_device_by_name(output_devices, sys.argv[2])
    else:
        input_device = choose_device(input_devices, "input")
        output_device = choose_device(output_devices, "output")

    print(f"Chosen input: {input_device['name']}")
    print(f"Chosen output: {output_device['name']}")

    # Simple MIDI monitor
    # monitor_inputs(midi.Input(input_device["idx"]))

    # Copy Input to Output
    # message_copy_loop(midi.Input(input_device["idx"]),
    #                   midi.Output(output_device["idx"]))

    # Transcode Band Hero to Volca Beats
    band_hero_to_volca_beats(midi.Input(input_device["idx"]),
                             midi.Output(output_device["idx"]))

    # Transcode Band Hero to Model Cycles
    # band_hero_to_electron_cycles(midi.Input(input_device["idx"]),
    #                              midi.Output(output_device["idx"]))

    # Round robin notes to create a polyphonic Model Cycles
    # round_robin_notes(midi.Input(input_device["idx"]),
    #                   midi.Output(output_device["idx"]),
    #                   in_channel=8,
    #                   out_channels=[0, 1, 2, 3])
