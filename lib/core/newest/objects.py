# A simple way of making objects and methods n stuff...

from itertools import zip_longest
from copy import deepcopy as copy
import varproc
import constants
import error

run_code = None
run_fn = None

def register_run(run):
    global run_code
    run_code = run
    return run

def register_run_fn(run):
    global run_fn
    run_fn = run
    return run

class object_type(dict):
    def __instancecheck__(self, instance):
        return instance["_type_name"] == self["_type_name"]

    def __call__(self, *args):
        data = copy(self)
        data.update(zip(filter(lambda x: not x.startswith("_"), self.keys()), args))
        return data

    def __repr__(self):
        op_name = "_impl::repr"
        if op_name in self:
            method = self[op_name]
            return run_fn(method["capture"]["_frame_stack"], method)
        if "_instance_name" in self:
            return f'<instance {self["_instance_name"]} of object {self["_type_name"]}>'
        return f'<object {self["_type_name"]}>'

    def __add__(self, other):
        op_name = "_impl::add"
        if op_name in self:
            method = self[op_name]
            return run_fn(method["capture"]["_frame_stack"], method, other)
        return constants.nil
    
    def __sub__(self, other):
        op_name = "_impl::sub"
        if op_name in self:
            method = self[op_name]
            return run_fn(method["capture"]["_frame_stack"], method, other)
        return constants.nil
    
    def __mul__(self, other):
        op_name = "_impl::mul"
        if op_name in self:
            method = self[op_name]
            return run_fn(method["capture"]["_frame_stack"], method, other)
        return constants.nil
    
    def __div__(self, other):
        op_name = "_impl::div"
        if op_name in self:
            method = self[op_name]
            return run_fn(method["capture"]["_frame_stack"], method, other)
        return constants.nil
    
    def __pow__(self, other):
        op_name = "_impl::pow"
        if op_name in self:
            method = self[op_name]
            return run_fn(method["capture"]["_frame_stack"], method, other)
        return constants.nil
    
    def __floordiv__(self, other):
        op_name = "_impl::fdiv"
        if op_name in self:
            method = self[op_name]
            return run_fn(method["capture"]["_frame_stack"], method, other)
        return constants.nil
    
    def __mod__(self, other):
        op_name = "_impl::modulo"
        if op_name in self:
            method = self[op_name]
            return run_fn(method["capture"]["_frame_stack"], method, other)
        return constants.nil
    
    def __hash__(self):
        op_name = "_impl::hash"
        if op_name in self:
            method = self[op_name]
            return run_fn(method["capture"]["_frame_stack"], method)
        return super().__hash__()

    def __len__(self):
        op_name = "_impl::length"
        if op_name in self:
            method = self[op_name]
            return run_fn(method["capture"]["_frame_stack"], method)
        return super().__len__()
    
    def __rshift__(self, other):
        op_name = "_impl::right_shift"
        if op_name in self:
            method = self[op_name]
            return run_fn(method["capture"]["_frame_stack"], method, other)
        return constants.nil
    
    def __lshift__(self, other):
        op_name = "_impl::left_shift"
        if op_name in self:
            method = self[op_name]
            return run_fn(method["capture"]["_frame_stack"], method, other)
        return constants.nil
    
    def __and__(self, other):
        op_name = "_impl::logical_and"
        if op_name in self:
            method = self[op_name]
            return run_fn(method["capture"]["_frame_stack"], method, other)
        return constants.nil
    
    def __or__(self, other):
        op_name = "_impl::logical_or"
        if op_name in self:
            method = self[op_name]
            return run_fn(method["capture"]["_frame_stack"], method, other)
        return constants.nil
    
    def __xor__(self, other):
        op_name = "_impl::logical_xor"
        if op_name in self:
            method = self[op_name]
            return run_fn(method["capture"]["_frame_stack"], method, other)
        return constants.nil
    
    def __neg__(self):
        op_name = "_impl::negate"
        if op_name in self:
            method = self[op_name]
            return run_fn(method["capture"]["_frame_stack"], method)
        return constants.nil
    
    def __invert__(self):
        op_name = "_impl::invert"
        if op_name in self:
            method = self[op_name]
            return run_fn(method["capture"]["_frame_stack"], method)
        return constants.nil
    
    def __contains__(self, other):
        op_name = "_impl::contains"
        if super().__contains__(op_name):
            method = self[op_name]
            return run_fn(method["capture"]["_frame_stack"], method, other)
        return super().__contains__(other)
    
    def __str__(self):
        op_name = "_impl::str"
        if op_name in self:
            method = self[op_name]
            return run_fn(method["capture"]["_frame_stack"], method)
        return self.__repr__()
    
    def __int__(self):
        op_name = "_impl::int"
        if op_name in self:
            method = self[op_name]
            return run_fn(method["capture"]["_frame_stack"], method)
        return constants.nil
    
    def __float__(self):
        op_name = "_impl::float"
        if op_name in self:
            method = self[op_name]
            return run_fn(method["capture"]["_frame_stack"], method)
        return constants.nil

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


def make_function(capture, name, body, params):
    vname = constants.nil
    vindex = 0
    defs = {}
    checks = {}
    params_ = []
    def handle_check(expr):
        cname, _checks, *body = expr
        if _checks == "checks":
            checks[cname] = make_function(capture, f"check:{name}:{cname}", [(0, "::internal", "return", [], [Expression(body)])], ("self",))
        elif _checks == "follows":
            a = []
            for n in body:
                a.extend((
                    "and",
                    Expression(["call", f":{n}", (":self",)])
                ))
                checks[cname] = make_function(capture, f"check:{name}:{cname}", [(0, "::internal", "return", [], [Expression(a[1:] if len(body) > 1 else ["call", f":{body[0]}", (":self",)])])], ("self",))
    for n in params:
        if isinstance(n, dict):
            (n, v), = n.items()
            if isinstance(n, tuple):
                handle_check(n)
                n = n[0]
            if not run_fn([{}], checks[n], v):
                error.error(f"near {body[0][0]-1}", body[0][1], f"Default value of {n!r} ({v!r}) of function {name} does not pass check {checks[n]['body'][0][3][0]}")
                raise error.DPLError(error.CHECK_ERROR)
            defs[n] = v
        elif isinstance(n, tuple):
            handle_check(n)
            n = n[0]
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
        "capture": capture,
        "variadic":{
            "name": vname,
            "index": vindex,
        },
        "tags": { # tags for DPL to treat functions differently.
            "preserve-args": False, # save un-evaluated arguments?
        },
        "defaults": defs,
        "checks": checks,
        "self": None,
        })


def make_method(capture, name, body, params, self):
    func = make_function(capture, name, body, params)
    func["self"] = self
    return func


def make_object(name, frame=None):
    return object_type({
        "_type_name": name,
        "_frame": frame
    })
