import sys

from coolc.lexer import Lexer
from coolc.parser import Parser, ParseError
from coolc.tokens import TokenType
from coolc.astprinter import print_tree

def format_token(token):
    lines = [f"{token.tipo.name}"]
    if token.valor is not None:
        lines.append(f"     Valor: {token.valor!r}")
    lines.append(f"     Linha: {token.linha}")
    return "\n".join(lines)

def main():
    if len(sys.argv) < 2:
        print("Uso: python -m coolc.main <arquivo.cl>")
        sys.exit(1)

    path = sys.argv[1]

    try:
        with open(path, encoding="utf-8") as source_file:
            source = source_file.read()
    except OSError as error:
        print(f"Erro ao abrir o arquivo: {error}")
        sys.exit(1)

    lexer = Lexer(source)
    tokens = lexer.tokenize()

    errors = [t for t in tokens if t.tipo == TokenType.ERROR]
    if errors:
        for token in errors:
            print(f"Erro léxico na linha {token.linha}: {token.valor}")
        sys.exit(1)

    try:
        tree = Parser(tokens).parse_program()
    except ParseError as error:
        print(f"Erro de sintaxe na linha {error.line}: {error.message}")
        sys.exit(1)

    print_tree(tree)

if __name__ == "__main__":
    main()