import functools
from pyzmo.handler import EventHandler
from evdev import ecodes


default_handler = EventHandler('default-handler')

def default_handler_wrap(name):
    'Return a callable that relays calls to a default handler.'

    # @functools.wraps(getattr(default_handler, name))
    def wrapper(*args, **kw):
        return getattr(default_handler, name)(*args, **kw)

    return wrapper

key    = default_handler_wrap('key')
chord  = default_handler_wrap('chord')
keyseq = default_handler_wrap('keyseq')
event  = default_handler_wrap('event')
poll   = default_handler_wrap('poll')


__all__ = ('key', 'chord', 'keyseq', 'event', 'poll', 'default_handler',
           'EventHandler', 'ecodes')
