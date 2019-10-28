import os
from unittest.mock import MagicMock
from notesnv import extension
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from utils import with_temp_dir


def test_filename_from_query():
    fn = extension.note_filename_from_query(":what ? this test!")
    # No double-spaces in the name
    assert fn.find("  ") == -1

    # No whitespaces in front or back
    assert fn[0] != " "
    assert fn[-1] != " "


def test_do_open_note_wrong_command():
    notesnv = extension.NotesNv({"open-note-command": "nosuchcommand_asdfasdf {fn}"})
    action = notesnv.do_open_note("/tmp/nothing.txt")
    assert isinstance(action, RenderResultListAction)
    assert len(action.result_list) == 1
    assert "Could not" in action.result_list[0].get_name()


@with_temp_dir()
def test_create_note(path):
    notesnv = extension.NotesNv({})
    notesnv.do_open_note = MagicMock()
    fn = os.path.join(path, "file.txt")
    notesnv.do_create_note(fn)
    assert os.path.exists(fn)
    notesnv.do_open_note.assert_called_with(fn)


@with_temp_dir()
def test_create_note_wrong_path(path):
    notesnv = extension.NotesNv({})
    notesnv.do_open_note = MagicMock()
    bad_path = os.path.join(path, "nosuchdir_asdfasdf")
    fn = os.path.join(bad_path, "file.txt")
    action = notesnv.do_create_note(fn)
    assert isinstance(action, RenderResultListAction)
    assert len(action.result_list) == 1
    assert "Could not" in action.result_list[0].get_name()
    notesnv.do_open_note.assert_not_called()
