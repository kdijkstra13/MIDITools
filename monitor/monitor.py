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


drClass' MIDI Monitor
View incoming MIDI messages
Convert incoming messages to other messages
Convert Guitar Hero Drums to Volca Beats
"""
import sys
import time
from typing import Dict, List, Any

import pygame.midi as midi

# Note messages
NOTE_ON = 0x9
NOTE_OFF = 0x8
NOTE_AT = 0xD

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


def transcode_message(message, conv, in_channel, out_channel):
    timestamp, channel, cmd, note, velo = decode_message(message)
    result = message
    if cmd in [NOTE_ON, NOTE_OFF] and channel == in_channel:
        for note_from, note_to in conv:
            if note == note_from:
                result = encode_message(timestamp, out_channel, cmd, note_to, velo)
    return result


def get_midi():
    result = []
    for i in range(midi.get_count()):
        info = midi.get_device_info(i)
        result.append({"idx": i, "iface": info[0].decode("ascii"), "name": info[1].decode("ascii"),
                       "input": info[2], "output": info[3], "opened": info[4]})
    return result


def get_midi_input(): return [info for info in get_midi() if info["input"] == 1]
def get_midi_output(): return [info for info in get_midi() if info["output"] == 1]


def choose_device(devices: List[Any], type="input"):
    print(f"Please choose a MIDI {type} device:")
    for i, device in enumerate(devices):
        print(f"{i}: {device['iface']}.{device['name']}")
    print(f"Enter a number between [0..{len(devices)-1}]")
    device_idx = int(input())
    return devices[device_idx]


def choose_device_by_name(devices: List[Any], name: str):
    for i, device in enumerate(devices):
        if device["name"] == name:
            return device
    raise RuntimeError(f"Device named {name} not found")


def decode_note_message(cmd, byte1, byte2):
    return "ON" if cmd == NOTE_ON else "OFF", number_to_octave(byte1), number_to_note(byte1), byte2


def decode_message(message):
    ((status, byte1, byte2, _), timestamp) = message
    chan = status & 0x0F
    cmd = status >> 4
    return timestamp, chan, cmd, byte1, byte2


def encode_message(timestamp, channel, cmd, byte1, byte2):
    status = (cmd << 4) + channel
    message = ((status, byte1, byte2, 0), timestamp)
    return message


def monitor_inputs(midi_input):
    while True:
        if midi_input.poll():
            message = midi_input.read(1)[0]
            timestamp, channel, cmd, byte1, byte2 = decode_message(message)
            if cmd in [NOTE_ON, NOTE_OFF]:
                print(message)
                onoff, oct, note, velocity = decode_note_message(cmd, byte1, byte2)
                print(f"{timestamp}: channel: {channel} command:{onoff} note:{byte1}({note}{oct}) velocity:{velocity}")
            else:
                print(f"{timestamp}: channel: {channel} command:{cmd} byte1:{byte1} byte2:{byte2}")
        time.sleep(0)


def friendly_message(message):
    timestamp, channel, cmd, byte1, byte2 = decode_message(message)
    if cmd in [NOTE_ON, NOTE_OFF]:
        onoff, oct, note, velocity = decode_note_message(cmd, byte1, byte2)
        msg = f"{timestamp}: channel: {channel} command:{onoff} note:{byte1}({note}{oct}) velocity:{velocity}"
    else:
        msg = f"{timestamp}: channel: {channel} command:{cmd} byte1:{byte1} byte2:{byte2}"
    return msg


def band_hero_to_volca_beats(midi_input, midi_output):
    conv = [[BH_BASS, VB_KICK],
            [BH_RED_TOM, VB_SNARE],
            [BH_BLUE_TOM, VB_LO_TOM],
            [BH_GREEN_TOM, VB_HI_TOM],
            [BH_YELLOW_HI, VB_OP_HAT],
            [BH_ORANGE_HI, VB_CL_HAT]]
    in_channel = BH_CHANNEL
    out_channel = VB_CHANNEL
    while True:
        if midi_input.poll():
            in_message = midi_input.read(1)[0]
            out_message = transcode_message(in_message, conv, in_channel, out_channel)
            midi_output.write([out_message])
            print(f"{friendly_message(in_message)} -> {friendly_message(out_message)}")


def number_to_note(number):
    notes = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    return notes[number % 12]


def number_to_octave(number):
    return number // 12


def number_to_full_note(number):
    return f"{number_to_note(number)}{number_to_octave(number)}"


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
    # monitor_inputs(midi.Input(input_device["idx"]))
    band_hero_to_volca_beats(midi.Input(input_device["idx"]),
                             midi.Output(output_device["idx"]))
