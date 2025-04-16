# Welcome to DPL!

In this markdown file, the basics of my programming
language will be taught to you!

## Data types

Data types in DPL are just python types, no wrappers,
just raw python types!

In fact you can call their methods using an operator!

```DuProL
&use {std/text_io.py}
set keys [.dict@keys]
io:println :keys
```

Data types:
- Strings
- Integers
- Floats
- Bools (just integers)
- Lists
- Dictionaries
- Tuples
- Sets

## Variables

Variables in DPL are somewhat complicated.
This to allow the interpreter to optimize some expressions.

```DuProL
&use {std/text_io.py}

&set this 90
# optimized to 'io:println 90 180' before runtime
io:println .:this [.:this * 2]
# only fetches the value on runtime
io:println :this
```

### Identifiers

Identifiers in DPL are wonky, they can contain these characters "-_:"
and the rest are alphanumeric characters.
Meaning `90--90` is a valid identifier.
Under the hood identifiers are strings, DPL doesnt abstract that away.
Meaning `"this"` is a valid identifier.

Since strings can be used to denote variable names
you can even put strings!

```DuProL
set "my variable" 90
# we need to use a dict look up to fetch it
# doing :"my variable" isnt supported yet.
set get_my_var [:_local -> "my variable"]
```

### Special Variables

In DPL all scopes have these variables available.
These are `_local`, `_nonlocal`, `_global`, and `_meta`.
Every name except `_meta` is self explanatory.

`_meta` contains data that the interpreter uses or has.
For example debug flags and configs in `_meta.debug`, defined errors in `_meta.err`.
You can use `dump_vars :_meta` to see all of it.