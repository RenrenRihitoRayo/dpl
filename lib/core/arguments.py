# Used to handle arguments and expressions
# NOT FOR THE CLI

from . import dpl_ctypes

globals().update(vars(dpl_ctypes))

from sys import flags
import traceback
import operator

inf = float("inf")

# custom type to distinguish lists and expressions
class Expression(list):
    ...

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
    '+': operator.add,
    '-': operator.sub,
    '*': operator.mul,
    '/': operator.truediv,
    '//': operator.floordiv,
    '%': operator.mod,
    '%%': lambda x, y: constants.true if x % y == 0 else constants.false,
    '<': lambda a, b: constants.true if operator.lt(a, b) else constants.false,
    '<=': lambda a, b: constants.true if operator.le(a, b) else constants.false,
    '>': lambda a, b: constants.true if operator.gt(a, b) else constants.false,
    '>=': lambda a, b: constants.true if operator.ge(a, b) else constants.false,
    '==': lambda a, b: constants.true if operator.eq(a, b) else constants.false,
    '!=': lambda a, b: constants.true if operator.ne(a, b) else constants.false,
    'and': lambda a, b: constants.true if a and b else constants.false,
    'or': lambda a, b: constants.true if a or b else constants.false,
    'in': lambda a, b: constants.true if a in b else constants.false,
    'is': lambda a, b: constants.true if a is b else constants.false,
    "**": operator.pow,
    "=": lambda name, value: {name: value},
    "=>": lambda text, pattern: constants.true if glob_match(pattern, text) else constants.false,
    "isinstanceof": lambda ins, typ: constants.true if isinstance(ins, typ) else constants.false,
}

chars = {
    "\\":"\\",
    "n": "\n",
    "b": "\b",
    "f": "\f",
    "v": "\v",
    "a": "\a",
    "r": "\r",
    "s": " ",
    "t": "\t",
    "N": "\n\r",
    "e": chr(27)
}

from . import objects

type_annotations = {
    "dpl::bool": int,
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
}

type_to_name = {value: name for name, value in (type_annotations | dpl_constants).items()}

from . import state
from . import constants
from . import varproc
from . import error
from .info import *
from . import py_argument_handler as pah
from . import fmt

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
        line = process_arg(frame, ins)
        data.append(line)
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


def is_preruntime_read_var(arg):
    return arg.startswith(".:") and is_id(arg[2:])


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
    args = exprs_preruntime(group(text))
    args = process_args(data, args)
    return evaluate(data, args)

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
                default=varproc.rget(frame[0], arg[1:]),
            )
        else:
            v = rget(frame[-1], arg[1:])
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


def is_static(frame, code):
    for i in code:
        if isinstance(i, list):
            if not is_static(frame, i):
                return False
        elif not isinstance(i, str):
            continue
        elif i in RT_EXPR:
            return False
        elif is_preruntime_read_var(i) and varproc.rget(frame[-1], i[2:], default=None) is None:
            return False
        elif is_read_var(i):
            return False
        # formatted string, must always be on runtime
        elif i.startswith("'") and i.startswith("'"):
            return False
    return True


def to_static(frame, code):
    for pos, i in enumerate(code):
        if isinstance(i, list):
            if is_static(frame, i):
                value = evaluate(frame, to_static(frame, i))
                if isinstance(value, str):
                    code[pos] = f'"{value}"'
                else:
                    code[pos] = value
            else:
                code[pos] = to_static(frame, i)
        elif not isinstance(i, str):
            continue
        elif is_preruntime_read_var(i) and (not (var:=varproc.rget(frame[-1], i[2:], default=None)) is None):
            code[pos] = var
    return code


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
    if not isinstance(expression, (list, tuple)):
        return expression
    processed = process_args(frame, expression)
    if len(processed) == 3 and isinstance(processed[1], str) and processed[1] in simple_ops:
        return simple_ops[processed[1]](processed[0], processed[2])
    elif processed and processed[0] == "!":
        return processed[1:]
    elif len(processed) == 2 and processed[0] == "not":
        return constants.true if not processed[1] else constants.false
    elif len(processed) == 2 and processed[0] == "-":
        return -processed[1]
    elif len(processed) == 2 and processed[0] == "~":
        return ~processed[1]
    elif len(processed) == 2 and processed[0] == "type":
        return getattr(type(processed[1]), "__name__", constants.nil)
    elif len(processed) == 2 and processed[0] == "sum":
        args = processed[1]
        t = type(args[0])
        start = args[0]
        for i in args:
            start += t(i)
        return start
    elif len(processed) == 2 and processed[0] == "eval":
        return evaluate(frame, processed[1])
    elif len(processed) == 2 and processed[0] == "oldformat":
        local = flatten_dict(frame[-1])
        text = processed[1]
        return fmt_old_format(text, local)
    elif len(processed) == 2 and processed[0] == "to_ascii":
        return chr(processed[1])
    elif len(processed) == 2 and processed[0] == "from_ascii":
        return ord(processed[1])
        return processed[1] % processed[2]
    elif len(processed) == 2 and processed[0] == "len":
        return len(processed[1])
    elif len(processed) == 2 and processed[0] == "head:body:tail":
        head, *rest, tail = processed[1]
        return head, rest, tail
    elif len(processed) == 2 and processed[0] == "head:body":
        head, *rest = processed[1]
        return head, rest
    elif len(processed) == 2 and processed[0] == "body:tail":
        *res, tail = processed[1]
        return rest, tail
    elif len(processed) == 2 and processed[0] == "head":
        return processed[1][0]
    elif len(processed) == 2 and processed[0] == "tail":
        return processed[1][-1]
    elif len(processed) == 3 and processed[0] == "pycall":
        args = pah.arguments_handler()
        args.parse(process_args(frame, processed[2]))
        return args.call(processed[1])
    elif len(processed) == 3 and processed[0] == "call":
        func, args = processed[1:]
        args = process_args(frame, args)
        varproc.nscope(frame)
        
        frame[-1]["_returns"] = ("_intern_result",)
        frame[-1].update({
            name: value
            for name, value
            in zip(func["args"], args)
        })
        if func["capture"]:
            frame[-1]["_capture"] = func["capture"]
        if func["self"] is not None:
            frame[-1]["self"] = func["self"]
        if err:=execute_code(func["body"], frame=frame):
            if err < 0: # control codes
                ...
            else:
                raise error.DPLError(err)
        if "_intern_result" in frame[-1]["_nonlocal"]:
            ret = frame[-1]["_nonlocal"]["_intern_result"]
        else:
            ret = constants.nil
        varproc.pscope(frame)
        return ret
    elif len(processed) == 2 and processed[0] == "typeof":
        for type in type_to_name:
            if isinstance(processed[1], type):
                return type_to_name[type]
        return "?::unknown"
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
                except:
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
        # ranges
        case ["rawrange", num]:
            return range(num)
        case ["range", num]:
            return tuple(range(num))
        case ["drange", num]:
            return tuple(my_range(0, num))
        case ["drawrange", num]:
            return my_range(0, num)
        case ["drange", num, end]:
            return tuple(my_range(num, end))
        case ["drawrange", num, end]:
            return my_range(num, end)
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
            if not hasattr(obj, attr):
                return constants.nil
            return obj.__getattr__(attr)
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
sym = [">=", "<=", "->", "=>", "==", "!=", "**", "//", "%%"]

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
                i = "\\"+i
                if i in chars:
                    str_tmp.append(chars[i])
                else:
                    str_tmp.append(i)
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
