"""
Parse user queries into "search query" and "command"
"""
from typing import NamedTuple
import re


COMMAND_SEP = "|"
KNOWN_COMMANDS = set(["cp"])
DEFAULT_COMMAND = "open"


class QueryCommand(NamedTuple):
    """
    Parts of the parsed query
    """

    cmd: str
    search_query: str

    def short(self) -> str:
        """
        Short str output of the tuple, for doctests
        """
        return f"{self.cmd}: {self.search_query}"


def parse(query):
    """
    Turn query string into an instance of QueryCommand

    ### Default command: open note

    >>> parse('py chea').short()
    'open: py chea'

    ### cp: copy note contents to clipboard

    >>> parse(' py chea | cp').short()
    'cp: py chea'

    >>> parse('snippet apt get | cp').short()
    'cp: snippet apt get'

    If the query string starts with |, then the next arg is command
    and the rest of the string is the search query:

    >>> parse(' |  cp  snippet apt get').short()
    'cp: snippet apt get'

    ### Unrecognized command names are treated as 'open' command:

    >>> parse('zsh ref | blahbalh').short()
    'open: zsh ref'
    """

    if COMMAND_SEP not in query:
        return QueryCommand(DEFAULT_COMMAND, query)

    query_chunk, cmd_chunk = [
        s.strip(" ") for s in query.split(COMMAND_SEP, maxsplit=1)
    ]

    # if query begins with COMMAND_SEP, use first token as command
    if not query_chunk:
        chunks = re.split(r" +", cmd_chunk, maxsplit=1)
        cmd_chunk = chunks[0]
        query_chunk = chunks[1] if len(chunks) == 2 else ""

    cmd_chunk = cmd_chunk.lower()

    if cmd_chunk not in KNOWN_COMMANDS:
        return QueryCommand(DEFAULT_COMMAND, query_chunk)

    return QueryCommand(cmd_chunk, query_chunk)
