# Especificação sintática — COOL

Documento de referência do analisador sintático.

---

## 1. Visão geral

| Item | Escolha |
|------|---------|
| Técnica | Descida recursiva, escrita manualmente |
| Entrada | Lista de `Token` produzida por `Lexer.tokenize()`, terminada em `EOF` |
| Saída | Árvore sintática abstrata (`ast.Program`) |
| Lookahead | 1 token; 2 tokens apenas para reconhecer atribuição |
| Tratamento de erro | Aborta no primeiro erro, lançando `ParseError` |

Cada regra da gramática corresponde a um método `parse_<regra>`. O método
consome exatamente os tokens da sua construção e devolve o nó da AST
correspondente.

O parser nunca recebe tokens `ERROR`: `main.py` verifica erros léxicos antes
de instanciar o `Parser` e encerra se houver algum.

---

## 2. Primitivas de navegação

Todos os métodos de regra são construídos sobre quatro operações.

| Método | Comportamento | Observações |
|--------|---------------|-------------|
| `peek(offset=0)` | Devolve o token na posição atual + `offset`, sem consumir | Além do fim, devolve o último token (`EOF`) |
| `advance()` | Consome e devolve o token atual | Nunca avança além de `EOF` |
| `check(tipo)` | `True` se o token atual é do tipo dado | Não consome |
| `expect(tipo)` | Consome se o tipo bate; senão lança `ParseError` | Única fonte da mensagem "Esperado X, encontrado Y" |

`advance()` parar em `EOF` é o que garante que laços como
`while not check(RBRACE)` não entrem em loop infinito nem estourem o índice
quando o arquivo termina antes do esperado. Por isso todo laço de repetição
também testa `EOF` explicitamente.

---

## 3. Gramática do manual

A gramática oficial, na notação do próprio manual:
`[ ]` é opcional, `[[ ]]*` é zero ou mais, `[[ ]]+` é um ou mais.

```text
program ::= [[ class ; ]]+
class   ::= class TYPE [ inherits TYPE ] { [[ feature ; ]]* }
feature ::= ID ( [ formal [[ , formal ]]* ] ) : TYPE { expr }
          | ID : TYPE [ <- expr ]
formal  ::= ID : TYPE
expr    ::= ID <- expr
          | expr [ @TYPE ] . ID ( [ expr [[ , expr ]]* ] )
          | ID ( [ expr [[ , expr ]]* ] )
          | if expr then expr else expr fi
          | while expr loop expr pool
          | { [[ expr ; ]]+ }
          | let ID : TYPE [ <- expr ] [[ , ID : TYPE [ <- expr ] ]]* in expr
          | case expr of [[ ID : TYPE => expr ; ]]+ esac
          | new TYPE
          | isvoid expr
          | expr + expr | expr - expr | expr * expr | expr / expr
          | ~ expr
          | expr < expr | expr <= expr | expr = expr
          | not expr
          | ( expr )
          | ID | integer | string | true | false
```

As regras de `program`, `class`, `feature` e `formal` são implementadas
praticamente como estão. A regra `expr` não pode ser: ela é **ambígua** e
**recursiva à esquerda**, e nenhuma das duas propriedades é compatível com
descida recursiva. A seção 4 descreve as transformações aplicadas.

---

## 4. Transformações aplicadas

### 4.1 Estratificação por precedência

A ambiguidade de `expr` vem dos operadores: `1 + 2 * 3` admite duas árvores.
O manual resolve isso fora da gramática, com a tabela de precedência da
seção 11.1. Aqui a precedência é codificada *dentro* da gramática: cada nível
de precedência vira uma regra, e cada regra só chama a do nível imediatamente
mais forte.

Quanto mais profunda a regra na cadeia de chamadas, mais cedo seus operadores
são agrupados, e portanto maior sua precedência.

### 4.2 Eliminação da recursão à esquerda

`arith ::= arith + term` faria `parse_arith` chamar a si mesmo sem consumir
nenhum token, em recursão infinita. A regra é reescrita como repetição:

```text
arith ::= arith + term | term        -- original, recursiva à esquerda
arith ::= term [[ + term ]]*         -- transformada
```

Implementação: um laço `while` que, a cada operador, cria um novo
`BinOperation` com o nó acumulado à esquerda. Isso produz associatividade à
esquerda: `1 - 2 - 3` vira `(1 - 2) - 3`, e não `1 - (2 - 3)`.

### 4.3 Fatoração à esquerda

Duas regras começam pelo mesmo token e só se distinguem pelo seguinte:

| Construção | Prefixo comum | Decisão |
|------------|---------------|---------|
| Método × atributo | `OBJECTID` | `(` → método; caso contrário → atributo |
| Despacho abreviado × identificador | `OBJECTID` | `(` → despacho; caso contrário → identificador |

O `OBJECTID` é consumido uma única vez e o token seguinte decide o ramo.
Em `parse_feature`, o token do nome é repassado para `parse_method` ou
`parse_attribute`, que não o consomem novamente.

### 4.4 Lookahead de dois tokens para atribuição

`x <- 1` e `x + 1` começam com o mesmo `OBJECTID`, e a atribuição tem a menor
precedência de todas. Decidir após consumir o `x` exigiria desfazer o consumo
caso não fosse atribuição. Em vez disso, `parse_expr` inspeciona dois tokens
sem consumir nada: `OBJECTID` seguido de `ASSIGN` é atribuição; qualquer outra
coisa segue para `parse_not`.

É o único ponto do parser que precisa de `peek(1)`.

### 4.5 Construções com palavra-chave como átomos

`if`, `while`, `let`, `case`, blocos e `new` começam com um token exclusivo e,
no caso das quatro primeiras, terminam com um token de fechamento (`fi`,
`pool`, `}`, `esac`) ou estendem-se até onde der (`let`). Por isso não
participam da cadeia de precedência: são tratadas como átomos. Isso permite
escrever `1 + if c then 2 else 3 fi` sem parênteses.

`let` não tem fechamento: o corpo é lido por `parse_expr`, que consome a
expressão mais longa possível. É exatamente a regra do manual de que o `let`
se estende o máximo possível para a direita.

---

## 5. Gramática implementada

Resultado das transformações. Cada linha corresponde a um método de
`parser.py`.

```text
program     ::= [[ class ; ]]+
class       ::= class TYPEID [ inherits TYPEID ] { [[ feature ; ]]* }
feature     ::= OBJECTID ( method_rest | attr_rest )
method_rest ::= ( [ formal [[ , formal ]]* ] ) : TYPEID { expr }
attr_rest   ::= : TYPEID [ <- expr ]
formal      ::= OBJECTID : TYPEID

expr        ::= OBJECTID <- expr
              | not_expr
not_expr    ::= not not_expr | comparison
comparison  ::= arith [ ( < | <= | = ) arith ]
arith       ::= term [[ ( + | - ) term ]]*
term        ::= isvoid_expr [[ ( * | / ) isvoid_expr ]]*
isvoid_expr ::= isvoid isvoid_expr | neg_expr
neg_expr    ::= ~ neg_expr | dispatch
dispatch    ::= atom [[ [ @ TYPEID ] . OBJECTID args ]]*
atom        ::= if_expr | while_expr | block | let_expr | case_expr
              | new TYPEID
              | INT_CONST | STR_CONST | BOOL_CONST
              | OBJECTID [ args ]
              | ( expr )
args        ::= ( [ expr [[ , expr ]]* ] )

if_expr     ::= if expr then expr else expr fi
while_expr  ::= while expr loop expr pool
block       ::= { [[ expr ; ]]+ }
let_expr    ::= let binding [[ , binding ]]* in expr
binding     ::= OBJECTID : TYPEID [ <- expr ]
case_expr   ::= case expr of [[ branch ]]+ esac
branch      ::= OBJECTID : TYPEID => expr ;
```

| Regra | Método |
|-------|--------|
| `program` | `parse_program` |
| `class` | `parse_class` |
| `feature` | `parse_feature`, `parse_method`, `parse_attribute` |
| `formal` | `parse_formal` |
| `expr` | `parse_expr` |
| `not_expr` | `parse_not` |
| `comparison` | `parse_comparison` |
| `arith` | `parse_arith` |
| `term` | `parse_term` |
| `isvoid_expr` | `parse_isvoid` |
| `neg_expr` | `parse_neg` |
| `dispatch` | `parse_dispatch` |
| `atom` | `parse_atom` |
| `args` | `parse_args` |
| `if_expr` … `branch` | `parse_if`, `parse_while`, `parse_block`, `parse_let`, `parse_let_binding`, `parse_case`, `parse_case_branch` |

---

## 6. Precedência e associatividade

Da maior para a menor, conforme o manual, seção 11.1.

| Nível | Operadores | Regra | Associatividade | Observações |
|-------|------------|-------|-----------------|-------------|
| 1 | `.` `@` | `dispatch` | esquerda | `a.f().g()` → `(a.f()).g()` |
| 2 | `~` | `neg_expr` | direita (prefixo) | |
| 3 | `isvoid` | `isvoid_expr` | direita (prefixo) | |
| 4 | `*` `/` | `term` | esquerda | |
| 5 | `+` `-` | `arith` | esquerda | |
| 6 | `<` `<=` `=` | `comparison` | **não associativa** | `a < b < c` é erro |
| 7 | `not` | `not_expr` | direita (prefixo) | |
| 8 | `<-` | `expr` | direita | `a <- b <- 1` → `a <- (b <- 1)` |

Operadores prefixos são associativos à direita por natureza: `~~x` só pode
ser `~(~x)`. Na implementação, a regra chama a si mesma após consumir o
operador.

A não associatividade da comparação vem de usar `if` em vez de `while` em
`parse_comparison`: após uma comparação, um segundo operador relacional não é
consumido por ninguém e causa erro na regra que chamou a expressão.

A associatividade à direita da atribuição vem de `parse_expr` chamar a si
mesmo para o valor.

---

## 7. Nós da AST

Definidos em `ast.py`. São dataclasses sem comportamento: guardam dados e
nada mais.

### 7.1 Estrutura

| Nó | Produção | Campos | Observações |
|----|----------|--------|-------------|
| `Program` | `program` | `classes` | Único nó sem linha |
| `Class` | `class` | `name`, `parent`, `features`, `line` | `parent` é `None` sem `inherits` |
| `Method` | `feature` (método) | `name`, `formals`, `return_type`, `body`, `line` | |
| `Attribute` | `feature` (atributo) | `name`, `type_name`, `init`, `line` | `init` é `None` sem `<-` |
| `Formal` | `formal` | `name`, `type_name`, `line` | |

### 7.2 Expressões

| Nó | Produção | Campos | Observações |
|----|----------|--------|-------------|
| `Assign` | `ID <- expr` | `name`, `value`, `line` | |
| `BinOperation` | `expr op expr` | `operator`, `left`, `right`, `line` | `operator` é um `TokenType` |
| `UnaryOperation` | `~`, `not`, `isvoid` | `operator`, `operand`, `line` | `operator` é um `TokenType` |
| `Dispatch` | as três formas de despacho | `receiver`, `static_type`, `name`, `args`, `line` | Ver 7.3 |
| `If` | `if_expr` | `condition`, `then_branch`, `else_branch`, `line` | |
| `While` | `while_expr` | `condition`, `body`, `line` | |
| `Block` | `block` | `expressions`, `line` | Nunca vazio |
| `Let` | `let_expr` | `bindings`, `body`, `line` | |
| `LetBinding` | `binding` | `name`, `type_name`, `init`, `line` | `init` é `None` sem `<-` |
| `Case` | `case_expr` | `expression`, `branches`, `line` | Nunca sem ramos |
| `CaseBranch` | `branch` | `name`, `type_name`, `body`, `line` | |
| `New` | `new TYPEID` | `type_name`, `line` | |

### 7.3 Folhas

| Nó | Token de origem | Campos |
|----|-----------------|--------|
| `IntLiteral` | `INT_CONST` | `value` (`int`), `line` |
| `StringLiteral` | `STR_CONST` | `value` (`str`, escapes já resolvidos), `line` |
| `BoolLiteral` | `BOOL_CONST` | `value` (`bool`), `line` |
| `Identifier` | `OBJECTID` | `name`, `line` |

### 7.4 As três formas de despacho

Todas produzem o mesmo nó `Dispatch`. Só os campos preenchidos mudam.

| Forma | Exemplo | `receiver` | `static_type` |
|-------|---------|------------|---------------|
| Dinâmico | `obj.f(x)` | nó de `obj` | `None` |
| Estático | `obj@A.f(x)` | nó de `obj` | `"A"` |
| Abreviado | `f(x)` | `Identifier("self")` sintético | `None` |

---

## 8. Erros sintáticos

Todo erro é um `ParseError(mensagem, linha)`. A linha é a do token onde o
erro foi detectado, não necessariamente a da construção que o causou.

| Situação | Mensagem | Origem |
|----------|----------|--------|
| Token diferente do exigido pela regra | `Esperado X, encontrado Y` | `expect` |
| Token que não inicia nenhuma expressão | `Expressão inesperada: TIPO` | `parse_atom` |
| Arquivo sem nenhuma classe | `Programa vazio: ao menos uma classe é exigida` | manual, `[[ class ; ]]+` |
| `{ }` como expressão | `Bloco vazio: ao menos uma expressão é exigida` | manual, `[[ expr ; ]]+` |
| `case ... of esac` | `Case sem ramos: ao menos um é exigido` | manual, `[[ ... ]]+` |
| `let` sem declaração | `Esperado objectid, encontrado 'in'` | `expect` em `parse_let_binding` |
| Comparação encadeada `a < b < c` | `Esperado X, encontrado '<'`, com X dependente do contexto | não associatividade, seção 6 |

Os textos de `X` e `Y` vêm de `describe()`, em `tokens.py`: símbolos e
palavras reservadas aparecem entre aspas (`'fi'`, `';'`); identificadores,
literais e `EOF` aparecem pelo nome do tipo (`objectid`, `eof`).
