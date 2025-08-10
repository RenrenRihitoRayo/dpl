# DPL – The Dumb Programming Language

> "Simplicity is everywhere in DPL, like an airport cutting expenses.
> DPL gives you freedom. In return, it's your fault when you fail."

Welcome to **DPL**, the programming language that doesn't try to be smart — just **dumb enough to let you do whatever you want**. DPL is minimal, messy, and proud of it.
There are no style rules. There are no guardrails. Just a loosely-held-together interpreter and your own chaotic energy.

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

# 1.4.9

## Inline Call Expressions

See `15-functions.dpl` in examples.

## CFFI Support

CFFI Support will be back!
Better and more convinient
than ever before!