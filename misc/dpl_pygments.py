from pygments.lexer import RegexLexer
from pygments.token import *
from pygments import highlight
from pygments.formatters import TerminalFormatter

class DPLLexer(RegexLexer):
    name = "DPL"
    aliases = ["dpl"]
    filenames = ["*.dpl"]

    tokens = {
        'root': [
            (r'\s+', Text),
            (r'#[^\n]*', Comment.Single),
            (r'".*?"', String.Double),
            (r'\b(set|fn|method|return|end|case|with|del|object|new|for|pass|in|and|not|or|switch|set|if|loop|match|stop|skip)\b', Keyword),
            (r':[a-zA-Z_][a-zA-Z0-9_]*', Name.Variable),
            (r'\d+\.\d+|\d+', Number),
            (r'[+\-*/=<>!&|]', Operator),
            (r'\w+', Name),
        ],
    }

dpl_formatter = TerminalFormatter(style="monokai")

def highlight_code(code, formatter=dpl_formatter):
    print(highlight(code, DPLLexer(), formatter))