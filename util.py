from __future__ import print_function

import collections
import contextlib
import sys


color_stack = collections.deque(['0'])
attrs = {
    'gray': '30',
    'red': '31',
    'green': '32',
    'yellow': '33',
    'blue': '34',
    'purple': '35',
    'cyan': '36',
}
color_code = '\x1b[{}m'.format


@contextlib.contextmanager
def hilite(color):
    """
    Create a context where all text printed to stdout is highlighted
    in the color provided if possible.

    This is not even threadsafe in the slightest, which is probably a
    legitimate issue.

    Valid colors include gray, red, green, yellow, blue, purple,
    and cyan.

    Example:
    >>> with hilite('blue'):
    ...     print "This text is blue"
    ...     with hilite('green'):
    ...         print "This text is green now!"
    ...         print "So is this."
    ...     print "This text is blue again."
    ... print "This text is back to normal colored."
    """
    if sys.stdout.isatty():
        attr = attrs[color]
        print(color_code(attr), end='')
        sys.stdout.flush()
        color_stack.append(attr)
        yield
        color_stack.pop()
        print(color_code(color_stack[-1]), end='')
        sys.stdout.flush()
    else:  # Can't hilight if it's not a tty.
        yield


def hilite_string(color, string, skip_stack=False):
    """
    Return the given `string` highlighted in the color provided.

    For a full list of colors see `hilite`.

    `hilite_string` attempts to set the tty settings as they were
    prior to its call rather than leaving the terminal printing
    `color` text. If `skip_stack` is not specified the previous stack
    value from `hilite` will be used, otherwise it may be overridden
    with a color name, a color code, or True (in which case
    all style is cleared).
    """
    if sys.stdout.isatty():
        attr = attrs[color]
        if skip_stack is False:
            outro = color_stack[-1]
        elif skip_stack is True:
            outro = '0'
        elif skip_stack in attrs:
            outro = attrs[skip_stack]
        else:
            outro = skip_stack
        return ''.join((color_code(attr), string, color_code(outro)))
    else:
        return string
