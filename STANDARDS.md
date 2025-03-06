# Major Rules

Rules that must always be followed:
- No more than 6 nested blocks of code.
- No more than 4 expressions within a lambda
- No more than 4 hidden imports
    1. Imports in a non global scope
    2. Optional imports
- Exception to the rule above: as long as it is documented it is valid to go over.
- Files must be less than 3k lines.

# Minor Rules

- Do not include binaries (executables)
unless it is required for a certain function
in DPL (tooling can be done with pure python)
- Unecessary complexity is prohibited unless
necessary for logic. (Violating the first major
rule via this rule is valid, but must be documented
extensively.)