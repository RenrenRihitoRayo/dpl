# Exposes DPL internals for modules.
# Damn relative imports are a mess.

import dpl.lib.core.newest.py_parser as parser
import dpl.lib.core.newest.py_parser2 as parser2
import dpl.lib.core.newest.varproc as varproc
import dpl.lib.core.newest.arguments as argproc
import dpl.lib.core.newest.info as info
import dpl.lib.core.newest.module_handling as module_handling
import dpl.lib.core.newest.error as error
import dpl.lib.core.newest.scanner as scanner
import dpl.lib.core.newest.utils as utils
import dpl.lib.core.newest.ast_gen as ast_gen
import dpl.project_mngr.pmfdpl as project_manager
import dpl.dfpm.dfpm as dfpm
import dpl.misc.dpl_pygments as dpl_pygments

def process(*args, **kwargs):
    "Wrapper for dpl.lib.core.newest.py_parser.process(...)"
    return parser.process_code(*args, **kwargs)

def run(*args, **kwargs):
    "Run a DPL script in an easier way"
    if err := parser.run(*args, **kwargs):
        raise DPLError(err) from None
