# Exposes DPL internals for modules.
# Damn relative imports are a mess.

import dpl.lib.core.py_parser as parser
import dpl.lib.core.py_parser2 as parser2
import dpl.lib.core.varproc as varproc
import dpl.lib.core.arguments as argproc
import dpl.lib.core.info as info
import dpl.lib.core.module_handling as module_handling
import dpl.lib.core.error as error
import dpl.lib.core.dpl_configure_imports as dci
import dpl.lib.core.scanner as scanner
import dpl.lib.core.utils as utils
import dpl.project_mngr.pmfdpl as project_manager
import dpl.dfpm.dfpm as dfpm
import dpl.misc.dpl_pygments as dpl_pygments

def process(*args, **kwargs):
    "Wrapper for dpl.lib.core.py_parser.process(...)"
    return parser.process(*args, **kwargs)

def run(*args, **kwargs):
    "Run a DPL script in an easier way"
    if err := parser.run(*args, **kwargs):
        raise DPLError(err) from None