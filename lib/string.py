

if __name__ != "__dpl__":
	raise Exception

@add_method("string.split")
def split(string, deliminator, maxsplit=-1):
	return string.split(deliminator, maxsplit),

@add_method("string.join")
def join(string, *strings):
	return string.join(map(str, strings))

@add_method("string.startswith")
def test(string, prefix):
	return 1 if string.startswith(prefix) else 0

@add_method("string.endswith")
def test(string, suffix):
	return 1 if string.endswith(suffix) else 0

@add_method("string.contains")
def contains(string, other):
	return 1 if other in string else 0