"""Command-line interface for XDM; language parsing lives in main.py."""
import argparse
from io import BytesIO
from pathlib import Path
import sys

from .main import create_midi, parse_xdm, validate_xdm


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="xdmgen", description="Validate Xala Delta Music Markup Language or generate MIDI."
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("input", nargs="?", type=Path, help="UTF-8 .xdm input file")
    source.add_argument("--code", help="literal XDM text instead of an input file")
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--validate", action="store_true", help="validate only; write no MIDI file")
    action.add_argument("-o", "--output", type=Path, help="output MIDI path (default: input path with .mid suffix)")
    args = parser.parse_args(argv)
    if args.code is not None and not args.validate and args.output is None:
        parser.error("literal MIDI generation requires -o/--output")
    output = args.output
    if not args.validate and output is None:
        output = args.input.with_suffix(".mid")
    if args.input is not None and output is not None and args.input.resolve() == output.resolve():
        parser.error("output must differ from the input file")
    try:
        text = args.code if args.code is not None else args.input.read_text(encoding="utf-8-sig")
        if args.validate:
            validate_xdm(text)
            print("Valid XDM")
        else:
            events = parse_xdm(text)
            midi = create_midi([args.input.stem if args.input is not None else "XDM"])
            for method, values in events:
                getattr(midi, method)(**values)
            # Serialize first so invalid MIDI never leaves a partial output file.
            data = BytesIO()
            midi.writeFile(data)
            output.write_bytes(data.getvalue())
            print(f"Wrote {output}")
    except ImportError as exc:
        print(f"xdmgen: {exc}. Install MIDIUtil to generate MIDI.", file=sys.stderr)
        return 1
    except (OSError, UnicodeError, ValueError, KeyError, OverflowError) as exc:
        print(f"xdmgen: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
