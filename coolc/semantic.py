import coolc.ast as ast
from coolc.tokens import TokenType, describe

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

# Operadores binários agrupados pela regra de tipo
ARITHMETIC_OPERATORS = {TokenType.PLUS, TokenType.MINUS, TokenType.TIMES, TokenType.DIVIDE}
COMPARISON_OPERATORS = {TokenType.LT, TokenType.LE}

# Tipos que só podem ser comparados com '=' a um valor do mesmo tipo
BASIC_VALUE_TYPES = {"Int", "String", "Bool"}

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

# Tabela de símbolos com escopos aninhados
class SymbolTable:
    def __init__(self):
        self.scopes = []

    def enter_scope(self):
        self.scopes.append({})

    def exit_scope(self):
        self.scopes.pop()

    def add(self, name, type_name):
        self.scopes[-1][name] = type_name

    def lookup(self, name):
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        return None

# Classe do analisador semântico
class SemanticAnalyzer:
    def __init__(self, program):
        self.program = program
        self.classes = {}
        self.attributes = {}
        self.methods = {}
        self.current_class = None
        self.symbols = None

    # Ponto de entrada
    def analyze(self):
        self.register_classes()
        self.check_parents()
        self.check_cycles()
        self.check_main()
        self.collect_features()
        self.check_feature_types()
        self.check_inheritance()
        self.check_main_method()
        self.check_expressions()
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

    # Exige que Main declare main() sem parâmetros
    def check_main_method(self):
        main_class = self.classes["Main"]
        main_method = self.methods["Main"].get("main")

        if main_method is None:
            inherited = self.find_inherited(self.methods, main_class, "main")
            if inherited is not None:
                ancestor, _ = inherited
                raise SemanticError(f"Classe 'Main' não herda 'main' de '{ancestor}', mas precisa declará-lo", main_class.line)
            raise SemanticError("Classe 'Main' não declara o método 'main'", main_class.line)

        if main_method.formals:
            raise SemanticError(f"Método 'main' da classe 'Main' não pode ter parâmetros (declarado com {len(main_method.formals)})", main_method.line)

    # Conformidade A <= B: um valor do tipo A pode ser usado onde se espera B
    def conforms(self, a, b):
        if b == "SELF_TYPE":
            return a == "SELF_TYPE"

        if a == "SELF_TYPE":
            a = self.current_class.name

        current = a

        while current is not None:
            if current == b:
                return True
            current = self.classes[current].parent

        return False

    # Join A U B: o menor tipo do qual A e B são subtipos
    def join(self, a, b):
        if a == b:
            return a

        if a == "SELF_TYPE":
            a = self.current_class.name
        if b == "SELF_TYPE":
            b = self.current_class.name

        ancestors = set()
        current = a
        while current is not None:
            ancestors.add(current)
            current = self.classes[current].parent

        current = b
        while current not in ancestors:
            current = self.classes[current].parent

        return current

    # Busca um método no próprio tipo e, se não houver, nos ancestrais
    # Devolve o nó da definição mais próxima ou None
    def lookup_method(self, type_name, name):
        if name in self.methods[type_name]:
            return self.methods[type_name][name]

        inherited = self.find_inherited(self.methods, self.classes[type_name], name)
        if inherited is None:
            return None
        _, method = inherited
        return method

    # Percorre as features de cada classe do programa com os escopos corretos
    def check_expressions(self):
        for cls in self.program.classes:
            self.current_class = cls
            self.symbols = SymbolTable()
            self.symbols.enter_scope()
            self.symbols.add("self", "SELF_TYPE")
            current = cls.name
            while current is not None:
                for attribute in self.attributes[current].values():
                    self.symbols.add(attribute.name, attribute.type_name)
                current = self.classes[current].parent

            for feature in cls.features:
                if isinstance(feature, ast.Method):
                    self.symbols.enter_scope()
                    for formal in feature.formals:
                        self.symbols.add(formal.name, formal.type_name)
                    body_type = self.visit(feature.body)
                    self.symbols.exit_scope()

                    if body_type is not None and not self.conforms(body_type, feature.return_type):
                        raise SemanticError(f"Método '{feature.name}': tipo do corpo '{body_type}' não conforma com o retorno declarado '{feature.return_type}'", feature.line)

                elif feature.init is not None:
                    init_type = self.visit(feature.init)
                    if init_type is not None and not self.conforms(init_type, feature.type_name):
                        raise SemanticError(f"Atributo '{feature.name}': tipo do inicializador '{init_type}' não conforma com o tipo declarado '{feature.type_name}'", feature.line)

            self.symbols.exit_scope()

    # Padrão visitor: chama visit_<NomeDoNó> e anota o tipo devolvido no nó
    def visit(self, node):
        rule = getattr(self, f"visit_{type(node).__name__}", self.visit_default)
        node.expr_type = rule(node)
        return node.expr_type

    # Temporário: nós ainda sem regra de tipo não são verificados
    def visit_default(self, node):
        return None

    # Constantes: o tipo é a classe básica correspondente
    def visit_IntLiteral(self, node):
        return "Int"

    def visit_StringLiteral(self, node):
        return "String"

    def visit_BoolLiteral(self, node):
        return "Bool"

    # Identificador: o tipo declarado no escopo visível mais interno
    def visit_Identifier(self, node):
        type_name = self.symbols.lookup(node.name)
        if type_name is None:
            raise SemanticError(f"Identificador '{node.name}' não foi declarado", node.line)
        return type_name

    # Exige que uma expressão já visitada tenha exatamente o tipo esperado
    def require_type(self, node, expected, description):
        actual = node.expr_type
        if actual is None:
            return
        if actual != expected:
            raise SemanticError(f"{description} deve ser tipo '{expected}', mas tem tipo '{actual}'", node.line)

    # Operação binária: aritmética, comparação ou igualdade
    def visit_BinOperation(self, node):
        left_type = self.visit(node.left)
        right_type = self.visit(node.right)
        symbol = describe(node.operator)

        if node.operator in ARITHMETIC_OPERATORS or node.operator in COMPARISON_OPERATORS:
            self.require_type(node.left, "Int", f"Operando esquerdo de {symbol}")
            self.require_type(node.right, "Int", f"Operando direito de {symbol}")
            return "Int" if node.operator in ARITHMETIC_OPERATORS else "Bool"

        if left_type is not None and right_type is not None:
            if (left_type in BASIC_VALUE_TYPES or right_type in BASIC_VALUE_TYPES) and left_type != right_type:
                raise SemanticError(f"Comparação {symbol} entre tipos incompatíveis '{left_type}' e '{right_type}'", node.line)

        return "Bool"

    # Operação unária: ~, not ou isvoid
    def visit_UnaryOperation(self, node):
        self.visit(node.operand)
        symbol = describe(node.operator)

        if node.operator == TokenType.NEG:
            self.require_type(node.operand, "Int", f"Operando de {symbol}")
            return "Int"

        if node.operator == TokenType.NOT:
            self.require_type(node.operand, "Bool", f"Operando de {symbol}")
            return "Bool"

        return "Bool"

    # Instanciação: new T tem tipo T, e T precisa existir
    def visit_New(self, node):
        if not self.is_valid_type(node.type_name):
            raise SemanticError(f"Tipo inexistente '{node.type_name}' em 'new'", node.line)
        return node.type_name

    # Bloco: avalia em ordem e tem o tipo da última expressão
    def visit_Block(self, node):
        block_type = None
        for expression in node.expressions:
            block_type = self.visit(expression)
        return block_type

    # Atribuição: o valor precisa conformar com o tipo declarado
    def visit_Assign(self, node):
        if node.name == "self":
            raise SemanticError("Não é possível atribuir a 'self'", node.line)

        declared_type = self.symbols.lookup(node.name)
        if declared_type is None:
            raise SemanticError(f"Identificador '{node.name}' não foi declarado", node.line)

        value_type = self.visit(node.value)
        if value_type is not None and not self.conforms(value_type, declared_type):
            raise SemanticError(f"Atribuição a '{node.name}': tipo '{value_type}' não conforma com o tipo declarado '{declared_type}'", node.line)

        return value_type

    # Condicional: predicado Bool; tipo é o join dos dois ramos
    def visit_If(self, node):
        self.visit(node.condition)
        self.require_type(node.condition, "Bool", "Predicado do 'if'")

        then_type = self.visit(node.then_branch)
        else_type = self.visit(node.else_branch)

        if then_type is None or else_type is None:
            return None
        return self.join(then_type, else_type)

    # Laço: predicado Bool; o tipo do while é sempre Object
    def visit_While(self, node):
        self.visit(node.condition)
        self.require_type(node.condition, "Bool", "Predicado do 'while'")
        self.visit(node.body)
        return "Object"