import os
import pytest
from utils import with_temp_dir
from notesnv import search


@with_temp_dir(["python cheatsheet.txt", "java cheatsheet.txt"])
def test_find_one_file(path):
    matches = search.find_dir(path, ["txt"], ["python"])
    assert len(matches) == 1
    assert matches[0] == "python cheatsheet.txt"


@with_temp_dir(["python cheatsheet.txt", "java cheatsheet.txt", "books.txt"])
def test_find_two_files(path):
    matches = search.find_dir(path, ["txt"], ["cheats"])
    assert len(matches) == 2


@with_temp_dir(["PYTHON cheatsheet.txt", "JAVA cheatsheet.txt"])
def test_find_case_insensitive(path):
    matches = search.find_dir(path, ["txt"], ["py"])
    assert len(matches) == 1
    assert matches[0] == "PYTHON cheatsheet.txt"


@with_temp_dir(["python cheatsheet.txt", "python pep8.txt", "java cheatsheet.txt"])
def test_find_pattern_with_two_parts(path):
    matches = search.find_dir(path, ["txt"], ["py", "che"])
    assert len(matches) == 1
    assert matches[0] == "python cheatsheet.txt"


@with_temp_dir(["python cheatsheet.txt", "python pep8.txt", "java cheatsheet.txt"])
def test_find_pattern_with_two_parts_swapped(path):
    matches = search.find_dir(path, ["txt"], ["che", "py"])
    assert len(matches) == 1
    assert matches[0] == "python cheatsheet.txt"


@with_temp_dir(["python cheatsheet.txt", "python pep8.txt", "java cheatsheet.txt"])
def test_find_right_extension(path):
    matches = search.find_dir(path, ["gif"], ["che", "py"])
    assert len(matches) == 0


@with_temp_dir([("file1.txt", "books you love"), ("file2.txt", "who ordered snakes?")])
def test_grep_one_file(path):
    matches = search.grep_dir(path, ["txt"], "snake")
    assert len(matches) == 1
    assert matches[0][0] == "file2.txt"


@with_temp_dir()
def test_grep_wrong_command(path):
    with pytest.raises(search.SearchError):
        search.grep_dir(path, ["txt"], "snake", grep_cmd="no_such_grep_command_ever")


@with_temp_dir()
def test_grep_wrong_path(path):
    with pytest.raises(search.SearchError):
        search.grep_dir(os.path.join(path, "nosuchdir"), ["txt"], "snake")


@with_temp_dir()
def test_find_wrong_command(path):
    with pytest.raises(search.SearchError):
        search.grep_dir(
            search.find_dir(path, ["txt"], ["python"], find_cmd="no_such_find_cmdn")
        )


@with_temp_dir()
def test_find_wrong_path(path):
    with pytest.raises(search.SearchError):
        search.grep_dir(
            search.find_dir(
                os.path.join(path, "nosuchdir"),
                ["txt"],
                ["python"]
            )
        )
