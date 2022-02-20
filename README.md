# MIDITools
Collection of MIDI tools

# Volca FM velocity
Adds note velocity for the KORG Volca FM by prepending a velocity message to the note message.

* Platform: Ubuntu (Jack-Client)
* ./volcafm_velo/volcafm_velo.py - Python script for starting the Jack port.
* ./volcafm_velo/volcafm_velo.sh - Shell script to connect a Jack MIDI input via the transcoder to a Jack MIDI output.

# Band Hero to Volca Beats
Converts notes send by the Wii Band Hero Drums to the Korg Volca Beats.

* Platform: Windows (PyGame.midi)
* ./monitor/monitor.py - Python script converting MIDI messages and monitoring MIDI messages.
