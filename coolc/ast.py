from dataclasses import dataclass

# Nós da árvore sintática abstrata
# Cada classe corresponde a uma construção da gramática de COOL.
# Guardam dados apenas, não têm comportamento.

# Raiz da árvore
@dataclass
class Program:
    # Lista de Class, na ordem em que aparecem no código
    classes: list

# Gramática do 'class TYPEID [ inherits TYPEID ] { [[ feature ; ]]* }'
@dataclass
class Class:
    name: str
    # 'parent' podendo ser uma str ou None, caso 'inherits' esteja ausente
    parent: str | None
    # Métodos e atributos misturados, na ordem do código-fonte
    features: list
    # Linha do 'class' para mensagens de erro
    line: int

# Gramática do 'OBJECTID ( [ formal [[ , formal ]]* ] ) : TYPEID { expr }'
@dataclass
class Method:
    name: str
    # Lista de Formal
    formals: list
    return_type: str
    # O body é uma expressão única já que COOL é uma linguagem de expressões
    body: object
    line: int

# Gramática do 'OBJECTID : TYPEID [ <- expr ]'
@dataclass
class Attribute:
    name: str
    type_name: str
    # None quando não há inicialização explícita
    init: object | None
    line: int

# Gramática do 'OBJECTID : TYPEID'
@dataclass
class Formal:
    name: str
    type_name: str
    line: int