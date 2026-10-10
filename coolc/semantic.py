import coolc.ast as ast

# Classe para erro
class SemanticError(Exception):
    def __init__(self, message, line=None):
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
        self.attributes = {}
        self.methods = {}

    # Ponto de entrada
    def analyze(self):
        self.register_classes()
        self.check_parents()
        self.check_cycles()
        self.check_main()
        self.collect_features()
        self.check_feature_types()
        self.check_inheritance()
        return self.classes

    # Registra as classes básicas e as do programa na tabela de classes
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

    # Valida o pai de cada classe do programa e preenche o pai implícito
    def check_parents(self):
        for cls in self.program.classes:
            if cls.parent is None:
                cls.parent = "Object"
                continue

            if cls.parent in FORBIDDEN_PARENTS:
                raise SemanticError(f"Classe '{cls.name}' não pode herdar de '{cls.parent}'", cls.line)

            if cls.parent not in self.classes:
                raise SemanticError(f"Classe '{cls.name}' herda de '{cls.parent}', que não foi declarada", cls.line)

    # Detecta ciclos de herança subindo a cadeia de pais de cada classe
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

    # Exige a classe Main, ponto de partida da execução
    def check_main(self):
        if "Main" not in self.classes:
            raise SemanticError("Programa sem classe 'Main'")

    # Registra os atributos e métodos declarados diretamente em cada classe
    def collect_features(self):
        for cls in self.classes.values():
            attributes = {}
            methods = {}

            for feature in cls.features:
                if isinstance(feature, ast.Method):
                    if feature.name in methods:
                        first = methods[feature.name]
                        raise SemanticError(f"Método '{feature.name}' já foi declarado na classe '{cls.name}', na linha {first.line}", feature.line)
                    methods[feature.name] = feature
                else:
                    if feature.name == "self":
                        raise SemanticError(f"Atributo não pode se chamar 'self' (classe '{cls.name}')", feature.line)
                    if feature.name in attributes:
                        first = attributes[feature.name]
                        raise SemanticError(f"Atributo '{feature.name}' já foi declarado na classe '{cls.name}', na linha {first.line}", feature.line)
                    attributes[feature.name] = feature

            self.attributes[cls.name] = attributes
            self.methods[cls.name] = methods

    # Tipo declarável em atributo ou retorno: classe registrada ou SELF_TYPE
    def is_valid_type(self, type_name):
        return type_name == "SELF_TYPE" or type_name in self.classes

    # Valida os tipos citados nas features das classes do programa
    def check_feature_types(self):
        for cls in self.program.classes:
            for feature in cls.features:
                if isinstance(feature, ast.Method):
                    self.check_method_types(cls, feature)
                elif not self.is_valid_type(feature.type_name):
                    raise SemanticError(f"Atributo '{feature.name}' da classe '{cls.name}' tem tipo inexistente '{feature.type_name}'", feature.line)

    # Valida os parâmetros formais e o tipo de retorno de um método
    def check_method_types(self, cls, method):
        names = set()

        for formal in method.formals:
            if formal.name == "self":
                raise SemanticError(f"Parâmetro não pode se chamar 'self' (método '{method.name}')", formal.line)
            if formal.name in names:
                raise SemanticError(f"Parâmetro '{formal.name}' declarado mais de uma vez no método '{method.name}'", formal.line)
            names.add(formal.name)

            if formal.type_name == "SELF_TYPE":
                raise SemanticError(f"Parâmetro '{formal.name}' do método '{method.name}' não pode ter tipo 'SELF_TYPE'", formal.line)
            if formal.type_name not in self.classes:
                raise SemanticError(f"Parâmetro '{formal.name}' do método '{method.name}' tem tipo inexistente '{formal.type_name}'", formal.line)

        if not self.is_valid_type(method.return_type):
            raise SemanticError(f"Método '{method.name}' da classe '{cls.name}' tem tipo de retorno inexistente '{method.return_type}'", method.line)

    # Busca a feature mais próxima com esse nome nos ancestrais da classe, sem incluir a própria
    def find_inherited(self, table, cls, name):
        current = cls.parent

        while current is not None:
            if name in table[current]:
                return current, table[current][name]
            current = self.classes[current].parent

        return None

    # Valida as regras de herança de features
    def check_inheritance(self):
        for cls in self.program.classes:
            for feature in cls.features:
                if isinstance(feature, ast.Method):
                    self.check_override(cls, feature)
                    continue

                inherited = self.find_inherited(self.attributes, cls, feature.name)
                if inherited is not None:
                    ancestor, _ = inherited
                    raise SemanticError(f"Atributo '{feature.name}' da classe '{cls.name}' redefine atributo herdado de '{ancestor}'", feature.line)

    # Compara a assinatura de um método com a do método herdado que ele redefine
    def check_override(self, cls, method):
        inherited = self.find_inherited(self.methods, cls, method.name)

        if inherited is None:
            return
        ancestor, original = inherited

        if len(method.formals) != len(original.formals):
            raise SemanticError(f"Método '{method.name}' redefinido em '{cls.name}' com {len(method.formals)} parâmetro(s), mas declarado em '{ancestor}' com {len(original.formals)}", method.line)

        for formal, original_formal in zip(method.formals, original.formals):
            if formal.type_name != original_formal.type_name:
                raise SemanticError(f"Parâmetro '{formal.name}' do método '{method.name}' tem tipo '{formal.type_name}' em '{cls.name}', mas '{original_formal.type_name}' em '{ancestor}'", formal.line)

        if method.return_type != original.return_type:
            raise SemanticError(
                f"Método '{method.name}' redefinido em '{cls.name}' com retorno '{method.return_type}', mas declarado em '{ancestor}' com retorno '{original.return_type}'", method.line)
