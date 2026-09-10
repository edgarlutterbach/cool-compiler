from coolc.tokens import TokenType
from coolc.ast import Program, Class

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

    # program ::= [[ class ; ]]+
    def parse_program(self):
        classes = []

        # Consome classes até esgotar os tokens.
        while not self.check(TokenType.EOF):

            # parse_class consome todos os tokens de uma classe e devolve o nó já montado
            classes.append(self.parse_class())
            # Espera um ';' após cada classe
            self.expect(TokenType.SEMI)

        # A gramática diz que ao menos uma classe é exigida
        if not classes:
            raise ParseError("Programa vazio: ao menos uma classe é exigida", self.peek().linha)

        # Devolve a raiz da AST
        return Program(classes)

    # class ::= class TYPEID [ inherits TYPEID ] { [[ feature ; ]] }
    def parse_class(self):

        # Palavra 'Class' é obrigatória e, se o token não for esse, a regra inteira
        # não se aplica e é erro de sintaxe
        keyword = self.expect(TokenType.CLASS)

        # Nome da classe
        name = self.expect(TokenType.TYPEID).valor

        # Como 'inherits' é opcional, parent é inicializado como None
        parent = None

        if self.check(TokenType.INHERITS):

            # Avança o 'inherits'
            self.advance()

            # Armazena o próximo Token (que seria de quem herda) em parent
            parent = self.expect(TokenType.TYPEID).valor

        # Abertura do corpo da classe
        self.expect(TokenType.LBRACE)

        # Acumulador de features
        features = []

        # O laço roda até encontrar '}' e o teste do EOF protege de laço infinito
        while not self.check(TokenType.RBRACE and not self.check(TokenType.EOF)):

            # parse_feature decide se está diante de um método ou atributo
            features.append(self.parse_feature())

            # ';' é obrigatório após cada feature
            self.expect(TokenType.SEMI)

        # Fechamento do corpo
        self.expect(TokenType.RBRACE)

        # Retorna o nó com tudo que foi coletado
        return Class(name, parent, features, keyword.linha)