# A simple way of making objects and methods n stuff...

from itertools import zip_longest
from . import varproc
from . import constants

class object_type(dict):
    def __repr__(self):
        return f"<object {self['_name']}>"

class reference_type(object_type):
    def __repr__(self):
        return f"<reference {self['name']} = {self['value']!r} in scope {self['scope']}:{self['scope_uuid']}>"

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


def make_function(name, body, params):
    vname = constants.nil
    vindex = 0
    defs = {}
    params_ = []
    for n in params:
        if isinstance(n, dict):
            (n, v), = n.items()
            defs[n] = v
        params_.append(n)
    for pos, an in enumerate(params_):
        if an.startswith("variadic:"):
            vindex = pos
            vname = an[9:]
            break
    return function_type(
        {
            "name": name,
            "body": body,
            "args": params_,
            "capture": constants.nil,
            "variadic":{
                "name": vname,
                "index": vindex,
            },
            "tags": { # tags for DPL to treat functions differently.
                "preserve-args": False, # save un-evaluated arguments?
            },
            "defaults": defs,
        }
    )

def make_method(name, body, params, self):
    vname = constants.nil
    vindex = 0
    defs = {}
    params_ = []
    for n in params:
        if isinstance(n, dict):
            (n, v), = n.items()
            defs[n] = v
        params_.append(n)
    for pos, an in enumerate(params_):
        if an.startswith("variadic:"):
            vindex = pos
            vname = an[9:]
            break
    return function_type(
        {
            "name": name,
            "body": body,
            "args": params_,
            "capture": constants.nil,
            "variadic":{
                "name": vname,
                "index": vindex,
            },
            "tags": { # tags for DPL to treat functions differently.
                "preserve-args": False, # save un-evaluated arguments?
            },
            "defaults": defs,
            "self": self,
        },
    )

def make_object(name):
    return object_type(
        {
            "_name": name,
        },
    )
