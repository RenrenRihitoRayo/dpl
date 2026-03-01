'''
Rudimentary AST Generator for DPL code.

Currently only has nodes for (heirchy):
* Program Node
* Instruction Node
  * Loops
  * Functions
  * Conditionals
  * Assignments
  * Runtime Imports
* Body Node

Note:
This isnt for codegen!
Only for type checking and static analysis.

Sample code:
```
use {std/text_io.py}

fn main()
    io:println("Hello, world!")
    set loops = 90
    loop :loops
        io:println("Loop like this")
    end
end
```

With walk(gen_ast_from_str(code)):
```
ProgramNode
  line: 1, ins: use, module: {std/text_io.py}
  line: 3, ins: fn, name: main
    line: 4, ins: io:println
    line: 5, ins: set, name: loops, value: 90
    line: 6, ins: loop, iterations: :loops
      line: 7, ins: io:println
```
'''

from .common_types import Expression
from . import serialize_dpl
from . import info
from . import py_parser
import sys

MAIN_FILE = "__main__"

def set_main(main):
    global MAIN_FILE
    MAIN_FILE = main

def blockade(tokens):
    "Called blockade because it generates blocks. Blocking... blockades."
    instructions = []
    for token in tokens:
        line, _, ins, body, args = token
        if ins == "fn":
            node = FunctionNode(token)
        elif ins == "method":
            node = MethodNode(token)
        elif ins == "loop":
            node = LoopNode(token)
        elif ins == "for":
            node = ForLoopNode(token)
        elif ins == "if":
            node = IfNode(token)
        elif ins == "match":
            node = MatchNode(token)
        elif ins == "case":
            node = CaseNode(token)
        elif ins == "with":
            node = WithNode(token)
        elif ins == "default":
            node = DefaultNode(token)
        elif ins == "switch":
            node = SwitchNode(token)
        elif ins == "switch::static":
            node = SwitchNode(token)
        elif ins == "while":
            node = WhileLoopNode(token)
        elif ins == "string":
            node = StringNode(token)
        elif ins == "dict":
            node = DictNode(token)
        elif ins == "list":
            node = ListNode(token)
        elif ins == "set":
            node = AssignNode(token)
        elif ins == "del":
            node = UnassignNode(token)
        elif ins == "use":
            node = UseNode(token)
        elif ins == "use_luaj":
            node = UseLuaNode(token)
        elif ins == "catch":
            node = CatchNode(token)
        elif ins == "return":
            node = ReturnNode(token)
        elif ins == "new":
            node = NewNode(token)
        elif ins == "tuple":
            node = TupleNode(token)
        elif ins == "use_c":
            node = UseCNode(token)
        elif args and isinstance(args[0], tuple | list):
            node = CallNode(token)
        else:
            node = InstructionNode(token)
        instructions.append(node)
    return instructions

def gen_ast_from_str(code, file=None):
    return [ProgramNode(
        blockade(
            py_parser.process_code(code)["code"]
        ),
        file
    )]

def gen_ast_from_hlir(code, file=None):
    return [ProgramNode(
        blockade(
            code
        ),
        file
    )]

def gen_ast_from_cdpl(file):
    with open(file, "rb") as f:
        data =\
        serialize_dpl.deserialize(f.read())
    return gen_ast_from_hlir(data["code"])

def walk_for_each(node_type, tree):
    for ins in tree:
        if isinstance(ins, node_type):
            yield ins
        elif isinstance(ins, ProgramNode):
            yield from walk_for_each(node_type, ins.value)
        elif isinstance(ins, BodyNode):
            yield from walk_for_each(node_type, ins.value)

def walk(tree, depth=0, file=sys.stdout):
    if tree is None:
        print("  "*depth + "Body: Empty", file=file)
        return
    for ins in tree:
        match ins:
            case ProgramNode(instructions):
                if ins.file:
                    print("  "*depth + f"# ProgramNode `{ins.file}`", file=file)
                else:
                    print("  "*depth + f"# ProgramNode", file=file)
                walk(ins, depth+1, file=file)
            case _:
                print("  "*depth + f"{ins}", file=file)
                if ins.body:
                    walk(ins.body, depth+1, file=file)
                    print("  "*depth + "end", file=file)

class ASTNode:
    __match_args__ = ("name", "value")
    
    def __init__(self, name, value):
        self.__name = name
        self.__value = value
    def __iter__(self):
        return iter(self.__value)
    def __getitem__(self, name):
        return self.__value[name]
    def __setitem__(self, name, value):
        self.__value[name] = value
    def __bool__(self):
        return bool(self.__value)
    @property
    def value(self):
        return self.__value
    @property
    def node_type(self):
        return self.__name
    @node_type.setter
    def node_type(self, value):
        self.__name = value
    def __repr__(self):
        return f"{self.__name}({self.__value!r})"

# __match_args__ is overwritten
# or wed need to do Node(node_name, node_value)
# for every case
# future nodes may need it
# so we just manually override it.

class ProgramNode(ASTNode):
    __match_args__ = ("value",)
    def __init__(self, value, file=None):
        super().__init__("ProgramNode", value)
        self.file = file

class InstructionNode(ASTNode):
    __match_args__ = ("value",)
    def __init__(self, value):
        self.line_pos, self.source_file, self.instruction, self.body, self.args = value
        if self.body:
            self.body = blockade(self.body)
        if self.source_file == "__main__":
            self.source_file = MAIN_FILE
        super().__init__("InstructionNode", value)
    def __repr__(self):
        if self.args:
            return f"{self.instruction} {repr(Expression(self.args))[1:-1]} # {self.__class__.__name__} in line {self.line_pos} @ {self.source_file}"
        return f"{self.instruction} # {self.__class__.__name__} in line {self.line_pos} @ {self.source_file}"

class ReturnNode(InstructionNode):
    __match_args__ = ("value",)
    def __init__(self, value):
        super().__init__(value)
        self.node_type = "ReturnNode"
        self.return_expr = self.args

class DictNode(InstructionNode):
    __match_args__ = ("value",)
    def __init__(self, value):
        super().__init__(value)
        self.node_type = "DictNode"
        self.name = self.args[0] if self.args else "???" # can be a variable
        self.is_object = self.args[0].startswith(":")
        self.body = None

class ListNode(InstructionNode):
    __match_args__ = ("value",)
    def __init__(self, value):
        super().__init__(value)
        self.node_type = "ListNode"
        self.name = self.args[0] if self.args else "???" # can be a variable
        self.is_object = self.args[0].startswith(":")
        self.body = None

class StringNode(InstructionNode):
    __match_args__ = ("value",)
    def __init__(self, value):
        super().__init__(value)
        self.node_type = "StringNode"
        self.name = self.args[0] if self.args else "???"
        self.body = None

class TupleNode(InstructionNode):
    __match_args__ = ("value",)
    def __init__(self, value):
        super().__init__(value)
        self.node_type = "TupleNode"
        self.name = self.args[0] if self.args else "???"
        self.body = None

class FunctionNode(InstructionNode):
    __match_args__ = ("value",)
    def __init__(self, value):
        super().__init__(value)
        self.node_type = "FunctionNode"
        self.function_name = self.args[0]
        self.function_parameters = self.args[1]
        function_tags = self.function_tags = {}
        for item in self.args[2:]:
            if isinstance(item, dict):
                (name, value), = item.items()
                function_tags[name] = value
            else:
                function_tags[item] = True

class MethodNode(FunctionNode):
    __match_args__ = ("value",)
    def __init__(self, value):
        super().__init__(value)
        self.node_type = "MethodNode"
        self.function_name = self.args[0]
        self.object_root = self.args[0].split(".", 1)[0]
        self.function_parameters = self.args[1]
        function_tags = self.function_tags = {}
        for item in self.args[2:]:
            if isinstance(item, dict):
                (name, value), = item.items()
                function_tags[name] = value
            else:
                function_tags[item] = True
        self.body = None

class CallNode(InstructionNode):
    __math_args__ = ("value",)
    def __init__(self, value):
        super().__init__(value)
        self.node_type = "CallNode"
        self.function_name = self.instruction
        self.args_list, = self.args

    def __repr__(self):
        return f"{self.function_name}({repr(Expression(self.args_list))[1:-1]}) # CallNode in line {self.line_pos} @ {self.source_file}"

class UseNode(InstructionNode):
    __match_args__ = ("value",)
    def __init__(self, value):
        super().__init__(value)
        self.node_type = "UseNode"
        self.module = self.args[0]
        if len(self.args) == 3:
            self.alias = self.args[2]
        else:
            self.alias = None

class UseLuaNode(InstructionNode):
    __match_args__ = ("value",)
    def __init__(self, value):
        super().__init__(value)
        self.node_type = "UseLuaNode"
        self.module = self.args[0]

class UseCNode(InstructionNode):
    __match_args__ = ("value",)
    def __init__(self, value):
        super().__init__(value)
        self.node_type = "UseCNode"
        self.module = self.args[0]


class AssignNode(InstructionNode):
    __match_args__ = ("value",)
    def __init__(self, value):
        super().__init__(value)
        self.node_type = "AssignNode"
        self.variable_name = self.args[0]
        self.variable_value = self.args[2]

class UnassignNode(InstructionNode):
    __match_args__ = ("value",)
    def __init__(self, value):
        super().__init__(value)
        self.node_type = "UnassignNode"
        self.variable_name = self.args[0]

class NewNode(InstructionNode):
    __match_args__ = ("value",)
    def __init__(self, value):
        super().__init__(value)
        self.node_type = "NewNode"
        self.object, self.instance_name = self.args

class LoopNode(InstructionNode):
    __match_args__ = ("value",)
    def __init__(self, value):
        super().__init__(value)
        self.node_type = "LoopNode"
        self.iterations = self.args[0] if self.args else "infinite"
        self.body = None

class ForLoopNode(InstructionNode):
    __match_args__ = ("value",)
    def __init__(self, value):
        super().__init__(value)
        self.node_type = "ForLoopNode"
        self.item_name = self.args[0]
        self.iterable = self.args[2]
        self.body = None

class IfNode(InstructionNode):
    __match_args__ = ("value",)
    def __init__(self, value):
        super().__init__(value)
        self.node_type = "IfNode"
        self.condition = self.args[0]
        self.body = None

class WhileLoopNode(InstructionNode):
    __match_args__ = ("value",)
    def __init__(self, value):
        super().__init__(value)
        self.node_type = "WhileLoopNode"
        self.condition = self.args[0]
        self.body = None

class CaseNode(InstructionNode):
    __match_args__ = ("value",)
    def __init__(self, value):
        super().__init__(value)
        self.node_type = "CaseNode"
        self.condition = self.args[0]
        self.body = None

class WithNode(InstructionNode):
    __match_args__ = ("value",)
    def __init__(self, value):
        super().__init__(value)
        self.node_type = "CaseNode"
        self.constant = self.args[0]
        self.body = None

class DefaultNode(InstructionNode):
    __match_args__ = ("value",)
    def __init__(self, value):
        super().__init__(value)
        self.node_type = "DefaultNode"
        self.body = None

class MatchNode(InstructionNode):
    __match_args__ = ("value",)
    def __init__(self, value):
        super().__init__(value)
        self.node_type = "MatchNode"
        self.match_value = self.args[0]
        self.body = None

class SwitchNode(InstructionNode):
    __match_args__ = ("value",)
    def __init__(self, value):
        super().__init__(value)
        self.node_type = "SwitchNode"
        self.switch_value = self.args[0]
        self.body = None

class BodyNode(ASTNode):
    __match_args__ = ("value",)
    def __init__(self, value):
        super().__init__("BodyNode", value)
