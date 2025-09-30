import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

import py_parser
import info
import varproc

def run_code(file, file_path):
    return py_parser.run_code(
        py_parser.process_code(file)
    )