# py_parser2.py - The brother of the parser.
# prototype for the new execution loop

from ..runtime import *
from ..py_parser import process_code, register_execute, register_process_hlir, get_run

hlir_matcher_registry = []
def end_block(): ... # not meant to do anything
op_code_registry = [end_block]
run = get_run()
inc_op_code = set()

def get_block(current_p, code, supress=False, start=1):
    "Get a code block"
    instruction_pointer = current_p + 1
    _, _, [ins, _, _] = code[instruction_pointer]
    k = start
    if k == 0 and ins not in info.INCREAMENTS:
        error.error(pos, file, "Expected to have started with an instruction that indents.")
        return instruction_pointer, None
    res = []
    while instruction_pointer < len(code):
        _, _, [ins, _, _] = code[instruction_pointer]
        if ins in inc_op_code:
            k += 1
        elif ins == 0:
            k -= 1
        if k == 0:
            break
        instruction_pointer += 1
    else:
        if not supress:
            print(f"Error in line {pos} file {file!r}\nCause: Block wasnt closed!")
        return instruction_pointer, None
    return instruction_pointer, code[current_p+(2-start):instruction_pointer]

def disassemble(code):
    "Disassemble llir"
    for pos, file, [ins, args, kwargs] in code:
        print(pos, file, op_code_registry[ins].__name__, args, kwargs)

def instruction(func):
    """
    This registers an instruction to op_code_registry.
    Uses the current length for the id.
    Please this is very sensitive on order so use
    this function rather than manually assigning op_codes.
    This returns a lambda `lambda *args: (op_code, args)`
    """
    op_code = len(op_code_registry)
    op_code_registry.append(func)
    return lambda *a, **kw: (op_code, a, kw)

def inc_instruction(func):
    """
    This registers an instruction to op_code_registry
    and inc_op_code, enabling this function to take a
    block of code when using get_block.
    Uses the current length for the id.
    Please this is very sensitive on order so use
    this function rather than manually assigning op_codes.
    This returns a lambda `lambda *args: (op_code, args)`
    """
    op_code = len(op_code_registry)
    op_code_registry.append(func)
    inc_op_code.add(op_code)
    return lambda *a, **kw: (op_code, a, kw)

def register_hlir_matcher(func):
    hlir_matcher_registry.append(func)

def process_line(line):
    """
    Loops through every matchers in hlir_matcher_registry.
    This are highly sensitive functions. Do not modify if
    you dont know what youre doing, unless youre
    Mr Zozin ;)
    """
    for matcher in hlir_matcher_registry:
        if (res:=matcher(line)) is not None:
            return res
    return None
    # ^^^
    # no matchers matched with line
    # handle this outside the function.

def process_hlir(frame):
    """
    Takes output from process_code (the HLIR)
    and compiles it down to an even more
    low level ir now LLIR, this to achive
    an even faster execution via dictionary
    dispatch.
    """
    code = frame["code"]
    res = []
    for [pos, file, ins, args] in code:
        line = process_line([ins, *(args or [])])
        if line is None:
            # op_raise will be an intrinsic, safe to hardcode it here.
            res = [(pos, file, op_raise(error.PRERUNTIME_ERROR, "Syntax error!"))]
            break
        if isinstance(line, list):
            for op in line:
                res.append((pos, file, op))
        else:
            res.append((pos, file, line))
    frame["code"] = res
    frame["llir"] = True

def execute(code, frame=None):
    class context:
        instruction_pointer = 0
        code = None
        frame = None
        file = None
        line = None
    if isinstance(code, int):
        return code
    if isinstance(code, dict):
        code, nframe = code["code"], code["frame"]
    else:
        nframe = new_frame()
    if frame is not None:
        frame[0].update(nframe[0])
    else:
        frame = nframe

    context.code = code
    context.frame = frame
    while context.instruction_pointer < len(code):
        pos, file, [ins, args, kwargs] = code[context.instruction_pointer]
        context.file = file
        context.line = pos
        if ins not in op_code_registry:
            print(f"Error [{file}:{pos}] Invalid op_code: {ins}")
            exit(1)
        if err:=op_code_registry[ins](context, *args, **kwargs):
            if err > 0:
                print(f"Error [{file}:{pos}] Instruction {op_code_registry[ins].__name__} raised an error!")
            return err
        context.instruction_pointer += 1

register_execute(execute)
register_process_hlir(process_hlir)