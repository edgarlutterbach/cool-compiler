from coolc.tokens import TokenType

class ParseError(Exception):
    # Erro de sintaxe
    def __init__(self, message, line):
        # Carrega mensagem e linha para relatório
        super().__init__(message)
        self.message = message
        self.line = line

class Parser:
    # Construtor do Parser
    def __init__(self, tokens):
        # Recebe a lista produzida pelo Lexer.tokenize()
        self.tokens = tokens
        # Índice do token atual
        self.pos = 0

    # Função primitiva para retornar o token atual, sem consumir.
    def peek(self):
        return self.tokens[self.pos]

    # Função primitiva para retornar o token atual, consumindo e avançando a posição
    def advance(self):
        token = self.tokens[self.pos]
        # Só avança se o próximo não for EOF
        if token.tipo != TokenType.EOF:
            self.pos += 1
        return token

    # Função primitiva para verificar se o token atual é do tipo informado
    # Retorna um booleano e não consome o token
    def check(self, token_type):
        return self.peek().tipo == token_type

    # Função primitiva para verificar se o token atual é do tipo informado
    # Caso true, avança, caso contrário, retorna erro
    def expect(self, token_type):
        if not self.check(token_type):
            found = self.peek()
            raise ParseError(f"Esperado {token_type.name}, encontrado {found.tipo.name}", found.linha)
        return self.advance()