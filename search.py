import subprocess
import re
import os
from typing import NamedTuple
from functools import partial


class SearchResultItem(NamedTuple):
    filename: str
    filename_lower: str
    match_content: str
    match_content_lower: str
    match_summary: str


class SubprocessError(Exception):
    pass


def grep_dir(path, file_exts, pattern):
    include_globs = ["--include=*.{}".format(e) for e in file_exts]
    cp = subprocess.run(
        [
            "grep",
            "--with-filename",
            "--ignore-case",
            "--recursive",
            "--extended-regexp",
            "--null",
            "--max-count=1",
        ]
        + include_globs
        + ["-e", pattern, path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    if cp.returncode == 2:
        raise SubprocessError(cp.stderr.decode("utf-8"))
    else:
        s = cp.stdout.decode("utf-8")
        # Can't use .splitlines below because some of my files contain lines with weird linebreaks
        lines = s.split("\n")
        return [tuple(l.split("\x00", maxsplit=1)) for l in lines if l]


def escape_regex(s):
    return re.sub(r"([\?\*\.\\\{\}\[\]\+])", r"\\\1", s)


def file_exts_to_regex(exts):
    globs = ["\\.{}".format(escape_regex(e)) for e in exts]
    return ".+({})$".format("|".join(globs))


def find_dir(path, file_exts, query_args):
    name_glob = "*" + "*".join(query_args) + "*"
    cp = subprocess.run(
        [
            "find",
            path,
            "-type",
            "f",
            "-regextype",
            "egrep",
            "-iregex",
            file_exts_to_regex(file_exts),
            "-iname",
            name_glob,
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    if cp.returncode != 0:
        raise SubprocessError(cp.stderr.decode("utf-8"))
    else:
        s = cp.stdout.decode("utf-8")
        return s.splitlines()


def summarized_content_match(s, ctx_word, ctx_len):
    i = s.find(ctx_word)
    if i == -1:
        return s
    else:
        start = max(0, i - ctx_len)
        end = min(len(s), i + len(ctx_word) + ctx_len)
        ctx = "..." if start > 0 else ""
        ctx += s[start:end]
        ctx += "..." if end < len(s) else ""
        return ctx


def search_note_file_contents(path, file_exts, query):
    args = query.lower().split(" ")
    pattern = ".+".join(escape_regex(a) for a in args)
    full_path = os.path.expanduser(path)
    grep_matches = grep_dir(full_path, file_exts, pattern)
    matches = []
    file_name_start = len(full_path) + 1
    for fn, mtext in grep_matches:
        fn = fn[file_name_start:]
        matches.append(
            SearchResultItem(
                fn,
                fn.lower(),
                mtext,
                mtext.lower(),
                summarized_content_match(mtext, args[0], 25),
            )
        )
    return matches


def search_note_file_titles(path, file_exts, query):
    args = query.lower().split(" ")
    full_path = os.path.expanduser(path)
    find_matches = find_dir(full_path, file_exts, args)
    matches = []
    file_name_start = len(full_path) + 1
    for fn in find_matches:
        fn = fn[file_name_start:]
        matches.append(SearchResultItem(fn, fn.lower(), "", "", ""))
    return matches


def match_sort_key(word_boundary_regex, match):
    """
    Generate a tuple that can be used as a sorting key.

    Sorting criteria, in the order of most-to-least important:

    - file name matches first query arg on word boundary
    - how close the file name match is to the beginning of the filename
    - note content matches first query arg on word boundary
    - has text summary
    - alpha-numeric sort of filenames
    """
    fm = word_boundary_regex.search(match.filename_lower)
    return (
        fm.start() if fm else 2**10,
        0 if word_boundary_regex.search(match.match_content_lower) is not None else 1,
        0 if match.match_summary else 1,
        match.filename_lower,
    )


def search_notes(path, file_exts, query):
    grep_matches = search_note_file_contents(path, file_exts, query)
    find_matches = search_note_file_titles(path, file_exts, query)
    # dont include `find` matches for the same fn that appeared in `grep` matches
    grep_fns = set(m.filename for m in grep_matches)
    matches = grep_matches + [m for m in find_matches if m.filename not in grep_fns]
    args = query.split(" ")
    word_boundary_regex = re.compile("\\b{}\\b".format(re.escape(args[0])))
    return list(sorted(matches, key=partial(match_sort_key, word_boundary_regex)))
