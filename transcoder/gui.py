import tkinter as tk
from threading import Event
from tkinter import font

import pygame.midi as midi
import threading
import time

from transcoder.utils.midi import get_midi, choose_device_by_name, monitor_inputs, friendly_message, decode_message, \
    encode_message, NOTE_OFF, NOTE_ON

class UI:
    def __init__(self):
        # Create the main window
        self.root = tk.Tk()
        self.root.title("MIDI Channel Selector")

        # Create labels for input and output channels
        input_label = tk.Label(self.root, text="Input MIDI Channel")
        output_label = tk.Label(self.root, text="Output MIDI Channel")
        thru_label = tk.Label(self.root, text="Thru MIDI Channels")
        input_label.grid(row=0, column=0, columnspan=8)
        output_label.grid(row=1, column=0, columnspan=8)
        thru_label.grid(row=2, column=0, columnspan=8)

        self.on_font = font.Font(size=14)
        self.other_color = "#7b7c8a"
        self.on_color = "#c93030"
        self.off_color = "#521818"

        # Buttons
        self.init_button = tk.Button(self.root, text="Init", font=self.on_font, bg=self.other_color, fg="white",
                                     width=8, height=1)
        self.init_button.grid(row=4, column=0, columnspan=8)

        # Create arrays to store checkbox variables
        self.input_buttons = []
        self.output_buttons = []
        self.thru_buttons = []

        for r, t in zip([0, 1, 2], ["input", "output", "thru"]):
            all_button = tk.Button(self.root, text="On", width=4, height=2,
                                   command=lambda x=t: self.on_all(x, "on"), font=self.on_font,
                                   bg=self.other_color, fg="white")
            all_button.grid(row=r, column=8, padx=5, pady=5)

            all_button = tk.Button(self.root, text="Off", width=4, height=2,
                                   command=lambda x=t: self.on_all(x, "off"), font=self.on_font,
                                   bg=self.other_color, fg="white")
            all_button.grid(row=r, column=9, padx=5, pady=5)

        # Create and place checkboxes for input and output channels
        for i in range(16):
            input_button = tk.Button(self.root, text=str(i + 1), width=4, height=2,
                                     command=lambda m=i: self.on_click(m, "input"), font=self.on_font,
                                     bg=self.on_color, fg="white")
            self.input_buttons.append(input_button)
            input_button.grid(row=0, column=i + 10, padx=5, pady=5)
            input_button.config(relief="sunken")

            output_button = tk.Button(self.root, text=str(i + 1), width=4, height=2,
                                      command=lambda m=i: self.on_click(m, "output"), font=self.on_font,
                                      bg=self.off_color, fg="black")
            self.output_buttons.append(output_button)
            output_button.grid(row=1, column=i + 10)

            thru_button = tk.Button(self.root, text=str(i + 1), width=4, height=2,
                                    command=lambda m=i: self.on_click(m, "thru"), font=self.on_font,
                                    bg=self.on_color, fg="white")
            thru_button.config(relief="sunken")
            self.thru_buttons.append(thru_button)
            thru_button.grid(row=2, column=i + 10)

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

    def on_click(self, button_id, button_type):
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
                print("Wait for init")
                time.sleep(1)
                continue
            if self.midi_input.poll():
                message = self.midi_input.read(1)[0]
                timestamp, channel, cmd, note, velo = decode_message(message)
                if cmd in [NOTE_ON, NOTE_OFF] and self.ui.input_buttons[channel].cget("relief") == "sunken":
                    for i in range(16):
                        if self.ui.output_buttons[i].cget("relief") == "sunken":
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
