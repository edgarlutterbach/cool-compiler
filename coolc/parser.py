from coolc.tokens import TokenType
from coolc.ast import Program, Class, Method, Attribute, Formal

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

    # feature ::= OBJECTID ( [ formal [[ , formal ]]* ] ) : TYPEID { expr }
    #           | OBJECTID : TYPEID [ <- expr ]
    def parse_feature(self):

        # Espera o nome, o que é comum as duas alternativas: método ou atributo
        name_token = self.expect(TokenType.OBJECTID)

        # Se observamos '(', é um método, mandamos para o parse_method
        if self.check(TokenType.LPAREN):
            return self.parse_method(name_token)

        # Caso contrário, é um atributo, mandamos para o parse_attribute
        return self.parse_attribute(name_token)

    # Função para a alternativa de método
    def parse_method(self, name_token):

        # Consome o '(' abrindo o campo de parâmetros do método
        self.expect(TokenType.LPAREN)

        # Lista de parâmetros
        formals = []

        # Se não fechar imediatamente (o que é permitido), adicionamos os parâmetros a lista
        if not self.check(TokenType.RPAREN):
            formals.append(self.parse_formal())

            # Verifica as vírgulas separando os parâmetros e avança
            while self.check(TokenType.COMMA):
                self.advance()

                # Adiciona os parâmetros a lista
                formals.append(self.parse_formal())

        # Espera ')' e avança
        self.expect(TokenType.RPAREN)

        # Espera ':' e avança
        self.expect(TokenType.COLON)

        # Lê e guarda o tipo de retorno, avançando o token
        return_type = self.expect(TokenType.TYPEID).valor

        # Espera o '{' e avança
        self.expect(TokenType.LBRACE)

        # Armazena o corpo do método
        body = self.parse_expr()

        # Espera o '}' e avança
        self.expect(TokenType.RBRACE)

        # Retorna o nó do método
        return Method(name_token.valor, formals, return_type, body, name_token.linha)

    # Função para a alternativa de atributo
    def parse_attribute(self, name_token):

        # Consome o ':' indicando que é um atributo
        self.expect(TokenType.COLON)

        # Armazena o tipo declarado do atributo
        type_name = self.expect(TokenType.TYPEID).valor

        # Inicializa o atributo como None
        init = None

        # Se tiver uma atribuição, avança
        if self.check(TokenType.ASSIGN):
            self.advance()

            # Armazena a expressão como valor do atributo
            init = self.parse_expr()

        # Retorna o nó do atributo montado
        return Attribute(name_token.valor, type_name, init, name_token.linha)

    # formal ::= OBJECTID : TYPEID
    def parse_formal(self):

        # Espera o nome do parâmetro
        name_token = self.expect(TokenType.OBJECTID)

        # Espera ':'
        self.expect(TokenType.COLON)

        # Espera o tipo do parâmetro
        type_name = self.expect(TokenType.TYPEID).valor

        # Retorna o nó do parâmetro
        return Formal(name_token.valor, type_name, name_token.linha)