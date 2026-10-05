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
6) Transcode and forward midi messages between channels with a convenient GUI.

* Platform: Windows (PyGame.midi)
* ./transcoder/transcoder.py - Python script converting MIDI messages and monitoring MIDI messages.
* ./transcoder/gui.py - Python script transcoding and forwarding MIDI messages.

# Gen MIDI
Xala Delta Music Markup Language (XDM) generates MIDI files for melody,
chords, and drums. Save music directly in `.xdm` files and use `xdmgen`:

```sh
python -m pip install .
xdmgen genmidi/generated/HipHop.xdm -o hiphop.mid
xdmgen genmidi/JustForYou.xdm --validate
xdmgen --code '[t1/1][A+C+E]' -o chord.mid
```

Supports compact prefixed headers, local note expression, drums, and parallel
voices. For example, these two voices play together in each group, and the
groups play one after another:

```text
[t4/4s120@mf]
[[m1][C4|D4|E4|F4][m2][C3|_|G3|_]]
[[G4|F4|E4|D4][F3|_|G3|_]]
```

`[]` is a full silent measure. Headers set defaults; modifiers such as
`C4mf'` affect only their own event. Ambiguous parallel structures and
conflicting shared settings raise errors.

See the [language reference and examples](genmidi/README.md), including
[parallel voices](genmidi/README.md#parallel-voices), for the complete rules.

* ./genmidi/src/xdm.py - XDM parser, validation, and MIDI API.
* ./genmidi/xdmgen.py - Separate command-line interface, installed as `xdmgen`.
* ./genmidi/JustForYou.xdm - Left-hand chords and right-hand melody.
* ./genmidi/generated/ - Standalone `.xdm` music examples.
