
-- Test script for DPL/Lua using Lupa!

test = require("test")
print(test.some_func(), test.some_var)

if type(__dpl__) == "nil" then
    -- Check if its being included via dpl
    error("DPL only script!")
elseif type(__dpl_debug__) ~= "nil" then
    print("Debug mode.")
end

-- dpl.pycall(py_function: Callable, args: None | list, kwargs: dict) -> None
-- dpl.pycall provides *args and **kwargs passing.
-- To call functions using those.
-- args can be set to null indicating no positional arguments
-- this is to reduce memory overhead in creating a table

-- Provide an alias for dpl
dpl = api.dpl

ext = dpl.pycall(dpl.extension, null, {meta_name = "lua_hello"})
ext:add_func("hi")(function(frame, locdir)
    -- frame: Current scope context
    -- locdir: Local directory of the script that called it
    print("Hello Pythonistas, Lua, and DPL programmers!\nLocal " .. locdir)
end)