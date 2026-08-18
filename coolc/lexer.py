from coolc.tokens import TokenType, Token, KEYWORDS

class Lexer:
    def __init__(self, text):
        self.text = text
        self.pos = 0
        self.line = 1

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
