"""XDM syntax machines. Musical defaults and MIDI timing belong to main.py.

Every machine consumes input left to right. Tokens retain their source column;
no parser removes suffixes or guesses structure by searching the whole score.
"""
from dataclasses import dataclass, field
from enum import Enum, auto
import re


@dataclass(frozen=True)
class Token:
    kind: str
    value: str
    offset: int


# Order matters: longest named dynamics and two-letter drums precede notes.
_LEXEMES = re.compile(
    r"(?P<SPACE>\s+)|(?P<NOTE>[A-Z]{2}|[A-G](?:#|b)?\d?)|"
    r"(?P<DYNAMIC>ppp|fff|pp|mp|mf|ff|p|f)|(?P<NUMBER>\d+)|"
    r"(?P<FIELD>[mbtsi])|(?P<ART>['.~-])|"
    r"(?P<SYMBOL>[\[\]|,+@:/^_<>])"
)


def tokenize(source):
    """Recognize lexical units only; states decide which units are legal."""
    position = 0
    while position < len(source):
        match = _LEXEMES.match(source, position)
        if match is None:
            raise ValueError(f"Unexpected character {source[position]!r} at column {position + 1}")
        kind, value = match.lastgroup, match.group()
        if kind != "SPACE":
            yield Token(value if kind == "SYMBOL" else kind, value, position)
        position = match.end()
    yield Token("EOF", "", len(source))


def unexpected(token, expected):
    raise ValueError(f"Expected {expected} at column {token.offset + 1}; got {token.value or 'end of input'!r}")


@dataclass(frozen=True)
class Group:
    """A bracket context, retaining its exact text for compatibility adapters."""
    text: str
    children: tuple = ()


def bracket_groups(source):
    """Push on '[' and pop on ']'; reject text beside nested groups.

    The stack distinguishes score/parallel/leaf contexts. XDM permits only
    two bracket levels, so a third push is an explicit grammar error.
    """
    stack = []
    roots = []
    for index, char in enumerate(source):
        if char == "[":
            if len(stack) == 2:
                raise ValueError(f"Parallel groups cannot be nested at column {index + 1}")
            stack.append((index + 1, []))
        elif char == "]":
            if not stack:
                raise ValueError(f"Unexpected closing bracket at column {index + 1}")
            begin, children = stack.pop()
            text = source[begin:index]
            if children:
                # All non-whitespace content in a container must be a child.
                depth = 0
                for c in text:
                    if c == "[":
                        depth += 1
                    elif c == "]":
                        depth -= 1
                    elif not depth and not c.isspace():
                        raise ValueError("Expected a bracketed voice in parallel group")
            group = Group(text, tuple(children))
            (stack[-1][1] if stack else roots).append(group)
        elif not stack and not char.isspace():
            raise ValueError(f"Expected a bracketed header, measure, or parallel group at column {index + 1}")
    if stack:
        raise ValueError("Unclosed bracket")
    return roots


class HeaderState(Enum):
    FIELD = auto()
    VALUE = auto()
    SLASH = auto()
    DENOMINATOR = auto()


def header_fields(source):
    """Read unordered fields; commas are separators only between fields."""
    state = HeaderState.FIELD
    fields = {}
    name = None
    numerator = None
    for token in tokenize(source):
        if state == HeaderState.FIELD:
            if token.kind == ",":
                continue
            if token.kind == "EOF":
                if not fields:
                    unexpected(token, "at least one header field")
                return fields
            if token.kind not in ("FIELD", "@", ":"):
                unexpected(token, "prefixed fields, e.g. t4/4 or @mf")
            name = token.value
            if name in fields:
                raise ValueError(f"Duplicate header field {name!r}")
            state = HeaderState.VALUE
        elif state == HeaderState.VALUE:
            allowed = ("NUMBER",)
            if name == "@":
                allowed += ("DYNAMIC",)
            elif name == ":":
                allowed += ("ART",)
            if token.kind not in allowed:
                unexpected(token, f"value for {name!r}")
            if name == "t":
                numerator = token.value
                state = HeaderState.SLASH
            else:
                fields[name] = token.value
                state = HeaderState.FIELD
        elif state == HeaderState.SLASH:
            if token.kind != "/":
                unexpected(token, "'/' in timing fraction, e.g. t4/4")
            state = HeaderState.DENOMINATOR
        else:
            if token.kind != "NUMBER":
                unexpected(token, "time-signature denominator")
            fields[name] = numerator + "/" + token.value
            state = HeaderState.FIELD


@dataclass
class Event:
    """Local overrides: None means inherit, never update voice defaults."""
    notes: list = field(default_factory=list)
    velocity: int | None = None
    gate: int | None = None
    articulation: str | None = None
    marcato: bool = False
    ramp: str | None = None
    ramp_end: str | None = None
    hold: bool = False

    def legacy(self):
        """Compatibility shape for the existing musical-resolution layer."""
        return {name: getattr(self, name) for name in
                ('notes', 'velocity', 'gate', 'articulation', 'marcato', 'ramp', 'ramp_end')}


class EventState(Enum):
    START = auto()
    PITCH = auto()
    AFTER_PITCH = auto()
    VELOCITY = auto()
    AFTER_VELOCITY = auto()
    GATE = auto()
    ENDING = auto()
    DONE = auto()


def parse_event(source, dynamics, articulations, drums):
    """Grammar: [ramp] pitch(+pitch)* [velocity] [ending] [ramp-end].

    States enforce modifier order and the single-ending rule. Delimiters are
    consumed by the measure machine, so EOF here is an event boundary.
    """
    state = EventState.START
    event = Event()
    for token in tokenize(source):
        kind = token.kind
        if kind == "EOF":
            if state == EventState.START:
                return None  # An empty position is a rest.
            if state in (EventState.PITCH, EventState.VELOCITY, EventState.GATE):
                unexpected(token, state.name.lower() + " value")
            return event
        if state == EventState.START:
            state = EventState.PITCH
            if kind in ("<", ">"):
                event.ramp = token.value
                continue
            if kind == "_":
                event.hold = True
                state = EventState.DONE
                continue
            # First pitch falls through, consuming this same token.
        if state == EventState.PITCH:
            if kind != "NOTE" or (len(token.value) == 2 and token.value.isalpha() and token.value.isupper() and token.value not in drums):
                unexpected(token, "note or drum")
            event.notes.append(token.value)
            state = EventState.AFTER_PITCH
        elif state == EventState.VELOCITY:
            if kind not in ("NUMBER", "DYNAMIC"):
                unexpected(token, "velocity percentage or dynamic")
            event.velocity = _value(token, dynamics, "velocity")
            state = EventState.AFTER_VELOCITY
        elif state == EventState.GATE:
            if kind not in ("NUMBER", "ART"):
                unexpected(token, "gate percentage or articulation")
            event.gate = _value(token, articulations, "gate")
            state = EventState.ENDING
        elif state in (EventState.AFTER_PITCH, EventState.AFTER_VELOCITY, EventState.ENDING):
            if state == EventState.AFTER_PITCH and kind == "+":
                state = EventState.PITCH
            elif state == EventState.AFTER_PITCH and kind == "@":
                state = EventState.VELOCITY
            elif state == EventState.AFTER_PITCH and kind == "DYNAMIC":
                event.velocity = dynamics[token.value]
                state = EventState.AFTER_VELOCITY
            elif state != EventState.ENDING and kind == ":":
                state = EventState.GATE
            elif state != EventState.ENDING and kind in ("ART", "^"):
                event.articulation = token.value if kind == "ART" else None
                event.marcato = kind == "^"
                state = EventState.ENDING
            elif kind in ("<", ">"):
                if event.ramp is not None:
                    raise ValueError("An event cannot both start and end a ramp")
                event.ramp_end = token.value
                state = EventState.DONE
            else:
                unexpected(token, "modifier or end of event")
        else:
            unexpected(token, "end of event")


def _value(token, presets, what):
    if token.value in presets:
        return presets[token.value]
    value = int(token.value)
    if not 0 <= value <= 100:
        raise ValueError(f"{what.capitalize()} must be between 0 and 100 at column {token.offset + 1}")
    return value


@dataclass(frozen=True)
class Measure:
    beats: tuple


def parse_measure(source, dynamics, articulations, drums):
    """Each delimiter completes a position; '|' also completes its beat.

    Empty positions are preserved, including trailing commas and bars, since
    they contribute to subdivision and silence. Notes are parsed before MIDI
    resolution so the renderer never reparses strings.
    """
    beats, positions = [], []
    begin = 0
    for token in tokenize(source):
        if token.kind in (",", "|", "EOF"):
            positions.append(parse_event(source[begin:token.offset], dynamics, articulations, drums))
            begin = token.offset + 1
            if token.kind in ("|", "EOF"):
                beats.append(tuple(positions))
                positions = []
    return Measure(tuple(beats))
