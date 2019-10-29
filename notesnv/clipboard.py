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

    def get_text(self):
        """
        Get text from the clipboard

        :returns: contents of the clipboard
        """
        Gdk.threads_enter()
        text = self.clipboard.wait_for_text()
        Gdk.threads_leave()
        return text

    def set_text(self, text):
        """
        Copy text into the clipboard

        :param text: text to be copied into the clipboard
        """
        Gdk.threads_enter()
        self.clipboard.set_text(text, -1)
        Gdk.threads_leave()