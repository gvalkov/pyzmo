import logging
import subprocess
import sys
from unittest.mock import Mock

import pytest
from evdev import InputEvent
from evdev import ecodes as e

from pyzmo import EventHandler

UP, DOWN, HOLD = 0, 1, 2


def feed(handler, *events, start=0.0, step=0.01):
    """Send (code, value) key events, or (type, code, value) events, to a handler."""
    for n, ev in enumerate(events):
        etype, code, value = ev if len(ev) == 3 else (e.EV_KEY, *ev)
        sec, usec = divmod(round((start + n * step) * 1_000_000), 1_000_000)
        handler.process_event(InputEvent(sec, usec, etype, code, value))


def tap(code):
    return (code, DOWN), (code, UP)


@pytest.fixture
def handler():
    return EventHandler("test")


def codes(events):
    return [(ev.code, ev.value) for ev in events]


class TestKey:
    def test_default_state_is_down(self, handler):
        cb = Mock()
        handler.key(e.KEY_B)(cb)

        feed(handler, (e.KEY_C, DOWN), (e.KEY_B, DOWN), (e.KEY_B, HOLD), (e.KEY_B, UP))

        cb.assert_called_once()
        assert codes(cb.call_args.args[0]) == [(e.KEY_B, DOWN)]

    def test_states(self, handler):
        cb = Mock()
        handler.key(e.KEY_B, states=["down", "up"])(cb)

        feed(handler, (e.KEY_B, DOWN), (e.KEY_B, HOLD), (e.KEY_B, UP))

        assert [codes(c.args[0]) for c in cb.call_args_list] == [
            [(e.KEY_B, DOWN)],
            [(e.KEY_B, UP)],
        ]

    def test_single_state_string(self, handler):
        cb = Mock()
        handler.key(e.KEY_B, states="up")(cb)

        feed(handler, *tap(e.KEY_B))

        assert codes(cb.call_args.args[0]) == [(e.KEY_B, UP)]

    @pytest.mark.parametrize("states", [["pressed"], ["down", "bogus"], []])
    def test_invalid_states(self, handler, states):
        with pytest.raises(ValueError, match="Invalid key states"):
            handler.key(e.KEY_B, states=states)


class TestChord:
    def test_fires_when_last_key_pressed_while_others_held(self, handler):
        cb = Mock()
        handler.chord(e.KEY_LEFTCTRL, e.KEY_LEFTALT, e.KEY_DELETE)(cb)

        feed(
            handler, (e.KEY_LEFTCTRL, DOWN), (e.KEY_LEFTALT, DOWN), (e.KEY_DELETE, DOWN)
        )

        cb.assert_called_once()
        assert codes(cb.call_args.args[0]) == [
            (e.KEY_LEFTCTRL, DOWN),
            (e.KEY_LEFTALT, DOWN),
            (e.KEY_DELETE, DOWN),
        ]

    def test_modifiers_in_any_order(self, handler):
        cb = Mock()
        handler.chord(e.KEY_LEFTCTRL, e.KEY_LEFTALT, e.KEY_DELETE)(cb)

        feed(
            handler, (e.KEY_LEFTALT, DOWN), (e.KEY_LEFTCTRL, DOWN), (e.KEY_DELETE, DOWN)
        )

        cb.assert_called_once()

    def test_modifier_autorepeat(self, handler):
        cb = Mock()
        handler.chord(e.KEY_LEFTCTRL, e.KEY_C)(cb)

        feed(
            handler,
            (e.KEY_LEFTCTRL, DOWN),
            (e.KEY_LEFTCTRL, HOLD),
            (e.KEY_LEFTCTRL, HOLD),
            (e.KEY_C, DOWN),
        )

        cb.assert_called_once()

    def test_released_key_is_not_part_of_chord(self, handler):
        """Regression: chords used to match keys pressed at any earlier time."""
        cb = Mock()
        handler.chord(e.KEY_LEFTCTRL, e.KEY_LEFTALT)(cb)

        feed(handler, *tap(e.KEY_LEFTCTRL), *tap(e.KEY_B), (e.KEY_LEFTALT, DOWN))

        cb.assert_not_called()

    def test_last_key_must_be_pressed_last(self, handler):
        cb = Mock()
        handler.chord(e.KEY_LEFTCTRL, e.KEY_C)(cb)

        feed(handler, (e.KEY_C, DOWN), (e.KEY_LEFTCTRL, DOWN))

        cb.assert_not_called()

    def test_fires_again_while_modifiers_held(self, handler):
        cb = Mock()
        handler.chord(e.KEY_LEFTCTRL, e.KEY_C)(cb)

        feed(handler, (e.KEY_LEFTCTRL, DOWN), *tap(e.KEY_C), *tap(e.KEY_C))

        assert cb.call_count == 2


class TestKeySequence:
    def test_fires_on_complete_sequence(self, handler):
        cb = Mock()
        handler.keyseq(e.KEY_A, e.KEY_B, e.KEY_C)(cb)

        feed(handler, *tap(e.KEY_A), *tap(e.KEY_B), *tap(e.KEY_C))

        cb.assert_called_once()
        assert codes(cb.call_args.args[0]) == [
            *tap(e.KEY_A),
            *tap(e.KEY_B),
            *tap(e.KEY_C),
        ]
        assert handler.trigger_events == {}

    def test_unrelated_key_resets_sequence(self, handler):
        """Regression: partial matches used to survive unrelated key presses."""
        cb = Mock()
        handler.keyseq(e.KEY_A, e.KEY_B)(cb)

        feed(handler, *tap(e.KEY_A), *tap(e.KEY_C), *tap(e.KEY_B))

        cb.assert_not_called()

    def test_repeated_first_key_restarts_sequence(self, handler):
        cb = Mock()
        handler.keyseq(e.KEY_A, e.KEY_B)(cb)

        feed(handler, *tap(e.KEY_A), *tap(e.KEY_A), *tap(e.KEY_B))

        cb.assert_called_once()

    def test_autorepeat_and_other_events_are_ignored(self, handler):
        cb = Mock()
        handler.keyseq(e.KEY_A, e.KEY_B)(cb)

        feed(
            handler,
            (e.KEY_A, DOWN),
            (e.KEY_A, HOLD),
            (e.KEY_LEFTSHIFT, UP),
            (e.EV_REL, e.REL_WHEEL, 1),
            (e.KEY_A, UP),
            *tap(e.KEY_B),
        )

        cb.assert_called_once()

    def test_timeout(self, handler):
        cb = Mock()
        handler.keyseq(e.KEY_A, e.KEY_B, timeout=0.5)(cb)

        feed(handler, *tap(e.KEY_A), start=0)
        feed(handler, *tap(e.KEY_B), start=10)
        cb.assert_not_called()

        feed(handler, *tap(e.KEY_A), *tap(e.KEY_B), start=20, step=0.1)
        cb.assert_called_once()

    def test_sequences_progress_independently(self, handler):
        ab, ac = Mock(), Mock()
        handler.keyseq(e.KEY_A, e.KEY_B)(ab)
        handler.keyseq(e.KEY_A, e.KEY_C)(ac)

        feed(handler, *tap(e.KEY_A))
        handler.key(e.KEY_X)(Mock())  # registering a new trigger keeps the progress
        feed(handler, *tap(e.KEY_C))

        ab.assert_not_called()
        ac.assert_called_once()


class TestHandler:
    def test_event(self, handler):
        cb = Mock()
        handler.event(e.EV_REL, e.REL_WHEEL, -1)(cb)

        feed(handler, (e.EV_REL, e.REL_WHEEL, 1), (e.EV_REL, e.REL_WHEEL, -1))

        cb.assert_called_once()

    def test_quick_stops_processing(self, handler):
        first, second = Mock(), Mock()
        handler.chord(e.KEY_LEFTCTRL, e.KEY_V, quick=True)(first)
        handler.key(e.KEY_V)(second)

        feed(handler, (e.KEY_LEFTCTRL, DOWN), (e.KEY_V, DOWN))

        first.assert_called_once()
        second.assert_not_called()

    def test_filter_passes_key_events_and_handled_events(self, handler):
        handler.key(e.KEY_A)(Mock())
        handler.event(e.EV_REL, e.REL_WHEEL, 1)(Mock())
        handler.create_filters()

        events = [
            InputEvent(0, 0, e.EV_KEY, e.KEY_Z, 1),
            InputEvent(0, 0, e.EV_REL, e.REL_WHEEL, 1),
            InputEvent(0, 0, e.EV_REL, e.REL_X, 1),
            InputEvent(0, 0, e.EV_SYN, e.SYN_REPORT, 0),
        ]

        assert [(ev.type, ev.code) for ev in handler.filter(events)] == [
            (e.EV_KEY, e.KEY_Z),
            (e.EV_REL, e.REL_WHEEL),
        ]

    def test_import_does_not_configure_logging(self):
        """Regression: importing pyzmo used to call logging.basicConfig(level=DEBUG)."""
        code = "import logging, pyzmo; root = logging.getLogger(); print(len(root.handlers), root.level)"
        out = subprocess.run(
            [sys.executable, "-c", code], capture_output=True, text=True, check=True
        )
        assert out.stdout.split() == ["0", str(logging.WARNING)]
