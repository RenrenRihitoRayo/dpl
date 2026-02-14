# DPL – The Dumb Programming Language

> "Simplicity is everywhere in DPL, like an airport cutting expenses.
> DPL gives you freedom. In return, it's your fault when you fail."

Welcome to **DPL**, the programming language that doesn\'t try to be smart - just **dumb enough to let you do whatever you want**.
DPL is minimal, messy, and proud of it.
There are no style rules. There are no guardrails. Just a loosely-held-together interpreter and your own chaotic energy.

## Features

* Simple syntax

Yes DPL has 30+ keywords
even more than pythons.
But syntax is easy to catch.

* OOP is simple (but manual)

Objects with operator overloading.

* Simple interopt between Python and C

DPL can be used as a glue between the two
and has minimal wrapper requirements.

* Simple Execution Model

No JIT, no unsuprising async hell,
you get what you use.

* Small standard library

DPL can interopt with python hence
the lack of libraries.

* Small source size

Below 13K LOC which is big for toy
programming languages like DuProL
(yes DPL is a toy language... somehow...)

* Opt-In optimizations

DPL never changes code unless you
tell it so, in such way you choose
whether to optimize init time or preruntime.

## Code Sample

```DuProL
&use {std/text_io.py}

io:println("Hello, world!")

fn greet(name)
    io:println('Hello ${name}!')
    return 42
end

set result = [call :greet(Alex)]
greet(Andrew)
io:println(:result)
```

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

## Footnote

DPL just works, if it doesnt its your fault.
We dont push standards, but your confusion is
YOUR problem not DPL\'s.
<br><br>
Notice repetition?
We dont enforce DRY here, why? In most cases
you either end up having one class being
inherited by layers of subclasses (trust me, I\'ve been there)
and messed up dependency injection (which DPL currently has
in its code base)
<br><br>
DPL once was a toy programming language,
it still is in essence, however will still
mature. I could say that when the entire project
could fit into 50KB (now almost half a megabyte),
but I can no longer say the same.
<br><br>
Calling DPL a toy programming language is a little
bit... underestimating DPL...
<br><br>
After all DPL can call C functions, Python functions
(with AND without wrappers), Lua functions (using lupa),
and most importantly, overcomes every other python based
toy languages except in speed. Still better though.
<br><br>
Yeah DPL was a mistake... but this mistake wasn\'t bad at all,
in fact it came out better.
<br><br>
In DPL we dont care if you write messy code,
dev to dev, we know if it works, it works.
No need to waste a weeks worth of coffe
trying to fix a bug because your senior dev
asked you to make the code ***prettier***.

## Installation

After cloning this repository
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

## !! ✨✨NEW IN DPL 2.0.0✨✨ (as of 2026) !!

* A new expression! 

Instead of `[call :func()]` you can do `func!()` which
is just a shorthand but is much more convenient!

* C interopt has been improved vastly!

Example in `lib/std-c/lib/tect_c.c` (its cdef file is `lib/std-c/test_c.cdef`) 
has shown how to use the python c api to be able to manipulate the local scope!

* Performance Improvement

A consistent 8% to 10% speed improvement.
Bellow was the test to determine the speed increase.
```DuProL
set x = 1

for i in [range 100000]
    set x = [:x * 2]
end
```
Python 3.14: 580-590ms (5.85 microseconds per iteration)
Pypy3 7.x.x: 240-250ms (2.45 microseconds per iteration)
On Arch, intel i3.

