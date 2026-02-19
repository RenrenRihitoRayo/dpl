from pycparser import c_parser, c_ast, c_generator
import sys

C_BUILTINS = {
    "void", "char", "short", "int", "long", "float", "double",
    "signed", "unsigned", "_Bool", "size_t"
}


def remove_preprocessor(text):
    lines = []
    for line in text.splitlines():
        if not line.strip().startswith("#include"):
            lines.append(line)
    return "\n".join(lines)


class CDefGenerator(c_ast.NodeVisitor):
    def __init__(self):
        self.types = set(C_BUILTINS)
        self.unknown_types = set()
        self.output = []
        self.codegen = c_generator.CGenerator()

    # ---------- TYPES ----------

    def visit_Typedef(self, node):
        self.types.add(node.name)
        self.output.append(f"#type {node.name}")
        self.output.append(self.codegen.visit(node) + ";")

    def visit_Struct(self, node):
        if node.name:
            self.types.add(node.name)
            self.output.append(f"#type {node.name}")
            self.output.append(self.codegen.visit(node) + ";")

    def visit_Enum(self, node):
        if node.name:
            self.types.add(node.name)
            self.output.append(f"#type {node.name}")
            self.output.append(self.codegen.visit(node) + ";")

    # ---------- FUNCTIONS ----------

    def visit_Decl(self, node):
        if isinstance(node.type, c_ast.FuncDecl):
            name = node.name
            print(node)
            self.output.append(f"#func \"[raw]{name}\"")
            self.output.append(self.codegen.visit(node) + ";")
            self._collect_types(node)
        elif hasattr(self, f"visit_{node.type.__class__.__name__}"):
            getattr(self, f"visit_{node.type.__class__.__name__}")(node.type)

    # ---------- TYPE COLLECTION ----------

    def _collect_types(self, node):
        for _, child in node.children():
            if isinstance(child, c_ast.TypeDecl):
                t = self._extract_type(child)
                if t and t not in self.types:
                    self.unknown_types.add(t)

    def _extract_type(self, node):
        if hasattr(node.type, "names"):
            return node.type.names[0]
        return None


def generate_cdef(header_text):
    header_text = remove_preprocessor(header_text)

    parser = c_parser.CParser()
    ast = parser.parse(header_text)

    gen = CDefGenerator()
    gen.visit(ast)

    # unknown types fallback
    for t in sorted(gen.unknown_types):
        gen.output.insert(0, f"typedef void {t};")

    return "\n".join(gen.output)


if __name__ == "__main__":
    with open(sys.argv[1]) as f:
        content = f.read()

    print(generate_cdef(content))
