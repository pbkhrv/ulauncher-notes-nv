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

from .extension_method_caller import call_method_action, CallObjectMethodEventListener
from .search import search_notes, contains_filename_match, SearchError
from .cmd_arg_utils import argbuild


MAX_RESULTS_VISIBLE = 10


def error_item(message, details=None):
    """
    Show small result item with error icon and a message.
    """
    if not details:
        return ExtensionSmallResultItem(
            icon="images/error.svg", name=message, on_enter=DoNothingAction()
        )

    return ExtensionResultItem(
        icon="images/error.svg",
        name=message,
        description=details,
        on_enter=DoNothingAction(),
    )


def note_filename_from_query(fn):
    """
    Remove characters from note title that could cause filename problems
    """
    fn = re.sub(r"[^a-zA-Z0-9 _\-]", "", fn)
    fn = re.sub(r"\s+", " ", fn)
    fn = re.sub(r"^\s+", "", fn)
    fn = re.sub(r"\s+$", "", fn)
    return fn


class NotesNv:
    """
    Main logic of the extension. Responsible for the following:
    - handling of user queries
    - searching of notes
    - creation of notes
    - error reporting
    """

    def __init__(self, preferences):
        self.preferences = preferences

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
        new_note_title = note_filename_from_query(query_arg)
        if not new_note_title:
            return None

        exts = self.get_note_file_extensions()
        if contains_filename_match(query_matches, new_note_title, exts):
            return None

        ext = exts[0]
        new_note_filename = f"{new_note_title}.{ext}"
        return ExtensionResultItem(
            icon="images/create-note.svg",
            name="Create note",
            description=new_note_filename,
            on_enter=call_method_action(
                self.do_create_note,
                os.path.join(self.get_notes_path(), new_note_filename),
            ),
        )

    def process_search_query(self, arg):
        """
        Show results that match user's query.
        """
        try:
            matches = search_notes(
                self.get_notes_path(), self.get_note_file_extensions(), arg
            )
        except SearchError as exc:
            return RenderResultListAction([error_item(exc.message, exc.details)])

        items = []
        for match in matches[:MAX_RESULTS_VISIBLE]:
            item = ExtensionResultItem(
                icon="images/note.svg",
                name=match.filename,
                description=match.match_summary,
                on_enter=call_method_action(
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
        try:
            with open(path, "x"):
                pass
        except OSError as exc:
            return RenderResultListAction(
                [error_item("Could not create note file", exc.strerror)]
            )
        return self.do_open_note(path)

    def do_open_note(self, path):
        """
        Open note file using command specified in preferences
        or OpenAction() if no command specified
        """
        cmd = self.preferences["open-note-command"]
        if not cmd:
            return OpenAction(path)
        args = argbuild(cmd, {"fn": path}, append_missing_field="fn")
        try:
            subprocess.Popen(args)
        except OSError as exc:
            return RenderResultListAction(
                [error_item("Could not execute note open command", exc.strerror)]
            )

        return DoNothingAction()


class NotesNvExtension(Extension):
    """
    Extension class, only exists to coordinate others
    """

    def __init__(self):
        super(NotesNvExtension, self).__init__()
        self.notesnv = NotesNv(self.preferences)
        self.subscribe(KeywordQueryEvent, KeywordQueryEventListener(self.notesnv))
        self.subscribe(ItemEnterEvent, CallObjectMethodEventListener(self.notesnv))


# pylint: disable=too-few-public-methods
class KeywordQueryEventListener(EventListener):
    """ KeywordQueryEventListener class manages user input """

    def __init__(self, notesnv):
        super(KeywordQueryEventListener, self).__init__()
        self.notesnv = notesnv

    def on_event(self, event, extension):
        """
        Handle keyword query event.
        """
        # assuming only one ulauncher keyword
        arg = event.get_argument()
        if not arg:
            return self.notesnv.process_empty_query()
        return self.notesnv.process_search_query(arg)
