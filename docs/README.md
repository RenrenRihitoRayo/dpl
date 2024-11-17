# This is the documentation for the Standard Library

## Info

    Written by: Darren Papa

## Libraries

- `text_io.py`
- `file_io.py`
- `dicts.py`
- `typed_vars.py`
- `error_handling.py`
- `how_to.py`
- `string.py`
- `temp_utils.py`
- `to_dicts.py`
- `to_callable.py`
- `run_local.py`
- `script_detect.py`

## text_io.py

    This library has one function which takes care of IO.

```
# this prints the values without a new line
io raw_print
# this prints the values with a newline.
io raw_println

# they both behave like raw_print and raw_println
# but they process objects via `_im_repr`
io print
io println

# this allows DPL to output ansii escape codes
# and uses sys.stdout.write instead of print under the hood.
io raw_term_print
```

## file_io.py

    This enables the user to open and manipulate files.

```
pycatch [this_file] _mods.py.file_io.open_file "this.txt" "w"
_mods.py.file_io.write_file :this_file "This should be in this.txt"
# WHEN THE FILE IS NOT CLOSED IT MIGHT NOT BE WRITTEN TO.
_mods.py.file_io.close_file :this_file
```

## dicts.py

    This is a helpful util in making dictionaries.

```
object my_dict
body _mods.py.dict :my_dict
    name = value
    .def name
    .let name = value
end

# if you wish to nest them, you need to do some nasty stuff.

object my_other_dict
body _mods.py.dict :my_dict
    name = value
    .def name
    .let name = value
end

object my_nested_dict
body _mods.py.dict :my_nested_dict
    this_dict = :my_other_dict
end
```

## typed_vars.py

    This extension will help you manage type safety in DPL.

```
# Define a variable
defv this_var _mods.types.integer

setv this_var 90

# 180
io println (%this_var * 2)

# Error!
setv this_var "this is a string"
```

## error_handling.py

    This provides a way of manually raising errors.
    An assert function is also available.

```
_mods.py.panic error_message error_code

_mods.py.assert condition error_message error_code
```

    By default error name is (ASSERT_ERROR)