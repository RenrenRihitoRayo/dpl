# Used to handle arguments and expressions
# NOT FOR THE CLI

from . import dpl_ctypes
from sys import flags
import traceback
from . import constants
from . import varproc
from . import error
from .info import *
from . import py_argument_handler as pah
from . import fmt
from . import objects

globals().update(vars(dpl_ctypes))

inf = float("inf")


# custom type to distinguish lists and expressions
class Expression(list):
    def __repr__(self):
        return "Expr"+super().__repr__()

run_fn = None


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
        if "*" not in p:
            return p.replace("\xFF\u200B", "*") == t

        pre, _, post = p.partition("*")

        if not t.startswith(pre):
            return False

        t = t[len(pre):]
        if post == "":
            return True
        for i in range(len(t) + 1):
            if match(post, t[i:]):
                return True
        return False
    pattern = pattern.replace("\\*", "\xFF\u200B")
    if pattern == "*":
        result = True
    else:
        result = match(pattern, text)
    return not result if negate else result

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
    "..": lambda min, max: range(min, max),
    "..+": lambda min, max: range(min, max+1),
    "isinstanceof": lambda ins, typ: constants.true if isinstance(ins, typ) else constants.false,
}

chars = {
    "\\": "\\",
    "n": "\n",
    "b": "\b",
    "f": "\f",
    "v": "\v",
    "a": "\a",
    "r": "\r",
    "s": " ",
    "t": "\t",
    "N": "\n\r",
    '"': '"',
    "'": "'",
    "e": chr(27)
}

type_annotations = {
    "dpl::int": int,
    "dpl::string": str,
    "dpl::float": float,
    "dpl::function": objects.function_type,
    "dpl::object": objects.object_type,
    "dpl::reference": objects.reference_type,
    "dpl::sequence": list | set | tuple,
    "py::int": int,
    "py::string": str,
    "py::float": float,
    "py::bool": bool,
    "py::dict": dict,
    "py::sequence": list | set | tuple,
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
                stack[-1].append(Expression(stack[-1].pop()))
            else:
                assert False, "SHOULD NOT BE REACHED!"
        else:
            stack[-1].append(token)
    if len(stack) > 1:
        raise ValueError(f"Mismatched parentheses: {tokens}")
    return stack[0]


def get_block(code, current_p):
    "Get a code block"
    pos, file, _, _ = code[current_p]
    p = current_p + 1
    k = 1
    res = []
    while p < len(code):
        _, _, ins, _ = code[p]
        if ins in INC_EXT:
            k += 1
        elif ins in INC:
            k -= INC[ins]
        elif ins in DEC:
            k -= 1
        if k == 0:
            break
        else:
            res.append(code[p])
        p += 1
    else:
        print(f"Error in line {pos} file {file!r}\nCause: Block wasnt closed!")
        return None
    return p, res


def parse_match(frame, body, value):
    "Parse a match statement."
    # TODO: Split this function for
    # preruntime - like how switch compiles into _intern.switch
    # runtime - like how _intern.switch is ran but with the match thingy.
    name = None
    np = 0
    ft = False # fallthrough
    if value != constants.nil:
        for p, [pos, file, ins, args] in enumerate(body):
            if ins == "as":
                varproc.rset(frame[-1], process_arg(frame, args[0]), value)
            elif ins == "case":
                if (v := process_arg(frame, args[0])) or ft:
                    if ft:
                        ft = False
                    temp = get_block(body, p)
                    if temp is None:
                        error.error(pos, file, "Expected a case block!")
                        return error.SYNTAX_ERROR
                    res = execute_code(temp[1], frame=frame)
                    if res != error.FALLTHROUGH:
                        return res
                    ft = True
            elif ins == "with":
                if (v := process_arg(frame, args[0])) == value or ft:
                    if ft:
                        ft = False
                    temp = get_block(body, p)
                    if temp is None:
                        error.error(pos, file, "Expected a case block!")
                        return error.SYNTAX_ERROR
                    res = execute_code(temp[1], frame=frame)
                    if res != error.FALLTHROUGH:
                        return res
                    ft = True
            elif ins == "default":
                temp = get_block(body, p)
                if temp is None:
                    error.error(pos, file, "Expected a case block!")
                    return error.SYNTAX_ERROR
                if name:
                    frame[-1][name] = value
                return execute_code(temp[1], frame=frame)
    else:
        for p, [pos, file, ins, args] in enumerate(body):
            if ins == "case":
                if (v := process_arg(frame, args[0])) or ft:
                    if ft:
                        ft = False
                    temp = get_block(body, p)
                    if temp is None:
                        error.error(pos, file, "Expected a case block!")
                        return error.SYNTAX_ERROR
                    if name:
                        frame[-1][name] = value
                    res = execute_code(temp[1], frame=frame)
                    if res != error.FALLTHROUGH:
                        return res
                    ft = True
            elif ins == "default":
                temp = get_block(body, p)
                if temp is None:
                    error.error(pos, file, "Expected a case block!")
                    return error.SYNTAX_ERROR
                if name:
                    frame[-1][name] = value
                return execute_code(temp[1], frame=frame)
    return 0


def parse_dict(frame, temp_name, body):
    data = {} if not isinstance(temp_name, objects.object_type) else temp_name
    varproc.rset(frame[-1], temp_name, data)
    p = 0
    while p < len(body):
        [pos, file, ins, args] = body[p]
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
            temp = get_block(body, p)
            if temp is None:
                return 1
            p, block = temp
            tmp = [data]
            if parse_dict(tmp, args[0], block):
                return 1
        elif ins == "list" and argc == 1:
            temp = get_block(body, p)
            if temp is None:
                return 1
            p, block = temp
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
        [pos, file, ins, args] = body[p]
        args = process_args(frame, args or [])
        argc = len(args)
        if ins == "expand" and argc == 1:
            data.extend(args[0])
        elif ins == "." and argc == 1:
            data.append(args[0])
        elif ins == "dict" and argc == 0:
            temp = get_block(body, p)
            if temp is None:
                return 1
            p, block = temp
            tmp = [{}]
            if parse_dict(tmp, "???", block):
                return 1
            data.append(tmp[-1]["???"])
        elif ins == "list" and argc == 0:
            temp = get_block(body, p)
            if temp is None:
                return 1
            p, block = temp
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
        [pos, file, ins, _] = body[p]
        data.append(process_arg(frame, ins))
        p += 1
    varproc.rset(frame[-1], temp_name, sep.join(data) if new_line else "".join(data))


def parse_struct(frame, ffi, s_name, body):
    names = ["typedef struct {"]
    for p, [pos, file, name, [eq, type]] in enumerate(body):
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
    elif arg == "neg_infinity":
        return -inf
    elif arg == ".dict":
        return {}
    elif arg == ".list":
        return []
    elif arg == ".set":
        return set()
    elif arg == ".tuple":
        return set()
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
            print(i)
            if is_static(i):
                value = evaluate(env, to_static(i, env=env))
                if isinstance(value, str):
                    code[pos] = f'"{value}"'
                else:
                    code[pos] = value
            else:
                code[pos] = to_static(i, env=env)
        elif isinstance(i, tuple):
            if is_static(i):
                value = tuple(evaluate(env, to_static(list(i), env=env)))
                if isinstance(value, str):
                    code[pos] = f'"{value}"'
                else:
                    code[pos] = value
            else:
                code[pos] = to_static(i, env=env)
        elif not isinstance(i, str):
            continue
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
    if processed and processed[0] == "!":
        return processed[1:]
    elif len(processed) == 3:
        if isinstance(processed[1], str) and processed[1] in simple_ops:
            return simple_ops[processed[1]](processed[0], processed[2])
        elif processed[0] == "pycall":
            args = pah.arguments_handler()
            args.parse(process_args(frame, processed[2]))
            return args.call(processed[1])
        elif processed[0] == "call":
            return run_fn(processed[1]["capture"]["_frame_stack"], processed[1], *processed[2])
        elif processed[0] == "call::static":
            func = varproc.rget(frame[-1], processed[1], default=None, resolve=True)
            if func is None:
                func = varproc.rget(frame[0], processed[1], default=None, resolve=True)
            if func is None:
                error.error("???", "???", f"Function {processed[1]!r} does not exist.")
                raise error.DPLError(error.PYTHON_ERROR)
            return run_fn(func["capture"]["_frame_stack"], func, *processed[2])
    elif len(processed) == 2:
        if processed[0] == "not":
            return constants.true if not processed[1] else constants.false
        elif processed[0] == "-":
            return -processed[1]
        elif processed[0] == "~":
            return ~processed[1]
        elif processed[0] == "type":
            return getattr(type(processed[1]), "__name__", constants.nil)
        elif processed[0] == "sum":
            args = processed[1]
            t = type(args[0])
            start = args[0]
            for i in args[1:]:
                start += t(i)
            return start
        elif processed[0] == "eval":
            return evaluate(frame, processed[1])
        elif processed[0] == "oldformat":
            local = flatten_dict(frame[-1])
            text = processed[1]
            return fmt_old_format(text, local)
        elif processed[0] == "to_ascii":
            return chr(processed[1])
        elif processed[0] == "from_ascii":
            return ord(processed[1])
        elif processed[0] == "len":
            return len(processed[1])
        elif processed[0] == "head:body:tail":
            head, *rest, tail = processed[1]
            return head, rest, tail
        elif processed[0] == "head:body":
            head, *rest = processed[1]
            return head, rest
        elif processed[0] == "body:tail":
            *rest, tail = processed[1]
            return rest, tail
        elif processed[0] == "head":
            return processed[1][0]
        elif processed[0] == "tail":
            return processed[1][-1]
        elif processed[0] == "typeof":
            for type_ in type_to_name:
                if isinstance(processed[1], type_):
                    return type_to_name[type_]
            return "?::unknown"
        elif processed[0] == "dpercent":
            min, max = process_args(frame, processed[1])
            return ((abs(min - max))/((min + max) * 2)) * 100
        elif processed[0] == "median":
            min, max = process_args(frame, processed[1])
            return ((max - min)/2)+min
        elif processed[0] == "irange":
            return range(processed[1])
        elif processed[0] == "reverse":
            return type(processed[1])(reversed(processed[1]))
        elif processed[0] == "ireverse":
            return reversed(processed[1])
        elif processed[0] == "range":
            return tuple(range(processed[1]))
    elif 1 > len(processed) <= 4 and processed[0] == "slice":
        return slice(*processed[1:])
    match (processed):
        # conditionals
        case ["if", value, "then", true_v, "else", false_v]:
            return true_v if value else false_v
        case [obj, tuple(index)]:
            if not obj:
                return constants.nil
            index = process_arg(frame, index[0])
            if isinstance(index, (str, int, float, tuple)) and isinstance(obj, dict):
                return obj.get(index, constants.nil)
            elif isinstance(index, int) and isinstance(obj, (str, tuple, list)):
                try:
                    return obj[index]
                except Exception as e:
                    return constants.nil
            else:
                return constants.nil
        # types
        case ["tuple", *lst]:
            return tuple(lst)
        case ["?tuple", lst]:
            return tuple(lst)
        case ["?set", lst]:
            return set(lst)
        case ["?dict", lst]:
            return dict(lst)
        case ["?string", item]:
            return str(item)
        case ["?bytes", item]:
            try:
                return bytes(item) if not isinstance(item, str) else item.encode("utf-8")
            except:
                return constants.nil
        case ["?int", item]:
            try:
                return int(item)
            except:
                return constants.nil
        case ["?float", item]:
            try:
                return float(item)
            except:
                return constants.nil
        case ["?dict", item]:
            try:
                return dict(item)
            except:
                return constants.nil
        case ["dict", *args]:
            temp = {}
            for i in args:
                temp.update(i)
            return temp
        # values
        case ["nil?", value]:
            return value == constants.nil
        case ["none?", value]:
            return value == constants.none
        case ["def?", name]:
            value = varproc.rget(frame[-1], name, default=None)
            if value is None:
                return constants.false
            return constants.true
        case [value1, "or", value2, "instead"]:
            return value1 if value1 else value2
        # values
        case ["set", name, "=", value]:
            varproc.rset(frame[-1], name, value)
            return value
        case ["@", method, tuple(args)] if method in methods:
            return methods[method](frame, process_args(frame, args))
        case ["?", method, tuple(args)]:
            return method(*process_args(frame, args))
        case ["@", ins, tuple(args)]:
            return ins(frame, None, *process_args(frame, args))[0]
        case [obj, "@", method, tuple(args)]:
            args = pah.arguments_handler(process_args(frame, args))
            return args.call(getattr(obj, method))
        case [obj, "->", attr]:
            return getattr(obj, attr, constants.nil)
        # other
        case default:
            for name, fn in matches.items():
                try:
                    if not (res:=fn(frame, default)) is None:
                        return res
                except:
                    raise Exception(f"Error while evaluating: {default}\nMatcher: {name}\n{traceback.format_exc()}") from None
    raise Exception(f"Unknown expression: {processed!r}")

sep = " ,"
special_sep = "@()+/*[]π<>=!π%"
sym = [">=", "<=", "->", "=>", "==", "!=", "**", "//", "%%", "..", "..+"]

def group(text):
    res = []
    str_tmp = []
    id_tmp = []
    this = False
    rq = False
    quotes = {"str": '"', "pre": "}", "str1": "'"}
    str_type = "str"
    for i in text:
        if str_tmp:
            if this:
                if i in chars:
                    str_tmp.append(chars[i])
                else:
                    str_tmp.append("\\"+i)
                this = False
                continue
            if i == "\\":
                this = True
            elif i == quotes[str_type]:
                text = "".join(str_tmp) + quotes[str_type]
                res.append(text)
                str_tmp.clear()
            else:
                str_tmp.append(i)
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
            str_tmp.append(i)
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
