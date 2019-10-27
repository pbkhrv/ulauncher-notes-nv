"""
Utilities for working with command line strings and arguments
"""
import re


DOUBLE_QUOTED_GROUPS = re.compile(r"(\".+?\")")
DOUBLE_QUOTED_STRING = re.compile(r"^\".+\"?")


def argsplit(cmd):
    """
    Split a command line string on spaces into an argument list
    that can be passed to subprocess.run()
    Use doublequotes to preserve spaces.

    >>> argsplit(" word1  word2")
    ['word1', 'word2']

    >>> argsplit('word1 word2 "blah  blah"')
    ['word1', 'word2', 'blah  blah']
    """

    # Strip string of whitespace and remove repeated spaces
    cmd = cmd.strip()

    # Split into quoted and unquoted chunks
    # (This trips up on escaped doublequotes!)
    args = []
    chunks = DOUBLE_QUOTED_GROUPS.split(cmd)
    for chunk in chunks:
        if chunk:
            if DOUBLE_QUOTED_STRING.fullmatch(chunk):
                # Strip then add quoted chunks
                args.append(chunk.strip('"'))
            else:
                # Clean unquoted chunks and further split on spaces
                chunk = re.sub(r" +", " ", chunk).strip()
                if chunk:
                    args += chunk.split(" ")
    return args


def argbuild(cmd, mapping, append_missing_field=None):
    """
    Turn a command template string into list of args
    suitable for subprocess.run() by replacing fields with values
    using Python's str.format_map() function.

    :param cmd: command to be turned into list of args
    :param mapping: fields and their replacements
    :param append_missing_field: if this field wasn't used in cmd, pass it as last arg
    :returns: list of args

    If `append_missing_field` is specified, it must be in `mapping`

    Examples:
    >>> argbuild('gedit --new-window', {'fn': '/foo/bar', 'ln': 12})
    ['gedit', '--new-window']

    >>> argbuild('gedit --new-window {fn} {ln}', {'fn': '/foo/bar', 'ln': 12})
    ['gedit', '--new-window', '/foo/bar', '12']

    >>> argbuild('gedit {ln}', {'fn': '/foo/bar', 'ln': 12}, append_missing_field='fn')
    ['gedit', '12', '/foo/bar']
    """
    append_field_used = False
    if append_missing_field:
        append_map = dict((k, "{" + k + "}") for k, v in mapping.items())
        append_map[append_missing_field] = mapping[append_missing_field]

    args = []
    for arg in argsplit(cmd):
        # Track if append_missing_field was used
        if append_missing_field and not append_field_used:
            # Try replacing the append field and see if string changes
            append_field_used = arg != arg.format_map(append_map)
        args.append(arg.format_map(mapping))

    if append_missing_field and not append_field_used:
        args.append(mapping[append_missing_field])

    return args
