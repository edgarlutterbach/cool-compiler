from coolc.tokens import TokenType, describe
import coolc.ast as ast

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
    def peek(self, offset=0):
        target = self.pos + offset

        if target >= len(self.tokens):
            return self.tokens[-1]

        return self.tokens[target]

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
            raise ParseError(f"Esperado {describe(token_type)}, encontrado {describe(token_type)}", found.linha)
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
        return ast.Program(classes)

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
        while not self.check(TokenType.RBRACE) and not self.check(TokenType.EOF):

            # parse_feature decide se está diante de um método ou atributo
            features.append(self.parse_feature())

            # ';' é obrigatório após cada feature
            self.expect(TokenType.SEMI)

        # Fechamento do corpo
        self.expect(TokenType.RBRACE)

        # Retorna o nó com tudo que foi coletado
        return ast.Class(name, parent, features, keyword.linha)

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
        return ast.Method(name_token.valor, formals, return_type, body, name_token.linha)

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
        return ast.Attribute(name_token.valor, type_name, init, name_token.linha)

    # formal ::= OBJECTID : TYPEID
    def parse_formal(self):

        # Espera o nome do parâmetro
        name_token = self.expect(TokenType.OBJECTID)

        # Espera ':'
        self.expect(TokenType.COLON)

        # Espera o tipo do parâmetro
        type_name = self.expect(TokenType.TYPEID).valor

        # Retorna o nó do parâmetro
        return ast.Formal(name_token.valor, type_name, name_token.linha)

    # expr ::= ID <- expr
    #        | ...
    def parse_expr(self):
        if self.check(TokenType.OBJECTID) and self.peek(1).tipo == TokenType.ASSIGN:
            name_token = self.advance()

            # Descarta o '<-'
            self.advance()

            # Recursão na própria regra: a atribuição associa à direita
            value = self.parse_expr()

            return ast.Assign(name_token.valor, value, name_token.linha)

        return self.parse_not()

    # As folhas da árvore de expressões e as construções com palavra-chave
    # ( expr ) | OBJECTID | INT_CONST | STR_CONST | true | false
    # | if | while | { } | new | let | case
    def parse_atom(self):
        token = self.peek()

        # Construções com palavra-chave inicial
        # O primeiro token identifica a regra sem ambiguidade
        if self.check(TokenType.IF):
            return self.parse_if()

        if self.check(TokenType.WHILE):
            return self.parse_while()

        if self.check(TokenType.LBRACE):
            return self.parse_block()

        if self.check(TokenType.LET):
            return self.parse_let()

        if self.check(TokenType.CASE):
            return self.parse_case()

        if self.check(TokenType.NEW):
            self.advance()
            return ast.New(self.expect(TokenType.TYPEID).valor, token.linha)

        #Literais
        if self.check(TokenType.INT_CONST):
            self.advance()
            return ast.IntLiteral(token.valor, token.linha)

        if self.check(TokenType.STR_CONST):
            self.advance()
            return ast.StringLiteral(token.valor, token.linha)

        if self.check(TokenType.BOOL_CONST):
            self.advance()
            return ast.BoolLiteral(token.valor, token.linha)

        # Identificador e chamada abreviada
        if self.check(TokenType.OBJECTID):
            self.advance()

            # 'f(...)' é chamada abreviada, açúcar para 'self.f(...)'.
            # Registramos já desaçucarado (parser.md, 6.3)
            if self.check(TokenType.LPAREN):
                args = self.parse_args()
                return ast.Dispatch(ast.Identifier("self", token.linha), None,
                                token.valor, args, token.linha)

            return ast.Identifier(token.valor, token.linha)

        # Expressão entre parênteses
        if self.check(TokenType.LPAREN):
            self.advance()

            # Volta ao topo da cadeia: qualquer expressão é válida dentro
            # dos parênteses, inclusive as de menor precedência
            node = self.parse_expr()
            self.expect(TokenType.RPAREN)

            return node

        raise ParseError(f"Expressão inesperada: {token.tipo.name}", token.linha)

    # term ::= isvoid_expr [[ (* | /) isvoid_expr ]]*
    def parse_term(self):

        # Consome o operando da esquerda
        node = self.parse_isvoid()

        # Enquanto tiver operadores
        while self.check(TokenType.TIMES) or self.check(TokenType.DIVIDE):
            operator = self.advance()

            # Consome o operando da direita
            right = self.parse_isvoid()

            # O nó acumulado vira o filho esquerdo do novo nó
            node = ast.BinOperation(operator.tipo, node, right, operator.linha)

        return node

    # arith ::= term [[ ( + | - ) term ]]*
    def parse_arith(self):

        # Consome o termo da esquerda
        node = self.parse_term()

        # Enquanto tiver operadores
        while self.check(TokenType.PLUS) or self.check(TokenType.MINUS):
            operator = self.advance()

            #Consome o termo da direita
            right = self.parse_term()

            node = ast.BinOperation(operator.tipo, node, right, operator.linha)

        return node

    # comparison ::= arith [ ( < | <= | = ) arith ]
    def parse_comparison(self):

        # Consome o operando da esquerda
        node = self.parse_arith()

        # Nesse caso, não temos associam em comparações, portanto, usamos apenas 'if'
        if self.check(TokenType.LT) or self.check(TokenType.LE) or self.check(TokenType.EQ):
            operator = self.advance()

            # Consome o operando da direita
            right = self.parse_arith()

            node = ast.BinOperation(operator.tipo, node, right, operator.linha)

        return node

    # not_expr ::= not not_expr | comparison
    def parse_not(self):

        # Se 'not' está presente, ele vem antes do operando
        if self.check(TokenType.NOT):
            operator = self.advance()

            # Não há laço porque o advance já consumiu um token antes da chamada
            operand = self.parse_not()

            return ast.UnaryOperation(operator.tipo, operand, operator.linha)

        # Sem 'not', desce para o maior nível de precedência
        return self.parse_comparison()

    # isvoid_expr ::= isvoid isvoid_expr | neg_expr
    def parse_isvoid(self):
        if self.check(TokenType.ISVOID):
            operator = self.advance()

            # Recursão na própria regra, permitindo 'isvoid isvoid x'
            operand = self.parse_isvoid()

            return ast.UnaryOperation(operator.tipo, operand, operator.linha)

        return self.parse_neg()

    # neg_expr ::= ~ neg_expr | dispatch
    def parse_neg(self):
        if self.check(TokenType.NEG):
            operator = self.advance()

            # Recursão dentro da própria regra, permitindo '~~x'
            operand = self.parse_neg()

            return ast.UnaryOperation(operator.tipo, operand, operator.linha)

        return self.parse_dispatch()

    # dispatch ::= atom [[ [@TYPEID] . OBJECTID ( [ args ] ) ]]*
    def parse_dispatch(self):

        # Consome o receptor
        node = self.parse_atom()

        # Laço porque o despacho encadeia: 'a.f().g()'
        while self.check(TokenType.DOT) or self.check(TokenType.AT):

            # Despacho estático: '@TYPEID' antes do ponto
            static_type = None
            if self.check(TokenType.AT):
                self.advance()
                static_type = self.expect(TokenType.TYPEID).valor

            # O ponto é obrigatório nas duas formas
            dot = self.expect(TokenType.DOT)

            name_token = self.expect(TokenType.OBJECTID)
            args = self.parse_args()

            node = ast.Dispatch(node, static_type, name_token.valor, args, dot.linha)

        return node

    # Lista de argumentos entre parênteses, possivelmente vazia
    def parse_args(self):
        self.expect(TokenType.LPAREN)

        args = []

        # Se não fecha imediatamente, há pelo menos um argumento
        if not self.check(TokenType.RPAREN):
            args.append(self.parse_expr())

            # A vírgula separa argumentos
            while self.check(TokenType.COMMA):
                self.advance()
                args.append(self.parse_expr())

        self.expect(TokenType.RPAREN)
        return args

    # if_expr ::= if expr then expr else expr fi
    def parse_if(self):
        keyword = self.expect(TokenType.IF)

        condition = self.parse_expr()
        self.expect(TokenType.THEN)

        then_branch = self.parse_expr()
        self.expect(TokenType.ELSE)

        # O ramo 'else' é obrigatório em COOL, diferente de outras linguagens
        else_branch = self.parse_expr()
        self.expect(TokenType.FI)

        return ast.If(condition, then_branch, else_branch, keyword.linha)

    # while_expr ::= while expr loop expr pool
    def parse_while(self):
        keyword = self.expect(TokenType.WHILE)

        condition = self.parse_expr()
        self.expect(TokenType.LOOP)

        body = self.parse_expr()
        self.expect(TokenType.POOL)

        return ast.While(condition, body, keyword.linha)

    # block ::= { [[ expr ; ]]+ }
    def parse_block(self):
        keyword = self.expect(TokenType.LBRACE)

        expressions = []

        # O ';' é terminador, não separador
        while not self.check(TokenType.RBRACE) and not self.check(TokenType.EOF):
            expressions.append(self.parse_expr())
            self.expect(TokenType.SEMI)

        self.expect(TokenType.RBRACE)

        # '+': ao menos uma expressão é exigida
        if not expressions:
            raise ParseError("Bloco vazio: ao menos uma expressão é exigida", keyword.linha)

        return ast.Block(expressions, keyword.linha)

    # let_expr ::= let ID : TYPE [ <- expr ] [[ , ... ]]* in expr
    def parse_let(self):
        keyword = self.expect(TokenType.LET)

        bindings = []

        # Exige ao menos uma declaração, então lê uma antes do laço
        bindings.append(self.parse_let_binding())

        # A vírgula separa declarações adicionais
        while self.check(TokenType.COMMA):
            self.advance()
            bindings.append(self.parse_let_binding())

        self.expect(TokenType.IN)

        # Chama a regra mais externa da cadeia
        body = self.parse_expr()

        return ast.Let(bindings, body, keyword.linha)

    # Uma declaração isolada dentro do let
    def parse_let_binding(self):
        name_token = self.expect(TokenType.OBJECTID)
        self.expect(TokenType.COLON)
        type_name = self.expect(TokenType.TYPEID).valor

        # A inicialização é opcional
        init = None
        if self.check(TokenType.ASSIGN):
            self.advance()
            init = self.parse_expr()

        return ast.LetBinding(name_token.valor, type_name, init, name_token.linha)

    # case_expr ::= case expr of [[ ID : TYPE => expr ; ]]+ esac
    def parse_case(self):
        keyword = self.expect(TokenType.CASE)

        expression = self.parse_expr()
        self.expect(TokenType.OF)

        branches = []

        # Roda até o 'esac', com guarda de EOF contra laço infinito
        while not self.check(TokenType.ESAC) and not self.check(TokenType.EOF):
            branches.append(self.parse_case_branch())

        self.expect(TokenType.ESAC)

        # Usa '+': ao menos um ramo é exigido
        if not branches:
            raise ParseError("Case sem ramos: ao menos um é exigido",
                             keyword.linha)

        return ast.Case(expression, branches, keyword.linha)

    # Um ramo isolado do case
    def parse_case_branch(self):
        name_token = self.expect(TokenType.OBJECTID)
        self.expect(TokenType.COLON)
        type_name = self.expect(TokenType.TYPEID).valor

        self.expect(TokenType.DARROW)
        body = self.parse_expr()

        # O ';' encerra cada ramo, inclusive o último
        self.expect(TokenType.SEMI)

        return ast.CaseBranch(name_token.valor, type_name, body, name_token.linha)