from io import StringIO
from . import constants
from . import varproc

def old_format(template, vars):
    for name, value in vars.items(): # expect a flattened dict
        template = template.replace(f"${{{name}}}", str(value))
    return template

og_format = format

def format(template: str, data: dict, strict=True, expr_fn=eval) -> str:

    result = StringIO()
    i = 0
    missing = []

    while i < len(template):
        char = template[i]
        if char == '\\':
            i += 1
            if i < len(template):
                result.write(template[i])
                i += 1
            continue

        elif char in ('$', '&') and i + 1 < len(template) and template[i + 1] == '{':
            is_expr = (char == '&')
            i += 2
            is_str = True
            if template[i] == "!":
                is_str = True
                i += 1
            elif template[i] == "?":
                is_str = False
                i += 1
            start = i
            while i < len(template) and template[i] != '}':
                i += 1
            if i >= len(template):
                raise ValueError(f"Unclosed placeholder in {'expression' if is_expr else 'variable'}: {template[start:]}")
            placeholder = template[start:i]
            i += 1  # skip the closing '}'
            if is_expr:
                format_spec = ""
                if "|" in placeholder:
                    format_spec, placeholder = placeholder.split("|", 1)
                try:
                    result.write(og_format(expr_fn(placeholder, data), format_spec))
                except Exception as e:
                    raise e
                continue

            # Variable placeholder
            if not placeholder:
                raise ValueError("Empty variable literal!")
            var_part = placeholder.split("|")
            default_text = None
            format_spec = ""

            if ":" in var_part[0]:
                format_spec, var_part[0] = var_part[0].split(":", 1)
            if ":" in var_part[-1]:
                var_part[-1], default_text = var_part[-1].split(":", 1)

            for name in var_part:
                if (value := varproc.rget(data[-1], name, default=varproc.rget(data[0], name))) != constants.nil:
                    result.write(og_format(value if is_str else repr(value), format_spec))
                    break
            else:
                if default_text is not None:
                    result.write(default_text)
                else:
                    result.write("${" + var_part[0] + "}")
                    missing.extend(var_part)
            continue

        else:
            # old logic did it char by char.
            # at least now we try to do it the greedy way.
            # avoids calling write on every character that doesnt match.
            # for reference old code is:
#            result.write(char)
#            i += 1
            start = i
            while i < len(template) and template[i] not in ("&", "$"):
                i += 1
            result.write(template[start:i])

    if missing and strict:
        if len(missing) == 1:
            raise ValueError(f"Value {missing[0]} is missing.")
        else:
            *head, tail = missing
            missing_text = ", ".join(head) + f", and {tail}"
            raise ValueError(f"Values {missing_text} are missing.")

    return result.getvalue()

# no circular imports
# because 'dpl' and 'module' is 
if __name__ == "__dpl__":
    handle_in_string_expr = dpl.arguments.handle_in_string_expr
    def fmt_format(frame, text):
        this = lambda text, _: handle_in_string_expr(text, frame)
        values = dpl.arguments.flatten_dict(frame[-1])
        return format(text, values, expr_fn=this)
    dpl.arguments.add_method("fmt:format", fmt_format)
    dpl.info.add_runtime_dependent_method("fmt:format")
    frame_stack[0]["fmt:format"] = lambda frame, _, text, name=None: (
        dpl.varproc.rset(frame[-1], name, text:=fmt_format(frame, text)),
        frame[-1].__setitem__(name, text) if name is not None else None,
        (text,)
    )[-1]

if __name__ == "__main__":
    # just a test case to test the greedy concat
    # text is ha and ha twice is haha!
    print(format('text is ${text} and ${text} twice is &{text * 2}! How humorful isnt it?', {"text": "ha"}))
    print(format('formated &{.2f:90}', {"text": "ha"}))