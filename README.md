# DPL – The Dumb Programming Language

> "Simplicity is everywhere in DPL, like an airport cutting expenses.
> DPL gives you freedom. In return, it's your fault when you fail."

Welcome to **DPL**, the programming language that doesn\'t try to be smart - just **dumb enough to let you do whatever you want**. DPL is minimal, messy, and proud of it.
There are no style rules. There are no guardrails. Just a loosely-held-together interpreter and your own chaotic energy.

## !! ✨✨NEW IN DPL 1.4.9✨✨ !!

* in-expression calls!

    You can now call DPL function inside expressions!

* entry point functions

    Tired of manually calling a main function and struggling
    with colliding global variables? No need to worry!
    Functions now support the "entry_point" tag!

* Tired of manually binding C code?

    DPL has a special syntax for header files!
    All you need to do is tell DPL where the file is and
    bam! Your C library is callable in DPL!

## Philosophy

- The **language** shouldnt have standards.  
- **If your code looks weird, that’s your aesthetic.**  
- If it breaks, that\'s your fault.  
- If it works, that\'s DPL.

## Features

- Functions? Yes, and they sometimes even work.  
- Syntax? Let\'s call it... *flexible*.  
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

catch (result) greet(Alex)
greet(Andrew)
io:println(:result)
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

# 1.4.9

## In-expression Calls

_In-expression Calls_ no longer treats control codes as error codes.
See below

```DuProL

fn test()
    break
end

# This would error out with the control code for break
# since return also returns a control code, this breaks
# for all functions that have return values
# this has been fixed in the recent commit of DPL 1.4.9
set result = [call :test()]
```

## Notice for the code base

The code base has been partially rewritten for readability.
"py_parser2.py" have been updated partially.

## DPL Can now run directories!

When DPL gets a directory as the script path.
It will search for what script it should execute.
These are the list:
* "dir/dpl_main.txt" its content should be the script path relative to the root. IE if its in "dir/othername.dpl" it should be "othername.dpl"
* "dir/main.dpl" will be ran when "dpl_main.txt" doesnt exist in the directory.
* If it fails to see both of the above it exits and prints an error.

## Syntax Files Updated

The syntax files for both sublime text and vim have been
updated. From now on both files will be maintained per update.

## CFFI Has been finalized

Using the new ".cdef" file extension.
Using C with DPL has never been so easier than
ever before! No "ffi.cdef" nonsense, its been hidden
from you. Just do "&use:c" and call the functions
like its any other DPL code.

#### /lib/std-c/lib/test_c.c
```C
#include <stdio.h>

void print_greeting(void) {
    printf("Hello, from C!\n");
}

void print_num(int num) {
    printf("Number: %i\n", num);
}
```

#### /lib/std-c/test_c.cdef
```C
/*
    test.cdef
    A C library for testing DPL C-Compat
*/


/* What the library name is */
#lib "test_c"

/* Where the library file is */
#path "std-c/lib/test_c.so@global"

#func "print_greeting"
void print_greeting(void);

#func "print_num"
void print_num(int num);
```

#### 16-c-opt.dpl
```DuProL
-- Setup is hidden from user.
   cdef and dlopen is hidden
   from the user for simplicity --
&use:c {std-c/test_c.cdef}

-- Include io --
&use {std/text_io.py}

-- Hello, from C! --
test_c.print_greeting()
--  Number: 148   --
test_c.print_num(148)
```

## Added Pre-Evaluation Arguments

This makes argument introspection possible.
Since the function call syntax change,
there was a side effect of the argument list
to be lazily evaluated, DPL 1.4.9 just exposes
this.


```DuProL
&use {std/text_io.py}

fn test(num) [preserve-args = true]
    -- [90,] (':arg',) --
    io:println(:_args, :_raw_args)
end

set arg = 90

test(:arg)
```

This enables the users to check how the argument
was before evaluation if it was a variable or
a constant.
<br><br>
This happens on runtime, and not preruntime however
provides almost no slowdown (this is a side effect
not an additional feature)

## Inline Call Expressions

```DuProL
&use {std}

fn square(num)
    return [:num ** 2]
end

set res = [call :square(4)]
-- 16 --
io:println(:res)
```

## CFFI Support

CFFI Support will be back!
Better and more convinient
than ever before!
