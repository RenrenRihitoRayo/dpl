# A simple way of making objects and methods n stuff...

from . import varproc
from . import constants

class object_type(dict):
    def __repr__(self):
        return "<object>"

class reference_type(object_type):
    def __repr__(self):
        return f"<reference {self['name']} in scope {self['scope']}:{self['scope_uuid']}>"

class function_type(object_type):
    def __repr__(self):
        return f"<function {self['name']}({', '.join(self['args'])})>"

def make_reference(scope_index, scope_uuid, name, value, data=constants.none):
    return reference_type({
        "scope": scope_index,
        "scope_uuid": scope_uuid,
        "name": name,
        "value": value,
        "tag": data,
    })

def set_repr(frame, name="???", type_name=None, repr=None, func=False):
    if "_internal" not in frame:
        frame["_internal"] = {
            "name": name,
            "type": f"type:{type_name or name}",
            "docs": "An object.",
        }
    if func:
        return frame
    if "_im_repr" not in frame:
        frame["_im_repr"] = {  # define a boring default _im_repr
            "name": 0,
            "args": [],
            "defaults": 0,
            # "self": 0,
            "variadic": {
                "name": constants.nil,
                "index": 0
            },
            "body": [
                (
                    0,
                    "_internal",
                    "return",
                    (repr or f"<{type_name or 'Object'} {name}>",),
                )
            ],
        }
    return frame


def make_function(name, body, params):
    vname = constants.nil
    vindex = 0
    for pos, an in enumerate(params):
        if an.startswith("variadic:"):
            vindex = pos
            vname = an[9:]
            break
    return function_type(set_repr(
        {
            "name": name,
            "body": body,
            "args": params,
            "capture": constants.nil,
            "variadic":{
                "name": vname,
                "index": vindex,
            },
            "tags": { # tags for DPL to treat functions differently.
                "preserve-args": False, # save un-evaluated arguments?
            },
        },
        name,
        "builtin-function-object",
        func=True
    ))

def make_object(name):
    return object_type(set_repr(
        {
            "_internal": {
                "name": name,
                "type": f"type:{name}",
                "instance_name": f"{name}:root"
            }
        },
        name,
        "builtin-object:Object",
    ))
