# A simple way of making objects and methods n stuff...

from itertools import zip_longest
from copy import deepcopy as copy
from . import varproc
from . import constants

run_code = None


def register_run(run):
    global run_code
    run_code = run


class object_type(dict):
    def __instancecheck__(self, instance):
        return instance["_type_name"] == self["_type_name"]

    def __call__(self, *args):
        data = copy(self)
        data.update(zip(filter(lambda x: not x.startswith("_"), self.keys()), args))
        return data

    def __repr__(self):
        if "_instance_name" in self:
            return f'<instance {self["_instance_name"]} of object {self["_type_name"]}>'
        return f'<object {self["_type_name"]}>'

    def __dpl_repr__(self):
        methods = []
        attributes = []
        implicit = []
        for name, value in self.items():
            if name.startswith("_"):
                continue
            if isinstance(value, function_type):
                methods.append(value.__repr__(True))
            else:
                if value == constants.nil:
                    implicit.append(name)
                else:
                    attributes.append(name)
        return f'<object {self["_type_name"]}\n  instance name: {self["_instance_name"] if "_instance_name" in self else "class definition"}\n  attrs: {", ".join(attributes) or "no attributes"}\n  implicit attributes: {", ".join(implicit) if implicit else "no implicit attributes"}\n  methods:\n    {(","+chr(10)+"    ").join(methods) if methods else "no methods"}>'


class reference_type(object_type):
    def __repr__(self):
        return f"<reference {self['name']} = {self['value']!r} in scope {self['scope']}:{self['scope_uuid']}>"


class function_type(object_type):
    def __repr__(self, less=False):
        if not less and self["self"]:
            return f"<method {self['name']}({', '.join(self['args'])}) of {self['self']['_type_name']}>"
        if less:
            return f"{self['name']}({', '.join(self['args'])})"
        return f"<function {self['name']}({', '.join(self['args'])})>"

    def __dpl_repr__(self, less=False):
        if not less and self["self"]:
            return f"<method {self['name']}({', '.join(self['args'])}) of {self['self']['_type_name']}>"
        if less:
            return f"{self['name']}({', '.join(self['args'])})"
        return f"<function {self['name']}({', '.join(self['args'])})>"


objects = (
    reference_type,
    function_type
)



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
    return function_type({
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
        "self": None,
        })


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
    return function_type({
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
    })


def make_object(name, frame=None):
    return object_type({
        "_type_name": name,
        "_frame": frame
    })
