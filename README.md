# DPL 1.4.0

## Starting with DPL

### Hello world!

```DuProL
import "text_io.py"
io:println "Hello, World!"
```

### Variables

```DuProL
import "text_io.py"

set value 90
# Output: 90 90
io:println :value %value
set value 80
# Output: 80
io:println :value

const value 80
# fset stands for "force set" which bypasses constants
fset value 180
# Raises an error
set value 80
```

	`:name` is recommended and is faster than `%name` which uses a mechanism for meta programming.
	This mechanism is called the "meta value" mechanism. It is used by the "typed_vars.py" extension.
	An attribute "[meta_value]" will be used when found instead of the entire object. To be precise
	its implicitly ":object.[meta_value]" thats being fetched rather than ":object". Using ":object" will
	always return the object as is, with no other hidden mechanisms other than the constants behavior.

```DuProL
import "typed_vars.py"
import "types.py"

defv name :types.str
setv name "This"
# An error will be raised.
setv name 90
```

### Functions

```DuProL
# Define a function
fn name arg1 arg2 ...
	...
	return value1 value2 ...
end

# set a default value for its argument(s)
set name.defs.arg1 90

# Call the function
name arg1 arg2 ...

# Get the return values
catch [return_value1 return_value2 ...] name arg1 arg2 ...
```

	Functions do not support keyword arguments yet.
	Although they do support default values for those arguments.

### If statements

```DuProL
if (val op val)
	...
end

if_else (val op val)
	# true
else
	# false
end
```

### Loops

```DuProL
loop
	...
end

while (expr)
	...
end

for i in val

end

loop 1,000,000
	...
end
```

	"break" will exit the loop.
	"skip" will skip to the next iteration.
	I dont know where the "continue" keyword got traction,
	its just highly counter intuitive.

### Templates

	Templates are used to easily define objects with strict typing.

```DuProL
template name
	member_name member_type
end
```

	If the member_type is not present then by default its type is any.

```DuProL
import "types.py"

template person
	name :types.str
	age  :types.int
	data
end

from_template :person Andrew
	name $name
	age  90
	data [1 2 3 4 5 6 7 8 9 0 "This is a list!"]
end
```