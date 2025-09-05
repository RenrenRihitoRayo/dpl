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
    end
end

```

* Flask wrapper is available in `std/other/flask.py`

    There is an example given in the examples directory.

* Reworked the switch statement


<!-- ************************ TODO: ACTUALLY DO THIS *****************************
    * New parser has been fully implemented
-->

## Philosophy

- The **language** shouldnt have standards.  
- **If your code looks weird, that’s your aesthetic.**  
- If it breaks, that\'s your fault.  
- If it works, that\'s DPL.

## Features

- Functions? Yes, and they sometimes even work.  
- Syntax? Let\'s call it... *flexible*.  
- Naming conventions? **snake\_case**, **PascalCase**, **camelCase**, or **whoknows\_\_\_???case** - all welcome.

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

### (most recent release 1.4.9)

# 2.0.0 (Indev)

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