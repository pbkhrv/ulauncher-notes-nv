"""
Note searching functionality

- Uses `grep` to search note contents
- Uses `find` to search note titles
"""
import subprocess
import re
import os
from typing import NamedTuple
from functools import partial


class SearchResultItem(NamedTuple):  # pylint: disable=too-few-public-methods
    """
    Note search result item

    *_lower properties used for sort key generation
    """

    filename: str
    filename_lower: str
    match_content: str
    match_content_lower: str
    match_summary: str


class SubprocessError(Exception):
    """
    Subprocess run didn't return expected exit code
    """

    pass


def grep_dir(path, file_exts, pattern):
    """
    Call `grep` recursively on a directory and return matching filenames and
    first matching line of each file

    Only include files with certain extensions.
    """
    include_globs = ["--include=*.{}".format(e) for e in file_exts]
    ret = subprocess.run(
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

    if ret.returncode == 2:
        raise SubprocessError(ret.stderr.decode("utf-8"))
    else:
        out = ret.stdout.decode("utf-8")
        # Can't use .splitlines below because some of my files contain lines with weird linebreaks
        lines = out.split("\n")
        return [tuple(l.split("\x00", maxsplit=1)) for l in lines if l]


def file_exts_to_regex(exts):
    """
    Turn list of file extensions into one regex to be used with `find`
    """
    globs = ["\\.{}".format(re.escape(e)) for e in exts]
    return ".+({})$".format("|".join(globs))


def name_chunks_to_find_args(chunks):
    """
    Turn array of name chunks into a set of '-iname' arg segments joined by '-a' predicate.

    For example:
    ["good"] becomes `-iname "*good*"`
    ["py","note"] becomes `( -iname "*py*" -a -iname "*note*" )`
    """
    if len(chunks) == 1:
        return ["-iname", f"*{chunks[0]}*"]
    args = ["(", "-iname", f"*{chunks[0]}*"]
    for chunk in chunks[1:]:
        args += ["-a", "-iname", f"*{chunk}*"]
    args += [")"]
    return args


def find_dir(path, file_exts, name_chunks):
    """
    Execute `find` on a directory and find all files that:
    - have one of the extensions in `file_exts`
    - have names that contain all `name_chunks` in any order
    """
    ret = subprocess.run(
        [
            "find",
            path,
            "-type",
            "f",
            "-regextype",
            "egrep",
            "-iregex",
            file_exts_to_regex(file_exts),
        ]
        + name_chunks_to_find_args(name_chunks),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    if ret.returncode != 0:
        raise SubprocessError(ret.stderr.decode("utf-8"))
    else:
        return [
            os.path.relpath(fpath, path)
            for fpath in ret.stdout.decode("utf-8").splitlines()
        ]


def summarized_content_match(text, ctx_word, ctx_len):
    """
    Summarize a line of text by leaving ctx_len characters around the ctx_word and trimming the rest
    """
    i = text.find(ctx_word)
    if i == -1:
        return text
    start = max(0, i - ctx_len)
    end = min(len(text), i + len(ctx_word) + ctx_len)
    ctx = "..." if start > 0 else ""
    ctx += text[start:end]
    ctx += "..." if end < len(text) else ""
    return ctx


def search_note_file_contents(path, file_exts, query):
    """
    Call `grep` and turn results into SearchResultItem's
    """
    args = query.lower().split(" ")
    pattern = ".+".join(re.escape(a) for a in args)
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
    """
    Call `find` and turn results into SearchResultItem's
    """
    args = query.lower().split(" ")
    full_path = os.path.expanduser(path)
    find_matches = find_dir(full_path, file_exts, args)
    matches = []
    for fn in find_matches:
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
    word_matched = word_boundary_regex.search(match.filename_lower)
    return (
        word_matched.start() if word_matched else 2 ** 10,
        0 if word_boundary_regex.search(match.match_content_lower) is not None else 1,
        0 if match.match_summary else 1,
        match.filename_lower,
    )


def search_notes(path, file_exts, query):
    """
    Search note contents and titles, combine, dedup and sort results.
    """
    grep_matches = search_note_file_contents(path, file_exts, query)
    find_matches = search_note_file_titles(path, file_exts, query)
    # dont include `find` matches for the same fn that appeared in `grep` matches
    grep_fns = set(m.filename for m in grep_matches)
    matches = grep_matches + [m for m in find_matches if m.filename not in grep_fns]
    args = query.split(" ")
    word_boundary_regex = re.compile("\\b{}".format(re.escape(args[0])))
    return list(sorted(matches, key=partial(match_sort_key, word_boundary_regex)))
