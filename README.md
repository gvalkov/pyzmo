# Pyzmo

<p>
    <a href="https://pypi.python.org/pypi/pyzmo"><img alt="pypi version" src="https://img.shields.io/pypi/v/pyzmo.svg"></a>
    <a href="https://github.com/gvalkov/pyzmo/blob/main/LICENSE"><img alt="License" src="https://img.shields.io/pypi/l/pyzmo"></a>
</p>

Pyzmo is a small hotkey library based on [python-evdev]. It can call
arbitrary Python functions in response to key presses, key chords
(simultaneously pressed keys) and key sequences (keys pressed in
succession).

## Usage (Python)

``` python
from pyzmo import *
from evdev.ecodes import *

# triggered when KEY_PLAYPAUSE is pressed
@key(KEY_PLAYPAUSE)
def playpause(events):
    pass

# triggered when KEY_B is pressed, held or released
@key(KEY_B, states=['down', 'hold', 'up'])
def back(events):
    pass

# triggered when either KEY_C or KEY_D are pressed
@key(KEY_C, KEY_D)
def c_or_d(events):
    pass

# triggered when KEY_DELETE is pressed while KEY_LEFTCTRL and
# KEY_LEFTALT are held down (in any order)
@chord(KEY_LEFTCTRL, KEY_LEFTALT, KEY_DELETE)
def ctrlaltdel(events):
    pass

# triggered when KEY_A, KEY_B and KEY_C are pressed one after the other
# (pressing any other key starts the sequence over)
@keyseq(KEY_A, KEY_B, KEY_C)
def abc(events):
    pass

# same, but with at most 1 second between key events
@keyseq(KEY_X, KEY_Y, timeout=1.0)
def xy(events):
    pass

# specifying multiple sequences for one callback (syntax applies for
# @chord and @event as well)
@keyseq( (KEY_1, KEY_2, KEY_3), (KEY_Z, KEY_X, KEY_C) )
def zxc_or_123(events):
    pass

# each handler receives the list of input events, because of
# which it was triggered
@chord(e.KEY_LEFTMETA, e.KEY_A)
def term(events):
    for event in events:
        print(event)  # instance of evdev.events.InputEvent
        #event at 1352244701.749908, code 125, type 01, val 01
        #event at 1352244701.861897, code 30, type 01, val 01

## Note 1:
# If we define two triggers:
#  - @chord(KEY_LEFTCTRL, KEY_V)
#  - @key(KEY_V)
#
# Pressing 'ctrl-v' will run both their callbacks. To stop
# processing any further triggers after a match is made, use:
@chord(KEY_LEFTCTRL, KEY_V, quick=True)
def copy(events):
    pass

## Note 2:
# Pyzmo can actually match arbitrary input events. The following
# will be triggered on scroll-wheel movement:
@event(EV_REL, REL_WHEEL, -1)
def vertical_scroll(events):
    pass

# start main loop
poll('/dev/input/event1', '/dev/input/event2')

# .. or if you wish to get exclusive access to a input device
from evdev import InputDevice
dev = InputDevice('/dev/input/eventX')
dev.grab()
poll(dev)
```

You can also avoid polluting the global namespace with:

``` python
from pyzmo import EventHandler
from evdev import ecodes as e

app = EventHandler('name')

@app.key(e.KEY_F)
def f(events): pass

@app.poll(...)
```

Pyzmo logs to the `pyzmo` logger and does not configure logging. To
see the registered triggers and device messages, enable logging in
your script:

``` python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Usage (Hy)

Pyzmo also has a DSL that can be used from [Hy], which is a dialect of
lisp that is embedded in Python.

``` hylang
(require pyzmo.dsl)
(import pyzmo [pyzmo [poll util]])

# triggered when KEY_PLAYPAUSE is pressed
(key PLAYPAUSE (print events))

# triggered when KEY_B is pressed, held or released
(key B [:down :hold :up] (print events))

# triggered when either KEY_C or KEY_D are pressed
(key [C D] (print events))

# triggered when KEY_LEFTCTRL, KEY_LEFTALT and KEY_DELETE are
# pressed at the same time
(chord [LEFTCTRL LEFTALT DELETE] (print events))

# triggered when KEY_A, KEY_B and KEY_C are pressed one after the other
(seq [A B C] (print events))

# start main loop
(poll "/dev/input/eventX" "/dev/input/eventY")
```

## Development

The project uses [uv] for packaging and dependency management.

``` bash
$ uv sync          # create .venv and install all dependencies
$ uv run example.py # run a script in the environment
$ uv run ruff check
$ uv build         # build sdist and wheel into dist/
```

## Similar Projects

-   [triggerhappy]
-   [actkbd]
-   [inputexec]

## License

Pyzmo is released under the terms of the [Revised BSD License].

[uv]: https://docs.astral.sh/uv/

  [python-evdev]: https://github.com/gvalkov/python-evdev.git
  [Hy]: http://docs.hylang.org/en/stable/
  [triggerhappy]: https://github.com/wertarbyte/triggerhappy.git
  [actkbd]: http://users.softlab.ece.ntua.gr/~thkala/projects/actkbd/
  [inputexec]: https://github.com/rbarrois/inputexec
  [Revised BSD License]: https://raw.github.com/gvalkov/pyzmo/master/LICENSE
