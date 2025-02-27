
if __name__ != "__dpl__":
    raise Exception

if not dpl.info.VERSION.isLater((1, 4, None)):
    raise Exception("This is for version 1.4.x!")

ext = dpl.extension(meta_name="sng")

@ext.add_func()
def set(frame, _, name, value):
    dpl.varproc.rset(frame[-1], name, value)

@ext.add_func()
def get(frame, _, name, name1):
    dpl.varproc.rset(frame[-1], name, dpl.rget(frame[-1], name1))