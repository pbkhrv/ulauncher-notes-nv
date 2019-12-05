"""
Note searching functionality

- Uses `grep` to search note contents
- Uses `find` to search note titles
"""
import subprocess
import re
import os
from typing import NamedTuple, List, Optional, Tuple, Pattern
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


class SearchError(Exception):
    """
    Search failure, message intended for the user.
    """

    def __init__(self, message: str, details: Optional[str] = None):
        super(SearchError, self).__init__(message, details)
        self.message = message
        self.details = details


def grep_dir(
    path: str, file_exts: List[str], pattern: str, grep_cmd: str = "grep"
) -> List[Tuple[str, str]]:
    """
    Call `grep` recursively on a directory and return matching filenames and
    first matching line of each file

    Only include files with certain extensions.
    """
    include_globs = ["--include=*.{}".format(e) for e in file_exts]
    try:
        ret = subprocess.run(
            [
                grep_cmd,
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
            check=False,
        )
    except OSError as exc:
        raise SearchError("Could not execute `grep` system command", exc.strerror)

    if ret.returncode == 2:
        raise SearchError(
            "Could not search through note contents", ret.stderr.decode("utf-8")
        )

    out = ret.stdout.decode("utf-8")
    # Can't use .splitlines below because
    # some of my files contain lines with weird linebreaks
    lines = out.split("\n")
    matches = []
    for line in lines:
        if line:
            fn, text = line.split("\x00", maxsplit=1)
            matches.append((os.path.relpath(fn, path), text))
    return matches


def file_exts_to_regex(exts: List[str], quoted: bool = False) -> str:
    """
    Turn list of file extensions into one regex
    """
    quote = '"' if quoted else ""
    globs = "|".join("\\.{}".format(re.escape(e)) for e in exts)
    return f"^{quote}.+({globs}){quote}$"


def name_chunks_to_find_args(chunks: List[str]) -> List[str]:
    """
    Turn array of name chunks into a set of '-iname' args joined by '-a' predicate.

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


def find_dir(
    path: str, file_exts: List[str], name_chunks: List[str], find_cmd: str = "find"
) -> List[str]:
    """
    Execute `find` on a directory and find all files that:
    - have one of the extensions in `file_exts`
    - have names that contain all `name_chunks` in any order
    """
    try:
        ret = subprocess.run(
            [
                find_cmd,
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
            check=False,
        )
    except OSError as exc:
        raise SearchError("Could not execute `find` system command", exc.strerror)

    if ret.returncode != 0:
        raise SearchError("Could not search for note files", ret.stderr.decode("utf-8"))

    return [
        os.path.relpath(fpath, path)
        for fpath in ret.stdout.decode("utf-8").splitlines()
    ]


# pylint: disable=unused-argument
def ls_dir(path: str, file_exts: List[str], ls_cmd: str = "/bin/ls") -> List[str]:
    """
    Execute `ls` on a directory and return all files...
    - that have one of the extensions in `file_exts`
    - sorted by modified time, most recent first
    """
    try:
        ret = subprocess.run(
            [ls_cmd, "--quote-name", "-t", "-1", "--escape", "--quote-name", path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    except OSError as exc:
        raise SearchError("Could not execute `ls` system command", exc.strerror)

    if ret.returncode != 0:
        raise SearchError(
            "Could not get a directory listing", ret.stderr.decode("utf-8")
        )

    extensions_regex = file_exts_to_regex(file_exts, quoted=True)
    return [
        fn.strip('"')
        for fn in ret.stdout.decode("utf-8").splitlines()
        if re.fullmatch(extensions_regex, fn, re.IGNORECASE)
    ]


def summarized_content_match(text: str, ctx_word: str, ctx_len: int) -> str:
    """
    Summarize a line of text by leaving ctx_len characters around the ctx_word
    and trimming the rest
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


def search_note_file_contents(
    path: str, file_exts: List[str], query: str
) -> List[SearchResultItem]:
    """
    Call `grep` and turn results into SearchResultItem's
    """
    args = query.lower().split(" ")
    pattern = ".+".join(re.escape(a) for a in args)
    full_path = os.path.expanduser(path)
    grep_matches = grep_dir(full_path, file_exts, pattern)
    matches = []
    for fn, text in grep_matches:
        matches.append(
            SearchResultItem(
                fn,
                fn.lower(),
                text,
                text.lower(),
                summarized_content_match(text, args[0], 25),
            )
        )
    return matches


def search_note_file_titles(
    path: str, file_exts: List[str], query: str
) -> List[SearchResultItem]:
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


def match_sort_key(word_boundary_regex: Pattern, match: SearchResultItem) -> Tuple:
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


def search_notes(path: str, file_exts: List[str], query: str) -> List[SearchResultItem]:
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


def contains_filename_match(
    matches: List[SearchResultItem], filename: str, extensions: List[str]
) -> bool:
    """
    Whether search results contain given filename with one of possible extensions.
    """
    possible_fns = set(f"{filename.lower()}.{ext.lower()}" for ext in extensions)
    for match in matches:
        if match.filename_lower in possible_fns:
            return True
    return False
