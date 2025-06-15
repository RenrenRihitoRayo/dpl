# DPL – The Dumb Programming Language

> "Simplicity is everywhere in DPL, like an airport cutting expenses.
> DPL gives you freedom. In return, it's your fault when you fail."

Welcome to **DPL**, the programming language that doesn't try to be smart — just **dumb enough to let you do whatever you want**. DPL is minimal, messy, and proud of it.
There are no style rules. There are no guardrails. Just a loosely-held-together interpreter and your own chaotic energy.

## Philosophy

- The **language** shouldnt have standards.  
- **If your code looks weird, that’s your aesthetic.**  
- If it breaks, that's your fault.  
- If it works, that's DPL.

## Features

- Functions? Yes, and they sometimes even work.  
- Syntax? Let's call it... *flexible*.  
- Naming conventions? **Snake case**, **PascalCase**, **camelCase**, or **whoknows_case** — all welcome.

## Types

Primitives:
- int
- float
- str

Containers:
- dict (objects and scopes)
- list
- sets
- tuples

Flags:
- nil
- none
- true
- false

We dont abstract the python types here,
you can call its methods and do some stuff with it.
`set CAPS = ["my string"@upper]`

### Truthy Values

- Any non-empty containers and strings.
- If an int or float is not zero.
- true (duh)

### Falsy Values

- Empty containers and strings
- 0 and 0.0
- false (duh)
- none
- nil

## Usecases For `none` and `nil`

### `none`

To explicitly say that this variable exists and is not yet set.

### `nil`

Returns when an unset variable is read.
Setting a var to nil wont delete!

#### Explicit and Implicitly Defined (for nil)

Explicitly undefined means that the variable doesnt exist in scope!
While Implicitly undefined means that the variable does exist but is set as nil.

To differentiate between these two use the `def?` operator. Ex: `set exists [def? var]`
To make sure its only implicitly undefined use `def?` with `nil?`. Ex: `set exists_bit_is_nil [[def? var] and [nil? :var]]`

### Extra Note

Even values representing a state of nothingness
has value here, too sad you dont have any...

## How To Use DPL

You must have python and python-pip installed.

```Plaintext
[root@localhost ~]# git clone https://github.com/DarrenPapa/dpl
[root@localhost ~]# cd dpl
[root@localhost ~/dpl]# pip install -r requirements.txt
[root@localhost ~/dpl]# bash scripts/install.sh
Added ... to PATH in ~/.bashrc
[root@localhost ~/dpl]# dpl
DPL REPL for DPL v1.4.7
Python 3.11.4 (...) [...]
>>> &use {std/text_io.py}
>>> io:println "Hello, world!"
Hello, world!
>>> exit
[root@localhost ~/dpl]# dpl example/hello-world.dpl
Hello, world!
[root@localhost ~/dpl]# # get info about the code base
[root@localhost ~/dpl]# python3 info.py
```

## Code Sample

```DuProL
&use {std/text_io.py}

io:println "Hello, world!"

fn greet(name)
    io:println 'Hello ${name}!'
    return 420
end

catch (result) greet Alex
greet Andrew
io:println :result
```

## Reasons to use DPL

- To suffer
- To show off
- To look smart-ish

Why use DPL?
* You’re tired of languages judging you.
* You believe standards are optional. You want full control and full responsibility.
* You enjoy chaos, minimalism, or pain.

## DPL's Moto

> DPL just works.
> What your code doesnt?
> Thats on you dumbass not DPL.

---

# Change Notes / Dev Logs

Most recent at top.

# 1.4.8

## Pipe Line Explained

Current Pipe line:
* Source
> The source code.
* Preprocessing
> Preprocess the source code
> like preruntime directives.
* HLIR Generation
> (High Level IR, almost reconstructable
> to original source)
> Turn the now preprocessed code
> into a interpretable form.
* Execution
> Execution step (if else dispatch)
> Op code execution is
> O(n) per iteration where n is the
> number of operations built in
> to the execution loop.
* Output
> Programs output/side effects.

New Parser Pipe Line (with py_parser2):
> The new parser is a simple
> slap on replacement.
> Uses a flag and a preprocessing directive.
> "-use-py-parser2" and "&enable:EXPERIMENTAL_LLIR"
> The old parser will still be present
> for direct HLIR execution.

* Source
> The source code.
* Preprocessing
> Preprocess the source code
> like preruntime directives.
* HLIR Generation
> (High Level IR, almost reconstructable
> to original source, human readable)
> Turn the now preprocessed code
> into an interpretable form.
* LLIR Generation
> (Low Level IR, machine readable)
> Replaces text op codes into integer
> based opcodes for fast look up.
* Execution
> Execution step.
> Uses a dictionary look up table.
> Faster and op code execution is
> O(1) per iteration.
* Output
> Programs output/side effects.

## Runtime Type Checking is now deprecated.

Overhead even when optional.
Init time is just too long.

## New parser may be used for ast generation?

## OOP is temporarily dropped in support.

I dont know why it doesnt work :)

## Default variables are now deprecated

To save memory space and male function
definitions faster.

## Overhauled py_parser2

Made it more flexible in syntax ;)

## Renamed extension_support into module_handling

## Moved inclusion logic to extention_support

I was bored.

## Added "Humorful" Text in the repo

I was bored okay?

## DPL now supports references!

See 'example/references.dpl'
to see how it works!

## Updated suport for multiple parsers..

DPL may now use an argument to explicitly
point to the new parser to use.
Basically making DPL a customizable front end.

## Added Doc strings to every function...

## Added syntactic meaning to "_" as a name.

if "set _ = ..." is called, it ignores the value.
Same for every variant of "catch _ ...".

## Changed for loop syntax.

Old syntax
```DuProL
for index, name in iter
    ...
end
```

New syntax
```DurpProL

for (index, name) in iter
    ...
end
```

## Concerns for threading

> WARNING
> Threading may be moved to a separate module!
> Make sure to have your code adjusted.
> The new syntax is the same just with the new `&use {std/threads.py}` at the top.


> CAUTION
> Reading and writing variables are no longer atomic!
> You may need to manually use the "lock" keyword.

```DuProl
&use {std/threads.py}

set g_var = 90
thread
    lock
        while (_global.g_var < 1000)
            inc _global.g_var
        end
    end
end
thread
    lock
        while (_global.g_var < 1000)
            inc _global.g_var
        end
    end
end
```

## Optimized "pass" instruction.

"pass" no longer is seen in the bytecode,
but unlike the "..." statement it is ignored
by the "DEAD_CODE_OPT" optimization setting.

## New command

DPL when running "install.sh" installs
"dpl", "dpl-run", and "dplpm".

* "dpl" is the cli itself.
* "dpl-run" is an alias to "dpl run ..."
* "dplpm" is an alias to "dpl pm ..."

"dpl-run" is meant to be used for shebangs.
I.E. `#!/usr/bin/env ...`

## DPL now has a Package Manager!

PMFDPL (Package Manager for DPL)
is a simplified version handling system.

```Plaintext
[root@localhost ~/dpl]# dpl pm init my_package
[root@localhost ~/dpl]# cd my_package/src
... do the rest!
```

Use `dpl pm help` for more!

## REPL now supports syntax highlighting!

## New `std-dpl/ansi.dpl` module

```DuProL
&use {std/text_io.py}
&include {std-dpl/ansi.dpl}

ansi.print_color :ansi.fg.cyan
io:println "Cyan!"
ansi.change_style :ansi.style.reset_all

ansi.print_rgb_fg 16 255 255
io:println "Also Cyan!"
ansi.change_style :ansi.style.reset_all
```

## Added def statement in dictionaries

```DuProL

# old syntax
dict numbers
    set one => 1
    set two => 2
    # mamually writing up to:
    set twenty => 20
end

# new synyax
dict numbers
    set one => 1
    def two
    def three
    # up to:
    def twenty
end
```

## Major Refurbish

* Renamed expression methods to lowercase.
* Added new expression methods (`to_ascii` and `from_ascii`)
* Removed some scripts

### New Expression Methods

The two new methods "to_ascii" and "from_ascii" are methods
to convert integers into ascii character (or unicode) and back.

## Did some stuff

* Cleaned up the examples
* Fixed issues in Python functions
* Fixed issues with VIM syntax highlighting.

## Lazy expressions have been reintroduced.

Using `(expr)` will not immediately evaluate it.
You can do `[Eval (expr)]` to evaluate it.

While loops no longer automatically excludes its arguments when evaluating.
Meaning the old syntax "while [expr]" is now invalid
and has been changed into "while (expr)". This small overhead
introduced a slight speed boost, although benchmarks arent available yet.

## New instruction

The new "local" instruction executes a function
but has the same scope where it was called.

```DuProL
set locals = "what??"
fn func
    dump_scope
    # func = ...
    # locals = "what??"
end

local :func
```

Beware as this is strictly for functions, methods
require a scope to insert "self", we could but it will
polute and might overwrite the scope its called in.

Special Attributes that cannot be injected or acts differently:
* "_local" (just uses the scope its called in)
* "_nonlocal" (relative to the scope its called in)
* "_global" (as is)
* "_capture" (doesnt get injected)
* "self" for methods (doesnt get injected)

FYI:
The "_capture" variable is for closures.
The reason it doesnt expose the variables
in the normal way is to avoid polution of the
scope.

Use in performance critical code where scopes
are not necessarily important.

## Keyword arguments

DPL now supports a more easier way of defining
default values for parameters as well as suplying
keyword arguments for these functions.

Old Synyax
```DuProL
fn greet(name)
    ...
end
set greet.defaults.name = "Andrew"

greet
greet "Max"
# kw arguments not yet supported
```
New Syntax
```DuProL
fn greet([name = "Andrew"])
    ...
end

greet
greet "Max"
greet [name => "Max"]
```

## Function calls

To not modify the type checker, the function
calls are still `func arg1 arg2 ... argN`.

## Getting blocks in DPL in python functions.

You no longer need the "block" instruction to pass blocks in DPL!

Old syntax (only one block)
```DuProL
block ins args ...
    ...
end
```
Mew syntax (any number of blocks)
```DuProL
ins args ...
    ...
end

or
ins
indent_ins
    ...
end
```

Thats just like calling a function, you say.
Because it is! The actual change is a semantic
definition of parameters in the function.

```PyDPLE
@add_func()
def fn(frame, file, codr_body):
    ...
```

The interpreter detects if the parameter
ends with either "_body" or "_xbody".
"_body" is inclusive meaning it starts the indent at 1.
"_xbody" is exclusive, you have to indent (put an instruction that increaments the indent)
for it to be valid.

```DuProL
# inclusive "_body"
test_func
    ...
end

# Exclusive "_xbody"
my_if_else
begin
    ...
end

```
 

## Re-introduced "include-py.txt" in `lib/std`

See "Including Directories" in [here](https://darrenpapa.github.io/learn.html#incdir)

## Templates

Template syntax has now been removed.
Replaced by the new dict keyword!
```DuProL
dict name
    set name => value
end
```

## `export set` and `set` syntax

New syntax for setting variables
```DuProL
set name = value
export set name = value
```

## Upcomming syntax changes!

DPL 1.4.8 will try to adhere to standardized and
common syntax. This is to facilitate accessability
and makes learning DPL easier.

## Tuples!

Tuples are now supported using parenthesis!
Along with the new function calling and definition!

```DuProL
fn func(arg1 arg2 ... argN)

end
func(arg1 arg2 ... argN)
```

## New switch statements!

```DuProL
# compiles into
# _intern.switch {"test":..., "darren":..., None:...} :value
# doesnt allow fallthroughs since its not a real
# jump table.
io:input "Name: " value
switch :value
    case test
        io:println "Test!"
    end
    case darren
        io:println "Hello Creator, welcome back!"
    end
    # also case PyNone
    default
        io:println 'Hello ${value}!'
    end
end
# internally
# _intern.switch is just fetching the value and running it.
# no comparisons at the cost of no fallthroughs.
# Switch statements only uses literals.
# No conditions unlike the match statement.
```

## Added CString literals

```DuProL
set my_cstring cstr?"Bytes!"
```

## Update mappings

Update mappings are now unsupported!

## New website

At [DarrenPapa.github.io](https://darrenpapa.github.io) still under work!

## New function definition syntax

```DuProL
fn [!arg1 arg2 ... arg3]
    ... body
end
```

Examples will be updated for the new syntax in
the future.

## Introduced new flags

Certain flags has been added.
See `dpl help`

## The great renaming

Renaming every variable possible for maintainability
and code clarity.

## More bloat removal...

Removed unnecessary imports.
Using `-skip-non-essential` with `-simple-run` yields sub 400ms init time.
