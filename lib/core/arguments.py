# Used to handle arguments and expressions
# NOT FOR THE CLI

from . import state
from . import constants
from . import error
from . import varproc
from .info import *

# Functions in utils that ciuldnt be imported


def flatten_dict(d, parent_key="", sep=".", seen=None):
    if seen is None:
        seen = set()
    items = {}
    dict_id = id(d)
    if dict_id in seen:
        return d
    seen.add(dict_id)
    for key, value in d.items():
        new_key = f"{parent_key}{sep}{key}" if parent_key else key
        if isinstance(value, dict):
            items.update(flatten_dict(value, new_key, sep, seen))
        elif isinstance(value, list):
            items[f"{new_key}"] = value
            for i, item in enumerate(value):
                items[f"{new_key}[{i}]"] = item
        else:
            items[new_key] = value
    seen.remove(dict_id)
    return items


# Use to make the argument handler to handle
# char literals
class char:
    def __init__(self, value):
        self.val = value

    def __repr__(self):
        return self.val


methods = {}


# Need I explain?
def is_int(arg):
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
    return arg.replace("-", "").replace(",", "").replace(".", "").isdigit()


def is_id(arg):
    return arg.replace(".", "").replace("_", "").isalnum()


def is_sid(arg):
    return arg.startswith("name{") and arg.endswith("}")


def is_var(arg):
    return arg.startswith("%") and is_id(arg[1:])


def is_fvar(arg):
    return arg.startswith(":") and is_id(arg[1:])


def is_svar(arg):
    return arg.startswith("%{") and arg.endswith("}")


def is_sfvar(arg):
    return arg.startswith(":{") and arg.endswith("}")


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
    elif arg == "[]":
        return []
    return arg


def expr_runtime(frame, arg):
    "Process an argument at runtime"
    if isinstance(arg, char):
        return arg.val
    elif not isinstance(arg, str):
        return arg
    if is_id(arg):
        return arg
    elif is_var(arg):
        return varproc.rget(frame[-1], arg[1:], default=varproc.rget(frame[0], arg[1:]))
    elif is_fvar(arg):
        return varproc.rget(
            frame[-1],
            arg[1:],
            default=varproc.rget(frame[0], arg[1:], meta=False),
            meta=False,
        )
    elif is_svar(arg):
        return varproc.rget(
            frame[-1], arg[2:-1], default=varproc.rget(frame[0], arg[2:-1])
        )
    elif is_sfvar(arg):
        return varproc.rget(
            frame[-1],
            arg[2:-1],
            default=varproc.rget(frame[0], arg[2:-1], meta=False),
            meta=False,
        )
    elif is_sid(arg):
        return arg[5:-1]
    else:
        return expr_preruntime(arg)


def add_method(name=None, from_func=False, process=True):
    def wrapper(func):
        fname = name if name is not None else getattr(func, "__name__", "_dump")
        methods[fname] = (
            lambda *arg: func(None, None, *arg) if from_func else func,
            process,
        )
        return func

    return wrapper


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


def evaluate(frame, expression):
    "Evaluate an expression"
    ins, *args = expression
    if ins in methods:
        if methods[ins][0]:
            args = bs_thing(frame, args)
        return methods[ins][1](frame, *args)
    match (expression):
        case ["Range", arg]:
            arg = express(frame, arg)
            return tuple(range(arg))
        case ["dRange", start, end]:
            start = express(frame, start)
            end = express(frame, end)
            return tuple(my_range(start, end))
        case ["dRawRange", start, end]:
            start = express(frame, start)
            end = express(frame, end)
            return my_range(start, end)
        case ["RawRange", arg]:
            arg = express(frame, arg)
            return range(arg)
        case ["Sum", *items]:
            items = exprs_runtime(frame, items)
            start_t = type(items[0])
            start = start_t()
            for i in items:
                try:
                    start += i
                except:
                    start += start_t(i)
            return start
        case ["Index", lst, index]:
            return express(frame, lst)[express(frame, index)]
        case [op1, "+", op2]:
            return express(frame, op1) + express(frame, op2)
        case [op1, "..", op2]:
            return str(express(frame, op1)) + str(express(frame, op2))
        case [op1, "-", op2]:
            return express(frame, op1) - express(frame, op2)
        case [op1, "*", op2]:
            return express(frame, op1) * express(frame, op2)
        case [op1, "/", op2]:
            return express(frame, op1) / express(frame, op2)
        case [op1, "%", op2]:
            return express(frame, op1) % express(frame, op2)
        case [op1, "^", op2]:
            return express(frame, op1) ** express(frame, op2)
        case [op1, "caseless{==}", *op2]:
            express(frame, op2)[0].lower()
            return (
                constants.true
                if express(frame, op1).lower() == bs_thing(frame, op2)[0].lower()
                else constants.false
            )
        case [op1, "caseless{!=}", *op2]:
            return (
                constants.true
                if express(frame, op1).lower() != bs_thing(frame, op2)[0].lower()
                else constants.false
            )
        case [op1, "caseless{>}", *op2]:
            return (
                constants.true
                if express(frame, op1).lower() > bs_thing(frame, op2)[0].lower()
                else constants.false
            )
        case [op1, "caseless{<}", *op2]:
            return (
                constants.true
                if express(frame, op1).lower() < bs_thing(frame, op2)[0].lower()
                else constants.false
            )
        case [op1, "caseless{>=}", *op2]:
            return (
                constants.true
                if express(frame, op1).lower() >= bs_thing(frame, op2)[0].lower()
                else constants.false
            )
        case [op1, "caseless{<=}", *op2]:
            return (
                constants.true
                if express(frame, op1).lower() <= bs_thing(frame, op2)[0].lower()
                else constants.false
            )
        case [op1, "==", op2]:
            v1, v2 = express(frame, op1), express(frame, op2)
            return constants.true if v1 is v2 or v1 == v2 else constants.false
        case [op1, "!=", op2]:
            v1, v2 = express(frame, op1), express(frame, op2)
            return constants.true if v1 is v2 or v1 != v2 else constants.false
        case [op1, ">", op2]:
            return (
                constants.true
                if express(frame, op1) > express(frame, op2)
                else constants.false
            )
        case [op1, "<", op2]:
            return (
                constants.true
                if express(frame, op1) < express(frame, op2)
                else constants.false
            )
        case [op1, ">", "=", op2]:
            return (
                constants.true
                if express(frame, op1) >= express(frame, op2)
                else constants.false
            )
        case [op1, "<", "=", op2]:
            return (
                constants.true
                if express(frame, op1) <= express(frame, op2)
                else constants.false
            )
        case ["not", op1]:
            return constants.true if not express(frame, op1) else constants.false
        case [op1, "or", op2]:
            return (
                constants.true
                if express(frame, op1) or express(frame, op2)
                else constants.false
            )
        case [op1, "and", op2]:
            return (
                constants.true
                if express(frame, op1) and express(frame, op2)
                else constants.false
            )
        case [*op1, "in", op2]:
            return (
                constants.true
                if bs_thing(frame, op1)[0] in express(frame, op2)
                else constants.false
            )
        case ["LenOf", op1]:
            value = express(frame, op1)
            if hasattr(value, "__len__"):
                return len(value)
            else:
                return state.bstate("nil")
        case ["ToInt", op1]:
            value = express(frame, op1)
            try:
                return int(value)
            except:
                return state.bstate("nil")
        case ["ToFloat", op1]:
            value = express(frame, op1)
            try:
                return int(value)
            except:
                return state.bstate("nil")
        case ["ToStr", op1]:
            value = express(frame, op1)
            return str(value)
        case ["IsType", op1, t]:
            value = express(frame, op1)
            vtype = express(frame, t)
            return constants.true if isinstance(value, vtype) else constants.false
        case ["Append", lst, item]:
            (lst := expr_runtime(frame, lst)).append(express(frame, item))
            return lst
        case ["Pop", list(lst)]:
            return lst.pop() if lst else state.bstate("nil")
        case _:
            return state.bstate("nil")


def exprs_runtime(frame, args):
    "Process arguments at runtime"
    args = list(args)
    put = []
    res = []
    p = 0
    while p < len(args):
        c = args[p]
        if not isinstance(c, str):
            res.append(c)
        elif c.startswith("("):
            args[p] = c[1:]
            c = ""
            k = 1
            put.clear()
            while p < len(args) and k:
                c = args[p]
                put.append(str(c))
                p += 1
                if isinstance(c, str):
                    if c.startswith("("):
                        k += 1
                    elif c.endswith(")"):
                        k -= 1
            p -= 1
            put[-1] = put[-1][:-1]
            while "" in put:
                put.remove("")
            res.append(evaluate(frame, put))
        elif c.startswith("["):
            args[p] = c[1:]
            c = ""
            put.clear()
            k = 1
            while p < len(args) and k:
                c = args[p]
                put.append(str(c))
                p += 1
                if isinstance(c, str):
                    if c.startswith("["):
                        k += 1
                    elif c.endswith("]"):
                        k -= 1
            p -= 1
            put[-1] = put[-1][:-1]
            while "" in put:
                put.remove("")
            res.append([*bs_thing(frame, put)])
        elif c.startswith("!["):
            args[p] = c[2:]
            c = ""
            put.clear()
            k = 1
            while p < len(args) and k:
                c = args[p]
                put.append(str(c))
                p += 1
                if isinstance(c, str):
                    if c.startswith("["):
                        k += 1
                    elif c.endswith("]"):
                        k -= 1
            p -= 1
            put[-1] = put[-1][:-1]
            while "" in put:
                put.remove("")
            res.append((*bs_thing(frame, put),))
        elif c.startswith('"') and c.endswith('"'):
            text = c[1:-1]
            res.append(text)
        elif c.startswith("'") and c.endswith("'"):
            text = c[1:-1]
            d = flatten_dict(frame[-1]).items()
            for c, cc in d:
                text = text.replace(f"${{{c}}}", str(cc))
            res.append(text)
        elif c.startswith("<") and c.endswith(">"):
            res.append(c)
        else:
            res.append(expr_runtime(frame, c))
        p += 1
    return res


sep = " ,"
special_sep = "()+/-*[]<>?"


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
                if i == "n":
                    str_tmp.append("\n")
                elif i == "r":
                    str_tmp.append("\r")
                elif i == "t":
                    str_tmp.append("\t")
                elif i == "b":
                    str_tmp.append("\b")
                elif i == "f":
                    str_tmp.append("\f")
                elif i == "a":
                    str_tmp.append("\a")
                elif i == "v":
                    str_tmp.append("\v")
                else:
                    str_tmp.append(i)
                this = False
                continue
            if i == "\\":
                this = True
            elif i == quotes[str_type]:
                text = "".join(str_tmp) + quotes[str_type]
                if rq:
                    text = f'"{text}"'
                res.append(text)
                str_tmp.clear()
                rq = False
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
        elif i == "!":
            rq = True
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
    return res


def exprs_preruntime(args):
    return [*map(expr_preruntime, args)]


def express(frame, e):
    return expr_runtime(frame, expr_preruntime(e))


def bs_thing(frame, e):
    return exprs_runtime(frame, exprs_preruntime(group(" ".join(map(str, e)))))
