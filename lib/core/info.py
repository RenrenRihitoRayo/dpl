# Used to system info and other data
# Variables are handled in varproc.py

import os, sys

ARGV = sys.argv
ARGC = len(ARGV)

INC = {
    "fn", "method",
    "for", "loop",
    "if"
}

DEC = {
    "end"
}

CHARS = {
    "\\\\":"\\[escape]",
    "\\n":"\n",
    "\\t":"\t",
    "\\s":"\s",
    "\\v":"\v",
    "\\f":"\f",
    "\\r":"\r",
    "\\[win_nl]":"\r\n",
    "\\[unix_nl]":"\n",
    "\\[null]":"\0",
    "\\[escape]":"\\"
}

CACHE = "_dpl_cache"

BINDIR = os.path.dirname(ARGV[0])
LIBDIR = os.path.join(BINDIR, "lib")