import dpl.lib.core.py_parser as parser
import dpl.lib.core.varproc as varproc
import dpl.lib.core.arguments as argproc
import dpl.lib.core.info as info
import dpl.lib.core.extension_support as extension_support
import dpl.lib.core.error as error
import dpl.dfpm.dfpm as dfpm

class DPLError(Exception):
    def __init__(self, code):
        self._code = code
        self._name = error.ERRORS_DICT.get(self._code, '???')
        super().__init__()
    @property
    def name(self): return self._name
    @property
    def code(self): return self._code
    def __repr__(self):
        return f"DPLError(code={self._code!r}, name={self._name!r})"
    def __str__(self):
        return self.__repr__()

def run(*args, **kwargs):
    "Run a DPL script in an easier way, hence ez_run"
    if err := parser.run(*args, **kwargs):
        raise DPLError(err) from None