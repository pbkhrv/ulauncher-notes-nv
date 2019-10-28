from notesnv import extension
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction


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
