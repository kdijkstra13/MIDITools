from typing import List, Any

import pygame.midi as midi
import time

NOTE_ON = 0x9
NOTE_OFF = 0x8
NOTE_AT = 0xD


def number_to_note(number):
    notes = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    return notes[number % 12]


def number_to_octave(number):
    return number // 12


def number_to_full_note(number):
    return f"{number_to_note(number)}{number_to_octave(number)}"


def full_note_to_number(full_note: str):
    notes = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    if full_note[1] == '#':
        note = full_note[:2]
        oct = full_note[2:]
    else:
        note = full_note[0]
        oct = int(full_note[1:])
    number = oct * 12 + notes.index(note)
    return number

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


def choose_device_by_name(devices: List[Any], name: str, type: str = None):
    for i, device in enumerate(devices):
        if device["name"] == name:
            if type is None:
                return device
            else:
                if type == "input" and device["input"] == 1:
                    return device
                if type == "output" and device["output"] == 1:
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


def friendly_message(message):
    timestamp, channel, cmd, byte1, byte2 = decode_message(message)
    if cmd in [NOTE_ON, NOTE_OFF]:
        onoff, oct, note, velocity = decode_note_message(cmd, byte1, byte2)
        msg = f"{timestamp}: channel: {channel} command:{onoff} note:{byte1}({note}{oct}) velocity:{velocity}"
    else:
        msg = f"{timestamp}: channel: {channel} command:{cmd} byte1:{byte1} byte2:{byte2}"
    return msg


def monitor_inputs(midi_input, only_notes=False):
    while True:
        if midi_input.poll():
            message = midi_input.read(1)[0]
            timestamp, channel, cmd, note, velo = decode_message(message)
            if cmd in [NOTE_ON, NOTE_OFF] or not only_notes:
                print(friendly_message(message))
        time.sleep(0)

