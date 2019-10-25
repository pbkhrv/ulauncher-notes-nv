import os
import re
from ulauncher.api.client.Extension import Extension
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.event import (
    KeywordQueryEvent,
    ItemEnterEvent,
)
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.item.ExtensionSmallResultItem import ExtensionSmallResultItem
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.action.ExtensionCustomAction import ExtensionCustomAction
from ulauncher.api.shared.action.DoNothingAction import DoNothingAction
from ulauncher.api.shared.action.OpenAction import OpenAction

from .search import search_notes


MAX_RESULTS_VISIBLE = 10


def error_item(message):
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


class NotesNvExtension(Extension):
    """ Extension class, coordinates everything """

    def __init__(self):
        super(NotesNvExtension, self).__init__()
        self.subscribe(KeywordQueryEvent, KeywordQueryEventListener())
        self.subscribe(ItemEnterEvent, ItemEnterEventListener())

    def get_notes_path(self):
        return os.path.expanduser(self.preferences["notes-directory-path"])

    def get_note_file_extensions(self):
        return ["txt", "md"]

    def create_note_action_item(self, query_arg, query_matches):
        new_note_title = safe_filename(query_arg)
        exts = self.get_note_file_extensions()
        if not contains_filename_match(query_matches, new_note_title, exts):
            ext = exts[0]
            new_note_filename = f"{new_note_title}.{ext}"
            return ExtensionResultItem(
                icon="images/create-note.svg",
                name="Create note",
                description=new_note_filename,
                on_enter=ExtensionCustomAction(
                    {
                        "action": "create_note",
                        "path": os.path.join(self.get_notes_path(), new_note_filename),
                    }
                ),
            )

    def process_search_kw_arg_query(self, kw, arg):
        matches = search_notes(
            self.get_notes_path(), self.get_note_file_extensions(), arg
        )

        items = []
        for m in matches[:MAX_RESULTS_VISIBLE]:
            item = ExtensionResultItem(
                icon="images/note.svg",
                name=m.filename,
                description=m.match_summary,
                on_enter=OpenAction(os.path.join(self.get_notes_path(), m.filename)),
            )
            items.append(item)

        create_note_item = self.create_note_action_item(arg, matches)
        if create_note_item:
            items.append(create_note_item)

        return RenderResultListAction(items)

    def process_empty_query(self, kw):
        return RenderResultListAction(
            [
                ExtensionResultItem(
                    icon="images/notes-nv.svg",
                    name="Please enter search query...",
                    on_enter=DoNothingAction(),
                )
            ]
        )

    def do_create_note(self, path):
        """
        Create empty note file with given path and open it
        """
        try:
            fd = open(path, "x")
            fd.close()
            print(path)
            return OpenAction(path)
        except Exception:
            return RenderResultListAction(
                [error_item(f"Cannot create note file {path}")]
            )


class KeywordQueryEventListener(EventListener):
    """ KeywordQueryEventListener class manages user input """

    def on_event(self, event, extension):
        # assuming only one ulauncher keyword
        kw = event.get_keyword()
        arg = event.get_argument()
        if arg:
            return extension.process_search_kw_arg_query(kw, arg)
        else:
            return extension.process_empty_query(kw)


class ItemEnterEventListener(EventListener):
    """ Handle custom actions """

    def on_event(self, event, extension):
        """
        Handle custom "item enter" events:

        - Create note
        """
        data = event.get_data()
        if data["action"] == "create_note":
            return extension.do_create_note(data["path"])
