"""
Call Ulauncher extension method from ExtensionCustomAction event listener
"""
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.action.ExtensionCustomAction import ExtensionCustomAction


def call_method_action(method, *args):
    """
    Encode the method and parameters to be called by the event listener
    """
    return ExtensionCustomAction((method.__name__, args), keep_app_open=True)


# pylint: disable=too-few-public-methods
class CallExtensionMethodEventListener(EventListener):
    """
    Call `extension`'s method the way it was passed via `call_method_action`
    """

    def on_event(self, event, extension):
        method_name, args = event.get_data()
        method = getattr(extension, method_name)
        return method(*args)


# pylint: disable=too-few-public-methods
class CallObjectMethodEventListener(EventListener):
    """
    Call `obj`'s method the way it was passed via `call_extension_method`
    """

    def __init__(self, obj):
        super(CallObjectMethodEventListener, self).__init__()
        self.obj = obj

    def on_event(self, event, extension):
        method_name, args = event.get_data()
        method = getattr(self.obj, method_name)
        return method(*args)
