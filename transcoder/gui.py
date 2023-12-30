"""
This file is part of the MIDITools distribution (https://github.com/kdijkstra13/MIDITools).
Copyright (c) 2023 Klaas Dijkstra

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

1) Transcode MIDI message from all enabled input channels to all enabled output channels
2) Forward MIDI messages from input channel to output channel.
3) A convenient GUI to enable or disable which channels are enabled.
"""

import tkinter as tk
from threading import Event
from tkinter import font

import pygame.midi as midi
import threading
import time

from transcoder.utils.midi import get_midi, choose_device_by_name, monitor_inputs, friendly_message, decode_message, \
    encode_message, NOTE_OFF, NOTE_ON, number_to_full_note, full_note_to_number


class UI:
    def __init__(self):
        # Create the main window
        self.root = tk.Tk()
        self.root.title("MIDI Channel Selector")

        # Create labels for input and output channels
        input_label = tk.Label(self.root, text="Input MIDI Channel")
        split_begin_label = tk.Label(self.root, text="Split Begin Note")
        split_end_label = tk.Label(self.root, text="Split End Note")
        output_label = tk.Label(self.root, text="Output MIDI Channel")
        thru_label = tk.Label(self.root, text="Thru MIDI Channels")

        input_label.grid(row=0, column=0, columnspan=8)
        split_begin_label.grid(row=1, column=0, columnspan=8)
        split_end_label.grid(row=2, column=0, columnspan=8)
        output_label.grid(row=3, column=0, columnspan=8)
        thru_label.grid(row=4, column=0, columnspan=8)

        self.on_font = font.Font(size=14)
        self.other_color = "#7b7c8a"
        self.on_color = "#c93030"
        self.off_color = "#521818"
        self.split_on_color = "#56bd31"
        self.split_off_color = "#2d5e1a"
        self.split_set_color = "#327ba8"

        # Buttons
        self.init_button = tk.Button(self.root, text="Init", font=self.on_font, bg=self.other_color, fg="white",
                                     width=8, height=1)
        self.init_button.grid(row=5, column=0, columnspan=8)

        self.show_button = tk.Button(self.root, text="Show", font=self.on_font, bg=self.other_color, fg="white",
                                     width=8, height=1)
        self.show_button.grid(row=5, column=3, columnspan=8)

        # Create arrays to store checkbox variables
        self.input_buttons = []
        self.output_buttons = []
        self.split_begin_buttons = []
        self.split_end_buttons = []
        self.split_begin_button_id = None
        self.split_end_button_id = None
        self.thru_buttons = []

        for r, t in zip([0, 3, 4], ["input", "output", "thru"]):
            all_button = tk.Button(self.root, text="On", width=4, height=2,
                                   command=lambda x=t: self.on_all(x, "on"), font=self.on_font,
                                   bg=self.other_color, fg="white")
            all_button.grid(row=r, column=8, padx=5, pady=5)

            all_button = tk.Button(self.root, text="Off", width=4, height=2,
                                   command=lambda x=t: self.on_all(x, "off"), font=self.on_font,
                                   bg=self.other_color, fg="white")
            all_button.grid(row=r, column=9, padx=5, pady=5)

        self.split_begin_set_button = tk.Button(self.root, text="Set", width=4, height=2,
                                                command=lambda x="split_begin": self.on_set_split(x, "set"),
                                                font=self.on_font,
                                                bg=self.other_color, fg="white")
        self.split_begin_set_button.grid(row=1, column=8, padx=5, pady=5)

        self.split_end_set_button = tk.Button(self.root, text="Set", width=4, height=2,
                                              command=lambda x="split_end": self.on_set_split(x, "set"),
                                              font=self.on_font,
                                              bg=self.other_color, fg="white")
        self.split_end_set_button.grid(row=2, column=8, padx=5, pady=5)
        # Create and place checkboxes for input and output channels
        for i in range(16):
            input_button = tk.Button(self.root, text=str(i + 1), width=4, height=2,
                                     command=lambda m=i: self.on_click(m, "input"), font=self.on_font,
                                     bg=self.on_color, fg="white")
            self.input_buttons.append(input_button)
            input_button.grid(row=0, column=i + 10, padx=5, pady=5)
            input_button.config(relief="sunken")

            split_begin_button = tk.Button(self.root, text="X", width=4, height=2,
                                           command=lambda m=i: self.on_click(m, "split_begin"), font=self.on_font,
                                           bg=self.split_off_color, fg="black")
            self.split_begin_buttons.append(split_begin_button)
            split_begin_button.grid(row=1, column=i + 10)

            split_end_button = tk.Button(self.root, text="X", width=4, height=2,
                                         command=lambda m=i: self.on_click(m, "split_end"), font=self.on_font,
                                         bg=self.split_off_color, fg="black")
            self.split_end_buttons.append(split_end_button)
            split_end_button.grid(row=2, column=i + 10)

            output_button = tk.Button(self.root, text=str(i + 1), width=4, height=2,
                                      command=lambda m=i: self.on_click(m, "output"), font=self.on_font,
                                      bg=self.off_color, fg="black")
            self.output_buttons.append(output_button)
            output_button.grid(row=3, column=i + 10)

            thru_button = tk.Button(self.root, text=str(i + 1), width=4, height=2,
                                    command=lambda m=i: self.on_click(m, "thru"), font=self.on_font,
                                    bg=self.on_color, fg="white")
            thru_button.config(relief="sunken")
            self.thru_buttons.append(thru_button)
            thru_button.grid(row=4, column=i + 10)

    def on_all(self, button_type, switch):
        if button_type == "input":
            l = self.input_buttons
        elif button_type == "output":
            l = self.output_buttons
        else:
            l = self.thru_buttons
        for b in l:
            if switch == "on":
                b.config(relief="sunken", bg=self.on_color, fg="white")
            else:
                b.config(relief="raised", bg=self.off_color, fg="black")

    def disable_split_button(self, button_type):
        if button_type == "split_begin":
            if self.split_begin_button_id is not None:
                if self.split_begin_buttons[self.split_begin_button_id].cget("relief") == "sunken":
                    self.split_begin_buttons[self.split_begin_button_id].config(bg=self.split_on_color)
                else:
                    self.split_begin_buttons[self.split_begin_button_id].config(bg=self.split_off_color)
                self.split_begin_button_id = None
        elif button_type == "split_end":
            if self.split_end_button_id is not None:
                if self.split_end_buttons[self.split_end_button_id].cget("relief") == "sunken":
                    self.split_end_buttons[self.split_end_button_id].config(bg=self.split_on_color)
                else:
                    self.split_end_buttons[self.split_end_button_id].config(bg=self.split_off_color)
                self.split_end_button_id = None

    def on_set_split(self, button_type, switch):
        if button_type == "split_begin" and switch == "set":
            if self.split_begin_set_button.cget("relief") == "raised":
                self.split_begin_set_button.config(relief="sunken", bg=self.split_set_color, fg="black")
            else:
                self.disable_split_button("split_begin")
                self.split_begin_set_button.config(relief="raised", bg=self.other_color, fg="white")

        if button_type == "split_end" and switch == "set":
            if self.split_end_set_button.cget("relief") == "raised":
                self.split_end_set_button.config(relief="sunken", bg=self.split_set_color, fg="black")
            else:
                self.disable_split_button("split_end")
                self.split_end_set_button.config(relief="raised", bg=self.other_color, fg="white")

    def on_click(self, button_id, button_type):
        if button_type in ["split_begin", "split_end"]:
            if button_type == "split_begin":
                if self.split_begin_set_button.cget("relief") == "sunken":
                    self.disable_split_button("split_begin")
                    self.split_begin_buttons[button_id].config(bg=self.split_set_color)
                    self.split_begin_button_id = button_id
                else:
                    if self.split_begin_buttons[button_id].cget("relief") == "sunken":
                        self.split_begin_buttons[button_id].config(relief="raised", bg=self.split_off_color, fg="black")
                    else:
                        self.split_begin_buttons[button_id].config(relief="sunken", bg=self.split_on_color, fg="white")
            if button_type == "split_end":
                if self.split_end_set_button.cget("relief") == "sunken":
                    self.disable_split_button("split_end")
                    self.split_end_buttons[button_id].config(bg=self.split_set_color)
                    self.split_end_button_id = button_id
                else:
                    if self.split_end_buttons[button_id].cget("relief") == "sunken":
                        self.split_end_buttons[button_id].config(relief="raised", bg=self.split_off_color, fg="black")
                    else:
                        self.split_end_buttons[button_id].config(relief="sunken", bg=self.split_on_color, fg="white")
        else:
            if button_type == "input":
                button = self.input_buttons[button_id]
            elif button_type == "output":
                button = self.output_buttons[button_id]
            else:
                button = self.thru_buttons[button_id]

            if button.cget("relief") == "sunken":
                button.config(relief="raised", bg=self.off_color, fg="black")
            else:
                button.config(relief="sunken", bg=self.on_color, fg="white")

    def start(self):
        self.root.mainloop()


class Messages:
    def __init__(self, midi_thru_name, midi_input_name, midi_output_name, ui):
        self.midi_input_name = midi_input_name
        self.midi_output_name = midi_output_name
        self.midi_thru_name = midi_thru_name
        self.midi_thru = None
        self.midi_input = None
        self.midi_output = None
        self.stop = Event()
        self.initialized = False
        self.ui = ui
        self.ui.init_button.bind("<Button>", lambda x: self.init_devices())
        self.ui.show_button.bind("<Button>", lambda x: self.show_devices())

    def show_devices(self):
        [print(d) for d in get_midi()]

    def init_devices(self):
        try:
            midi.init()
            devices = get_midi()
            input_dev = choose_device_by_name(devices, self.midi_input_name, "input")
            output_dev = choose_device_by_name(devices, self.midi_output_name, "output")
            thru_dev = choose_device_by_name(devices, self.midi_thru_name, "input")

            self.midi_thru = midi.Input(thru_dev["idx"])
            self.midi_input = midi.Input(input_dev["idx"])
            self.midi_output = midi.Output(output_dev["idx"])
            self.initialized = True
        except RuntimeError as e:
            print(e)
            self.initialized = False

    def __call__(self):
        self.init_devices()

        while not self.stop.is_set():
            if not self.initialized:
                print(".", end="")
                time.sleep(1)
                continue

            if self.midi_input.poll():
                message = self.midi_input.read(1)[0]
                timestamp, channel, cmd, note, velo = decode_message(message)

                # Use note to set split point
                if self.ui.split_begin_button_id is not None:
                    self.ui.split_begin_buttons[self.ui.split_begin_button_id].config(text=number_to_full_note(note))
                    self.ui.disable_split_button("split_begin")
                    self.ui.split_begin_button_id = None
                if self.ui.split_end_button_id is not None:
                    self.ui.split_end_buttons[self.ui.split_end_button_id].config(text=number_to_full_note(note))
                    self.ui.disable_split_button("split_end")
                    self.ui.split_end_button_id = None

                # Fetch and forward note
                if cmd in [NOTE_ON, NOTE_OFF] and self.ui.input_buttons[channel].cget("relief") == "sunken":
                    for i in range(16):
                        if self.ui.output_buttons[i].cget("relief") == "sunken":
                            min_note = -1
                            if self.ui.split_begin_buttons[i].cget("relief") == "sunken":
                                note_name = self.ui.split_begin_buttons[i].cget("text")
                                if note_name != "X":
                                    min_note = full_note_to_number(note_name)
                            max_note = 999
                            if self.ui.split_end_buttons[i].cget("relief") == "sunken":
                                note_name = self.ui.split_end_buttons[i].cget("text")
                                if note_name != "X":
                                    max_note = full_note_to_number(note_name)
                            if note > min_note and note <= max_note:
                                output_message = encode_message(timestamp, i, cmd, note, velo)
                                self.midi_output.write([output_message])
                                print(f"Forward: {friendly_message(message)} -> {friendly_message(output_message)}")

            if self.midi_thru.poll():
                message = self.midi_thru.read(1)[0]
                timestamp, channel, cmd, note, velo = decode_message(message)
                if self.ui.thru_buttons[channel].cget("relief") == "sunken":
                    self.midi_output.write([message])
                    if cmd in [NOTE_ON, NOTE_OFF]:
                        print(f"Thru: {friendly_message(message)}")
            time.sleep(0)


if __name__ == "__main__":
    ui = UI()
    message_handler = Messages(midi_thru_name="UM-ONE",
                               midi_input_name="Roland Digital Piano",
                               midi_output_name="UM-ONE",
                               ui=ui)
    # # Create a thread for MIDI forwarding
    midi_thread = threading.Thread(target=message_handler)
    midi_thread.start()
    message_handler.ui.start()
    message_handler.stop.set()
    midi_thread.join()
    print("Closed")
