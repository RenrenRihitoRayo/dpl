

if type(api) == "nil" then
    error()
end

ext = api.dpl.pycall(api.dpl.extension, nil, {meta_name="iter_utils"})

ext:add_func("run")(function(frame, _, body) return api.dpl.run_code(body, frame) end)

ext:add_func("map")
(function(frame, locdir, func, list)
    for pos, i in python.enumerate(list) do
        list[pos] = func(i)
    end
end)