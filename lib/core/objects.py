# A simple way of making objects and methods n stuff...

from . import varproc
from . import constants


def make_reference(scope_index, name, value, data=constants.none):
    return {
        "scope": scope_index,
        "name": name,
        "value": value,
        "tag": data
    }

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
            "self": 0,
            "body": [
                (
                    0,
                    "_internal",
                    "return",
                    (repr or f"<{type_name or 'Object'} {name}>",),
                )
            ],
        }
    if "to_int" not in frame:
        frame["to_int"] = {  # define a boring default _im_repr
            "name": 0,
            "args": [],
            "defaults": 0,
            "self": 0,
            "body": [
                (
                    0,
                    "_internal",
                    "return",
                    (constants.none,),
                )
            ],
        }
    if "to_float" not in frame:
        frame["to_float"] = {  # define a boring default _im_repr
            "name": 0,
            "args": [],
            "defaults": 0,
            "self": 0,
            "body": [
                (
                    0,
                    "_internal",
                    "return",
                    (constants.none,),
                )
            ],
        }
    if "to_str" not in frame:
        frame["to_str"] = {  # define a boring default _im_repr
            "name": 0,
            "args": [],
            "defaults": 0,
            "self": 0,
            "body": [
                (
                    0,
                    "_internal",
                    "return",
                    (constants.none,),
                )
            ],
        }
    if "to_list" not in frame:
        frame["to_list"] = {  # define a boring default _im_repr
            "name": 0,
            "args": [],
            "defaults": 0,
            "self": 0,
            "body": [
                (
                    0,
                    "_internal",
                    "return",
                    (constants.none,),
                )
            ],
        }
    if "to_dict" not in frame:
        frame["to_dict"] = {  # define a boring default _im_repr
            "name": 0,
            "args": [],
            "defaults": 0,
            "self": 0,
            "body": [
                (
                    0,
                    "_internal",
                    "return",
                    (constants.none,),
                )
            ],
        }
    if "to_none" not in frame:
        frame["to_none"] = {  # define a boring default _im_repr
            "name": 0,
            "args": [],
            "defaults": 0,
            "self": 0,
            "body": [
                (
                    0,
                    "_internal",
                    "return",
                    (constants.none,),
                )
            ],
        }
    if "to_nil" not in frame:
        frame["to_nil"] = {  # define a boring default _im_repr
            "name": 0,
            "args": [],
            "defaults": 0,
            "self": 0,
            "body": [
                (
                    0,
                    "_internal",
                    "return",
                    (constants.nil,),
                )
            ],
        }
    return frame


def make_function(name, body, params):
    vname = constants.nil
    vindex = 0
    for pos, name in enumerate(params):
        if name.startswith("variadic:"):
            vindex = pos
            vname = name[9:]
    return set_repr(
        {
            "name": name,
            "body": body,
            "args": params,
            "self": constants.nil,
            "memoize": {},
            "capture": constants.nil,
            "variadic":{
                "name": vname,
                "index": vindex,
            }
        },
        name,
        "builtin-function-object",
        func=True
    )


def make_method(name, body, params, self):
    return set_repr(
        {
            "name": name,
            "body": body,
            "args": params,
            "self": self,
            "defaults": {},
            "capture":constants.nil
        },
        name,
        "builtin-method-object",
        func=True
    )


def make_object(name):
    return set_repr(
        {
            "_internal": {
                "name": name,
                "type": f"type:{name}",
                "instance_name": f"{name}:root"
            }
        },
        name,
        "builtin-object:Object",
    )
