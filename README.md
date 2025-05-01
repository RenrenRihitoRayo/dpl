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

- To suffer
- To show off
- To look smart-ish

Why use DPL?
* You’re tired of languages judging you.
* You believe standards are optional. You want full control and full responsibility.
* You enjoy chaos, minimalism, or pain.

---

# Change Notes / Dev Logs

Most recent at top.

# 1.4.8

## Re-introduced "include-py.txt" in `lib/std`

See "Including Directories" in [here](darrenpapa.github.io)

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
