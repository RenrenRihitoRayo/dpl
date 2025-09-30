import json
import re
import os
try:
    from . import info
except:
    import info
from traceback import format_exc
from prompt_toolkit.lexers import Lexer
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.document import Document
from prompt_toolkit import print_formatted_text

try:
    try:
        json_config = json.loads(open(os.path.join(info.BINDIR, "repl_conf/colors_n_stuff.json")).read())
    except:
        json_config = json.loads(open(os.path.join("../../../repl_conf/colors_n_stuff.json")).read())
except Exception:
    json_config = {"classes": {}}
    print("Something went wrong with loading the highlighter config...\nSee 'log.txt' in the dpl directory.")
    with open(os.path.join(info.BINDIR, "log.txt"), "w") as f:
        f.write(format_exc())


def highlight_text(lexer, text):
    document = Document(text, cursor_position=0)
    get_line_tokens = lexer.lex_document(document)
    tokens = []
    for lineno, line in enumerate(document.lines):
        line_tokens = get_line_tokens(lineno)
        for style, chunk in line_tokens:
            tokens.append((style, chunk))
        tokens.append(('', '\n'))
    return FormattedText(tokens)


class DPLLexer(Lexer):
    def __init__(self):
        self.config = json_config
        self.token_rules = []
        self.sub_rules = {}

        for cls_name, cls in self.config.get("classes", {}).items():
            style = cls.get("style", "")

            if "words" in cls:
                wordlike = sorted([w for w in cls["words"] if re.match(r'^[\w:_-]+$', w)], key=len, reverse=True)
                symbolic = sorted([w for w in cls["words"] if not re.match(r'^\w+$', w)], key=len, reverse=True)

                if wordlike:
                    pattern = r'\b(?:' + '|'.join(re.escape(w) for w in wordlike) + r')\b'
                    self.token_rules.append((re.compile(pattern), style, None))

                if symbolic:
                    pattern = r'(?:' + '|'.join(re.escape(w) for w in symbolic) + r')'
                    self.token_rules.append((re.compile(pattern), style, None))

            if "match" in cls:
                try:
                    self.token_rules.append((re.compile(cls["match"]), style, None))
                except Exception as e:
                    print("Something went wrong for:", cls["match"], repr(e))

            if "startswith" in cls:
                pattern = re.compile(re.escape(cls["startswith"]) + r'.*')
                self.token_rules.append((pattern, style, None))

            for sub_name, sub_cls in self.config.get("classes", {}).items():
                if sub_name.startswith(f"in:{cls_name}:"):
                    sub_style = sub_cls.get("style", "")
                    sub_match = sub_cls.get("match")
                    if sub_match:
                        sub_pattern = re.compile(sub_match)
                        self.sub_rules.setdefault(cls_name, []).append((sub_pattern, sub_style))

    def lex_document(self, document):
        def get_line_tokens(lineno):
            line = document.lines[lineno]
            tokens = []
            i = 0
            while i < len(line):
                match_found = False
                for pattern, style, _ in self.token_rules:
                    match = pattern.match(line, i)
                    if match:
                        chunk = match.group()
                        parent_key = self._get_parent_class_for_pattern(pattern)
                        if parent_key and parent_key in self.sub_rules:
                            tokens.extend(self._apply_subrules(chunk, style, self.sub_rules[parent_key]))
                        else:
                            tokens.append((style, chunk))
                        i = match.end()
                        match_found = True
                        break
                if not match_found:
                    tokens.append(('', line[i]))
                    i += 1
            return tokens

        return get_line_tokens

    def _get_parent_class_for_pattern(self, pattern):
        for cls_name, cls in self.config.get("classes", {}).items():
            if "match" in cls:
                try:
                    if re.compile(cls["match"]).pattern == pattern.pattern:
                        return cls_name
                except:
                    pass
            if "startswith" in cls:
                pat = re.escape(cls["startswith"]) + r'.*'
                if pat == pattern.pattern:
                    return cls_name
        return None

    def _apply_subrules(self, chunk, parent_style, subrules):
        tokens = []
        i = 0
        while i < len(chunk):
            match_found = False
            for sub_pattern, sub_style in subrules:
                match = sub_pattern.match(chunk, i)
                if match:
                    tokens.append((sub_style, match.group()))
                    i = match.end()
                    match_found = True
                    break
            if not match_found:
                tokens.append((parent_style, chunk[i]))
                i += 1
        return tokens


if __name__ == "__main__":
    lexer = DPLLexer()
    # test highlighting
    sample = " ".join(info.ALL_INTRINSICS) + " '\\? ${some} &{test}' {test.lib} " + '"test\\n" 90'\
    + "\n# test comment!\ntest"
    highlighted = highlight_text(lexer, sample)
    print_formatted_text(highlighted)