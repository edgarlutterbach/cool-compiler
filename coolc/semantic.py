import coolc.ast as ast

# Classe para erro
class SemanticError(Exception):
    def __init__(self, message, line):
        super().__init__(message)
        self.message = message
        self.line = line

# Linha dos nós da árvore
BUILTIN_LINE = 0

# Método para construção de classes básicas de COOL
def basic_classes():
    object_class = ast.Class("Object", None, [
        ast.Method("abort", [], "Object", None, BUILTIN_LINE),
        ast.Method("type_name", [], "String", None, BUILTIN_LINE),
        ast.Method("copy", [], "SELF_TYPE", None, BUILTIN_LINE),
    ], BUILTIN_LINE)

    io_class = ast.Class("IO", "Object", [
        ast.Method("out_string", [ast.Formal("x", "String", BUILTIN_LINE)], "SELF_TYPE", None, BUILTIN_LINE),
        ast.Method("out_int", [ast.Formal("x", "Int", BUILTIN_LINE)], "SELF_TYPE", None, BUILTIN_LINE),
        ast.Method("in_string", [], "String", None, BUILTIN_LINE),
        ast.Method("in_int", [], "Int", None, BUILTIN_LINE),
    ], BUILTIN_LINE)

    int_class = ast.Class("Int", "Object", [], BUILTIN_LINE)
    bool_class = ast.Class("Bool", "Object", [], BUILTIN_LINE)

    string_class = ast.Class("String", "Object", [
        ast.Method("length", [], "Int", None, BUILTIN_LINE),
        ast.Method("concat", [ast.Formal("s", "String", BUILTIN_LINE)], "String", None, BUILTIN_LINE),
        ast.Method("substr", [ast.Formal("i", "Int", BUILTIN_LINE), ast.Formal("l", "Int", BUILTIN_LINE)], "String", None, BUILTIN_LINE),
    ], BUILTIN_LINE)

    return [object_class, io_class, int_class, bool_class]

# Classe do analisador semântico
class SemanticAnalyzer:
    def __init__(self, program):
        self.program = program
        self.classes = {}

    def analyze(self):
        return self.classes
