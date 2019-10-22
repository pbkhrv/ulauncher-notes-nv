import subprocess
import re
import os
from typing import NamedTuple


class GrepError(Exception):
    pass


class SearchResultItem(NamedTuple):
    filename: str
    match_content: str
    match_summary: str
    rank: int = 0


def regex_escape(s):
    return re.sub(r"([\?\*\.\\\{\}\[\]\+])", r"\\\1", s)


def grep_dir(path, globs, args):
    globs = ["--include={}".format(g) for g in globs]
    pattern = ".+".join(regex_escape(a) for a in args)
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
        + globs
        + ["-e", pattern, path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    if cp.returncode == 2:
        raise GrepError(cp.stderr.decode("utf-8"))
    else:
        s = cp.stdout.decode("utf-8")
        # Can't use .splitlines below because some of my files contain lines with weird linebreaks
        lines = s.split("\n")
        return [tuple(l.split("\x00", maxsplit=1)) for l in lines if l]


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


def search_note_file_contents(path, path_globs, query):
    args = query.split(" ")
    full_path = os.path.expanduser(path)
    grep_matches = grep_dir(full_path, path_globs, args)
    matches = []
    file_name_start = len(full_path) + 1
    for mpath, mtext in grep_matches:
        mpath = mpath[file_name_start:]
        matches.append(
            SearchResultItem(mpath, mtext, summarized_content_match(mtext, args[0], 25))
        )
    return matches
