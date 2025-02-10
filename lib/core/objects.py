# A simple way of making objects and methods n stuff...

from . import varproc
from . import constants

def set_repr(frame, name="???", type_name=None, repr=None):
    if "_internal" not in frame:
        frame["_internal"] = {
            "name":name,
            "type":f"type:{type_name or name}",
            "docs":"An object."
        }
    if "_im_repr" not in frame:
        frame["_im_repr"] = { # define a boring default _im_repr
            "name":0,
            "args":[],
            "defs":0,
            "docs":f"Default internal method for ({name}).",
            "self":0,
            "body":[
                (0, "_internal", "return", (repr or f"<{type_name or 'Object'} {name}>",))
            ]
        }
    return frame

def make_function(name, body, params):
    return set_repr({
        "name":name,
        "body":body,
        "args":params,
        "self":constants.nil,
        "docs":f"Function. ({name!r})",
        "defs":{}
    }, name, "builtin-function-object")

def make_method(name, body, params, self):
    return set_repr({
        "name":name,
        "body":body,
        "args":params,
        "self":self,
        "docs":f"Method of {varproc.rget(self, '_internal.name')}. ({name})",
        "defs":{}
    }, name, "builtin-method-object")

def make_object(name):
    return set_repr({
        "_internal":{
            "name":name,
            "type":f"type:{name}",
            "docs":f"An object. ({name})"
        }
    }, name, "builtin-object:Object")