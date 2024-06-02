#!/usr/bin/env python3

import os
import stat
import sys

LICENSE = """\
 The MIT License (MIT)

Copyright (c) 2024 Oscar Butler-Aldridge

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is furnished
to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

_DEBUG = 1
_INFO  = 2
_ERROR = 3


_debug                              = False
_ignore_blank_lines                 = True
_by_extension                       = False
_excluded_paths: set[str]           = set()
_already_counted_paths: set[str]    = set()
_count_by_extension: dict[str, int] = {}


def reset():
    global _debug, _ignore_blank_lines
    _debug              = False
    _ignore_blank_lines = True
    _excluded_paths.clear()
    _already_counted_paths.clear()
    _count_by_extension.clear()


def _main():
    if "-h" in sys.argv or "--help" in sys.argv:
        print(
            f"{sys.argv[0]} [OPTIONS] PATH...\n"
            "\n"
            "Count the lines of code in files and directories.\n"
            "\n"
            "The targeted files and directories are specified by passing\n"
            "one or more PATH arguments.\n"
            "\n"
            "OPTIONS:\n"
            "-x/--exclude PATH .... Exclude PATH from being counted.\n"
            "                       Multiple PATHs can be excluded by passing\n"
            "                       this option multiple times.\n"
            "-b/--count-blank ..... Count blank lines.\n"
            "                       Blank lines are NOT counted by default!\n"
            "-e/--by-ext .......... Display number of lines for each separate\n"
            "                       file extension.\n"
            "-h/--help ............ Display this usage message.\n"
            "--debug .............. Display debug log messages.\n"
            "--license ............ Display this software's license.\n"
            , file=sys.stdout)
        exit(0)
    if "--license" in sys.argv:
        print(LICENSE, file=sys.stdout)
        exit(0)

    argv_is_handled = [False]*len(sys.argv)

    script_name = sys.argv[0]
    argv_is_handled[0] = True

    def flag(name):
        """Return True and make arg as handled if the flag is contained within
        sys.argv."""
        for i, arg in enumerate(sys.argv):
            if argv_is_handled[i]:
                continue
            if arg == name:
                argv_is_handled[i] = True
                return True
        return False

    def opt(name):
        for i, arg in enumerate(sys.argv):
            if argv_is_handled[i]:
                continue
            if i == len(sys.argv) - 1:
                continue
            if arg == name:
                value = sys.argv[i + 1]
                argv_is_handled[i    ] = True
                argv_is_handled[i + 1] = True
                return value
        return None

    def opt_multiple(name):
        while True:
            value = opt(name)
            if value is None:
                return
            yield value

    reset()

    if flag("--debug"):
        enable_debug()

    if flag("-b") or flag("--count-blank"):
        count_blank_lines()

    if flag("-e") or flag("--by-ext"):
        count_by_extension()

    exclude_paths(list(opt_multiple("-x")) + list(opt_multiple("--exclude")))

    if _debug:
        # Log state in debug mode
        _log(_DEBUG, "Debug mode enabled.")
        if _ignore_blank_lines:
            _log(_DEBUG, "Ignoring blank lines.")
        else:
            _log(_DEBUG, "Counting blank lines.")
        for path in _excluded_paths:
            _log(_DEBUG, f"Excluding path '{path}'")

    # We assume that all remaining unhandled arguments are files or directories
    # in which the lines of code should be counted
    loc_total: int = 0
    for i, path in enumerate(sys.argv):
        if argv_is_handled[i]:
            continue
        try:
            loc_total += loc(path)
        except FileNotFoundError:
            _log(_ERROR, f"Path '{path}' does not exist!")
            exit(1)

    if _by_extension:
        loc_with_known_ext = 0
        for ext, loc_for_ext in _count_by_extension.items():
            print(f"{ext}\t{loc_for_ext}", file=sys.stdout)
            loc_with_known_ext += loc_for_ext

        loc_with_unknown_ext = loc_total - loc_with_known_ext
        if loc_with_unknown_ext > 0:
            print(f"misc.\t{loc_with_unknown_ext}", file=sys.stdout)

        print(f"total\t{loc_total}", file=sys.stdout)
    else:
        print(loc_total, file=sys.stdout)
    exit(0)


def loc(path: str) -> int:
    path = os.path.realpath(path)
    entry_stat = os.stat(path)
    if stat.S_ISREG(entry_stat.st_mode):
        return loc_in_file(path)
    elif stat.S_ISDIR(entry_stat.st_mode):
        return loc_in_dir(path)
    return -1


def loc_in_file(path: str) -> int:
    global _already_counted_paths

    if path in _excluded_paths:
        if _debug:
            _log(_DEBUG, f"Skipping excluded file '{path}'.")
        return 0
    if path in _already_counted_paths:
        if _debug:
            _log(_DEBUG, f"Skipping already counted file '{path}'.")
        return 0

    loc_total: int = 0

    if _debug:
        _log(_DEBUG, f"Counting lines of code in file '{path}'.")

    # Count lines in file
    with open(path, "r") as f:
        try:
            if _ignore_blank_lines:
                for line in f.readlines():
                    if line:
                        for c in line:
                            if c == '\n':
                                break
                            if c != ' ' and c != '\t':
                                loc_total += 1
                                break
            else:
                loc_total = len(f.readlines())
        except UnicodeDecodeError:
            if _debug:
                _log(_DEBUG, f"Cannot count lines in binary file '{path}'.")
                return 0
    _already_counted_paths.add(path)
    # Increment count in "by extension" dict if "by extension" mode is on.
    if _by_extension:
        key = None
        for i in range(len(path) - 1, 0, -1):
            if path[i] == '.' and i > 0 and path[i - 1] != '/':
                key = path[i:].lower()
            elif path[i] == '/':
                break;

        if key in _count_by_extension:
            _count_by_extension[key] += loc_total
        elif key is not None:
            _count_by_extension[key] = loc_total

    if _debug:
        _log(_DEBUG, f"{loc_total} in '{path}'.")

    return loc_total


def loc_in_dir(path: str) -> int:
    if path in _excluded_paths:
        if _debug:
            _log(_DEBUG, f"Skipping excluded directory '{path}'.")
        return 0
    if path in _already_counted_paths:
        if _debug:
            _log(_DEBUG, f"Skipping already directory file '{path}'.")
        return 0

    loc_total: int = 0

    if _debug:
        _log(_DEBUG, f"Counting lines of code in directory '{path}'.")

    for dirent in os.scandir(path):
        if dirent.is_file():
            loc_total += loc_in_file(dirent.path)
        elif dirent.is_dir():
            loc_total += loc_in_dir(dirent.path)
    _already_counted_paths.add(path)

    if _debug:
        _log(_DEBUG, f"{loc_total} in '{path}'.")

    return loc_total


def enable_debug():
    global _debug
    _debug = True


def count_blank_lines():
    global _ignore_blank_lines
    _ignore_blank_lines = False


def count_by_extension():
    global _by_extension
    _by_extension = True


def exclude_paths(paths):
    for path in paths:
        _excluded_paths.add(os.path.realpath(path))


def _log(level: int, msg: str):
    if level == _INFO:
        print(f"(loc.py) INFO:: {msg}", file=sys.stdout)
    elif level == _ERROR:
        print(f"(loc.py) ERROR: {msg}", file=sys.stderr)
    elif level == _DEBUG:
        print(f"(loc.py) DEBUG: {msg}", file=sys.stdout)


if __name__ == "__main__":
    _main()

