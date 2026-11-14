import os
import logging

from select import select
from functools import partial

from evdev import InputDevice, InputEvent
from evdev import ecodes as e
from . import decorators, util


log = logging.getLogger("pyzmo")
log.addHandler(logging.NullHandler())


class EventHandler:
    def __init__(self, name):
        self.name = name

        #: mapping of event sequences to triggers
        #: ex: { ((EV_KEY, KEY_1, 1), (EV_KEY, KEY_2, 1)): Trigger("chord", ..., callback, {'quick': True}) }
        self.triggers: dict[tuple, decorators.Trigger] = {}

        # event decorators
        self.event = partial(decorators.EventDecorator, self.triggers)
        self.key = partial(decorators.KeyDecorator, self.triggers)
        self.chord = partial(decorators.ChordDecorator, self.triggers)
        self.keyseq = partial(decorators.SequenceDecorator, self.triggers)

        self.handled_types = set()  #: event types this handler is interested in
        self.handled_codes = set()  #: (type, code) pairs this handler is interested in

        #: keys that are currently held down: {code: key-down event}
        self.held_keys: dict[int, InputEvent] = {}
        #: events matched so far by partially matched key sequences
        self.trigger_events: dict[tuple, list[InputEvent]] = {}

    def filter(self, events):
        """Filter events that are of no interest to this handler."""
        ht, hc = self.handled_types, self.handled_codes

        for ev in events:
            # All key events pass, because pressing an unrelated key must reset key sequences.
            if (ev.type == e.EV_KEY and ev.type in ht) or (ev.type, ev.code) in hc:
                yield ev

    def create_filters(self):
        """Populate ``handled_types`` and ``handled_codes``."""
        self.handled_types.clear()
        self.handled_codes.clear()
        for trigger in self.triggers:
            for etype, code, _ in trigger:
                self.handled_types.add(etype)
                self.handled_codes.add((etype, code))

    def process_event(self, ev):
        """Process a single event."""
        evkey = (ev.type, ev.code, ev.value)

        if ev.type == e.EV_KEY:
            if ev.value == 1:
                self.held_keys[ev.code] = ev
            elif ev.value == 0:
                self.held_keys.pop(ev.code, None)

        # iterate through all triggers set through @event, @key, @chord and @keyseq
        for trigger in list(self.triggers.values()):
            match trigger.kind:
                case "chord":
                    events = self.match_chord(trigger, ev, evkey)
                case "sequence":
                    events = self.match_sequence(trigger, ev, evkey)
                case _:
                    events = [ev] if trigger.events == (evkey,) else None

            if events is None:
                continue

            trigger.func(events)
            if trigger.options.get("quick", False):
                break

    def match_chord(self, trigger, ev, evkey):
        """Match when the last key is pressed while all other keys are held down."""
        *others, last = trigger.events
        if evkey != last:
            return None

        try:
            held = [self.held_keys[code] for _, code, _ in others]
        except KeyError:
            return None
        return [*held, ev]

    def match_sequence(self, trigger, ev, evkey):
        """Advance a key sequence and return its events when it is complete."""
        seq = trigger.events
        events = self.trigger_events.get(seq, [])

        timeout = trigger.options.get("timeout")
        if events and timeout is not None:
            if ev.timestamp() - events[-1].timestamp() > timeout:
                events = []

        if evkey != seq[len(events)]:
            # Pressing another key starts the sequence over. Other events (key releases,
            # autorepeat and non-key events) do not change the progress.
            if ev.type == e.EV_KEY and ev.value == 1:
                events = [ev] if evkey == seq[0] else []
            self.trigger_events[seq] = events
            return None

        events = [*events, ev]
        if len(events) == len(seq):
            del self.trigger_events[seq]
            return events

        self.trigger_events[seq] = events
        return None

    def poll(self, *fns: str | os.PathLike | InputDevice):
        """Read and react to input events."""

        makedev = lambda x: x if isinstance(x, InputDevice) else InputDevice(x)
        devices = map(makedev, fns)
        devices = {dev.fd: dev for dev in devices}

        self.create_filters()
        log.debug("Handled event types: %s", self.handled_types)
        log.debug("Handled event codes: %s", self.handled_codes)

        log.debug("Registered triggers:\n%s", "\n".join(util.describe_triggers(self.triggers)))

        for dev in devices.values():
            log.info("Listening on %s", dev)

        log.info("Entering main-loop ...")
        while True:
            r, _, _ = select(devices, [], [])
            for fd in r:
                for ev in self.filter(devices[fd].read()):
                    self.process_event(ev)
