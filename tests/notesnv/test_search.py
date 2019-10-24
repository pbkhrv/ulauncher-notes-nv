from utils import with_temp_dir
from notesnv import search


@with_temp_dir(["python cheatsheet.txt", "java cheatsheet.txt"])
def test_one_file(path):
    matches = search.find_dir(path, ["txt"], ["python"])
    assert len(matches) == 1
    assert matches[0] == "python cheatsheet.txt"


@with_temp_dir(["python cheatsheet.txt", "java cheatsheet.txt", "books.txt"])
def test_two_files(path):
    matches = search.find_dir(path, ["txt"], ["cheats"])
    assert len(matches) == 2


@with_temp_dir(["PYTHON cheatsheet.txt", "JAVA cheatsheet.txt"])
def test_case_insensitive(path):
    matches = search.find_dir(path, ["txt"], ["py"])
    assert len(matches) == 1
    assert matches[0] == "PYTHON cheatsheet.txt"


@with_temp_dir(["python cheatsheet.txt", "python pep8.txt", "java cheatsheet.txt"])
def test_pattern_with_two_parts(path):
    matches = search.find_dir(path, ["txt"], ["py", "che"])
    assert len(matches) == 1
    assert matches[0] == "python cheatsheet.txt"


@with_temp_dir(["python cheatsheet.txt", "python pep8.txt", "java cheatsheet.txt"])
def test_pattern_with_two_parts_swapped(path):
    matches = search.find_dir(path, ["txt"], ["che", "py"])
    assert len(matches) == 1
    assert matches[0] == "python cheatsheet.txt"


@with_temp_dir(["python cheatsheet.txt", "python pep8.txt", "java cheatsheet.txt"])
def test_right_extension(path):
    matches = search.find_dir(path, ["gif"], ["che", "py"])
    assert len(matches) == 0
