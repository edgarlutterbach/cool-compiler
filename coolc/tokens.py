from enum import Enum, unique
from dataclasses import dataclass

@unique
class TokenType(Enum):
    # Palavras reservadas
    CLASS = "CLASS"
    ELSE = "ELSE"
    FI = "FI"
    IF = "IF"
    IN = "IN"
    INHERITS = "INHERITS"
    ISVOID = "ISVOID"
    LET = "LET"
    LOOP = "LOOP"
    POOL = "POOL"
    THEN = "THEN"
    WHILE = "WHILE"
    CASE = "CASE"
    ESAC = "ESAC"
    NEW = "NEW"
    OF = "OF"
    NOT = "NOT"
    # Identificadores
    TYPEID = "TYPEID"
    OBJECTID = "OBJECTID"
    # Literais
    INT_CONST = "INT_CONST"
    STR_CONST = "STR_CONST"
    BOOL_CONST = "BOOL_CONST"
    # Operadores
    PLUS = "PLUS"
    MINUS = "MINUS"
    TIMES = "TIMES"
    DIVIDE = "DIVIDE"
    NEG = "NEG"
    LT = "LT"
    LE = "LE"
    EQ = "EQ"
    ASSIGN = "ASSIGN"
    DOT = "DOT"
    AT = "AT"
    # Separadores e pontuação
    LBRACE = "LBRACE"
    RBRACE = "RBRACE"
    LPAREN = "LPAREN"
    RPAREN = "RPAREN"
    COLON = "COLON"
    SEMI = "SEMI"
    COMMA = "COMMA"
    DARROW = "DARROW"
    # Tokens de Controle
    EOF = "EOF"
    ERROR = "ERROR"

@dataclass(frozen=True)
class Token:
    tipo: TokenType
    linha: int
    valor: int | str | bool | None = None

KEYWORDS = {
    "class": TokenType.CLASS,
    "else": TokenType.ELSE,
    "fi": TokenType.FI,
    "if": TokenType.IF,
    "in": TokenType.IN,
    "inherits": TokenType.INHERITS,
    "isvoid": TokenType.ISVOID,
    "let": TokenType.LET,
    "loop": TokenType.LOOP,
    "pool": TokenType.POOL,
    "then": TokenType.THEN,
    "while": TokenType.WHILE,
    "case": TokenType.CASE,
    "esac": TokenType.ESAC,
    "new": TokenType.NEW,
    "of": TokenType.OF,
    "not": TokenType.NOT
}