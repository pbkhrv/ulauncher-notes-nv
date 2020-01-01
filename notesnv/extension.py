"""
Notes search Ulauncher extension inspired by NotationalVelocity
"""
import os
import re
import subprocess
from typing import Optional, List
from ulauncher.api.client.Extension import Extension
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.event import KeywordQueryEvent, ItemEnterEvent
from ulauncher.api.shared.item.ResultItem import ResultItem
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.item.ExtensionSmallResultItem import ExtensionSmallResultItem
from ulauncher.api.shared.action.BaseAction import BaseAction
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.action.DoNothingAction import DoNothingAction
from ulauncher.api.shared.action.OpenAction import OpenAction
from ulauncher.api.shared.action.CopyToClipboardAction import CopyToClipboardAction

from .callable_action import callable_action, CallableEventListener
from .search import (
    search_notes,
    contains_filename_match,
    SearchError,
    ls_dir,
    SearchResultItem,
)
from .cmd_arg_utils import argbuild
from . import query_command
from .clipboard import GtkClipboard


MAX_RESULTS_VISIBLE = 10


def error_item(message: str, details: Optional[str] = None) -> ResultItem:
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


def note_filename_from_query(fn: str) -> str:
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
        self.clipboard = GtkClipboard()

    def get_notes_path(self) -> str:
        """
        Notes directory path preference.
        """
        return os.path.expanduser(self.preferences["notes-directory-path"])

    def get_note_file_extensions(self) -> List[str]:
        """
        Get list of notes file extensions from preferences.
        Stored as comma-separated list.
        """
        exts = self.preferences["file-extensions"]
        if not exts:
            exts = "txt,md"
        return exts.replace(" ", "").split(",")

    def can_be_new_note_title(
        self, query_arg: str, query_matches: List[SearchResultItem]
    ) -> bool:
        """
        Whether the search query can be turned into a new unique note title
        """
        new_note_title = note_filename_from_query(query_arg)
        if not new_note_title:
            return False

        exts = self.get_note_file_extensions()
        return not contains_filename_match(query_matches, new_note_title, exts)

    def new_note_filename(self, query_arg: str) -> str:
        """
        Construct a new note filename based on the search query
        """
        new_note_title = note_filename_from_query(query_arg)
        ext = self.get_note_file_extensions()[0]
        return f"{new_note_title}.{ext}"

    def item_create_empty_note(self, new_note_filename: str) -> ResultItem:
        """
        Construct "Create empty note" result item
        """
        return ExtensionResultItem(
            icon="images/create-note.svg",
            name="Create empty note",
            description=new_note_filename,
            on_enter=callable_action(
                self.create_empty_note,
                os.path.join(self.get_notes_path(), new_note_filename),
            ),
            highlightable=False,
        )

    def item_create_note_from_clipboard(self, new_note_filename: str) -> ResultItem:
        """
        Construct "Create note from clipboard" result item
        """
        return ExtensionResultItem(
            icon="images/create-note.svg",
            name="Create note from clipboard",
            description=new_note_filename,
            on_enter=callable_action(
                self.create_note_from_clipboard,
                os.path.join(self.get_notes_path(), new_note_filename),
            ),
            highlightable=False,
        )

    def items_open_note_command(
        self, matches: List[SearchResultItem], query: str
    ) -> List[ResultItem]:
        """
        Search result items for the "open note" command
        """
        items = []
        for match in matches[:MAX_RESULTS_VISIBLE]:
            item = ExtensionResultItem(
                icon="images/note.svg",
                name=match.filename,
                description=match.match_summary,
                on_enter=callable_action(
                    self.open_note, os.path.join(self.get_notes_path(), match.filename)
                ),
                on_alt_enter=callable_action(self.list_commands, match.filename),
            )
            items.append(item)

        # If the search query looks like a new unique note title,
        # offer to create the note
        if self.can_be_new_note_title(query, matches):
            fn = self.new_note_filename(query)
            items.append(self.item_create_empty_note(fn))
            items.append(self.item_create_note_from_clipboard(fn))

        return items

    def items_copy_note_command(
        self, matches: List[SearchResultItem]
    ) -> List[ResultItem]:
        """
        Search result items for the "copy to clipboard" command
        """
        items = []
        for match in matches[:MAX_RESULTS_VISIBLE]:
            item = ExtensionResultItem(
                icon="images/copy-note.svg",
                name=f"Copy: {match.filename}",
                description=match.match_summary,
                on_enter=callable_action(
                    self.copy_note, os.path.join(self.get_notes_path(), match.filename)
                ),
            )
            items.append(item)
        return items

    def process_search_query(self, arg: str) -> BaseAction:
        """
        Show results that match user's query.
        """
        qcmd = query_command.parse(arg)

        try:
            matches = search_notes(
                self.get_notes_path(),
                self.get_note_file_extensions(),
                qcmd.search_query,
            )
        except SearchError as exc:
            return RenderResultListAction([error_item(exc.message, exc.details)])

        if qcmd.cmd == "cp":
            items = self.items_copy_note_command(matches)
        else:
            items = self.items_open_note_command(matches, qcmd.search_query)

        return RenderResultListAction(items)

    def process_empty_query(self) -> BaseAction:
        """
        Show something if query is empty
        """
        try:
            recently_modified = ls_dir(
                self.get_notes_path(), self.get_note_file_extensions()
            )
        except SearchError as exc:
            return RenderResultListAction([error_item(exc.message, exc.details)])

        items = [
            ExtensionResultItem(
                icon="images/notes-nv.svg",
                name="Please enter search query...",
                on_enter=DoNothingAction(),
            )
        ]

        for fn in recently_modified[:MAX_RESULTS_VISIBLE]:
            items.append(
                ExtensionResultItem(
                    icon="images/note.svg",
                    name=fn,
                    on_enter=callable_action(
                        self.open_note, os.path.join(self.get_notes_path(), fn)
                    ),
                )
            )
        return RenderResultListAction(items)

    def create_empty_note(self, path: str) -> BaseAction:
        """
        Create empty note file at the given path and open it
        """
        try:
            with open(path, "x"):
                pass
        except OSError as exc:
            return RenderResultListAction(
                [error_item("Could not create note file", exc.strerror)]
            )
        return self.open_note(path)

    def create_note_from_clipboard(self, path: str) -> BaseAction:
        """
        Create a note file with the contents of the clipboard
        at the given path and open it
        """
        try:
            with open(path, "x") as f:
                text = self.clipboard.get_text()
                print(text, file=f)
        except OSError as exc:
            return RenderResultListAction(
                [error_item("Could not create note file", exc.strerror)]
            )
        return self.open_note(path)

    def open_note(self, path: str) -> BaseAction:
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

    def copy_note(self, path: str) -> BaseAction:  # pylint: disable=no-self-use
        """
        Copy the contents of note file into the clipboard
        """
        with open(path, "rt") as f:
            text = os.linesep.join(f.readlines())
        return CopyToClipboardAction(text)

    def list_commands(self, filename: str) -> BaseAction:
        """
        Show list of commands that can be run on the given note file
        """
        items = []
        items.append(
            ExtensionResultItem(
                icon="images/copy-note.svg",
                name="Copy note contents to clipboard",
                description=filename,
                on_enter=callable_action(
                    self.copy_note, os.path.join(self.get_notes_path(), filename)
                ),
                highlightable=False,
            )
        )
        return RenderResultListAction(items)


class NotesNvExtension(Extension):
    """
    Extension class, only exists to coordinate others
    """

    def __init__(self):
        super(NotesNvExtension, self).__init__()
        self.notesnv = NotesNv(self.preferences)
        self.subscribe(KeywordQueryEvent, KeywordQueryEventListener(self.notesnv))
        self.subscribe(ItemEnterEvent, CallableEventListener())


# pylint: disable=too-few-public-methods
class KeywordQueryEventListener(EventListener):
    """ KeywordQueryEventListener class manages user input """

    def __init__(self, notesnv):
        super(KeywordQueryEventListener, self).__init__()
        self.notesnv = notesnv

    def on_event(self, event, extension) -> BaseAction:
        """
        Handle keyword query event.
        """
        # assuming only one ulauncher keyword
        arg = event.get_argument()
        if not arg:
            return self.notesnv.process_empty_query()
        return self.notesnv.process_search_query(arg)
