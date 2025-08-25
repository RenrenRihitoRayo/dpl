if __name__ != "__dpl__":
    raise Exception()

from flask import Flask, session, request
from threading import Lock


# Flask runs functions in threads
# Make sure its thread safe
run_lock = Lock()

ext = dpl.extension(meta_name="flask")
app = None

frame_stack["flask"] = {
    "session": session
}


@ext.add_function()
def app(_, path):
    global app
    app =  Flask("DPL:SCRIPT (the path is set automatically without needing a real module name)")
    app.root_path = path


@ext.add_function()
def route(frame, __, route, function, methods=("GET",)):
    def bind():
        def func(*args, **kwargs):
            with run_lock:
                dpl.varproc.nscope(frame).update(kwargs)
                frame[-1]["_returns"] = ("_flask",)
                frame[-1]["request"] = {
                    "method": request.method,
                    "form": dict(request.form)
                }
                for name, value in zip(args, function["args"]):
                    frame[-1][name] = value
                if (err:=dpl.execute_code(function["body"], frame)) > 0:
                    raise dpl.error.DPLError(err)
                dpl.varproc.pscope(frame)
                return frame[-1]["_flask"] if "_flask" in frame[-1] else None
        return func
    app.add_url_rule(route, function["name"], bind(), methods=methods)


@ext.add_function()
def run_app(_, __, port=5000):
    app.run(port=port)
