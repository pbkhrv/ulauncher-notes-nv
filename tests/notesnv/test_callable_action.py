from ulauncher.api.shared.event import ItemEnterEvent
from notesnv.callable_action import callable_action, CallableEventListener


class Recorder:
    """
    Record last method call and args
    """

    def __init__(self):
        self.was_called = False
        self.arg = None
        self.kwarg = None

    def foo(self, arg, kwarg=None):
        """
        Record this method
        """
        self.was_called = True
        self.arg = arg
        self.kwarg = kwarg


def test_callable_is_called():
    obj = Recorder()
    assert not obj.was_called

    action = callable_action(obj.foo, "arg", kwarg="kwarg")
    event_listener = CallableEventListener()
    event_listener.on_event(ItemEnterEvent(action._data), None)

    assert obj.was_called
    assert obj.arg == "arg"
    assert obj.kwarg == "kwarg"


def test_right_callable_is_called():
    right = Recorder()
    wrong = Recorder()
    assert not right.was_called
    assert not wrong.was_called

    right_action = callable_action(right.foo, "arg", kwarg="kwarg")
    wrong_action = callable_action(wrong.foo, "arg", kwarg="kwarg")  # noqa: F841
    event_listener = CallableEventListener()
    event_listener.on_event(ItemEnterEvent(right_action._data), None)

    assert right.was_called
    assert not wrong.was_called
