from evdev import ecodes as e


def maketuple(arg):
    if len(arg) and isinstance(arg[0], tuple):
        return tuple(arg)
    else:
        return (arg,)

def raise_on_unknown_key(key):
    if key not in e.keys:
        msg = 'Unknown KEY or BTN event code passed to decorator: {}'
        raise ValueError(msg.format(key))
    
def describe_triggers(triggers):
    '''Verbosely describe a trigger dictionary.'''

    keystate = {0:'up', 1:'down', 2:'hold'}

    def _fmt_event(ev):
        if ev[0] == e.EV_KEY:
            keyname = e.KEY[ev[1]].split('KEY_')[-1]
            return 'key %s (%s) %s (%s)' % (keyname, ev[1], keystate[ev[2]], ev[1])
        else:
            return 'event {} {} {}'.format(e.EV[ev[0]], ev[1], ev[2])

    for trigger, func in triggers.items():
        for n,i in enumerate(trigger):
            indent = '+%s' % ' '*(n+1) if n==0 else ' '*(n+2)
            yield '%s%s' % (indent, _fmt_event(i))
        
        yield '%s func %s() at %s\n' % (' '*(n+2), func[0].__name__, id(func[0]))
