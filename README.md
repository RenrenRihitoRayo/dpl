# DPL - Dumb Programing language

## Info

	Created by: Darren Chase Papa<br>
	Written using: Python 3.10

## Whats new in 1.0-a

- System info can now be accessed in `_meta.internal.os`
- Library info can now be accessed in `_meta.internal.libs`
- New extensions to aid in writing DPL code.
- `to_callable` adds a way to make DPL code runnable via python without using `run_code`
- Changes were made to accommodate `tkinter_dpl`

	`tkinter_dpl` is an extension attempting to port tkinter to DPL.
	Some scripts were made using it, and it shows promissing results.
- Extension `dicts` helps define dictionaries

	Example:
	```
	import "dicts.py"
	import "text_io.py"

	object :my_dict
	body _mods.py.dict :my_dict
		# To define a variable (with true as a value)
		.def NAME
		# To define a variable with a name without whitespace
		NAME = VALUE
		# To define a variable with white space as a name
		.let "NAME HERE" = VALUE
		# You can nests dicts by referencing them.
		# Example: NAME = :dict
	end
	```
- `io flush` is now added to the `io` extension to manually flush the stdout.

## Using dictionaries as keyword arguments for python functions

```
import "some_func.py"
import "dicts.py"
import "text_io.py"

object :my_dict
body _mods.py.dict :my_dict
	.def "[KWARGS]"
	# Manually give positional arguments
	.let "[PARGS]" = [key word args here]
	numerator = 138
	denominator = 2
end

# make sure that `my_dict` is the only argument
pycatch [res] _mods.py.SOME_DIV_FUNC :my_dict
io println %res
```

## Hello world

	In pursuit of making the parser faster, and also smaller.
	We modularized the functions, since DPL can interface with python,
	we made extensions, one of which is used here (`text_io.py`)

```
# By default the search path is the library path
import "text_io.py"

io println "Hello, world!"

# To import a local module/extension use @loc
import "local_module.py" "@loc"
```

## Literals

- strings: `"Hello there!"`
- integers: `1,000,000 (yes commas are allowed)`
- floats: `1,000.00`
- list: `[0 1 2 3 4 5 6 7 8 9 "Also strings!"]` (note that this must be on one line)
- bool: `true` and `false` (1 and 0)


## Variable system

	Using `%name` and `:name` is different adn not just syntactic sugar!
	`%name` searches for the meta attribute `[meta_value]` and if it is defined it is used as the value,
	meanwhile `:name` will bypass that behavior. Using `:name` is faster and safer!
	Only use `%name` when you intend to use its meta value!

## Variables

Variables are easy!

```
import "text_io.py"

set this_var "to this string"
# or with fancy names! (as long as dots are used properly and no spaces!)
set name{this-works?} "what?"
object test
set test.this "Oh this is an attribute!"

io println %this_var %{this-works?} %test.this
```

## Functions

```
import "text_io.py"

fn greet name
	_global.io println (sum "Hello " %name "!")
end

fn name{can_return?}
	return "Wow!" 69
end

greet "You"
catch [return_value nice_value] name{can_return?}
io println %return_value %nice_value
```

## If statements

```
import "text_io.py"

io print "Name: "
io input name
if (%input caseless{==} admin)
	io println "Hello admin!"
end
```


### Using `if-then`

```
import "text_io.py"

io print "Name: "
io input name
if-then (%input caseless{==} admin)
	io println "Hello admin!"
else
	io println "Hello user!"
end
```

## Typed variables!

```
import "text_io.py"
import "typed_vars.py"

defv name %_mods.types.string
defv age %_mods.types.string

setv name "John Doe"
setv age 30

# An error will occur
setv age "30"
```

## Loops

```
import "text_io.py"

for name in [John Carl Jason]
	io println (sum "Hello " %name)
end

loop 10
	io println "Say this 10 times"
end

set count 100

while (%count > 0)
	io println %count
	set count (%count - 1)
end

loop
	io println "LOOP FOREVER THERE IS NO ESCAPE"
end
```

## Runtime info

```
import "text_io.py"

# Getting memory
pycatch [mem] _meta.internal.get_memory
# print a tuple (value, unit)
io println %mem

# Getting size of object
object really
pycatch [mem] _meta.internal.sizeof %really
# print a tuple (value, unit)
io println %mem
```

## Requirements

Please make sure these modules are installed.
Packages such as `ncurses` and `tkinter` may not be
readily available.

- tkinter [(used by tkinter_dpl :: soon to be integreted)](https://github.com/DarrenPapa/tkinter_dpl)
- psutil

	For runtime info such as current memory usage.
- Python >=3.10
	
	For the match statements.

- ncurses (in the future, might get canceled or postponed)

	For CLI interfaces.

- argparse (in the future to ditch the match statements)

	To enhance the CLI logic.
	Currently we use match statements which are SLOW.

## Performance

	Dont use it. If you do, please use Pypy3.
	Performance on Python 3.13 is good.
	But on Pypy its much more better!