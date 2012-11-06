import logging

from select import select
from functools import partial
from collections import defaultdict, OrderedDict

from evdev import InputDevice
from pyzmo import decorators, util


log = logging.getLogger('handler')


class EventHandler:
    def __init__(self, name):
        self.name = name

        #: mapping of event sequences to (callback, options)
        #: ex: { ((EV_KEY, KEY_1, 1), (EV_KEY, KEY_2, 1)) : (callback, {'quick' : True}) }
        self.triggers = OrderedDict()

        # event decorators
        self.event  = partial(decorators.EventDecorator, self.triggers)
        self.key    = partial(decorators.KeyDecorator, self.triggers)
        self.chord  = partial(decorators.ChordDecorator, self.triggers)
        self.keyseq = partial(decorators.SequenceDecorator, self.triggers)

        self.handled_types = set()  #: event types this handler is interested in
        self.handled_codes = set()  #: event codes this handler is interested in

        self.trigger_position = defaultdict(int)
        self.trigger_events = defaultdict(list)

    def filter(self, events):
        '''Filter events that are of no interest to this handler.'''
        ht, hc = self.handled_types, self.handled_codes

        for ev in events:
            if (ev.type in ht) and (ev.code in hc):
                yield ev

    def create_filters(self):
        '''Populate ``handled_types`` and ``handled_codes``.'''
        for trigger in self.triggers:
            for ev in trigger:
                if callable(ev): break
                self.handled_types.add(ev[0])
                self.handled_codes.add(ev[1])

    def process_event(self, ev):
        '''Process a single event.'''
        evkey = (ev.type, ev.code, ev.value)

        # iterate through all triggers set through @key, @chord etc
        for n, key in enumerate(self.triggers):
            # the position within the event sequence for the current trigger
            pos = self.trigger_position[n]

            if key[pos] == evkey:
                self.trigger_events[n].append(ev)
                self.trigger_position[n] += 1

                # carry on if more events have been processed than the
                # length of the current trigger.
                if self.trigger_position[n] > len(key):
                    self.trigger_position[n] = 0
                    del self.trigger_events[n]
                    continue

                # sequence of events matched
                if self.trigger_position[n] == len(key):
                    func, options = self.triggers[key]
                    func(self.trigger_events[n])

                    self.trigger_position[n] = 0
                    del self.trigger_events[n]

                    if options.get('quick', False):
                        break
                    
                    continue

    def poll(self, *fns):
        '''Read and react to input events.'''

        makedev = lambda x: x if isinstance(x, InputDevice) else InputDevice(x)
        devices = map(makedev, fns)
        devices = {dev.fd : dev for dev in devices}

        self.create_filters()
        log.debug('Handled event types: %s', self.handled_types)
        log.debug('Handled event codes: %s', self.handled_codes)

        log.debug('Registered triggers:\n%s',
                  '\n'.join(util.describe_triggers(self.triggers)))

        for dev in devices.values():
            log.info('Listening on device: %s', dev)

        log.info('Entering main-loop ...')
        while True:
            r,w,x = select(devices, [], [])
            for fd in r:
                for ev in self.filter(devices[fd].read()):
                    self.process_event(ev)
