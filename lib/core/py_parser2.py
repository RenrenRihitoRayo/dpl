# py_parser2.py - The brother of the parser.
# prototype for the new execution loop

from .runtime import *
from .py_parser import process, get_block
import traceback


def get_var(frame, name, default=constants.nil, resolve_name=False):
    "Helper function to automatically resolve to global scope."
    value = rget(frame[-1], name)
    if value == constants.nil:
        value = rget(frame[0], name, default=default)
        name = f"_global.{name}"
    if resolve_name:
        return name, value
    else:
        return value

class instruction:
    class resolved:
        def __init__(self, name, func):
            self.value = func
            self.name = name
        def __repr__(self):
            return self.name

class executor:
    "A class that can be used easily to run DPL code,\nand even your own language if modified."
    instructions = {}
    def __init__(self, code, frame=None):
        "Make an executor instance."
        if isinstance(code, str):
            code = process(code)
        if isinstance(code, int):
            raise error.DPLError(code) from None
        elif isinstance(code, list):
            self.code = code
            self.frame = frame or new_frame()
        else:
            self.code, self.frame = code["code"], code["frame"]
        if frame:
            self.frame[0].update(frame[0])
        self.instruction_pointer = 0
    @staticmethod
    def add_intrinsic(name=None):
        "Add an intrinsic.\nBuiltin functions have already been defined in executor.instructions,\nclear it to define your own."
        def wrapper(func):
            executor.instructions[name or func.__name__] = func
            return func
        return wrapper
    def resolve_instructions(self):
        "Resolve the instructions."
        cache = []
        for file, pos, ins, oargs in self.code:
            if ins in executor.instructions:
                cache.append((file, pos, instruction.resolved(ins, executor.instructions[ins]), oargs))
            else:
                cache.append((file, pos, ins, oargs))
        self.code.clear()
        self.code.extend(cache)
    def run(self):
        "Run the code inside the current instance."
        while self.instruction_pointer < len(self.code):
            file, pos, ins, oargs = self.code[self.instruction_pointer]
            if not oargs is None:
                try:
                    args = process_args(self.frame, oargs)
                    argc = len(args)
                    if debug_settings["type_checker"]:
                        if (tmp:=(pos, file, ins)) not in tc_cache:
                            tc_cache.add(tmp)
                            if not check_ins(ins, args):
                                itypesr = get_ins(ins, args)
                                if itypesr is None and not varproc.is_debug_enabled("TC_DEFAULT_WHEN_NOT_FOUND"):
                                    error.error(pos, file, f"Type signature for {ins} is not defined.\nUse tc_register to register your function.")
                                    return error.TYPE_ERROR
                                itypes = tuple(map(lambda x: getattr(x, "__name__", x), itypesr))
                                atypes = tuple(map(lambda x: type(x).__name__, args))
                                error.error(pos, file, f"Type mismatch [{ins}]: Expected {itypes} but got {atypes}")
                                return error.TYPE_ERROR
                except Exception as e:
                    error.error(
                        pos,
                        file,
                        f"Something went wrong when arguments were processed:\n{e}\n> {oargs!r}",
                    )
                    return error.PYTHON_ERROR
            else:
                args = []
                argc = 0
            # Instead of O(n) we can get O(1)
            # or at least the closest we can go.
            if not isinstance(ins, instruction.resolved):
                if (func:=get_var(self.frame, ins)) != constants.nil \
                and isinstance(func, dict):
                    nscope(self.frame)
                    self.frame[-1].update(dict(zip(func["args"], args)))
                    if func["self"]:
                        self.frame[-1]["self"] = func["self"]
                    if func["capture"]:
                        self.frame[-1]["_capture"] = func["capture"]
                    res = executor(func["body"], self.frame).run()
                    pscope(self.frame)
                    if res == error.STOP_FUNCTION:
                        self.instruction_pointer += 1
                        continue
                    if res: return res
                    self.instruction_pointer += 1
                    continue
                elif hasattr(func, "__code__"):
                    try:
                        func_params = ext_s.get_py_params(func)[2:]
                        if func_params and any(map(lambda x: x.endswith("_body") or x.endswith("_xbody"), func_params)):
                            t_args = []
                            for i in func_params:
                                if i.endswith("_xbody"):
                                    temp = get_block(code, instruction_pointer, start=0)
                                    if temp is None:
                                        error.error(pos, file, f"Function '{function.__name__}' expected a block!")
                                        return (error.RUNTIME_ERROR, error.SYNTAX_ERROR)
                                    instruction_pointer, body = temp
                                    t_args.append(body)
                                elif i.endswith("_body"):
                                    temp = get_block(code, instruction_pointer)
                                    if temp is None:
                                        error.error(pos, file, f"Function '{function.__name__}' expected a block!")
                                        return (error.RUNTIME_ERROR, error.SYNTAX_ERROR) # say "runtime error" caised by "syntax error"
                                    instruction_pointer, body = temp
                                    t_args.append(body)
                                else:
                                    t_args.append(args.pop(0))
                        else:
                            t_args = args
                        res = ext_s.call(
                            func, self.frame, varproc.meta_attributes["internal"]["main_path"], t_args
                        )
                        if isinstance(res, int) and res:
                            return res
                        elif isinstance(res, str):
                            if res == "break":
                                break
                            elif res.startswith("err:"):
                                _, ecode, message = res.split(":", 2)
                                error.error(pos, file, message)
                                return int(ecode)
                    except:
                        error.error(pos, file, traceback.format_exc()[:-1])
                        return error.PYTHON_ERROR
                    self.instruction_pointer += 1
                    continue
                else:
                    error.error(
                        pos, file,
                        f"Invalid instruction: {ins}"
                    )
                    return error.RUNTIME_ERROR
            try:
                if err:=ins.value(self, file, pos, *args):
                    if err == error.STOP_FUNCTION:
                        self.instruction_pointer += 1
                        continue
                    if err: return err
            except Exception as e:
                error.error(
                    pos, file,
                    traceback.format_exc()
                )
                return error.PYTHON_ERROR
            self.instruction_pointer += 1
        return 0
    def reset(self):
        "Reset the current instance."
        self.instruction_pointer = 0

# implement bare minimum for testing.

@executor.add_intrinsic()
def _test(*_):
    print("This was a test for the new parser.", _)

@executor.add_intrinsic("_intern.switch")
def _(parser, file, pos, switch_body, switch_value):
    return executor(switch_body.get(switch_value, switch_body[None]), frame=parser.frame).run()

@executor.add_intrinsic("set")
def _(parser, file, pos, name, _eq, value):
    if _eq != "=":
        return error.SYNTAX_ERROR
    rset(parser.frame[-1], name, value)

@executor.add_intrinsic("if")
def _(parser, file, pos, value):
    temp = get_block(parser.code, parser.instruction_pointer)
    if not temp:
        return error.SYNTAX_ERROR
    parser.instruction_pointer, body = temp
    if value and body:
        return executor(body, frame=parser.frame).run()

@executor.add_intrinsic()
def fn(parser, file, pos, name, params):
    temp = get_block(parser.code, parser.instruction_pointer)
    if not temp:
        return error.SYNTAX_ERROR
    parser.instruction_pointer, body = temp
    rset(parser.frame[-1], name, make_function(
        name = name,
        body = body,
        params = params
    ))

@executor.add_intrinsic()
def loop(parser, file, pos, iterations=None):
    temp = get_block(parser.code, parser.instruction_pointer)
    if not temp:
        return error.SYNTAX_ERROR
    parser.instruction_pointer, body = temp
    if not body:
        return
    if iterations is None:
        while True:
            err = executor(body, frame=parser.frame).run()
            if err == error.SKIP_RESULT:
                continue
            elif err == error.STOP_RESULT or err == error.STOP_FUNCTION:
                break
            elif err > 0:
                break
    else:
        for _ in range(iterations):
            err = executor(body, frame=parser.frame).run()
            if err == error.SKIP_RESULT:
                continue
            elif err == error.STOP_RESULT or err == error.STOP_FUNCTION:
                break
            elif err > 0:
                break

@executor.add_intrinsic()
def inc(parser, file, pos, name):
    resolved_name, value = get_var(parser.frame, name, default=0, resolve_name=True)
    rset(parser.frame[-1], resolved_name, value+1)

@executor.add_intrinsic()
def dec(parser, file, pos, name):
    resolved_name, value = get_var(parser.frame, name, default=0, resolve_name=True)
    rset(parser.frame[-1], resolved_name, value-1)

@executor.add_intrinsic()
def START_TIME(parser, file, pos):
    parser.start_time = time.perf_counter()

@executor.add_intrinsic()
def STOP_TIME(parser, file, pos):
    parser.end_time = time.perf_counter()

@executor.add_intrinsic()
def LOG_TIME(parser, file, pos, message=None):
    ct, unit = utils.convert_sec(parser.end_time - parser.start_time)
    error.info(f"Elapsed time: {(' '+message+' ') if message else ''} {ct:,.8f}{unit}")

@executor.add_intrinsic()
def match(parser, file, pos, value):
    temp = get_block(parser.code, parser.instruction_pointer)
    if temp is None:
       return error.SYNTAX_ERROR
    else:
        parser.instruction_pointer, body = temp
        if (err := parse_match(parser.frame, body, value)) > 0:
           return err

@executor.add_intrinsic("println")
def _(_, __, ___, *values):
    print(*values)

@executor.add_intrinsic("print")
def _(_, __, ___, *values):
    print(*values, end="")

@executor.add_intrinsic("while")
def _(parser, file, pos, value):
    temp = get_block(parser.code, parser.instruction_pointer)
    if temp is None:
       return error.SYNTAX_ERROR
    else:
        parser.instruction_pointer, body = temp
        print(body)
        if not body:
            return
        while evaluate(parser.frame, value):
            err = executor(body, frame=parser.frame).run()
            if err == error.SKIP_RESULT:
                continue
            elif err == error.STOP_RESULT or err == error.STOP_FUNCTION:
                break
            elif err > 0:
                break

@executor.add_intrinsic("for")
def _(parser, file, pos, name, _in, value):
    if _in != "in":
        return error.SYNTAX_ERROR
    temp = get_block(parser.code, parser.instruction_pointer)
    if temp is None:
       return error.SYNTAX_ERROR
    else:
        parser.instruction_pointer, body = temp
        if not body:
            return
        for i in value:
            parser.frame[-1][name] = i
            err = executor(body, frame=parser.frame).run()
            if err == error.SKIP_RESULT:
                continue
            elif err == error.STOP_RESULT or err == error.STOP_FUNCTION:
                break
            elif err > 0:
                break

@executor.add_intrinsic()
def catch(parser, file, pos, values, _eq, func_name, *args):
    if _eq != "=":
        return error.SYNTAX_ERROR
    func = get_var(parser.frame, func_name)
    if func == constants.nil:
        error.error(pos, file, f"{func_name} does not exist!")
        return error.NAME_ERROR
    nscope(parser.frame)
    parser.frame[-1]["_returns"] = values
    parser.frame[-1].update(dict(zip(func["args"], args)))
    if func["self"]:
        parser.frame[-1]["self"] = func["self"]
    if func["capture"]:
        parser.frame[-1]["_capture"] = func["capture"]
    res = executor(func["body"], parser.frame).run()
    pscope(parser.frame)
    if res == error.STOP_FUNCTION:
        ...
    elif res: return res

@executor.add_intrinsic("return")
def _(parser, file, pos, *values):
    if (temp:=parser.frame[-1].get("_returns")) is not None:
        for name, value in zip(temp, values):
            rset(parser.frame[-1], f"_nonlocal.{name}", value)
    return error.STOP_FUNCTION

@executor.add_intrinsic()
def skip(_, __, ___):
    return error.SKIP_RESULT

@executor.add_intrinsic()
def stop(_, __, ___):
    return error.STOP_RESULT

@executor.add_intrinsic("exit")
def _(_, __, ___, code=0):
    exit(code)

@executor.add_intrinsic("_intern.jump")
def _(parser, _, __, index, condition=...):
    if condition == ...:
        parser.instruction_pointer = index
    else:
        if condition:
            parser.instruction_pointer = index

@executor.add_intrinsic("_intern.get_index")
def _(parser, _, __, name):
    rset(parser.frame[-1], name, parser.instruction_pointer)