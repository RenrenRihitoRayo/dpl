# Additions 1.2.0

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