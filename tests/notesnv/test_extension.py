import os
from unittest.mock import MagicMock
from notesnv import extension
from notesnv.search import SearchResultItem
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from utils import with_temp_dir


def test_filename_from_query():
    fn = extension.note_filename_from_query(":what ? this test!")
    # No double-spaces in the name
    assert fn.find("  ") == -1

    # No whitespaces in front or back
    assert fn[0] != " "
    assert fn[-1] != " "


def test_open_note_wrong_command():
    notesnv = extension.NotesNv({"open-note-command": "nosuchcommand_asdfasdf {fn}"})
    action = notesnv.open_note("/tmp/nothing.txt")
    assert isinstance(action, RenderResultListAction)
    assert len(action.result_list) == 1
    assert "Could not" in action.result_list[0].get_name()


@with_temp_dir()
def test_create_note(path):
    notesnv = extension.NotesNv({})
    notesnv.open_note = MagicMock()
    fn = os.path.join(path, "file.txt")
    notesnv.create_empty_note(fn)
    assert os.path.exists(fn)
    notesnv.open_note.assert_called_with(fn)


@with_temp_dir()
def test_create_note_wrong_path(path):
    notesnv = extension.NotesNv({})
    notesnv.open_note = MagicMock()
    bad_path = os.path.join(path, "nosuchdir_asdfasdf")
    fn = os.path.join(bad_path, "file.txt")
    action = notesnv.create_empty_note(fn)
    assert isinstance(action, RenderResultListAction)
    assert len(action.result_list) == 1
    assert "Could not" in action.result_list[0].get_name()
    notesnv.open_note.assert_not_called()


@with_temp_dir()
def test_empty_query_search_error(path):
    notesnv = extension.NotesNv(
        {"notes-directory-path": os.path.join(path, "nonono"), "file-extensions": "txt"}
    )
    action = notesnv.process_empty_query()
    assert isinstance(action, RenderResultListAction)
    assert len(action.result_list) == 1
    assert "Could not" in action.result_list[0].get_name()


@with_temp_dir(["hello.txt"])
def test_empty_query_ok(path):
    notesnv = extension.NotesNv(
        {"notes-directory-path": path, "file-extensions": "txt"}
    )
    action = notesnv.process_empty_query()
    assert isinstance(action, RenderResultListAction)
    assert len(action.result_list) == 2
    assert "query" in action.result_list[0].get_name()
    assert action.result_list[1].get_name() == "hello.txt"


def search_result_file(fn):
    return SearchResultItem(
        filename=fn,
        filename_lower=fn.lower(),
        match_content="",
        match_content_lower="",
        match_summary="",
    )


def test_new_note_title():
    notesnv = extension.NotesNv({"file-extensions": "txt"})
    assert notesnv.can_be_new_note_title("yes hello", [])
    assert not notesnv.can_be_new_note_title(
        "yes hello", [search_result_file("yes hello.txt")]
    )


def test_items_open_note_command():
    notesnv = extension.NotesNv(
        {"file-extensions": "txt", "notes-directory-path": "/tmp"}
    )
    items = notesnv.items_open_note_command(
        [search_result_file("yes hello.txt")], "but why"
    )
    # expecting 3 items: one search result and two "create note" actions
    assert len(items) == 3
    assert any(i for i in items if i.get_name() == "yes hello.txt")
    assert len(list(i for i in items if "Create" in i.get_name())) == 2
