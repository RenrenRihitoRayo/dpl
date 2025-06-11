from .py_parser2_internals.py_parser2_internals import *

# define built ins from here
@instruction
def op_call(context, name, arguments):
    arguments = process_args(context.frame, arguments)
    fn = rget(context.frame[-1], name, default=rget(context.frame[0], name, default=None))
    if fn is None or fn == constants.nil:
        print(f"Error [{context.file}:{context.line}] Function {name} isnt defined!")
        return error.RUNTIME_ERROR
    fn(context.frame, context.file, *arguments)

@inc_instruction
def op_while(context, cond):
    context.instruction_pointer, block = get_block(context.instruction_pointer, context.code)
    if block is None:
        return error.SYNTAX_ERROR
    while process_arg(context.frame, cond):
        if err:=execute(block, context.frame):
            if err == error.SKIP_RESULT:
                continue
            elif err == error.STOP_RESULT:
                break
            elif err == STOP_FUNCTION:
                continue
            else:
                return err

@instruction
def op_assign(context, name, value):
    name = process_arg(context.frame, name)
    value = process_arg(context.frame, value)
    rset(context.frame[-1], name, value)

@instruction
def op_raise(context, code, message=None):
    print(f"Raise error code {code}" + "" if message is None else f" with message {message}")

@instruction
def op_if(context, cond):
    context.instruction_pointer, block = get_block(context.instruction_pointer, context.code)
    if block is None:
        return error.SYNTAX_ERROR
    if process_arg(context.frame, cond):
        if err:=execute(block, context.frame):
            return err

@instruction
def op_fn(context, name, *args):
    ...

@register_hlir_matcher
def dpl_matcher(line):
    match line:
        case ["set", name, "=", value]:
            return op_assign(name, value)
        case ["while", cond]:
            return op_while(cond)
        case ["if", cond]:
            return op_if(cond)
        case ["end"]:
            return (0, (), {})
        case [func, *args]:
            return op_call(func, args)