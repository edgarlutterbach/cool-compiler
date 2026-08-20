import string

from coolc.tokens import TokenType, Token, KEYWORDS

LETTERS = set(string.ascii_letters)
LOWERCASE = set(string.ascii_lowercase)
DIGITS = set(string.digits)
IDENT_CHARS = LETTERS | DIGITS | {"_"}
WHITESPACES = set(string.whitespace)

class LexicalError(Exception):
    def __init__(self, message, line):
        super().__init__(message)
        self.message = message
        self.line = line

class Lexer:
    def __init__(self, text):
        self.text = text
        self.pos = 0
        self.line = 1
        self.token_line = 1

    def at_end(self):
        return self.pos >= len(self.text)

    def peek(self, offset=0):
        target = self.pos + offset
        if target >= len(self.text):
            return ""
        return self.text[target]

    def advance(self):
        char = self.peek()
        self.pos += 1
        if char == "\n":
            self.line += 1
        return char

    def match(self, char):
        if self.peek() != char:
            return False
        self.advance()
        return True

    def next_token(self):
        self.skip_whitespaces_and_comments()
        self.token_line = self.line

        if self.at_end():
            return self.make_token(TokenType.EOF)

        char = self.peek()

        if char in LETTERS or char == "_":
            return self.read_identifier()
        if char in DIGITS:
            return self.read_number()
        if char == '"':
            return self.read_string()
        return self.read_operator()

    def make_token(self, token_type, value=None):
        return Token(token_type, self.token_line, value)

    def skip_whitespaces_and_comments(self):
        while True:
            if self.peek() in WHITESPACES:
                self.advance()

                continue

            if self.peek() == "-" and self.peek(1) == "-":
                self.advance()
                self.advance()

                while not self.at_end() and self.peek() != "\n":
                    self.advance()
                continue

            if self.peek() == "(" and self.peek(1) == "*":
                cont = 1
                start_line = self.line
                self.advance()
                self.advance()

                while cont != 0 and not self.at_end():
                    if self.peek() == "(" and self.peek(1) == "*":
                        cont += 1
                        self.advance()
                        self.advance()
                    elif self.peek() == "*" and self.peek(1) == ")":
                        cont -= 1
                        self.advance()
                        self.advance()
                    else:
                        self.advance()

                if cont != 0:
                    raise LexicalError("Comentário de bloco não foi fechado", start_line)
                continue
            break

    def read_identifier(self):
        start = self.pos

        while self.peek() in IDENT_CHARS:
            self.advance()

        lexeme = self.text[start:self.pos]

        lex_lower = lexeme.lower()

        if lex_lower in ("true", "false") and lexeme[0] in LOWERCASE:
            return self.make_token(TokenType.BOOL_CONST, lex_lower == "true")

        keyword_type = KEYWORDS.get(lex_lower)
        if keyword_type is not None:
            return self.make_token(keyword_type)

        if lexeme[0] == "_":
            raise LexicalError("Identificador não pode começar com sublinhado", self.token_line)

        if lexeme[0] in LOWERCASE:
            return self.make_token(TokenType.OBJECTID, lexeme)

        return self.make_token(TokenType.TYPEID, lexeme)

    def read_number(self):
        start = self.pos

        while self.peek() in DIGITS:
            self.advance()

        lexeme = self.text[start:self.pos]

        return self.make_token(TokenType.INT_CONST, int(lexeme))

    def read_string(self):
        raise NotImplementedError

    def read_operator(self):
        raise NotImplementedError
