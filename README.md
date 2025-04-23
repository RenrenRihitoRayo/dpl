# DPL – The Dumb Programming Language

> "Simplicity is everywhere in DPL, like an airport cutting expenses."
> "DPL gives you freedom. In return, it's your fault when you fail."

Welcome to **DPL**, the programming language that doesn't try to be smart — just **dumb enough to let you do whatever you want**. DPL is minimal, messy, and proud of it.
There are no style rules. There are no guardrails. Just a loosely-held-together interpreter and your own chaotic energy.

## Philosophy

- The **language** shouldnt have standards.  
- **If your code looks weird, that’s your aesthetic.**  
- If it breaks, that's your fault.  
- If it works, that's DPL.

## Features

- Classes? Kinda.  
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
`set CAPS ["my string"@upper]`

### Truthy Values

- Any non-empty containers and strings
- If an int or float is not zero
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

#### Explicit and Implicitly Defined (for nil)

Explicitly undefined means that the variable doesnt exist in scope!
While Implicitly undefined means that the variable does exist but is set as nil.

To differentiate between these two use the `def?` operator. Ex: `set exists [def? var]`
To make sure its only implicitly undefined use `def?` with `nil?`. Ex: `set exists_bit_is_nil [[def? var] and [nil? :var]]`

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

object MathThing

method :MathThing new value1 value2
    new :self temp
    set temp.v1 value1
    set temp.v2 value2
    return :temp
end

method :MathThing add
    return [:self.v1 + :self.v2]
end

catch [obj] MathThing.new 5 7
catch [res] obj.add
io:println :res
```

## Reasons to use DPL

> Linting? None. You are the linter now. May your choices be wise, or at least funny.

Why use DPL?
* You’re tired of languages judging you.
* You believe standards are optional. You want full control and full responsibility.
* You enjoy chaos, minimalism, or pain.

## DPL's Core Ideals

> It works? Alright then DPL's works
> Doesnt? Well it's your fault.
> If you can only read it you're special, if no one can what the hell.
> You know what? F*ck it, do what ever you want shove in what fits.

---

# Change Notes / Dev Logs

Most recent at top.

# 1.4.7

## Cythonizing and bloat

DPL no longer has built in support for cythonizing.
This comes along with the effort to reducing bloat in the DPL
repo.

## DPL now has type checking and new stuff.

DPL now has type checking!
Although it slows down the interpreter a lot.
Static type checking is yet to be implemented.

A new expression was introduced for interpolated strings.
`[fast-format "string"]` which interpolated onlt the local variables
and hides variables starting with underscores ("_").

The syntax for indexing has now been changed from `[:object->index]`
to `[:object[index]]`

## DFPM

The package manager now generates the destination folder only when its successful in downloading the package.

## Symbol Packing

DPL now groups symbols.
`[90 >= 90]` is now `[90, ">=", 90]` rather than `[90, ">", "=", 90]`
this will speed up most expressions and will lessen memory usage on runtime.

This will help the match statement parse it more cleanly and efficiently.

## Added an attribute to check which implememtation is used

`_meta.internal.implementation` by default is `python` when using a compiled version `parser-cpython-ver.so` rather than
`py_parser`. Note it it is not recommended to hand write the parser in C oe C++,
but by writing Cython scripts then compiling, Nuitka is also suitable for this action.

## Info on implementations

Any python importable code that is named `parser-coython-[ver]` will be used when possible,
it treats it as the parser that implements the following functions:
- process: turns text into a list of tuples `(pos: int, file_name: str, instruction: str, args: list)`
- run: executes the code either from a string or the outout of process. should accept (code, frame, thread_event=IS_STILL_RUNNING), returns the error code, 0 for success, any erro code less than 0 is still }ropagated but as control codes (like skip and stop) rather then errors.

It should use the `lib/core/runtime` and use that to initiate the runtime,
as well as inherit data from it by calling `runtime.expose(globals())`

## Meta values and Update Mappings

Update mappings now support updating multiple values!
Meta values have now been removed. Doing `%variable` will result in an error!

```DuProL
Error in line 3 file '__main__'
Cause:
Something went wrong when arguments were processed:
Invalid literal: %test
> ['%test']

[/storage/emulated/0/temp.dpl]
Finished with an error: 4
Error Name: PYTHON_ERROR
```

## `std/math.py` and new dpl.add_matcher decorator

DPL now supports defining custom expression syntax!
As long as it doesnt clash with builtin expressions.
This is utilized by the new module `std/math.py` which
defines a syntax that comes more naturally than the builtin expressions.
You can finally chain expressions! `[math [! 90 + 90] * 2]` outputs 360.
By the way `[!...]` is not negation, thats `[not ...]`, for unary negation `[- ...]`
to invert [~ ...], `[!...]` is the array syntax.

```DuProL
# std/math.py
...

@dpl.add_matcher(ext.mangle("expr_match"))
def matcher(frame, expr):
    ...
```

For example I want to define a matcher that uses a match statement
to square anything

```DuProL
@dpl.add_matcher("my_expr_matcher")
def matcher_fn(frame, expr):
    match expr:
        case ["square", int(value)] if isinstance(value, (int, float)):
            return value ** 2
        case ["square", value] if isinstance(value, (str, list, tuple, dict)):
            return value * 2
        case ["square", default]: # unknown type
            return default
```

If your match function returns `None` it is considered as a fail.
If you want to return `None` without being detected as a fail, you need to wrap it in `dpl.wrap`
like this: `dpl.wrap(None)` and get its value by doing `:value.value`

## Meta values

Meta values are now deprecated and will be removed by 1.4.8

## `std/error_handling.py`

This module implements error handling similar to what rust does.
Where you return either an error or the values.

```DuProL
&use {std/text_io.py}
&use {std/error_handling.py}

fn func
    if cond
        return [@err:wrap_err :_meta.err.RUNTIME_ERROR "Yep"]
    end
    return [@err:wrap_ok 90]
end

catch [!value] func
# if 'value' is an error 'error' will be used
# 'value' if otherwise
err:unwrap :value [!error rvalue]
io:println :error :rvalue
if [not [nil? :error]]
    err:raise_from_string :error
end
```

## `ifmain` and the new `std-dpl/memory_handling.dpl` module

The `ifmain` is a block that only executes if the file it is in is ran as a script
and not included from another file. Basically like Python's `if __name__ == "__main__"`.

The new module contains the logic for manual reference counting for C/C++ objects.

```DuProL
&include {std-dpl/memory_handling.dpl}
&use {std/text_io.py}

catch [my_rc] RC.new "example value"

fn free_func state
    io:println 'Freeing ${state.value!}'
end

my_rc.set_free :free_func
# Prints <Rc [ref count] value> in this case:
# <RC [1] 'example value'>
io:println :my_rc
# should print "Freeing 'example value'"
my_rc.def_ref
```

Garbage collection maybe possible too,
just by using a list and a thread.

## Notice

Due to problems the "-remove-freedom" flag has been removed.
This is to keep the code base simpler to manage.

## Accuracy Loss Mode

By doing `&whatever` it will cause some inaccuracies.
With integers 0 might become -1, 1 or as is.
With floats it might lose its accuracy via truncation.
Strings might be shuffled.

## New proposals

- Migrate some parts of the interpreter to C if not all.
- Provide a more consistent documentation not just this dev history.

## Scheduling

DPL will suport scheduling in terms of seconds.

```DuProL
&use {std/text_io.py}

thread
    get_time cur_time
    sched [:cur_time + 5]
        io:println "Five seconds have passed!"
    end
end
```

## New Addition to objects

Objects must have methods to cast their contents into different types.
If the object shouldnt be casted to that type, the method should return none.
Why not nil? Well nil will means that there was a problem.

## Addition of the '-remove-freedom' flag

This flag changes the function that runs the code
with one that enforces type checking on the builtin
instructions.

### Example usage

hw.dpl
```DuProL
&use {std/text_io.py}
io:println "Hello, world!"
```

```Plaintext
[root@localhost ~]# neofetch
                   -`                    root@localhost
                  .o+`                   --------------
                 `ooo/                   OS: Arch Linux ARM aarc
                `+oooo:                  Host: [totaly rad pc]
               `+oooooo:                 Kernel: 6.2.1
               -+oooooo+:                Uptime: 6 years
             `/:-:++oooo+:               Packages: 133 (pacman),
            `/++++/+++++++:              Shell: bash 5.2.37
           `/++++++++++++++:             Terminal: linker64
          `/+++ooooooooooooo/`           CPU: MT6769V/CZ (8) @ 1
         ./ooosssso++osssssso+`          Memory: 2298MiB / 1GiB
        .oossssso-````/ossssss+`
       -osssssso.      :ssssssso.
      :osssssss/        osssso+++.
     /ossssssss/        +ssssooo/-
   `/ossssso+/:-        -:/+osssso+-
  `+sso+:-`                 `.-/+oso:
 `++:.                           `-/+/
 .`                                 `/

[root@localhost ~]# dpl -remove-host hw.dpl
*Hawk screeches* There goes your freedom.
Hello, world!
[root@localhost ~]# 
```

## In-expression variable instruction.

Similar to the walrus operator in python,
this allows us to make variables in statements.

```DuProL
&use {std/text_io.py}

# prints 'Darren' twice
io:println [set name = Darren]
io:println :name

# prints 'True!'
if [[set res = [90 + 90]] > 100]
    io:println "True!"
end
```

## New Module

A new module was added "std-dpl/state.dpl"
which implements a 'State' object.
Its only a few lines but its there for convinience.

## ***Bugs***

The undefined variables feature is still primitive.
We might ditch it temporarily and implement it in the future.

## Stricter Control on Undefined Variables

```DuProL
&use {std/text_io.py}

# Warning will be printed
io:println :this

# Warning will not be printed
&set _meta.debug.warn_undefined_vars false
io:println :this

&set _meta.debug.warn_undefined_vars true
&set _meta.debug.error_on_undefined_vars true

# Error will be issued
io:println :this
```

## Preruntime Changes

The preruntime now supports defining variables
and using them. Effectively enhancing the static
optimization of the code.

```DuProL
&set this (90 + 90)
# the line below is optimized down to 180
# even before runtime.
set this (.:this * 90)

# the line below is completely ran on runtime
set this 90
set result (:this * 2)
```

In the next iteration for 1.4.6, I willl try to optimize
unused variables out. This will enhance memory usage and
speed even by a tiny bit.

If you complain about the preruntime being too slow,
then compile the file to its bytecode and run it that way.

```Bash
dpl compile this.dpl # outputs to 'this.cdpl'
dpl rc this.cdpl # to run
```

## *New parser changes*

The parser now includes the instructions.

Meaning "-this 123" will be treated as ["-", "this", 123]
rather than the old way which wouldve just split the instruction (e.i. just ["-this", 123])
from the line.

And as a side effect we can run instructions using variables.
```DuProL
&use {std/text_io.py}
set my_print "io:println"
:my_print "Works!"
```

## Proposals

- Advanced optimizations (preruntime)
- Type checking for builtin instructions (preventing bugs)
- Loading dynamic libraries that are in memory

# 1.4.6

## Enums, Ternary and a 'Strict' setting.

```DuProL
&use {std/text_io.py}

# when reading variables with the value of nil
# (for undefined variables or marked vars)
# it will raise an error
set _meta.debug.disable_nil_values true

enum my_enum
    # enum:__main__:my_enum:v1
    v1
    # enum:__main__:my_enum:v2
    v2
    # enum:__main__:my_enum:v3
    v3
end

io:println (if true then "true" else "false")
```

## Debugging the scope

Two functions were added. "dump_scope" and "dump_vars".

```DuProL
-- Dump the local scope --
dump_scope

-- Dump an objects attributes --
object this
dump_vars :this
```

## Using dynamic libraries

You can now use C in DPL!
Using dynamically linked libraries for windows and
shared object files in posix compliant systems!

Look at the example at `example/dl.dpl`
as well as the C code in `example/test.c`

## Notice

As of now DPL will have a code
standard requirements.
In STANDARDS.md

## Using DLL and SO files

DPL now supports using dynamic libraries.

`test.dpl`
```DuProL
cdef "void hello();"
dlopen test "./test.so"
cget hello :test

ccall :hello
```
`test.c` => `test.so`
```C
#include <stdio.h>

void hello() {
    printf("Hello, world!\n");
}
```

## New template syntax

```DuProL
&use {std/text_io.py}
&use {std/types.py}

template Person
    define name as :types.str = "default_name"
    define age  as :types.int = 0
    define data as :types.dict
end

from_template :Person Andrew
    name $name
    age 15
    data [dict [this=what]]
end

io:println :Andrew

# Inline template (not recommended as it is hard to read)

from_template [dict [name=:types.str][age=:types.int][data=:types.dict]] Andrew
    name $name
    age 15
    data [dict [this=what]]
end

io:println :Andrew
```

## Aliases when importing

When using `&use` you can add `as name` at the end.
For example `&use {some.py} as alias`.
See `example/alias.dpl` for more details.

## Variable Handling

Auto resolution of names (being able to
implicitly use global variables) can be
disabled by setting `_meta.debug.allow_automatic_global_name_resolution`
to `0` or any falsy value.

```DuProL
&use {std/text_io.py}

set _meta.debug.allow_automatic_global_name_resolution 0
set my_var "Global Variable"

fn test
    io:println :my_var
    io:println :_global.my_var
end
test
```

## Added new functions

The `exec` and `sexec` functions were added,
these functions can run DPL code on runtime.
```DuProL
set code "&use {std/text_io.py}\nio:println \"Hello!\""
exec :code "string" [?list !dict]
```

To not propagate the errors through the main
program. Use `sexec`
```DuProL
set code "&use {std/text_io.py}\nio:println \"Hello!\""
sexec err :code "string" [?list !dict]
io:println :err
```

The `[?list !dict]` is the frame stack.
In python its just `[{}]`.

If you want to pass the current frame stack,
use `:_frame_stack` which has the execution
context of the main program.
```DuProL
&use {std/text_io.py}
set code "io:println \"Hello!\""
exec :code "string" :_frame_stack
```

## Another Update to the REPL

Added more features to the completer,
it now suggests directives.

```
DPL REPL for DPL v1.4.6
Python 3.11.4 (main, Sep 30 2023, 10:54:38) [GCC 11.4.0]
>>> &use {
           &use {std}
           &use {std/array_utils.py}
           &use {std/dicts.py}
           &use {std/file_io.py}
           &use {std/include-py.txt}
           &use {std/text_io.py}
           &use {std/types.py}
           &use {std/strings.py}
           &use {std/tests.py}
           &use {std/to_py.py}
           &use {std/to_dict.py}
           &use {std/typed_vars.py}
```

## 1.4.6 REPL

The REPL now supports code suggestions!
Or at least auto completion.


```
DPL REPL for DPL v1.4.6
Python 3.11.4 (main, Sep 30 2023, 10:54:38) [GCC 11.4.0]
>>> &use {std}
>>> io:
        io:print
        io:printf
        io:println
        io:rawprint
        io:rawprintln
        io:input
        io:setOutputFile
        io:rawoutput
        io:flush
        io:open
        io:seek
        io:read
        io:write
        io:append
        io:close
```

## Using `&use`, `&use:luaj`, `&include` and `&includec` on directories

Its pretty simple to setup.
Just write a "include-[lang].txt" file.
For example we'll use python.
In that case we will write "include-py.txt".
In that file we will list the files we want
to export.

The directory should look like this
```
example
├── file1.py
├── file2.py
├── file3.py
└── include-py.txt
```

If you want to only include `file1.py` and `file3.py`
but not `file2.py` your include file should look like
this:
```
file1.py
file3.py
```

You can have comments.

```
# file1 does ...
file1.py
# file2 needs to be manually included.
# file3 does ...
file3.py
```

You can also print stuff out.
```
#:Print with meta data
#?Print without meta data.
```

## New Syntax!

```DuProL

# Embed a file.
&embed "test.txt" as text_txt
# As a byte array
&embed_binary "test.bin" as text_bin

-- Multiline comments!
new expressions
... [...]
--

# Lists
set list [?list item1 item2]
## Indexing a list
pass [:list 0]
## Indexing strings
pass ["oh" -1] # grab last character

fn dangerous_func
    raise :_meta.err.RUNTIME_ERROR "Oh no!"
end

# Call it safely
safe dangerous_func
# Or if youre expecting a return value
scatch [?list error values] dangerous_func
io:println :error :values


```

## Lua JIT!

DPL can now interact with Lua through
Lua JIT or "luaj" internally.

You can use lua modules by using the new
`&use:luaj` directive.

### Example DPL/Lua Module

```Lua

if type(api) == "nil" then
    -- Make sure only DPL can use this
    error("DPL Module!")
end

ext = api.dpl.pycall(
    api.dpl.extension,
    null,
    {
        name = "scoped_name", -- takes precedence over meta_name
        meta_name = "mangled_name"
    }
)

ext:add_func("func_name")
(function(frame, locdir, ...)
    -- do stuff here
    return api.type.tuple({})
end)


```

## Match statements!

```DuProL
&use {std/text_io.py}

set test "Hello"

# New match statements!
match :test
    as this
    with "Hello"
        io:println :this
    end
    with "Hello world!"
        io:println "Hello user!"
    end
    case [[Type :this] == "int"]
        io:println "Wait a number?"
    end
    # invalid code
    io:println :this
end
```

## Bench Marks

```DuProL
for i in (Range 1000)
pass "test"
end
```

```
Benchmark 1: 100
  Time (mean ± σ):     679.3 ms ±  56.2 ms    [User: 575.1 ms, System: 103.0 ms]                                                    Range (min … max):   583.5 ms … 724.6 ms    10 runs            
  Warning: Ignoring non-zero exit code.
```

For some reason it was exiting with a non zero
exit code and I had to double check the source
but it has no errors and was running fine.

Keep in kind that this is heavily dependent
on the platform and the hardware used!

Specs:

```
Device:    Oppo A18
OS:        Termux (Android 14)
RAM:       4Gb
Processor: Helio G85
Python 3.12.9 (main, Feb  4 2025, 22:30:28) [Clang 18.0.3]
```

# Deprecation!

`import` statements are now nonexistent!
As well as the `dpl install` command!

# Added new command

`dpl docs file.mmu` and
`dpl docu file.mmu`

# New underlying mechanisms

`_meta.str_intern` has been added.
It will intern the string with `sys.intern`
thus optimizing freaquently used strings.

# 1.4.5 New features

Added the elipsis constant `...`
which will be used as empty statements
or empty expressions.

Implemented and rewrote some of the logic for
the optimizer.

# 1.4.5 Rewriting the codebase

Some of the instruction implementations
have been rewritten for performance.
The benchmarks will be here soon.

Any contributions to the codebase is
very much appreciated.

Before making a merge/pull request please
send the zip at `darrenchasepapa@gmail.com`.
I dont trust github to provide the changes.

Your credits will be added here.

# 1.4.5 Added new for loop syntax

```DuProL
for index, value in :list
    io:println '${index}: {value}'
end
```

# 1.4.5 Minor changes

`import*` is now removed.
The new directory structure in which all
standard library modules are in "std".
This is to facilitate order and to avoid
conflicts with future packages.

`dpl package install `<user> <repo> <branch>`,
`dpl package installto: <path_dest> `<user> <repo> <branch>`
and
`dpl package remove <package_name>`
has been added.

# 1.4.4 Patch Alpha

The memoization had some bugs in it.
The example too had some logic errors.
It is now fixed.

From my device `mcatch [] memoize_fact 28000`
in the first pass is `8s` while in the second
`below 1ms`

# Repo Notice

The master branch will always be the bleeding edge branch.

# Changes to 1.4.4

A major change in syntax.
Instead of `&use <standard_lib.py>` the new
syntax is `&use {standard_lib.py}`

Operations +, -, *, /, >, < must now have spaces.
Meaning `(2+2)` must now be `(2 + 2)`, I infer that
most people use the latter anyways.

Memoization has been builtin but not automatic.
It is controlled by the user and can only be used
by functions that can return.

(previous execution times removed as they could
fall under misinformation)

```DuProL
# DEPENDS ON DEVICE
# AND MUSNT BE TAKEN AT FACE VALUE

&use {text_io.py}

fn memoize_fact n
    if (:n <= 1)
        return 1
    end
    # mcatch stands for [m]emoized [catch]
    mcatch [f] _global.memoize_fact (:n - 1)
    return (:n * :f)
end

fn fact n
    if (:n <= 1)
        return 1
    end
    catch [f] _global.fact (:n - 1)
    return (:n * :f)
end

START_TIME
catch [this] memoize_fact 20000
STOP_TIME
LOG_TIME

START_TIME
catch [this] fact 20000
STOP_TIME
LOG_TIME

START_TIME
catch [this] memoize_fact 18000
STOP_TIME
LOG_TIME

START_TIME
catch [this] fact 18000
STOP_TIME
LOG_TIME
```

We might introduce a version bump to 1.5.x
Although we are going to be consistent so
1.4.4 might be the final choice.

# Another set of features

DPL now allows commas to seprate arguments!
Its still optional though.

```DuProL
set this [0,1,2,3]
# is just
set this [0 1 2 3]
```

Since the parser has evolved we can
finally not use spaces in our expressions!

```DuProL
set result (90+90)
```

# 1.4.4 Modules

New Modules:
- array_utils.py
```
    Contains functions and methods to
    join two arrays, reverse an array,
    and to slice an array.
```
New Functions:
- io:printf in text_io.py
```
    Has a simple formatter.
    io:printf "%N" value0 value1 ... valueN
    where N is the index of a value.
    Example:
    set test (90+90)
    io:printf "Result: %0\n" :test
```
# 1.4.4 In-comming Release

Release Date: March 15, 2025
Features:
- :white_check_mark: Dead code optimization.
- :white_check_mark: Profiling.
- :stop_sign: Generators
- :white_check_mark: Formatted strings.

# Repo Notice As Of Feb 9 2025

Every new versions including patches
will be made on separate branches.

This is to improve security.

# 1.4.3 Patch Alpha (1.4.3-a)

Added new info.

# Fixes 1.4.3

Fixed a bug that misinterpreted hex literals in strings.
Example: "This is a test" becomes "This is 10 test"
It is now fixed by making strings parsed before the hex literals.

Benchmarks (not totally accurate)
```
Device:    Oppo A18
OS:        Android 14
RAM:       4Gb
Processor: Helio G85
Python 3.11.4 (Pydroid3)
```

1 million loop
    
With string parsing
```
1.4.3: 11.812s
1.4.2: 17.017s
```

Code:
```DuProL
    START_TIME
    for i in (Range 1,000,000)
        # This tests the string parsing speed
        pass "test"
    end
    STOP_TIME
    LOG_TIME
```
    
Without string parsing
```
1.4.3: 65.914ms
1.4.2: 80.352ms
```
    
Code:
```DuProL
    START_TIME
    for i in (Range 1,000,000)
    end
    STOP_TIME
    LOG_TIME
```
    
Since the string parsing is now on the
preruntime side. The loops are a ton more
faster.

# Additions 1.4.0 - DuProL/Python API Update!

A "dpl" and "modules" class is defined on import of that script.
This is to make the global scope more clean.

Heres how its organized. Any DPL related modules will be in `dpl`
While modules like os, sys, time, ... and any other modules that are imported
by DPL will be found there.

You can now use `dpl.info.isCompat` to check version compatibility.
It accepts a tuple with three integers. (major, minor, patch)
It is calculated against "dpl.info.VERSION_TRIPLE". "dpl.info.VERSION" is
a `Version` object which has methods to calculate compatibility.

## More changes

    Drastic rewriting of the standard library.

# Additions 1.3.0

Incomplete documentation.

## Renamed expect-then to expect_then

This is to make the instructions more consistent.
Some instructions, this included, may be subjected to future changes.
Maybe it will be switch to camel case formatting.

## Renaming of most extensions

To enfore the new naming conventions for DuProL,
most python functions has been renamed.
_mods will now be deprecated as the new scope mechanisms simply
doesnt need it anymore.

## Posible Future Features

1. HTTPS requests.

2. More threading stuff? (partially implemented)

3. Slight overhauls:

    1. Actual parsing. (rejected)

    2. More standard libraries.

4. Built in linting. (Not Sure)

5. Better static typing support. (implemented)


# Additions 1.2.0

Incomplete documentation.

## Regarding This Repo

DuProL will now follow a semantic version format.

    "Major.Minor.Patch"

This file will be updated per update.

## Fixes 'N Stuff

1. Updated paths on linux. No more over complication

2. Added this file.

3. Made it so that when a local var isnt found it looks for it

   in the global scope.

4. Added new methods "append" and "pop"



Used like this 

```

import "text_io.py"

set array []

pass (append :array 90)

# prints array after it has appended the 80 so it should be [90, 80]

io println (append :array 80)

```



## Posible Future Features

1. HTTPS requests.

2. More threading stuff?

3. Slight overhauls:

    1. Actual parsing and stuff.

    2. More standard libraries.

