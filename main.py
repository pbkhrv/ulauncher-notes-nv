import os
from datetime import datetime, timedelta
from operator import attrgetter, itemgetter
from ulauncher.api.client.Extension import Extension
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.event import (
    KeywordQueryEvent,
    ItemEnterEvent,
    PreferencesUpdateEvent,
)
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.item.ExtensionSmallResultItem import ExtensionSmallResultItem
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.action.ExtensionCustomAction import ExtensionCustomAction
from ulauncher.api.shared.action.SetUserQueryAction import SetUserQueryAction
from ulauncher.api.shared.action.DoNothingAction import DoNothingAction
from ulauncher.api.shared.action.OpenAction import OpenAction

from search import search_note_file_contents


MAX_RESULTS_VISIBLE = 10


class NotesNvExtension(Extension):
    """ Extension class, coordinates everything """

    def __init__(self):
        super(NotesNvExtension, self).__init__()
        self.subscribe(KeywordQueryEvent, KeywordQueryEventListener())
        self.subscribe(ItemEnterEvent, ItemEnterEventListener())
        # self.subscribe(PreferencesUpdateEvent, PreferencesUpdateEventListener())

    def get_notes_path(self):
        return self.preferences["notes-directory-path"]

    def get_note_file_globs(self):
        return ["*.txt", "*.md"]

    def process_search_kw_arg_query(self, kw, arg):
        notes_path = os.path.expanduser(self.get_notes_path())
        matches = search_note_file_contents(
            notes_path, self.get_note_file_globs(), arg
        )
        matches = matches[:MAX_RESULTS_VISIBLE]

        items = []
        for m in matches:
            item = ExtensionResultItem(
                icon="images/empty.png",
                name=m.filename,
                description=m.match_summary,
                on_enter=OpenAction(os.path.join(notes_path, m.filename)),
            )
            items.append(item)
        return RenderResultListAction(items)

    def process_empty_query(self, kw):
        return RenderResultListAction(
            [
                ExtensionResultItem(
                    icon="images/empty.png", name="Nothing", on_enter=DoNothingAction()
                )
            ]
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
        pass


class PreferencesUpdateEventListener(EventListener):
    """ Handle preferences updates """

    def on_event(self, event, extension):
        if event.new_value != event.old_value:
            if event.id == "zeal-docsets-path":
                extension.reload_docsets()


if __name__ == "__main__":
    NotesNvExtension().run()
