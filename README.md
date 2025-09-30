# DPL – The Dumb Programming Language

> "Simplicity is everywhere in DPL, like an airport cutting expenses.
> DPL gives you freedom. In return, it's your fault when you fail."

Welcome to **DPL**, the programming language that doesn\'t try to be smart - just **dumb enough to let you do whatever you want**. DPL is minimal, messy, and proud of it.
There are no style rules. There are no guardrails. Just a loosely-held-together interpreter and your own chaotic energy.

## !! ✨✨NEW IN DPL 2.0.0✨✨ !!

* Objects now have short-hand constructors!

You can use `make_cons object` to automatically make a constructor for that object,
given that you have defined them implicitly in the object.

* New debug output!

Using `io:debug(object)` in `std/text_io.py`,
will yield more interesting output for objects.

* `declare` in multiline dictionaries.

You can use declare to define keys that would be
implicitly defined.

* Multiline dictionaries and lists can now be nested!

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

* Expression Folding has been fixed

* Parameter and Variable Checks

* Actual Expressions

* In-instruction blocks

* Added "excluded.txt"

This is to more efficiently ignore
test cases that intentionally or
predictably fails.

* CLI can call different versions!

This only works for uncompiled scripts.

## Features

* Simple syntax

Yes DPL has 30+ keywords
even more than pythons.
But syntax is easy to catch.

* Simple interopt between Python and C

DPL can be used as a glue between the two
and has minimal wrapper requirements.

* Simple Execution Model

No JIT no unsuprised async hell,
you get what you use.

* Small standard library

DPL can interopt with python hence
the lack of libraries.

* Small source size

Below 13K LOC which is big for toy
programming languages like DuProL
(yes DPL is a toy language)

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
    return 42
end

catch (result) greet(Alex)
greet(Andrew)
io:println(:result)
```

## DPL's Moto

> DPL just works.
> What your code doesnt?
> Thats on you not DPL.

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
* "--no-lupa" disables Lua inter-opt (via LuaJIT)
* "--no-cffi" disables C inter-opt
* use "--simple-mode" to disable most dependencies
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

# 2.0.0

Updates will be added here.