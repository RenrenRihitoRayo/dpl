# 1.4.5 Added new for loop syntax

```
for index, value in :list
    io:println '${index:rjust}: {value}'
end
```

# 1.4.5 Minor changes

`import*` is now deprecated.
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
- :x: Build system.
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

