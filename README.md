# DPL – The Dumb Programming Language

> "Simplicity is everywhere in DPL, like an airport cutting expenses.
> DPL gives you freedom. In return, it's your fault when you fail."

Welcome to **DPL**, the programming language that doesn\'t try to be smart - just **dumb enough to let you do whatever you want**. DPL is minimal, messy, and proud of it.
There are no style rules. There are no guardrails. Just a loosely-held-together interpreter and your own chaotic energy.

## !! ✨✨NEW IN DPL 2.0.0✨✨ !!

* Objects now have short\-hand constructors!

You can use `make_cons object` to automatically make a constructor for that object,
given that you have defined them implicitly in the object.

* New debug output!

Using `io:debug(object)` in `std/text_io.py`,
will yield more interesting output for objects.

* `declare` in multiline dictionaries.

You can use declare to define keys that would be
implicitly defined.

* Multiline dictionaries and lists can now be nested!

* Expression Folding has been fixed

* Parameter and Variable Checks

* Actual Expressions

* In-instruction blocks

* Added "excluded.txt"

This is to more efficiently ignore
test cases that intentionally or
predictably fails.

```DuProL

dict d1
    set depth = 1
    dict d2
        set depth = 2
    end
    list test
        . item1
        . item2
        . item3
        list
            . item4
            . item5
        end
        dict
            set depth = 4
        end
    end
end

```

* Flask wrapper is available in `std/other/flask.py`

There is an example given in the examples directory.

* Reworked the switch statement

* Text IO can disable input

* Files that are included are cached for fast init time

* Objects now support operator overloading!

* Static inline function calls

* CLI can call different versions!

## Philosophy

- The **language** shouldnt have standards.  
- **If your code looks weird, that’s your aesthetic.**  
- If it breaks, that\'s your fault.  
- If it works, that\'s DPL.

## Features

- OOP
- Functional-ish Programming
- Symple-ish Syntax
- Interopt with Python, C, and Lua
- Simple C interface (user facing code is easy to include)

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
To make sure its only implicitly undefined use `def?` with `nil?`. Ex: `set exists_but_is_nil [[def? var] and [nil? :var]]`

## How To Use DPL

You must have python and python-pip installed.

```Plaintext
[root@localhost ~]# git clone https://github.com/renrenrihitorayo/dpl
[root@localhost ~]# cd dpl
[root@localhost ~/dpl]# pip install -r requirements.txt
[root@localhost ~/dpl]# bash scripts/install.sh
Added ... to PATH in ~/.bashrc
[root@localhost ~/dpl]# dpl
DPL REPL for DPL v2.0.0
Python 3.x (...) [...]
>>> &use {std/text_io.py}
>>> io:println("Hello, world!")
Hello, world!
>>> exit
[root@localhost ~/dpl]# dpl run example/01-helloworld.dpl
Hello, world!
[root@localhost ~/dpl]# # get info about the code base
[root@localhost ~/dpl]# python3 info.py --silent # dont print per file info
```

## Code Sample

```DuProL
&use {std/text_io.py}

io:println("Hello, world!")

fn greet(name)
    io:println('Hello ${name}!')
    return 420
end

catch (result) greet(Alex)
greet(Andrew)
io:println(:result)
```

## Reasons to use DPL

- Simple interopt between Python and C

DPL can be used as a glue between the two.

- Simple Syntax

DPL has a simple syntax, given that it doesnt
have a lexer or AST in the normal sense.
One function call is needed to compile DPL code
into HLIR

## DPL's Moto

> DPL just works.
> What your code doesnt?
> Thats on you dumbass not DPL.

## Installation

After cloning this reporsitory
run the following commands.
```Plaintext
[root@localhost dpl]# pip install -r requirements.txt
[root@localhost dpl]# cd lib/std-c
[root@localhost dpl/lib/std-c]# python3 _build_.py
```

First line ensures DPL dependencies are installed.
However you will need flags to not use them as DPL
uses these by default.
* "-no-lupa" disables Lua inter-opt (via LuaJIT)
* "-no-cffi" disables C inter-opt
* use "-simple-mode" to disable most dependencies
You can also see `requirements.txt` to remove some
before installing the packages.
<br><br>
Third line builds C libraries for your platform.
Make sure you run this command before using a C
Library. This isnt necessarily needed (DPL has no
necessary C libraries yet)

---

# Change Notes / Dev Logs

Most recent at top.

### (most recent release 1.4.9)

# 2.0.0 (Indev)

## CLI can use a specific version of DPL

#### dpl_config.ini
```ini
# specifically use 2.0.0
# cli dispatches right interpreter
# if supports minimal version and
# is installed
[dpl]
version = 2.0.0
```

#### main.dpl
```duprol
&use {std/text_io.py}

# use 2.0.0 specific features
set awesome = [. 2 * 3 + 3] satisfies check(:self == 9)
```

### Setups

Any setup scripts, must use "setup" as the version,
this will use a special frozen version of DPL 2.0.0
for stability and predictability.
<br><br>
Features for setup specific tasks may also be added.
Which as of now is currently none.

#### dpl_config.ini
```ini
# specifically use frozen2_0_0
# cli dispatches right interpreter
# if supports minimal version and
# is installed
[dpl]
version = setup
```

#### CLI is blind

The CLI doesnt verify what interpreter its calling.
You could modify lib/core/config.json and call
an entirely different language using this cli.
<br><br>
Main points of dynamic version dispatch.
* One CLI multiple implementations
* User can copy and make their own DPL superset and use
the same CLI without problems
* DPL wont need explicit backwards compatibility (at least for 2.0.0+)
as you could just install the old interpreter youll use.

##### Example of CLI invoking Python

lib/core/py_inter/py.py
```python
def run(code):
    exec(code)
```
copy varproc and info.
info can be empty,
varproc needs meta_attributes and
internal_attributes as a dict
<br><br>
lib/core/config.py
```python
{
    "newest": "2.0.0",
    "versions": {
        "setup": {
            "lib_path": "@default",
            "core_lib": "frozen2_0_0",
            "call": "code = core.py_parser.process_code(code)\ncore.py_parser.run_code(code)",
            "warning": "This version is used for setups only, to silence this warning use '--no-version-warnings'"
        },
        "python": {
            "lib_path": "@default",
            "core_lib": "py_inter",
            "call": "core.py.run(code)"
        }
    }
}
```

## Blocks

In HLIR code blocks are finally included IN
the instruction, and happens before runtime.
Meaning execution is faster!

## Expressions! (Finaly.)

Using `[ . ... ]` where ... is your arithmetic
expression.
It operates based on precedence (pemdas)

## Checks

Checks are predicates arguments or
a variable must follow. Checks can
be annotated and binded to a function
or defined standalone as a statement.

```duprol
# reusable
check positive(:self > 0)

fn bounded((value follows positive))
    ...
end

# inline
fn bounded((value checks :self > 0))
    ...
end

set a = 10 satisfies(positive)
# or inline
set a = 10 satifies check(:self > 0)
```

## Expression Folding

Expression folding is fixed and is on by
default.

## Static In Expression Function Calls

```duprol
&use {std/text_io.py}

--
  Below is a static function.
  Every caller would get the result
  before runtime if arguments are not impure
--

fn::static add(a, b)
    return [:a + :b]
end

set meep = 90
# below compiles into
# io:println(30)
io:println([call::static add(10, 20)])

# below demotes to a regular call expression
io:println([call::static add(10, :meep)])
```

## Object operator overloading

Object operator overloading is
finally here! For over a year
DPL hasnt had official overloading
due for simplicity, but for convinience
it was added. The downside of using operator
overloading rather than raw calls is that
it is slower due to indirection.

```duprol
&use {std/text_io.py}

object t
method t.new(value)
    new :self t
    set t.value = :value
    del t._instance_name
    return :t
end
method t._impl::repr()
    return '<t ${self.value}>'
end
method t._impl::add(other)
    return [call :self.new([ :self.value + :other.value ])]
end

set t_a = [call :t.new(10)]
set t_b = [call :t.new(20)]
# <t 10> <t 20> <t 30>
io:println(:t_a, :t_b, [:t_a + :t_b])
```

## Expression Folding

Expresion folding is now disabled by default.
It isnt useful for small scripts and slows them
down if enabled by default. So I made the choice to
disable it by default.

## Inline Functions

```duprol
# acts like macro
# but instead of textual replacement
# its on the bytecode level
fn::inline add_inline(res, a, b)
    set ::res = [::a, ::b]
end

inline::add_inline(res, 20, 30)
# compiles into
set res = [20 + 30]
# when folded
set res = 50
```

## `io:input(var_name, prompt, default_value)`

The `text_io.py` extension now supports disabling the inputs
and use the defaults instead. Which is an improvement for testing.

## New switches

`switch::static` (old behavior) and `switch` (new behavior)
The new switch replaced the old one with one major difference.

```duprol
# New switch behavior fixed this.
# At the cost of O(n)

set something = 90

# new behavior allows
# variables in the cases
switch :some_value
    case :something
        ...
    end
end

# To use the old behavior and gain O(1)

# old behavior can only accept
# constants in cases
switch::static :some_value
    case "must be a constant"
        ...
    end
end
```

## Fixed a bug

In-expression function calls raise `KeyError` when the function
does not return anything, and must explicitly return `nil`
in the recent commit this has been fixed.
