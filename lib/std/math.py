if __name__ != "__dpl__":
    raise Exception("This must be included by a DuProL script!")

"""
Sorry if there are bugs
the entire module has been vibe coded by me :P

- Sincirely Darren
"""

ext = dpl.extension("math")

operators = [
   ["**"],                # Exponentiation (right to left)
   ["*", "/", "//", "%"], # Multiplication, division, etc. (left to right)
   ["+", "-"]             # Addition and subtraction (left to right)
]

def evaluate(expr):
    if isinstance(expr, (int, float)):
        return expr

    # Recursively evaluate any sublists first
    expr = [evaluate(e) if isinstance(e, list) else e for e in expr]

    # check for unary operators which isnt directly supported
    num_operands = sum(1 for e in expr if isinstance(e, (int, float)))
    num_operators = sum(1 for e in expr if isinstance(e, str) and e in {"**", "*", "/", "//", "%", "+", "-"})

    if num_operators >= num_operands:
        raise ValueError(f"Unsupported expression (likely unary op): {expr}")

    for ops in operators:
        i = 0
        while i < len(expr):
            if expr[i] in ops:
                op = expr[i]
                left = expr[i - 1]
                right = expr[i + 1]

                if op == "**":
                    result = left ** right
                elif op == "*":
                    result = left * right
                elif op == "/":
                    result = left / right
                elif op == "//":
                    result = left // right
                elif op == "%":
                    result = left % right
                elif op == "+":
                    result = left + right
                elif op == "-":
                    result = left - right

                # Replace the operator and its operands with the result
                expr = expr[:i - 1] + [result] + expr[i + 2:]
                i -= 1  # Step back to handle cascading ops of same precedence
            else:
                i += 1

    return expr

@dpl.add_matcher(ext.mangle("expr_match"))
def matcher(frame, expr):
    if expr and expr[0] == "math":
        return evaluate(expr[1:])[0]