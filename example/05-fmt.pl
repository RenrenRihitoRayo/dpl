--
  Using the new format strings.
  Not only do they support the old syntax,
  but adds on a new syntax to format strings.
  They now support expressions!
  They no longer just do text replacements
  which slowdown for each variable in the scope,
  but only substitutes specific parts!
  Making it a lot faster than the old one!
--

&use {std/text_io.py}

set this = 90

set object = .dict
set object.name = "what"
set object.list = (1 2 3 4 5 6)

# spikes but on average 1.5ms in this case
# min 1ms max 1.6ms
# prints: what 1 92 22
START_TIME
io:println('${object.name} ${object.list(0)} &{:this + 2} &{sum :object.list}')
STOP_TIME
LOG_TIME "new format strings (old syntax unchanged)"

# 2ms and above. sometimes 1.5ms as well
# min 1.5 max 3ms
# prints: what 1 &{:this + 2} &{sum :object.list}
START_TIME
io:println ([oldformat "${object.name} ${object.list(0)} &{:this + 2} &{sum :object.list}"])
STOP_TIME
LOG_TIME "old format strings (collapsed into a method instead)"

--
  Keep in mind that the new format strings
  is not guaranteed to run faster!
  The new format string are always O(N)
  where N is the length of the string.
  Unlike the old ones which is still O(N)
  but N is the number of variables.
  
  The new format strings also offer
  new syntax to atleast pay back on its
  draw backs. It supports fallback variables
  and default values.
  
  Ex:
  '${user|user_name|username:user name wasnt provided}'
  
  There are also new expression syntax.
  Why did we separate them from normal
  variable substitution?
  For compatibility and because doing
  `${name}` is faster than `&{:name}` since
  the latter doesnt just replaces it evaluates.
  
  Ex (x is 90):
  '&{:x * 2}' => '180'
  '${x}' => '90' (simply text replacement)
  
  Update:
  In more busy scopes, the new format strings
  win by a lot! A scope with 1000 variables was
  similated and the results are:
  * 4.5s~ for the new fmt strings
  * 5.1s~ for the old fmt strings.
--
