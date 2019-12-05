"""
Utilities to work with the Gtk clipboard
"""
import gi

gi.require_version("Gtk", "3.0")
# pylint: disable=wrong-import-position
from gi.repository import Gtk, Gdk  # noqa: E402


class GtkClipboard:
    """
    Access clipboard through Gtk
    """

    def __init__(self):
        self.clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)

    def get_text(self) -> str:
        """
        Get text from the clipboard

        :returns: contents of the clipboard
        """
        return self.clipboard.wait_for_text()

    def set_text(self, text: str) -> None:
        """
        Copy text into the clipboard

        :param text: text to be copied into the clipboard
        """
        self.clipboard.set_text(text, -1)
        self.clipboard.store()

    def is_text_available(self) -> bool:
        """
        Whether there is anything in the clipboard that can be returned as text
        """
        return self.clipboard.wait_is_text_available()
