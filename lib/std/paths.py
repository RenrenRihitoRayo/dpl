if __name__ != "__dpl__":
    raise Exception("This must be included by a DuProL script!")

import os
ext = dpl.extension(meta_name="paths")

@ext.add_method(from_func=True)
@ext.add_func()
def isfile(_, __, path):
    return dpl.to_dpl_bool(os.path.isfile(path)),

@ext.add_method(from_func=True)
@ext.add_func()
def isdir(_, __, path):
    return dpl.to_dpl_bool(os.path.isdir(path)),

@ext.add_method(from_func=True)
@ext.add_func()
def exists(_, __, path):
    return dpl.to_dpl_bool(os.path.exists(path)),

@ext.add_method(from_func=True)
@ext.add_func()
def get_sep(_, __):
    return os.sep,

@ext.add_method(from_func=True)
@ext.add_func()
def join(_, __, *args):
    return os.path.join(*args),