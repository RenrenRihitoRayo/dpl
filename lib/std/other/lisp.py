
ext = dpl.extension(meta_name="lisp")

@ext.add_function()
def add_fn(env, _, name, func):
    env[-1][name] = {"dpl": True, "body": func}

@ext.add_function("eval")
def eval_expr(env, _, code):
    code = dpl.arguments.process_args(env, code)
    res = None
    print("::", code)
    match code:
        case ["define", name, value]:
            res = env[-1][name] = eval_expr(env, None, value)
        case ["define", name, list(params), *body]:
            res = env[-1][name] = {"args": params, "body": body}
        case ["lambda", list(params), *body]:
            res = {"args": params, "body": body}
        case [name, *args] if (func := dpl.varproc.rget(env[-1], name, resolve=True)):
            print(":: call", name, args, func) 
            if "python" in func:
                return func["body"](env, args)
            elif "dpl" in func:
                return dpl.call_func(env, func["body"], args)
            dpl.varproc.nscope(env).update(zip(func["args"], args))
            for expr in func["body"]:
                res = eval_expr(env, None, expr)
            dpl.varproc.pscope(env)
        case _:
            return code
    return res

