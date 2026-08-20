import sys

from coolc.lexer import Lexer

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

    for token in lexer.tokenize():
        print(format_token(token))
        print()

if __name__ == "__main__":
    main()