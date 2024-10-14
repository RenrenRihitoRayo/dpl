DPL - Dumb Programming Language

A very simple OOP language.

Supports:
- Higher order functions
- Objects (similar to rusts struct and impl)
- Python extensions (not interop!)

Current Version: 0.1-a

Authors note:
Why...

Code example
```
fn greet name
  println (sum "Hello " %name "!")
end

greet "You"

# An object huh...
object test
# constructor
method %test new name
  new _nonlocal.test temp
  set temp.name %name
  return %temp
end
# method 
method %test greet name
  println (sum "Hello " %name " ,I am " %self.name)
end
# internal method to get the representation
method %test _im_repr
  return (sum "<Person (" %self.name ")>")
end

catch [my_person] test.new "Carl"
my_person.greet "Jason"
# prints <Person (Carl)>
println %my_person
```

Now with advanced meta programming!

    Using `[meta_value]` attribute of an object.
    When that attribute is defined in the object,
    when setting or reading the object it will read
    the `[meta_value]` sttribute instead of setting or
    reading the entire object.

    A new syntax has been added to facilitate working
    around this attribute so you dont always get that
    attribute in some cases.

    Note:

        The new `typed_vars.py` module uses this attribute
        to work with typed variables.

    ```
    object int_like
    method %int_like new value
      new _nonlocal.int_like temp
      # normal dotted.name syntax doesnt support this
      # which is normal to avoid easily using this.
      set "temp.[meta_value]" %value
      return :temp
    end
    set int_like.new.defs.value 0

    catch [my_int] int_like.new 90
    # sets the meta attribute (use fset to work around this)
    set my_int 80
    # should print 160 and <Object int_like>
    println (%my_int * 2) :my_int

    # sets my_int and bypasses the meta attribute mechanism
    # so under the hood it is no longer the object we created
    fset my_int 90
    # prints 90 and 90 since fset and not set was used
    println %my_int :my_int

    # if you have a _im_repr method use raw_print or raw_println
    # or when the default one is not removed.
    # to bypass that method and see the object as it is.
    ```
