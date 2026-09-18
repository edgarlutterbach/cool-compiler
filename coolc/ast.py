from dataclasses import dataclass
from coolc.tokens import TokenType

# Nós da árvore sintática abstrata
# Cada classe corresponde a uma construção da gramática de COOL.
# Guardam dados apenas, não têm comportamento.

# Raiz da árvore
@dataclass
class Program:
    classes: list

# Gramática do 'class TYPEID [ inherits TYPEID ] { [[ feature ; ]]* }'
@dataclass
class Class:
    name: str
    parent: str | None
    features: list
    line: int

# Gramática do 'OBJECTID ( [ formal [[ , formal ]]* ] ) : TYPEID { expr }'
@dataclass
class Method:
    name: str
    formals: list
    return_type: str
    body: object
    line: int

# Gramática do 'OBJECTID : TYPEID [ <- expr ]'
@dataclass
class Attribute:
    name: str
    type_name: str
    init: object | None
    line: int

# Gramática do 'OBJECTID : TYPEID'
@dataclass
class Formal:
    name: str
    type_name: str
    line: int

# Folhas da árvore. Onde a recursão termina

# integer
@dataclass
class IntLiteral:
    value: int
    line: int

# string
@dataclass
class StringLiteral:
    value: str
    line: int

# bool (true | false)
@dataclass
class BoolLiteral:
    value: bool
    line: int

# identificador
@dataclass
class Identifier:
    name: str
    line: int

# Operadores

# Operação binária -- expr <op> expr, sendo <op> em + - * / < <= =
@dataclass
class BinOperation:
    operator: TokenType
    left: object
    right: object
    line: int

# Operaçao unária -- ~expr | not expr | isvoid expr
@dataclass
class UnaryOperation:
    operator: TokenType
    operand: object
    line: int

# Atribução -- OBJECTID <- expr
@dataclass
class Assign:
    name: str
    value: object
    line: int

# Despacho de método -- expr[@TYPE].ID( args )
@dataclass
class Dispatch:
    receiver: object
    static_type: str | None
    name: str
    args: list
    line: int

# Condicional -- if expr then expr else expr fi
@dataclass
class If:
    condition: object
    then_branch: object
    else_branch: object
    line: int

# Laço -- while expr loop expr pool
@dataclass
class While:
    condition: object
    body: object
    line: int

# Bloco -- { [[ expr ; ]]+ }
@dataclass
class Block:
    expressions: list
    line: int

# Instanciação -- new TYPEID
@dataclass
class New:
    type_name: str
    line: int

# Declaração local dentro de um let
@dataclass
class LetBinding:
    name: str
    type_name: str
    init: object | None
    line: int

# let ID : TYPE [ <- expr ] [[ , ID : TYPE [ <- expr ] ]]* in expr
@dataclass
class Let:
    bindings: list
    body: object
    line: int

# Um ramo do case -- ID : TYPE => expr ;
@dataclass
class CaseBranch:
    name: str
    type_name: str
    body: object
    line: int

# case expr of [[ ID : TYPE => expr ; ]]+ esac
@dataclass
class Case:
    expression: object
    branches: list
    line: int