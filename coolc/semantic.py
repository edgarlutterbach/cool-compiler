import coolc.ast as ast

# Classe para erro
class SemanticError(Exception):
    def __init__(self, message, line):
        super().__init__(message)
        self.message = message
        self.line = line

# Linha dos nós da árvore
BUILTIN_LINE = 0

# Classes que nenhuma outra pode herdar
FORBIDDEN_PARENTS = {"Int", "String", "Bool", "SELF_TYPE"}

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

    return [object_class, io_class, int_class, string_class, bool_class]

# Classe do analisador semântico
class SemanticAnalyzer:
    def __init__(self, program):
        self.program = program
        self.classes = {}

    def analyze(self):
        self.register_classes()
        self.check_parents()
        self.check_cycles()
        return self.classes

    def register_classes(self):
        basics = basic_classes()
        basic_names = {cls.name for cls in basics}

        for cls in basics:
            self.classes[cls.name] = cls

        for cls in self.program.classes:
            if cls.name == "SELF_TYPE":
                raise SemanticError("'SELF_TYPE' não pode ser usado como nome de classe", cls.line)
            elif cls.name in basic_names:
                raise SemanticError(f"Classe básica '{cls.name}' não pode ser redefinida", cls.line)
            elif cls.name in self.classes:
                first = self.classes[cls.name]
                raise SemanticError(f"Classe '{cls.name}' já foi declarada na linha {first.line}", cls.line)
            else:
                self.classes[cls.name] = cls

    def check_parents(self):
        for cls in self.program.classes:
            if cls.parent is None:
                cls.parent = "Object"
                continue

            if cls.parent in FORBIDDEN_PARENTS:
                raise SemanticError(f"Classe '{cls.name}' não pode herdar de '{cls.parent}'", cls.line)

            if cls.parent not in self.classes:
                raise SemanticError(f"Classe '{cls.name}' herda de '{cls.parent}', que não foi declarada", cls.line)

    def check_cycles(self):
        for cls in self.program.classes:
            visited = set()
            current = cls.name

            while current != "Object":
                if current in visited:
                    cyclic_class = self.classes[current]
                    raise SemanticError(f"Herança cíclica: a classe '{cyclic_class.name}' herda de si mesma", cyclic_class.line)

                visited.add(current)
                current = self.classes[current].parent

