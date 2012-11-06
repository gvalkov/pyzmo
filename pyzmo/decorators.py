import logging

from evdev import ecodes as e
from pyzmo.util import maketuple, raise_on_unknown_key

log = logging.getLogger('decorator')


class Decorator:
    def __init__(self, triggers, *events, **options):
        '''
        @param triggers: reference to EventHandler.triggers
        @param events:   list of events - subclass specific
        @param options:  dictionary of options
        '''

        self.triggers = triggers
        self.options = options
        self.evseq = tuple(self.create_event_sequence(events))

    def create_event_sequence(self, events):
        raise NotImplementedError

    def __call__(self, func):
        for seq in self.evseq:
            self.triggers[seq] = (func, self.options)
        return func

class EventDecorator(Decorator):
    '''
    Arbitrary input event decorator. Example:

        @event(EV_REL, REL_WHEEL, -1)
        @event((EV_REL, REL_WHEEL, 1), (EV_REL, REL_HWHEEL, 1))

    The latter is used to specify multiple events for a single
    callback (not a sequence of events).
    '''

    def create_event_sequence(self, events):
        for ev in maketuple(events):
            yield (ev,)

class KeyDecorator(Decorator):
    '''
    Single key (EV_KEY or EV_BTN) decorator. Example:

        @key(KEY_A)
        @key(KEY_B, KEY_C)
        @key(KEY_D, states=('up', 'down', 'hold'))

    By default callbacks will be triggered once the key is
    pressed (value 1). The ``states`` options 
    '''
    def create_event_sequence(self, keys):
        states = self.options.get('states', ['down'])

        for pair in maketuple(keys):
            for key in pair:
                raise_on_unknown_key(key)
                for state in states:
                    val = {'up':0, 'down':1, 'hold':2}[state]
                    ev = [(e.EV_KEY, key, val)]
                    yield tuple(ev)

class ChordDecorator(Decorator):
    '''
    A combination of keys, pressed simultaneously. Example:

        @chord(KEY_LEFTCTRL, KEY_LEFTALT, KEY_DELETE)
        @chord((KEY_LEFTCTRL, KEY_C), (KEY_LEFTCTRL, KEY_X))
    '''
    def create_event_sequence(self, keys):
        for pair in maketuple(keys):
            seq = []
            for key in pair:
                raise_on_unknown_key(key)
                ev = (e.EV_KEY, key, 1)
                seq.append(ev)

            yield tuple(seq)

class SequenceDecorator(Decorator):
    '''
    A sequence of keys, pressed one after the other. Example:

        @keyseq(KEY_Q, KEY_W, KEY_E)
        @keyseq((KEY_A, KEY_B, KEY_C), (KEY_1, KEY_2, KEY_3))
    '''
    def create_event_sequence(self, keys):
        for pair in maketuple(keys):
            seq = []
            for key in pair:
                raise_on_unknown_key(key)
                events = ((e.EV_KEY, key, 1), (e.EV_KEY, key, 0))
                for ev in events:
                    seq.append(ev)

            yield tuple(seq)
