# A module to explain in extending DPL

# Every function recieves two arguments
# by default. 'frame' and 'file' which is the
# execution context and the file path of the
# origin of the instruction.

# Any other following arguments will be
# the given arguments.

if __name__ != "__dpl__":
    raise Exception

@add_func()
def my_instruction(frame, file):
    # Set 'my_var' to 138
    varproc.rset(frame[-1], "my_var", 138)
    # frame[-1] means the local or current
    # scope
    
    # Must always return a tuple or list.
    return 138//2,