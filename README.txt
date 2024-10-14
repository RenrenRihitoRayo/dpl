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
