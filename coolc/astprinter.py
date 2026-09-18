from coolc import ast
from coolc.tokens import describe

# Imprime a árvore sintática de forma indentada e legível.
def print_tree(node, level=0):
    indent = "  " * level

    # Raiz
    if isinstance(node, ast.Program):
        print(f"{indent}Program")
        for cls in node.classes:
            print_tree(cls, level + 1)
        return

    # Estrutura
    if isinstance(node, ast.Class):
        inherits = f" inherits {node.parent}" if node.parent else ""
        print(f"{indent}Class {node.name}{inherits}  (linha {node.line})")
        for feature in node.features:
            print_tree(feature, level + 1)
        return

    if isinstance(node, ast.Method):
        params = ", ".join(f"{f.name}: {f.type_name}" for f in node.formals)
        print(f"{indent}Method {node.name}({params}): {node.return_type}"
              f"  (linha {node.line})")
        print_tree(node.body, level + 1)
        return

    if isinstance(node, ast.Attribute):
        print(f"{indent}Attribute {node.name}: {node.type_name}"
              f"  (linha {node.line})")
        # A inicialização é opcional
        if node.init is not None:
            print_tree(node.init, level + 1)
        return

    # Operadores

    if isinstance(node, ast.BinOperation):
        print(f"{indent}BinOp {describe(node.operator)}")
        print_tree(node.left, level + 1)
        print_tree(node.right, level + 1)
        return

    if isinstance(node, ast.UnaryOperation):
        print(f"{indent}UnaryOp {describe(node.operator)}")
        print_tree(node.operand, level + 1)
        return

    if isinstance(node, ast.Assign):
        print(f"{indent}Assign {node.name}  (linha {node.line})")
        print_tree(node.value, level + 1)
        return

    # Controle

    if isinstance(node, ast.If):
        print(f"{indent}If  (linha {node.line})")
        print(f"{indent}  cond:")
        print_tree(node.condition, level + 2)
        print(f"{indent}  then:")
        print_tree(node.then_branch, level + 2)
        print(f"{indent}  else:")
        print_tree(node.else_branch, level + 2)
        return

    if isinstance(node, ast.While):
        print(f"{indent}While  (linha {node.line})")
        print(f"{indent}  cond:")
        print_tree(node.condition, level + 2)
        print(f"{indent}  body:")
        print_tree(node.body, level + 2)
        return

    if isinstance(node, ast.Block):
        print(f"{indent}Block  (linha {node.line})")
        for expression in node.expressions:
            print_tree(expression, level + 1)
        return

    if isinstance(node, ast.Let):
        print(f"{indent}Let  (linha {node.line})")
        for binding in node.bindings:
            print_tree(binding, level + 1)
        print(f"{indent}  in:")
        print_tree(node.body, level + 2)
        return

    if isinstance(node, ast.LetBinding):
        print(f"{indent}Binding {node.name}: {node.type_name}")
        if node.init is not None:
            print_tree(node.init, level + 1)
        return

    if isinstance(node, ast.Case):
        print(f"{indent}Case  (linha {node.line})")
        print_tree(node.expression, level + 1)
        for branch in node.branches:
            print_tree(branch, level + 1)
        return

    if isinstance(node, ast.CaseBranch):
        print(f"{indent}Branch {node.name}: {node.type_name}")
        print_tree(node.body, level + 1)
        return

    # Despacho e instanciação

    if isinstance(node, ast.Dispatch):
        static = f"@{node.static_type}" if node.static_type else ""
        print(f"{indent}Dispatch {static}.{node.name}  (linha {node.line})")
        print(f"{indent}  receiver:")
        print_tree(node.receiver, level + 2)
        if node.args:
            print(f"{indent}  args:")
            for arg in node.args:
                print_tree(arg, level + 2)
        return

    if isinstance(node, ast.New):
        print(f"{indent}New {node.type_name}  (linha {node.line})")
        return

    # Folhas

    if isinstance(node, ast.IntLiteral):
        print(f"{indent}Int {node.value}")
        return

    if isinstance(node, ast.StringLiteral):
        # repr para revelar escapes e delimitar a string
        print(f"{indent}String {node.value!r}")
        return

    if isinstance(node, ast.BoolLiteral):
        print(f"{indent}Bool {node.value}")
        return

    if isinstance(node, ast.Identifier):
        print(f"{indent}Identifier {node.name}")
        return

    print(f"{indent}<nó desconhecido: {type(node).__name__}>")