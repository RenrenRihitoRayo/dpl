import json
import re
import os
from . import info
from traceback import format_exc
from prompt_toolkit import PromptSession
from prompt_toolkit.lexers import Lexer
from prompt_toolkit.formatted_text import StyleAndTextTuples
from prompt_toolkit.styles import Style

# Your JSON config as a string
try:
    json_config = open(os.path.join(info.BINDIR, "repl_conf/colors_n_stuff.json")).read()
    print("Loaded highlighter config...")
except Exception as e:
    json_config = '{"classes":{}}'
    print("Something went wrong with loading the highlighter config...\nSee 'log.txt' in the dpl directory.")
    with open(os.path.join(info.BINDIR, "log.txt"), "w") as f:
        f.write(format_exc())

# Parse the config
config = json.loads(json_config)
classes = config['classes']

# Extract styles and word lists
class_styles = {}
word_map = {}  # word -> class name
regex_matchers = []  # (class name, regex)
sw_map = {}  # word -> class name

for class_name, rule in classes.items():
    class_styles[class_name] = rule['style']
    if 'words' in rule:
        for word in rule['words']:
            word_map[word] = class_name
    if 'match' in rule:
        regex_matchers.append((class_name, re.compile(eval(str(repr(rule['match']))))))
    if 'startswith' in rule:
        sw_map[class_name] = rule["startswith"]

# Construct the prompt_toolkit Style object
style = Style.from_dict(class_styles)

# Custom Lexer
class DPLLexer(Lexer):
    def lex_document(self, document):
        lines = document.lines

        def get_line(i: int) -> StyleAndTextTuples:
            text = lines[i]
            tokens = []
            
            for class_name, word in sw_map.items():
                if text.startswith(word):
                    tokens.append((f'class:{class_name}', text))
                    return tokens
            
            # Tokenize line by words
            i = 0
            while i < len(text):
#                if text[i] == '"':
#                    end = text[i+1:].find('"')
#                    if end == -1:
#                        string = text[i:]
#                    else:
#                        string = text[i:i+2+end]
#                    tokens.append(("class:string", string))
#                    
#                    i += len(string)
#                    if i >= len(text):
#                        break
                if text[i] == '"':
                    start = i
                    end = i + 1
                    tokens.append(("class:string", '"'))
                    while end < len(text):
                        char = text[end]
                        if char == '\\':
                            if end+1 < len(text): tokens.extend([
                                ("class:escape", "\\"),
                                ("class:escape", text[end+1])
                            ]); end += 2
                            else: tokens.extend([
                                ("class:escape", "\\"),
                            ]); end += 1
                            continue
                        end += 1
                        tokens.append(('class:string', char))
                        if char == '"':
                            break
                    i = end
                    if i >= len(text): break
                if text[i] == "'":
                    start = i
                    end = i + 1
                    tokens.append(("class:string", "'"))
                    while end < len(text):
                        char = text[end]
                        if char == '\\':
                            if end+1 < len(text): tokens.extend([
                                ("class:escape", "\\"),
                                ("class:escape", text[end+1])
                            ]); end += 2
                            else: tokens.extend([
                                ("class:escape", "\\"),
                            ]); end += 1
                            continue
                        if char == '$' and end + 1 < len(text) and text[end+1] == '{':
                            sub_end = end + 2
                            
                            continue
                        end += 1
                        tokens.append(('class:string', char))
                        if char == "'":
                            break
                    i = end
                    if i >= len(text): break

                if text[i].isspace():
                    tokens.append(('', text[i]))
                    i += 1
                    continue

                start = i
                while i < len(text) and not text[i].isspace():
                    i += 1
                word = text[start:i]

                class_name = word_map.get(word)
                if class_name:
                    tokens.append((f'class:{class_name}', word))
                else:
                    for class_name, regex in regex_matchers:
                        if (match:=regex.match(word)):
                            tokens.append((f"class:{class_name}", word))
                            break
                    else:
                        tokens.append(('', word))

            return tokens

        return get_line