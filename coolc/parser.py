from coolc.tokens import TokenType, describe
import coolc.ast as ast

class ParseError(Exception):
    def __init__(self, message, line):
        super().__init__(message)
        self.message = message
        self.line = line

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def peek(self, offset=0):
        target = self.pos + offset

        if target >= len(self.tokens):
            return self.tokens[-1]

        return self.tokens[target]

    def advance(self):
        token = self.tokens[self.pos]

        if token.tipo != TokenType.EOF:
            self.pos += 1

        return token

    def check(self, token_type):
        return self.peek().tipo == token_type

    def expect(self, token_type):
        if not self.check(token_type):
            found = self.peek()
            raise ParseError(f"Esperado {describe(token_type)}, encontrado {describe(found.tipo)}", found.linha)

        return self.advance()

    # program ::= [[ class ; ]]+
    def parse_program(self):
        classes = []

        while not self.check(TokenType.EOF):
            classes.append(self.parse_class())
            self.expect(TokenType.SEMI)

        if not classes:
            raise ParseError("Programa vazio: ao menos uma classe é exigida", self.peek().linha)

        return ast.Program(classes)

    # class ::= class TYPEID [ inherits TYPEID ] { [[ feature ; ]] }
    def parse_class(self):
        keyword = self.expect(TokenType.CLASS)
        name = self.expect(TokenType.TYPEID).valor
        parent = None

        if self.check(TokenType.INHERITS):
            self.advance()
            parent = self.expect(TokenType.TYPEID).valor

        self.expect(TokenType.LBRACE)
        features = []

        while not self.check(TokenType.RBRACE) and not self.check(TokenType.EOF):
            features.append(self.parse_feature())
            self.expect(TokenType.SEMI)

        self.expect(TokenType.RBRACE)
        return ast.Class(name, parent, features, keyword.linha)

    # feature ::= OBJECTID ( [ formal [[ , formal ]]* ] ) : TYPEID { expr }
    #           | OBJECTID : TYPEID [ <- expr ]
    def parse_feature(self):
        name_token = self.expect(TokenType.OBJECTID)

        if self.check(TokenType.LPAREN):
            return self.parse_method(name_token)

        return self.parse_attribute(name_token)

    # feature ::= OBJECTID ( [ formal [[ , formal ]]* ] ) : TYPEID { expr }
    def parse_method(self, name_token):
        self.expect(TokenType.LPAREN)
        formals = []

        if not self.check(TokenType.RPAREN):
            formals.append(self.parse_formal())

            while self.check(TokenType.COMMA):
                self.advance()
                formals.append(self.parse_formal())

        self.expect(TokenType.RPAREN)
        self.expect(TokenType.COLON)
        return_type = self.expect(TokenType.TYPEID).valor
        self.expect(TokenType.LBRACE)
        body = self.parse_expr()
        self.expect(TokenType.RBRACE)
        return ast.Method(name_token.valor, formals, return_type, body, name_token.linha)

    # feature ::= OBJECTID : TYPEID [ <- expr ]
    def parse_attribute(self, name_token):
        self.expect(TokenType.COLON)
        type_name = self.expect(TokenType.TYPEID).valor
        init = None

        if self.check(TokenType.ASSIGN):
            self.advance()
            init = self.parse_expr()

        return ast.Attribute(name_token.valor, type_name, init, name_token.linha)

    # formal ::= OBJECTID : TYPEID
    def parse_formal(self):
        name_token = self.expect(TokenType.OBJECTID)
        self.expect(TokenType.COLON)
        type_name = self.expect(TokenType.TYPEID).valor
        return ast.Formal(name_token.valor, type_name, name_token.linha)

    # expr ::= ID <- expr
    #        | ...
    def parse_expr(self):
        if self.check(TokenType.OBJECTID) and self.peek(1).tipo == TokenType.ASSIGN:
            name_token = self.advance()
            self.advance()
            value = self.parse_expr()
            return ast.Assign(name_token.valor, value, name_token.linha)

        return self.parse_not()

    # As folhas da árvore de expressões e as construções com palavra-chave
    # ( expr ) | OBJECTID | INT_CONST | STR_CONST | true | false
    # | if | while | { } | new | let | case
    def parse_atom(self):
        token = self.peek()

        # Construções com palavra-chave inicial
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
            if self.check(TokenType.LPAREN):
                args = self.parse_args()
                return ast.Dispatch(ast.Identifier("self", token.linha), None, token.valor, args, token.linha)

            return ast.Identifier(token.valor, token.linha)

        # Expressão entre parênteses
        if self.check(TokenType.LPAREN):
            self.advance()
            node = self.parse_expr()
            self.expect(TokenType.RPAREN)
            return node

        raise ParseError(f"Expressão inesperada: {token.tipo.name}", token.linha)

    # term ::= isvoid_expr [[ (* | /) isvoid_expr ]]*
    def parse_term(self):
        node = self.parse_isvoid()

        while self.check(TokenType.TIMES) or self.check(TokenType.DIVIDE):
            operator = self.advance()
            right = self.parse_isvoid()
            node = ast.BinOperation(operator.tipo, node, right, operator.linha)

        return node

    # arith ::= term [[ ( + | - ) term ]]*
    def parse_arith(self):
        node = self.parse_term()

        while self.check(TokenType.PLUS) or self.check(TokenType.MINUS):
            operator = self.advance()
            right = self.parse_term()
            node = ast.BinOperation(operator.tipo, node, right, operator.linha)

        return node

    # comparison ::= arith [ ( < | <= | = ) arith ]
    def parse_comparison(self):
        node = self.parse_arith()

        if self.check(TokenType.LT) or self.check(TokenType.LE) or self.check(TokenType.EQ):
            operator = self.advance()
            right = self.parse_arith()
            node = ast.BinOperation(operator.tipo, node, right, operator.linha)

        return node

    # not_expr ::= not not_expr | comparison
    def parse_not(self):
        if self.check(TokenType.NOT):
            operator = self.advance()
            operand = self.parse_not()
            return ast.UnaryOperation(operator.tipo, operand, operator.linha)

        return self.parse_comparison()

    # isvoid_expr ::= isvoid isvoid_expr | neg_expr
    def parse_isvoid(self):
        if self.check(TokenType.ISVOID):
            operator = self.advance()
            operand = self.parse_isvoid()
            return ast.UnaryOperation(operator.tipo, operand, operator.linha)

        return self.parse_neg()

    # neg_expr ::= ~ neg_expr | dispatch
    def parse_neg(self):
        if self.check(TokenType.NEG):
            operator = self.advance()
            operand = self.parse_neg()
            return ast.UnaryOperation(operator.tipo, operand, operator.linha)

        return self.parse_dispatch()

    # dispatch ::= atom [[ [@TYPEID] . OBJECTID ( [ args ] ) ]]*
    def parse_dispatch(self):
        node = self.parse_atom()

        while self.check(TokenType.DOT) or self.check(TokenType.AT):
            static_type = None
            if self.check(TokenType.AT):
                self.advance()
                static_type = self.expect(TokenType.TYPEID).valor

            dot = self.expect(TokenType.DOT)
            name_token = self.expect(TokenType.OBJECTID)
            args = self.parse_args()
            node = ast.Dispatch(node, static_type, name_token.valor, args, dot.linha)

        return node

    # Lista de argumentos entre parênteses, possivelmente vazia
    def parse_args(self):
        self.expect(TokenType.LPAREN)
        args = []

        if not self.check(TokenType.RPAREN):
            args.append(self.parse_expr())

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

        while not self.check(TokenType.RBRACE) and not self.check(TokenType.EOF):
            expressions.append(self.parse_expr())
            self.expect(TokenType.SEMI)

        self.expect(TokenType.RBRACE)

        if not expressions:
            raise ParseError("Bloco vazio: ao menos uma expressão é exigida", keyword.linha)

        return ast.Block(expressions, keyword.linha)

    # let_expr ::= let ID : TYPE [ <- expr ] [[ , ... ]]* in expr
    def parse_let(self):
        keyword = self.expect(TokenType.LET)
        bindings = []
        bindings.append(self.parse_let_binding())

        while self.check(TokenType.COMMA):
            self.advance()
            bindings.append(self.parse_let_binding())

        self.expect(TokenType.IN)
        body = self.parse_expr()
        return ast.Let(bindings, body, keyword.linha)

    # Uma declaração isolada dentro do let
    def parse_let_binding(self):
        name_token = self.expect(TokenType.OBJECTID)
        self.expect(TokenType.COLON)
        type_name = self.expect(TokenType.TYPEID).valor
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

        while not self.check(TokenType.ESAC) and not self.check(TokenType.EOF):
            branches.append(self.parse_case_branch())

        self.expect(TokenType.ESAC)

        if not branches:
            raise ParseError("Case sem ramos: ao menos um é exigido", keyword.linha)

        return ast.Case(expression, branches, keyword.linha)

    # Um ramo isolado do case
    def parse_case_branch(self):
        name_token = self.expect(TokenType.OBJECTID)
        self.expect(TokenType.COLON)
        type_name = self.expect(TokenType.TYPEID).valor
        self.expect(TokenType.DARROW)
        body = self.parse_expr()
        self.expect(TokenType.SEMI)
        return ast.CaseBranch(name_token.valor, type_name, body, name_token.linha)