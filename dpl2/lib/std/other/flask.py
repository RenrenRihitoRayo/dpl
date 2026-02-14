if __name__ != "__dpl__":
    raise Exception()

from flask import (
    Flask,
    render_template_string,
    session,
    request,
    redirect,
    url_for,
)
import json
from flask_session import Session
from threading import Lock
import os


# Flask runs functions in threads
# Make sure its thread safe
run_lock = Lock()

ext = dpl.extension(meta_name="flask")
app = None

flask_data = frame_stack[0]["flask"] = {
    "session": session,
    "app": app,
    "config": None
}


@ext.add_method("to_json", from_func=True)
@ext.add_function("to_json")
def _(_, __, data):
    return json.dumps(data),


@ext.add_method("from_json", from_func=True)
@ext.add_function("from_json")
def _(_, __, data):
    return json.loads(data),


@ext.add_method("url_for", from_func=True)
@ext.add_function("url_for")
def _(_, __, name):
    return url_for(name),


@ext.add_method("redirect", from_func=True)
@ext.add_function("redirect")
def _(_, __, url, data):
    return redirect(url, **(data or {})),


@ext.add_function()
def app(_, path, secret_key=None):
    global app
    app =  Flask("DPL:SCRIPT (the path is set automatically without needing a real module name)")
    app.root_path = path
    flask_data["app"] = app
    if secret_key is not None:
        app.secret_key = secret_key


@ext.add_function()
def init_session(_, path):
    Session(app)
    flask_data["config"] = app.config


@ext.add_function()
def route(frame, _, route, function, methods=("GET",)):
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
                if (err := dpl.execute_code(function["body"], frame)) > 0:
                    raise dpl.error.DPLError(err)
                dpl.varproc.pscope(frame)
                return frame[-1]["_flask"] if "_flask" in frame[-1] else None
        return func
    app.add_url_rule(route, function["name"], bind(), methods=methods)


@ext.add_function()
def serve_file(frame, path, name, data=None):
    if not os.path.isfile(file := os.path.join(path, name)):
        if "_returns" in frame[-1]:
            frame[-2][frame[-1]["_returns"][0]] = ("file not found", 404)
        return
    else:
        if "_returns" in frame[-1]:
            frame[-2][frame[-1]["_returns"][0]] = render_template_string(open(file).read(), **(data or {}))
            return dpl.error.STOP_FUNCTION


@ext.add_function()
def serve_raw_file(frame, path, name):
    if not os.path.isfile(file := os.path.join(path, name)):
        if "_returns" in frame[-1]:
            frame[-2][frame[-1]["_returns"][0]] = ("file not found", 404)
        return
    else:
        if "_returns" in frame[-1]:
            frame[-2][frame[-1]["_returns"][0]] = open(file).read()
            return dpl.error.STOP_FUNCTION


@dpl.tag_handler("flask:route")
def route_tag(frame, path, func, url, methods=("GET",)):
    route(frame, None, url, func, methods)


@ext.add_function()
def run_app(_, __, port=5000):
    app.run(port=port)
