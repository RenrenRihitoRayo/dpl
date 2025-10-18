# Used to handle arguments and expressions
# NOT FOR THE CLI

import dpl_ctypes
from sys import flags
import traceback
import constants
import varproc
import error
from info import *
import py_argument_handler as pah
import fmt
import objects
import uuid
import utils
import time

globals().update(vars(dpl_ctypes))

inf = float("inf")

# custom type to distinguish lists and expressions
class Expression(list):
    def __hash__(self):
        return hash(str(self))
    def __repr__(self):
        string = ""
        for i in self:
            if not isinstance(i, str):
                string += " "+str(i)
            elif i.startswith(":"):
                string += f" {i}"
            else:
                string += f' "{i}"' if " " in i else f" {i}"
        return f"[{string.strip()}]"
                

class Lazy(Expression):
    def __repr__(self):
        return f"lazy{{{self[1]!r}}}"

varproc.Lazy = Lazy

objects.Expression = Expression

run_fn = None

unary_ops = {
    "not", "~"
}

precedence_list = [
    ["==", "!=", ">=", "<=", ">", "<"],
    ["not"],
    ["~"],
    ["^"],
    ["*", "/"],
    ["+", "-"],
    ["and", "or"],
]

precedence = {}
for row, line in enumerate(precedence_list):
    for name in line:
        precedence[name] = len(precedence_list)-row


def glob_match(pattern, text):
    negate = False
    if pattern.startswith("\\!"):
        pattern = pattern[1:]
    elif pattern.startswith("!"):
        pattern = pattern[1:]
        negate = True
    def match(p, t):
        if p == "*":
            return True
        if p == "#":
            return t.isdigit()
        if "*" not in p and "#" not in p:
            return p.replace("\\[star_lit]", "*").replace("\\[pound_lit]", "#") == t
        pre, com, post = p.partition("#")
        if com == "#":
            if not match(pre, t[:len(pre)]):
                return False
            t = t[len(pre):]
            l = len(t)
            i = 0
            while i < l:
                if not t[i].isdigit():
                    break
                i += 1
            if i == 0:
                return False
            return match(post, t[i:])
        pre, com, post = p.partition("*")
        if com == "*":
            if not t.startswith(pre):
                return False
            t = t[len(pre):]
            if post == "":
                return True
            for i in range(len(t) + 1):
                if match(post, t[i:]):
                    return True
        return False
    pattern = pattern.replace("\\*", "\\[star_lit]").replace("\\#", "\\[pound_lit]")
    if pattern == "*":
        result = True
    else:
        result = match(pattern, text)
    return not result if negate else result


def match_pattern(pattern, values):
    star_idx = None
    star_name = None
    for i, p in enumerate(pattern):
        if not isinstance(p, str):
             continue
        if p.startswith("..."):
            star_idx = i
            star_name = p[3:]
            break
    if star_idx is None:
        if len(pattern) != len(values):
            return None
        bindings = {}
        for p, v in zip(pattern, values):
            if not isinstance(p, str):
                if p != v: return None
                continue
            elif p.startswith('"') and p.endswith('"') and p[1:-1] != v:
                return None
            else:
                bindings[p] = v
        return bindings
    head = pattern[:star_idx]
    tail = pattern[star_idx + 1:]
    if len(values) < len(head) + len(tail):
        return None
    head_values = values[:len(head)]
    tail_values = values[-len(tail):] if tail else []
    bindings = {}
    for p, v in zip(head, head_values):
        if not isinstance(p, str):
             if p != v: return None
             continue
        elif p.startswith('"') and p.endswith('"') and p[1:-1] != v:
             return None
        else:
            bindings[p] = v
    for p, v in zip(tail, tail_values):
        if not isinstance(p, str):
             if p != v: return None
             continue
        elif p.startswith('"') and p.endswith('"') and p[1:-1] != v:
             return None
        else:
            bindings[p] = v
    mid = values[len(head):len(values) - len(tail)] if tail else values[len(head):]
    if not mid:
        return None
    bindings[star_name] = mid
    return bindings


def nest_math(tokens):
    if not tokens:
        return None
    expect_operand = True
    for i, tok in enumerate(tokens):
        if expect_operand:
            if isinstance(tok, (int, float)):
                expect_operand = False
            elif tok in unary_ops:  # still expecting operand after unary
                continue
            else:
                return None
        else:  # expect operator
            if tok in precedence:
                expect_operand = True
            else:
                return None
    if expect_operand:  # expression ended on operator
        return None
    def process(tokens, level):
        if level == 0:
            return tokens
        # collect operators of this level
        ops = [op for op, prec in precedence.items() if prec == level]
        result = Expression()
        i = 0
        while i < len(tokens):
            tok = tokens[i]
            if tok in ops and tok in unary_ops:  # unary op
                if i+1 >= len(tokens):
                    return None
                right = tokens[i+1]
                result.append(Expression([tok, right]))
                i += 2
            elif tok in ops:  # binary op
                if not result or i+1 >= len(tokens):
                    return None
                left = result.pop()
                right = tokens[i+1]
                result.append(Expression([left, tok, right]))
                i += 2
            else:
                result.append(tok)
                i += 1
        return process(result, level-1)
    max_prec = max(precedence.values())
    res = process(tokens, max_prec)
    if res:
        return res[0]

simple_ops = {
    '+': lambda a, b: a + b,
    '-': lambda a, b: a - b,
    '*': lambda a, b: a * b,
    '/': lambda a, b: a / b,
    '//': lambda a, b: a // b,
    '%': lambda a, b: a % b,
    '%%': lambda x, y: constants.true if x % y == 0 else constants.false,
    '<': lambda a, b: constants.true if a < b else constants.false,
    '<=': lambda a, b: constants.true if a <= b else constants.false,
    '>': lambda a, b: constants.true if a > b else constants.false,
    '>=': lambda a, b: constants.true if a >= b else constants.false,
    '==': lambda a, b: constants.true if a == b else constants.false,
    '!=': lambda a, b: constants.true if a != b else constants.false,
    'and': lambda a, b: constants.true if a and b else constants.false,
    'or': lambda a, b: constants.true if a or b else constants.false,
    'in': lambda a, b: constants.true if a in b else constants.false,
    'is': lambda a, b: constants.true if a is b else constants.false,
    "**": lambda a, b: a ** b,
    "=": lambda name, value: {name: value},
    "=>": lambda text, pattern: constants.true if glob_match(pattern, text) else constants.false,
    "..": lambda min, max: my_range(min, max),
    "..+": lambda min, max: my_range(min, max+1),
    "isinstanceof": lambda ins, typ: constants.true if isinstance(ins, typ) else constants.false,
}

type_annotations = {
    "primitive::int": int,
    "primitive::string": str,
    "primitibe::float": float,
    "primitive::object.reference": objects.reference_type,
    "primitive::object.function": objects.function_type,
    "primitive::object": objects.object_type,
    "primitive::sequence": list | set | tuple,
    "c::int": c_int, "c::uint": c_uint,
    "c::double": c_double,
    "c::float": c_float,
    "c::char": c_char,
    "c::byte": c_byte, "c::ubyte": c_ubyte,
    "c::short": c_short, "c::ushort": c_ushort,
    "c::long": c_long, "c::ulong": c_ulong,
    "c::bool": c_bool,
    "py::object": object,
}

dpl_constants = {
    "py::none": None,
    "py::true": True,
    "py::false": False
}

type_to_name = {value: name for name, value in (type_annotations | dpl_constants).items()}

fmt_format = fmt.format
fmt_old_format = fmt.old_format

rget = varproc.rget
get_debug = varproc.get_debug

execute_code = None  # to be set by py_parser

tag_handlers = {}


def tag_handler(name=None):
    def _(fn):
        nonlocal name
        if name is None:
            name = fn.__name__
        tag_handlers[name] = fn
        return fn
    return _


def nest_args(tokens):
    "Magic thing."
    stack = [[]]
    for token in tokens:
        if not isinstance(token, str):
            stack[-1].append(token)
            continue
        if token in OPEN_P:
            new_list = []
            stack[-1].append(new_list)
            stack.append(new_list)
        elif token in CLOSE_P:
            if len(stack) == 1:
                raise ValueError("Mismatched parentheses")
            stack.pop()
            if token == ")":
                stack[-1].append(tuple(stack[-1].pop()))
            elif token == "]":
                stack[-1].append(Expression(stack[-1].pop()));
            else:
                assert False, "SHOULD NOT BE REACHED!"
        else:
            stack[-1].append(token)
    if len(stack) > 1:
        raise ValueError(f"Mismatched parentheses: {tokens}")
    return stack[0]


def parse_match(frame, body, value):
    "Parse a match statement."
    # TODO: Split this function for
    # preruntime - like how switch compiles into _intern.switch
    # runtime - like how _intern.switch is ran but with the match thingy.
    name = None
    np = 0
    ft = False # fallthrough
    if value != constants.nil:
        for p, [pos, file, ins, block, args] in enumerate(body):
            if ins == "as":
                varproc.rset(frame[-1], process_arg(frame, args[0]), value)
            elif ins == "case":
                if (v := process_arg(frame, args[0])) or ft:
                    if ft:
                        ft = False
                    res = execute_code(block, frame=frame)
                    if res != error.FALLTHROUGH:
                        return res
                    ft = True
            elif ins == "with":
                if (v := process_arg(frame, args[0])) == value or ft:
                    if ft:
                        ft = False
                    res = execute_code(block, frame=frame)
                    if res != error.FALLTHROUGH:
                        return res
                    ft = True
            elif ins == "default":
                if name:
                    frame[-1][name] = value
                return execute_code(block, frame=frame)
    else:
        for p, [pos, file, ins, args] in enumerate(body):
            if ins == "case":
                if (v := process_arg(frame, args[0])) or ft:
                    if ft:
                        ft = False
                    if name:
                        frame[-1][name] = value
                    res = execute_code(block, frame=frame)
                    if res != error.FALLTHROUGH:
                        return res
                    ft = True
            elif ins == "default":
                if name:
                    frame[-1][name] = value
                return execute_code(block, frame=frame)
    return 0


def parse_dict(frame, temp_name, body):
    data = {} if not isinstance(temp_name, objects.object_type) else temp_name
    varproc.rset(frame[-1], temp_name, data)
    p = 0
    while p < len(body):
        [pos, file, ins, block, args] = body[p]
        args = process_args(frame, args)
        argc = len(args)
        if ins == "set" and argc == 3 and args[1] == "=":
            name, _, value = args
            data[name] = value
        elif ins == "def" and argc == 1:
            name, = args
            if not data:
                data[name] = 0
            else:
                data[name] = tuple(data.items())[-1][1] + 1
        elif ins == "defi" and argc == 1:
            val, = args
            if not data:
                data[0] = val
            else:
                data[tuple(data.items())[-1][0] + 1] = val
        elif ins == "declare" and argc > 0:
            for name in args:
                data[name] = constants.nil
        elif ins == "dict" and argc == 1:
            tmp = [data]
            if parse_dict(tmp, args[0], block):
                return 1
        elif ins == "list" and argc == 1:
            tmp = [data]
            if parse_list(tmp, args[0], block):
                return 1
        else:
            error.error(pos, file, f"Invalid statement!")
            return 1
        p += 1


def parse_list(frame, temp_name, body):
    data = []
    varproc.rset(frame[-1], temp_name, data)
    p = 0
    while p < len(body):
        [pos, file, ins, block, args] = body[p]
        args = process_args(frame, args or [])
        argc = len(args)
        if ins == "expand" and argc == 1:
            data.extend(args[0])
        elif ins == "." and argc == 1:
            data.append(args[0])
        elif ins == "dict" and argc == 0:
            tmp = [{}]
            if parse_dict(tmp, "???", block):
                return 1
            data.append(tmp[-1]["???"])
        elif ins == "list" and argc == 0:
            tmp = [{}]
            if parse_list(tmp, "???", block):
                return 1
            data.append(tmp[-1]["???"])
        else:
            error.error(pos, file, f"Invalid statement!")
            return 1
        p += 1


def parse_string(frame, temp_name, body, new_line=False, sep="\n"):
    data = []
    p = 0
    while p < len(body):
        [pos, file, ins, _, _] = body[p]
        data.append(process_arg(frame, ins))
        p += 1
    varproc.rset(frame[-1], temp_name, sep.join(data) if new_line else "".join(data))


def parse_struct(frame, ffi, s_name, body):
    names = ["typedef struct {"]
    for p, [pos, file, name, _, [eq, type]] in enumerate(body):
        if eq != "as":
            error.error(pos, file, f"Invalid statement!")
            return 1
        names.append("   " + type.name(name) + ";")
    names.append(f"}} {s_name};")
    ffi.cdef("\n".join(names))
    varproc.rset(frame[-1], s_name, f"{s_name}*")


def flatten_dict(d, parent_key="", sep=".", seen=None):
    if seen is None:
        seen = set()
    items = {}
    dict_id = id(d)
    if dict_id in seen:
        return d
    seen.add(dict_id)
    for key, value in d.items():
        if key in ("_global", "_nonlocal", "_meta"):
            continue
        if not isinstance(key, str):
            continue
        new_key = f"{parent_key}{sep}{key}" if parent_key else key
        if isinstance(value, dict):
            items.update(flatten_dict(value, new_key, sep, seen))
        elif isinstance(value, (list, tuple)):
            items[f"{new_key}"] = value
            for i, item in enumerate(value):
                items[f"{new_key}({i})"] = item
        else:
            items[new_key] = value
    seen.remove(dict_id)
    return items


methods = {}
matches = {}


def add_method(func_name, func, from_func=False):
    varproc.to_be_methods.add(func_name)
    if not from_func:
        methods[func_name] = func
    else:
        methods[func_name] = lambda frame, args: func(frame, None, *args)[0]

# Need I explain?
def is_int(arg):
    arg = arg.replace("_", "")
    if arg.count("-") > 1:
        return False
    return arg.replace("-", "").replace(",", "").isdigit()


def is_hex(arg):
    if not arg.startswith("0x"):
        return False
    try:
        int(arg[2:], 16)
        return True
    except:
        return False


def is_bin(arg):
    if not arg.startswith("0b"):
        return False
    try:
        int(arg[2:], 2)
        return True
    except:
        return False


def is_float(arg):
    arg = arg.replace("_", "")
    if arg.count("-") > 1 or 0 <= arg.count(".") > 1:
        return False
    return arg.replace("-", "").replace(",", "").replace(".", "").isdigit()


def is_id(arg):
    return arg.replace(".", "a").replace("_", "a").replace(":", "a").replace("?", "a").replace("-", "a").isalnum()


def is_reference_var(arg):
    if arg.endswith("::ref"):
        arg = arg[:-5]
        if arg.endswith("::tag"):
            arg = arg[:-5]
        return is_id(arg)
    return False


def is_deref(arg):
    return arg.endswith("::deref") and is_id(arg[:-7])


def is_read_var(arg):
    return arg.startswith(":") and is_id(arg[1:])


def is_special_read_var(arg):
    return arg.startswith("?:") and is_id(arg[2:])


def expr_preruntime(arg):
    "Process arguments at preprocessing"
    if not isinstance(arg, str):
        return arg
    elif is_int(arg):
        return int(arg.replace(",", ""))
    elif is_float(arg.replace(",", "")):
        return float(arg)
    elif is_bin(arg):
        return int(arg, 2)
    elif is_hex(arg):
        return int(arg, 16)
    elif arg == "true":
        return constants.true
    elif arg == "false":
        return constants.false
    elif arg == "none":
        return constants.none
    elif arg == "nil":
        return constants.nil
    elif arg == "...":
        return constants.elipsis
    elif arg == "infinity":
        return inf
    elif arg == "-infinity":
        return -inf
    elif arg == ".dict":
        return {}
    elif arg == ".list":
        return []
    elif arg == ".set":
        return set()
    elif arg == ".tuple":
        return set()
    elif arg == ".unique::static":
        return f"{uuid.uuid4()}::{VERSION.as_id()}::{int(time.time()*10000)}"
    elif arg in dpl_constants:
        arg = dpl_constants[arg]
    elif arg in type_annotations:
        arg = type_annotations[arg]
    elif arg == "π":
        return 22/7
    return arg


def handle_in_string_expr(text, data):
    args = nest_args(exprs_preruntime(group(text)))
    args = process_args(data, args)
    return evaluate(data, Expression(args))


def expr_runtime(frame, arg):
    "Process an argument at runtime"
    if isinstance(arg, Expression):
        return evaluate(frame, arg)
    elif not isinstance(arg, str):
        return arg
    elif is_read_var(arg):
        if varproc.debug_settings["allow_automatic_global_name_resolution"]:
            v = varproc.rget(
                frame[-1],
                arg[1:],
                default=None,
            )
            if v is None:
                v = varproc.rget(frame[0], arg[1:])
        else:
            v = rget(frame[-1], arg[1:])
        if get_debug("disable_nil_values") and v == constants.nil:
            raise Exception(f"{arg!r} is nil!")
        return v
    elif is_special_read_var(arg):
        if varproc.debug_settings["allow_automatic_global_name_resolution"]:
            v = varproc.rget(
                frame[-1],
                arg[2:],
                default=None,
                meta=True
            )
            if v is None:
                v = varproc.rget(frame[0], arg[1:], meta=True)
        else:
            v = rget(frame[-1], arg[2:])
        if get_debug("disable_nil_values") and v == constants.nil:
            raise Exception(f"{arg!r} is nil!")
        return v
    elif is_reference_var(arg):
        full_name = arg[:-5]
        return objects.make_reference(frame[-1]["_scope_number"], frame[-1]["_scope_uuid"], full_name, varproc.rget(
                frame[-1],
                full_name,
                default=varproc.rget(frame[0], full_name),
            ), {})
    elif is_deref(arg):
        reference = varproc.rget(
                frame[-1],
                arg[:-7],
                default=varproc.rget(frame[0], arg[:-7]),
        )
        return reference["value"]
    elif arg == ".input":
        return input()
    elif arg == ".unique":
        return f"{uuid.uuid4()}::{VERSION.as_id()}::{int(time.time()*10000)}"
    elif is_id(arg):
        return arg
    elif arg.startswith('"') and arg.endswith('"'):
        t = arg[1:-1]
        for c, cc in CHARS.items():
            t = t.replace(c, cc)
        return t
    elif arg.startswith("'") and arg.endswith("'"):
        text = arg[1:-1]
        for c, cc in CHARS.items():
            text = text.replace(c, cc)
        return fmt_format(text, frame, expr_fn=lambda text, _: handle_in_string_expr(text, frame))
    elif (arg.startswith("{") and arg.endswith("}")) or arg in sep or arg in special_sep:
        return arg
    elif arg in ("?tuple", "?args", "?float", "?int", "?string", "?bytes", "?set", "?list", "nil?", "none?", "def?") or arg in sym:
        return arg
    else:
        raise Exception(f"Invalid literal: {arg}")


def my_range(start, end):
    def pos(start, end):
        while start < end:
            yield start
            start += 1

    def neg(start, end):
        while start > end:
            yield start
            start -= 1

    return pos(start, end) if start < end else neg(start, end)


def is_static(code):
    for i in code:
        if isinstance(i, Expression) and len(i) == 3 and i[0] == "call::static":
            if not is_static(i[2]):
                name, args = i[1:]
                i.clear()
                i.extend(["call", f":_global.{name}", args])
        elif isinstance(i, (tuple, list)):
            if not is_static(i):
                return False
        elif not isinstance(i, str):
            continue
        elif i in RT_EXPR:
            return False
        elif is_read_var(i):
            return False
        # formatted string, must always be on runtime
        elif i.startswith("'") and i.startswith("'"):
            return False
    return True


def to_static(code, env=None):
    env = env or [{}]
    t = None
    if not isinstance(code, list):
        t = type(code)
        code = list(code)
    for pos, i in enumerate(code):
        if isinstance(i, Expression):
            if is_static(i):
                value = evaluate(env, to_static(i, env=env))
                if isinstance(value, str):
                    code[pos] = f'"{value}"'
                else:
                    code[pos] = value
            else:
                code[pos] = to_static(i, env=env)
    return code if t is None else t(code)


class kwarg:
    def __init__(self, name, value=None):
        self.name = name
        self.value = value
    def keys():
        return [name]
    def __getitem__(self, _):
        return self.value
    def __repr__(self):
        return f"<{self.name} = {self.value!r}>"


def evaluate(frame, expression):
    "Evaluate an expression"
    if not isinstance(expression, Expression):
        return expression
    processed = process_args(frame, expression)
    # back then this was just one layer
    # of it statements
    # now if the length is not the correct one
    # we skip a barrage of conditions
    if processed:
        if processed[0] == "!":
            return processed[1:]
        elif processed[0] == ".":
            r = evaluate(frame, nest_math(processed[1:]))
            if r is None:
                error.error(0, "lib/core/arguments.py", f"Invalid expression: {Expression(processed[1:])!r}")
                raise error.DPLError(error.SYNTAX_ERROR)
            return r
        elif processed[0] == "lazy":
            return Lazy([frame, Expression(processed[1])])
        elif processed[0] == "dict":
            temp = {}
            for i in processed[1:]:
                temp.update(i)
            return temp
        elif processed[0] == "tuple":
            return tuple(processed[1:])
    if len(processed) == 3:
        e_ins = processed[0]
        if isinstance(processed[1], str) and processed[1] in simple_ops:
            return simple_ops[processed[1]](processed[0], processed[2])
        elif processed[1] == "->":
            obj, _, attr = processed
            return getattr(obj, attr, constants.nil)
        elif processed[0] == "?":
            return processed[1](*process_args(frame, processed[2]))
        elif e_ins == "pycall":
            args = pah.arguments_handler()
            args.parse(process_args(frame, processed[2]))
            return args.call(processed[1])
        elif e_ins == "fmt":
            return format(str(processed[1]), processed[2])
        elif e_ins == "call":
            return run_fn(processed[1]["capture"]["_frame_stack"], processed[1], *processed[2])
        elif e_ins == "call::static":
            func = varproc.rget(frame[-1], processed[1], default=None, resolve=True)
            return run_fn(func["capture"]["_frame_stack"], func, *processed[2])
        elif e_ins == "range":
            return tuple(my_range(processed[1], processed[2]))
        elif e_ins == "irange":
            return my_range(processed[1], processed[2])
        elif e_ins == "fn":
            return objects.make_function(
                frame,
                "::local",
                [(0, "::internal", "return", None, [Expression(processed[2])])],
                processed[1]
            )
        elif e_ins == "join":
            if isinstance(processed[1], dict):
                return "".join(map(lambda x: run_fn(frame, processed[1], x), processed[2]))
            else:
                return "".join(map(processed[1], processed[2]))
        elif e_ins == "pack":
            return utils.pack(processed[1], processed[2])
        elif e_ins == "vpack":
            return list(utils.pack(processed[1], processed[2]).values())
        elif processed[0] == "@" and processed[1] in methods:
            return methods[processed[1]](frame, process_args(frame, processed[2]))
        elif processed[0] == "@":
            return processed[1](frame, None, process_args(frame, processed[2]))[0]
    elif len(processed) == 2:
        e_ins = processed[0]
        if e_ins == "not":
            return constants.true if not processed[1] else constants.false
        elif e_ins == "nil?":
            return processed[1] == constants.nil
        elif e_ins == "none?":
            return processed[1] == constants.none
        elif e_ins == "def?":
            value = varproc.rget(frame[-1], processed[1], default=None)
            if value is None:
                return constants.false
            return constants.true
        elif e_ins == "?tuple":
            try:
                return tuple(processed[1])
            except:
                return constants.nil
        elif e_ins == "?se5":
            try:
                return set(processed[1])
            except:
                return constants.nil
        elif e_ins == "?dict":
            return str(processed[1])
        elif e_ins == "?bytes":
            try:
                item = processed[0]
                return bytes(item) if not isinstance(item, str) else item.encode("utf-8")
            except:
                return constants.nil
        elif e_ins == "?int":
            try:
                return int(processed[1])
            except:
                return constants.nil
        elif e_ins == "?float":
            try:
                return float(processed[1])
            except:
                return constants.nil
        elif e_ins == "?dict":
            try:
                return dict(processed[1])
            except:
                return constants.nil
        elif e_ins == "-":
            return -processed[1]
        elif e_ins == "~":
            return ~processed[1]
        elif e_ins == "type":
            return getattr(type(processed[1]), "__name__", constants.nil)
        elif e_ins == "sum":
            args = processed[1]
            t = type(args[0])
            start = args[0]
            for i in args[1:]:
                start += t(i)
            return start
        elif e_ins == "eval":
            return evaluate(frame, processed[1])
        elif e_ins == "oldformat":
            local = flatten_dict(frame[-1])
            text = processed[1]
            return fmt_old_format(text, local)
        elif e_ins == "to_ascii":
            return chr(processed[1])
        elif e_ins == "from_ascii":
            return ord(processed[1])
        elif e_ins == "len":
            return len(processed[1])
        elif e_ins == "head:body:tail":
            head, *rest, tail = processed[1]
            return head, rest, tail
        elif e_ins == "head:body":
            head, *rest = processed[1]
            return head, rest
        elif e_ins == "body:tail":
            *rest, tail = processed[1]
            return rest, tail
        elif e_ins == "head":
            return processed[1][0]
        elif e_ins == "tail":
            return processed[1][-1]
        elif e_ins == "join":
            return "".join(map(str, processed[1]))
        elif e_ins == "typeof":
            for type_ in type_to_name:
                if isinstance(processed[1], type_):
                    return type_to_name[type_]
            return "?::unknown"
        elif e_ins == "dpercent":
            min, max = process_args(frame, processed[1])
            return (abs(max - min)/((max + min)/2)) * 100
        elif e_ins == "median":
            min, max = process_args(frame, processed[1])
            return ((max - min)/2)+min
        elif e_ins == "irange":
            return range(processed[1])
        elif e_ins == "reverse":
            return type(processed[1])(reversed(processed[1]))
        elif e_ins == "ireverse":
            return reversed(processed[1])
        elif e_ins == "range":
            return tuple(range(processed[1]))
        elif e_ins == "unpack":
            return utils.unpack(frame[-1], processed[1])
        elif isinstance(processed[1], tuple):
            try:
                return processed[0][process_arg(frame, processed[1][0])]
            except:
                return constants.nil
    elif len(processed) == 4:
        if processed[0] == "join" and processed[2] == "with":
            return processed[3].join(map(str, processed[1]))
        elif processed[1] == "or" and processed[3] == "instead":
            return processed[0] if processed[0] else processed[2]
        elif processed[1] == "@":
            args = pah.arguments_handler(process_args(frame, processed[3]))
            return args.call(getattr(processed[0], processed[2]))
    elif len(processed) == 5:
        if processed[0] == "join" and processed[3] == "with":
            if isinstance(processed[1], dict):
                return processed[4].join(map(lambda x: run_fn(frame, processed[1], x), processed[2]))
            else:
                return processed[4].join(map(processed[1], processed[2]))
        elif processed[1] == "if" and processed[3] == "else":
            return evaluate(frame, processed[0] if processed[2] else processed[4])
    elif 1 > len(processed) <= 4 and processed[0] == "slice":
        return slice(*processed[1:])
    for name, fn in matches.items():
        try:
            if not (res:=fn(frame, default)) is None:
                return res
        except:
            raise Exception(f"Error while evaluating: {default}\nMatcher: {name}\n{traceback.format_exc()}") from None
    raise Exception(f"Unknown expression: {Expression(processed)!r}")


varproc.evaluate = evaluate
sep = " ,"
special_sep = "@()+/*[]π<>=!π%"
sym = [">=", "<=", "->", "=>", "==", "!=", "**", "//", "%%", "..", "..+", "]."]


def group(text):
    res = []
    str_tmp = ""
    id_tmp = []
    this = False
    rq = False
    quotes = {"str": '"', "pre": "}", "str1": "'"}
    str_type = "str"
    text = iter(text)
    for i in text:
        if str_tmp:
            if this:
                str_tmp += "\\"+i
                this = False
                continue
            if i == "\\":
                this = 1
            elif i == quotes[str_type]:
                text = str_tmp + quotes[str_type]
                res.append(text)
                str_tmp = ""
            else:
                str_tmp += i
            continue
        elif i in sep:
            if id_tmp:
                res.append("".join(id_tmp))
                id_tmp.clear()
        elif i in special_sep:
            if id_tmp:
                res.append("".join(id_tmp))
                id_tmp.clear()
            res.append(i)
        elif i in "\"{'":
            if id_tmp:
                res.append("".join(id_tmp))
                id_tmp.clear()
            str_tmp = i
            if i == '"':
                str_type = "str"
            elif i == "{":
                str_type = "pre"
            elif i == "'":
                str_type = "str1"
            else:
                str_type = "str"
        else:
            id_tmp.append(i)
    if id_tmp:
        res.append("".join(id_tmp))
    nres = []
    while res:
        i = res.pop(0)
        if not isinstance(i, str):
            nres.append(i)
        elif res and isinstance(res[0], str) and (tmp:=i+res[0]) in sym:
            nres.append(tmp)
            res.pop(0)
        else:
            nres.append(i)
    return nres


def exprs_preruntime(args):
    return [*map(expr_preruntime, args)]

def process_arg(frame, e):
    return expr_runtime(frame, e)

def process_args(frame, e):
    return list(map(lambda x: process_arg(frame, x), e))

class argproc_setter:
    def set_execute(func):
        global execute_code
        execute_code = func
        return func
    def set_run_fn(func):
        global run_fn
        run_fn = func
        return func
