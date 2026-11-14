import logging
from collections.abc import Callable
from dataclasses import dataclass, field

from evdev import ecodes as e
from .util import maketuple, raise_on_unknown_key

log = logging.getLogger("decorator")

#: key states accepted by ``@key(..., states=...)`` and their event values
KEY_STATES = {"up": 0, "down": 1, "hold": 2}


@dataclass(frozen=True, slots=True)
class Trigger:
    """A registered callback and the events that trigger it."""

    kind: str  #: "event", "chord" or "sequence"
    events: tuple  #: ((type, code, value), ...)
    func: Callable
    options: dict = field(default_factory=dict)


class Decorator:
    def __init__(self, triggers, *events, **options):
        """
        @param triggers: reference to EventHandler.triggers
        @param events:   list of events - subclass specific
        @param options:  dictionary of options
        """

        self.triggers = triggers
        self.options = options
        self.evseq = tuple(self.create_event_sequence(events))

    #: how EventHandler matches the event sequences of this decorator
    kind = "event"

    def create_event_sequence(self, events):
        raise NotImplementedError

    def __call__(self, func):
        for seq in self.evseq:
            self.triggers[seq] = Trigger(self.kind, seq, func, self.options)
        return func


class EventDecorator(Decorator):
    """
    Arbitrary input event decorator. Example:

        @event(EV_REL, REL_WHEEL, -1)
        @event((EV_REL, REL_WHEEL, 1), (EV_REL, REL_HWHEEL, 1))

    The latter form is used to specify multiple events for a single
    callback (not a sequence of events).
    """

    def create_event_sequence(self, events):
        for ev in maketuple(events):
            yield (ev,)


class KeyDecorator(Decorator):
    """
    Single key (EV_KEY or EV_BTN) decorator. Example:

        @key(KEY_A)
        @key(KEY_B, KEY_C)
        @key(KEY_D, states=('up', 'down', 'hold'))

    The ``states`` option may be used to set when a callback should be
    triggered. By default, this happens when the key is pressed (value 1).
    """

    def create_event_sequence(self, keys):
        states = self.options.get("states", ("down",))
        if isinstance(states, str):
            states = (states,)

        unknown = [state for state in states if state not in KEY_STATES]
        if unknown or not states:
            msg = "Invalid key states {!r} passed to decorator, expected one or more of: {}"
            raise ValueError(msg.format(unknown or states, ", ".join(KEY_STATES)))

        for pair in maketuple(keys):
            for key in pair:
                raise_on_unknown_key(key)
                for state in states:
                    yield ((e.EV_KEY, key, KEY_STATES[state]),)


class ChordDecorator(Decorator):
    """
    A combination of keys, pressed simultaneously. Example:

      @chord(KEY_LEFTCTRL, KEY_LEFTALT, KEY_DELETE)
      @chord((KEY_LEFTCTRL, KEY_C), (KEY_LEFTCTRL, KEY_X))

    The callback is triggered when the last key is pressed while all
    other keys are held down. The other keys can be pressed in any order.
    """

    kind = "chord"

    def create_event_sequence(self, keys):
        for pair in maketuple(keys):
            seq = []
            for key in pair:
                raise_on_unknown_key(key)
                ev = (e.EV_KEY, key, 1)
                seq.append(ev)

            yield tuple(seq)


class SequenceDecorator(Decorator):
    """
    A sequence of keys, pressed one after the other. Example:

      @keyseq(KEY_Q, KEY_W, KEY_E)
      @keyseq((KEY_A, KEY_B, KEY_C), (KEY_1, KEY_2, KEY_3))
      @keyseq(KEY_Q, KEY_W, timeout=1.0)

    A key press that does not continue the sequence starts it over. The
    ``timeout`` option sets the maximum number of seconds between two
    consecutive events of the sequence (default: no limit).
    """

    kind = "sequence"

    def create_event_sequence(self, keys):
        for pair in maketuple(keys):
            seq = []
            for key in pair:
                raise_on_unknown_key(key)
                events = ((e.EV_KEY, key, 1), (e.EV_KEY, key, 0))
                for ev in events:
                    seq.append(ev)

            yield tuple(seq)
