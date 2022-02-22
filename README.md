# MIDITools
Collection of MIDI tools

# Volca FM velocity
Adds note velocity for the KORG Volca FM by prepending a velocity message to the note message.

* Platform: Ubuntu (Jack-Client)
* ./volcafm_velo/volcafm_velo.py - Python script for starting the Jack port.
* ./volcafm_velo/volcafm_velo.sh - Shell script to connect a Jack MIDI input via the transcoder to a Jack MIDI output.

# MIDI Transcoder
The transcoder currently has these capabilities:

1) View incoming MIDI messages
2) Transcode incoming messages to other messages
3) Transcode Guitar Hero Drums to Korg Volca Beats
4) Transcode Guitar Hero Drums to Electron Model Cycles
5) Round robin channel MIDI, create polyphonic synth from the Electron Model Cycles

* Platform: Windows (PyGame.midi)
* ./transcoder/transcoder.py - Python script converting MIDI messages and monitoring MIDI messages.
