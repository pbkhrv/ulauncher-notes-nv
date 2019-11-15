"""
Execute a callable from ExtensionCustomAction event listener
"""
from collections import OrderedDict
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.action.ExtensionCustomAction import ExtensionCustomAction


__all__ = ["callable_action", "CallableEventListener"]


class LRU(OrderedDict):
    """
    Limit size, evicting the least recently looked-up key when full

    Borrowed from Python 3 docs.
    """

    def __init__(self, *args, maxsize=128, **kwds):
        self.maxsize = maxsize
        super().__init__(*args, **kwds)

    def __getitem__(self, key):
        value = super().__getitem__(key)
        self.move_to_end(key)
        return value

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        if len(self) > self.maxsize:
            oldest = next(iter(self))
            del self[oldest]


class Cache:
    """
    Simple dict-like cache with 'add' and 'get' operations
    """

    def __init__(self):
        self.cache = LRU(maxsize=128)

    def add(self, item):
        """
        Add item to the cache and return the key by which it can be retrieved later
        """
        key = id(item)
        self.cache[key] = item
        return key

    def get(self, key):
        """
        Retrieve item given its key or return None if not found
        """
        return self.cache.get(key, None)


_CALLABLE_CACHE = Cache()


def callable_action(func, *args, **keywords):
    """
    Call specified callable with specified arguments from a ItemEnterEvent listener

    Because extension actions are implemented by pickling data and sending it
    to and from the main Ulauncher process, you cannot pass to `on_enter` anything
    other than BaseAction subclasses defined by the Ulauncher itself.
    If you have a callable you need to execute in `on_enter`,
    it must somehow be encoded as picklable data in ExtensionCustomAction
    and then received and processed as `data` in an ItemEnterEvent listener.
    This utility function lets you shortcut some of that process - pass the callable
    that you want to call and all its parameters.
    Its companion class CallableEventListner (that you need to register
    in your extension), will make sure to call the callable that you specified
    whenever it receives the ItemEnterEvent.
    Usage:
        >>> from ulauncher.api.shared.item.ExtensionSmallResultItem import ExtensionSmallResultItem
        >>> SOME_RESULT_ITEM = ExtensionSmallResultItem(
        ...   icon="images/replace.svg",
        ...   name="Replace a's with b's!",
        ...   on_enter=callable_action("asdf".replace, "a", "b"),
        ... )
    """  # noqa: E501
    assert callable(func)
    func_key = _CALLABLE_CACHE.add(func)
    return ExtensionCustomAction((func_key, args, keywords), keep_app_open=True)


# pylint: disable=too-few-public-methods
class CallableEventListener(EventListener):
    """
    Companion class that makes callable_action work.
    You must subscribe an instance of this class to receive ItemEnterEvent:
    `self.subscribe(ItemEnterEvent, CallableEventListener())`
    """

    def on_event(self, event, _):
        data = event.get_data()
        if isinstance(data, tuple) and len(data) == 3 and isinstance(data[0], int):
            func_key, args, keywords = data
            func = _CALLABLE_CACHE.get(func_key)
            if func and callable(func):
                return func(*args, **keywords)
        return None
