

if __name__ != "__dpl__":
	raise Exception

@add_method("string.split")
def split(string, deliminator, maxsplit=-1):
	return string.split(deliminator, maxsplit),

@add_method("string.join")
def join(string, *strings):
	return string.join(map(str, strings))

@add_method("string.startswith")
def starts(string, prefix):
	return 1 if string.startswith(prefix) else 0

@add_method("string.endswith")
def ends(string, suffix):
	return 1 if string.endswith(suffix) else 0

@add_method("string.contains")
def contains(string, other):
	return 1 if other in string else 0

@add_method()
def isUpper(string):
    return string.isupper()

@add_method()
def isLower(string):
    return string.islower()

@add_method()
def toUpper(string):
    return string.upper()

@add_method()
def toLower(string):
    return string.lower()

@add_method()
def titleCase(string):
    return string.title()

@add_method()
def capitalize(string):
    return string.capitalize()