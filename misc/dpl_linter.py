from lib.core.newest.ast_gen import *

class Program:
    def __init__(self, code):
        if isinstance(code, dict):
            self.tree = gen_ast_from_hlir(code["code"])[0]
        else:
            self.tree = get_ast_from_str(code)[0]
        
        self.functions = None
        self.variables = None
        self.runtime_imports = []
    
    def get_variables(self):
        if self.variables:
            return self.variables
        else:
            self.variables = list(walk_for_each(AssignNode, self.tree))
            return self.variables
    
    def get_functions(self):
        if self.functions:
            return self.functions
        else:
            self.functions = list(walk_for_each(FunctionNode, self.tree))
            return self.functions
    
    def get_runtime_imports(self):
        if self.runtime_imports:
            return self.runtime_imports
        else:
            self.runtime_imports = list(walk_for_each(UseNode | UseLuaNode, self.tree))
            return self.runtime_imports
    
    def update(self):
        self.functions = None
        self.variables = None
        self.runtime_imports = None
        self.get_variables()
        self.get_functions()
        self.get_runtime_imports()