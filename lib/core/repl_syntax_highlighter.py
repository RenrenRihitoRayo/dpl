import json
import re
import os
try:
    from . import info
except:
    import info
from traceback import format_exc
from prompt_toolkit.lexers import Lexer
from prompt_toolkit.styles import Style

# Your JSON config as a string
try:
    try:
        json_config = json.loads(open(os.path.join(info.BINDIR, "repl_conf/colors_n_stuff.json")).read())
    except:
        json_config = json.loads(open(os.path.join("../../repl_conf/colors_n_stuff.json")).read())
    print("Loaded highlighter config...")
except Exception as e:
    json_config = '{"classes":{}}'
    print("Something went wrong with loading the highlighter config...\nSee 'log.txt' in the dpl directory.")
    with open(os.path.join(info.BINDIR, "log.txt"), "w") as f:
        f.write(format_exc())

from prompt_toolkit.lexers import Lexer
from prompt_toolkit.formatted_text import FormattedText
import re

class DPLLexer(Lexer):
    def __init__(self):
        self.config = json_config
        self.token_rules = []

        for cls_name, cls in self.config.get("classes", {}).items():
            style = cls.get("style", "")
            
            # If 'words' is present, match them as whole words
            if "words" in cls:
                words_pattern = r'\b(?:' + '|'.join(re.escape(word) for word in cls["words"]) + r')\b'
                self.token_rules.append((re.compile(words_pattern), style))
            
            # If 'match' regex is present, use it
            if "match" in cls:
                try:
                    self.token_rules.append((re.compile(cls["match"]), style))
                except Exception as e:
                    print("Something went wrong for:", cls["match"], repr(e))
            
            # If 'startswith' is present (like comments or directives)
            if "startswith" in cls:
                pattern = re.compile(re.escape(cls["startswith"]) + r'.*')
                self.token_rules.append((pattern, style))
        
    def lex_document(self, document):
        text = document.text

        def get_line_tokens(lineno):
            line = document.lines[lineno]
            tokens = []
            i = 0
            while i < len(line):
                match_found = False
                for pattern, style in self.token_rules:
                    match = pattern.match(line, i)
                    if match:
                        tokens.append((style, match.group()))
                        i = match.end()
                        match_found = True
                        break
                if not match_found:
                    tokens.append(('', line[i]))
                    i += 1
            return tokens

        return get_line_tokens


# Example usage with prompt_toolkit
if __name__ == "__main__":
    from prompt_toolkit import PromptSession
    from prompt_toolkit.styles import Style

    lexer = DPLLexer()
    session = PromptSession(lexer=lexer)
    while True:
        text = session.prompt('> ')
        print("You entered:", text)
