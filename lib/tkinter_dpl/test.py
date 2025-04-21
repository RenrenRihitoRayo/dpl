
ext = dpl.extension("some")

@ext.add_func()
def test(_, __, test=None, test2=None):
    print(test, test2)