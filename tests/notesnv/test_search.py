import os
import unittest
from utils import with_temp_dir
from notesnv import search


class FindTest(unittest.TestCase):
    @with_temp_dir(["python cheatsheet.txt", "java cheatsheet.txt"])
    def test_one_file(self, path):
        matches = search.find_dir(path, ["txt"], ["python"])
        self.assertEqual(1, len(matches))
        self.assertEqual("python cheatsheet.txt", matches[0])

    @with_temp_dir(["python cheatsheet.txt", "java cheatsheet.txt"])
    def test_two_files(self, path):
        matches = search.find_dir(path, ["txt"], ["cheats"])
        self.assertEqual(2, len(matches))

    @with_temp_dir(["PYTHON cheatsheet.txt", "JAVA cheatsheet.txt"])
    def test_case_insensitive(self, path):
        matches = search.find_dir(path, ["txt"], ["py"])
        self.assertEqual(1, len(matches))
        self.assertEqual("PYTHON cheatsheet.txt", matches[0])

    @with_temp_dir(["python cheatsheet.txt", "python pep8.txt", "java cheatsheet.txt"])
    def test_pattern_with_two_parts(self, path):
        matches = search.find_dir(path, ["txt"], ["py", "che"])
        self.assertEqual(1, len(matches))
        self.assertEqual("python cheatsheet.txt", matches[0])

    @with_temp_dir(["python cheatsheet.txt", "python pep8.txt", "java cheatsheet.txt"])
    def test_pattern_with_two_parts_swapped(self, path):
        matches = search.find_dir(path, ["txt"], ["che", "py"])
        self.assertEqual(1, len(matches))
        self.assertEqual("python cheatsheet.txt", matches[0])

    @with_temp_dir(["python cheatsheet.txt", "python pep8.txt", "java cheatsheet.txt"])
    def test_right_extension(self, path):
        matches = search.find_dir(path, ["gif"], ["che", "py"])
        self.assertEqual(0, len(matches))


if __name__ == "__main__":
    unittest.main()
