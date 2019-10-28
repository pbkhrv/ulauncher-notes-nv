from notesnv import extension


def test_filename_from_query():
    fn = extension.note_filename_from_query(":what ? this test!")
    # No double-spaces in the name
    assert fn.find("  ") == -1

    # No whitespaces in front or back
    assert fn[0] != " "
    assert fn[-1] != " "
