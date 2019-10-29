"""
Parse user queries into "search query" and "command"
"""
from typing import NamedTuple


COMMAND_SEP = "|"
KNOWN_COMMANDS = {"cp": "Copy to clipboard"}


class QueryCommand(NamedTuple):
    """
    Parts of the parsed query
    """

    result_item_pfx: str
    cmd: str
    search_query: str

    def short(self) -> str:
        """
        Short str output of the tuple, for doctests
        """
        return f"pfx='{self.result_item_pfx}', c='{self.cmd}', q='{self.search_query}'"


def parse(query):
    """
    Turn query string into an instance of QueryCommand

    ### Default command: open note

    >>> parse('py chea').short()
    "pfx='', c='open', q='py chea'"


    ### cp: copy note contents to clipboard

    >>> parse('py chea | cp').short()
    "pfx='Copy to clipboard', c='cp', q='py chea'"

    >>> parse('snippet apt get | cp').short()
    "pfx='Copy to clipboard', c='cp', q='snippet apt get'"


    Unrecognized command names are treated as "open" command:

    >>> parse('zsh ref | blahbalh').short()
    "pfx='', c='open', q='zsh ref'"
    """

    if COMMAND_SEP not in query:
        return QueryCommand("", "open", query)

    query_chunk, cmd_chunk = [
        s.strip(" ") for s in query.split(COMMAND_SEP, maxsplit=1)
    ]
    cmd_chunk = cmd_chunk.lower()

    if cmd_chunk in KNOWN_COMMANDS:
        return QueryCommand(KNOWN_COMMANDS[cmd_chunk], cmd_chunk, query_chunk)

    return QueryCommand("", "open", query_chunk)
