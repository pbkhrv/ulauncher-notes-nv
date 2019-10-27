"""
Notes search Ulauncher extension inspired by NotationalVelocity
"""
import os
import re
import subprocess
from ulauncher.api.client.Extension import Extension
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.event import KeywordQueryEvent, ItemEnterEvent
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.item.ExtensionSmallResultItem import ExtensionSmallResultItem
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.action.DoNothingAction import DoNothingAction
from ulauncher.api.shared.action.OpenAction import OpenAction

from .extension_method_caller import (
    call_extension_method,
    CallExtensionMethodEventListener,
)
from .search import search_notes
from .cmd_arg_utils import argbuild


MAX_RESULTS_VISIBLE = 10


def error_item(message):
    """
    Show small result item with error icon and a message.
    """
    return ExtensionSmallResultItem(
        icon="images/error.svg", name=message, on_action=DoNothingAction()
    )


def safe_filename(fn):
    """
    Remove characters from string that could cause problems if used in a filename
    """
    return re.sub(r"[^a-zA-Z0-9 _\-]", "", fn)


def contains_filename_match(matches, filename, extensions):
    """
    Whether search results contain given filename with one of possible extensions.
    """
    possible_fns = set(f"{filename.lower()}.{ext.lower()}" for ext in extensions)
    for match in matches:
        if match.filename_lower in possible_fns:
            return True
    return False


class NotesNvExtension(Extension):
    """ Extension class, coordinates everything """

    def __init__(self):
        super(NotesNvExtension, self).__init__()
        self.subscribe(KeywordQueryEvent, KeywordQueryEventListener())
        self.subscribe(ItemEnterEvent, CallExtensionMethodEventListener())

    def get_notes_path(self):
        """
        Notes directory path preference.
        """
        return os.path.expanduser(self.preferences["notes-directory-path"])

    def get_note_file_extensions(self):
        """
        Get list of notes file extensions from preferences.
        Stored as comma-separated list.
        """
        exts = self.preferences["file-extensions"]
        if not exts:
            exts = "txt,md"
        return exts.replace(" ", "").split(",")

    def create_note_action_item(self, query_arg, query_matches):
        """
        Construct "Create note" result item if new filename.

        Check list of matches to make sure the new filename doesnt exist already
        """
        # Split this up into "is_new_note_filename" and "create_note_action_item"
        new_note_title = safe_filename(query_arg)
        exts = self.get_note_file_extensions()
        if contains_filename_match(query_matches, new_note_title, exts):
            return None

        ext = exts[0]
        new_note_filename = f"{new_note_title}.{ext}"
        return ExtensionResultItem(
            icon="images/create-note.svg",
            name="Create note",
            description=new_note_filename,
            on_enter=call_extension_method(
                self.do_create_note,
                os.path.join(self.get_notes_path(), new_note_filename),
            ),
        )

    def process_search_query(self, arg):
        """
        Show results that match user's query.
        """
        matches = search_notes(
            self.get_notes_path(), self.get_note_file_extensions(), arg
        )

        items = []
        for match in matches[:MAX_RESULTS_VISIBLE]:
            item = ExtensionResultItem(
                icon="images/note.svg",
                name=match.filename,
                description=match.match_summary,
                on_enter=call_extension_method(
                    self.do_open_note,
                    os.path.join(self.get_notes_path(), match.filename),
                ),
            )
            items.append(item)

        create_note_item = self.create_note_action_item(arg, matches)
        if create_note_item:
            items.append(create_note_item)

        return RenderResultListAction(items)

    def process_empty_query(self):  # pylint: disable=no-self-use
        """
        Show something if query is empty
        """
        return RenderResultListAction(
            [
                ExtensionResultItem(
                    icon="images/notes-nv.svg",
                    name="Please enter search query...",
                    on_enter=DoNothingAction(),
                )
            ]
        )

    def do_create_note(self, path):  # pylint: disable=no-self-use
        """
        Create empty note file with given path and open it
        """
        with open(path, "x"):
            pass
        return OpenAction(path)

    def do_open_note(self, path):
        """
        Open note file using command specified in preferences
        or OpenAction() if no command specified
        """
        cmd = self.preferences["open-note-command"]
        if not cmd:
            return OpenAction(path)
        args = argbuild(cmd, {"fn": path}, append_missing_field="fn")
        subprocess.Popen(args)
        return DoNothingAction()


# pylint: disable=too-few-public-methods
class KeywordQueryEventListener(EventListener):
    """ KeywordQueryEventListener class manages user input """

    def on_event(self, event, extension):
        """
        Handle keyword query event.
        """
        # assuming only one ulauncher keyword
        arg = event.get_argument()
        if not arg:
            return extension.process_empty_query()
        return extension.process_search_query(arg)
