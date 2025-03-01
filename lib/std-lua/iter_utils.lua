

if type(api) == "nil" then
    error()
end

ext = api.dpl.pycall(api.dpl.extension, nil, {meta_name="iter_utils"})

map = ext:add_func("map")
(function(frame, locdir, func, list)
    for pos, i in python.enumerate(list) do
        list[pos] = func(i)
    end
end)

ext:add_method("map", true)(map)