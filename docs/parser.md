# Especificação sintática — COOL

Documento de referência do analisador sintático.

---

## 1. Papel da fase

Entrada: a sequência de tokens produzida pelo analisador léxico.
Saída: uma árvore sintática abstrata (AST).

Duas responsabilidades:

- Validar a estrutura. Determinar se a sequência de tokens forma um
  programa bem construído segundo a gramática.
- Construir a árvore. Produzir a estrutura hierárquica que as fases de
  análise semântica e geração de código vão percorrer.

### Fronteira com a análise semântica

O sintático verifica forma, não sentido.

| Entrada | Sintático | Semântico |
|---|---|---|
| `if x then y fi` | Rejeita — falta `else` | — |
| `if 42 then y else z fi` | Aceita | Rejeita — predicado não é `Bool` |
| `x <- "texto"` | Aceita | Rejeita se `x` for `Int` |
| `new Inexistente` | Aceita | Rejeita — classe não declarada |

---

## 2. Técnica adotada: descida recursiva

Cada regra da gramática corresponde a uma função. As chamadas entre essas
funções reproduzem a estrutura da gramática, e a recursão mútua permite
aninhamento arbitrário de expressões.

### Primitivas

Análogas às do lexer, um nível acima: operam sobre tokens em vez de
caracteres.

| Primitiva | Função |
|---|---|
| `peek()` | Devolve o token atual **sem consumir** |
| `advance()` | Consome e devolve o token atual |
| `check(tipo)` | O token atual é do tipo indicado? |
| `expect(tipo)` | Consome o token exigido; erro de sintaxe se não for |

`check` decide qual alternativa da regra seguir. `expect` implementa as partes
obrigatórias: quando a gramática determina que após `if` vem `then`, o `then`
não é opcional.

### Lookahead necessário

Um token, exceto em `feature` (ver 3.3), onde são necessários dois.

---

## 3. Gramática — estrutura do programa

Notação: `[ ]` marca construção opcional, `*` zero ou mais repetições, `+` uma
ou mais.

### 3.1 program

```
program ::= [[ class ; ]]+
```

Um ou mais classes, cada uma terminada por ponto e vírgula. Arquivo vazio é
inválido.

### 3.2 class

```
class ::= class TYPEID [ inherits TYPEID ] { [[ feature ; ]]* }
```

A cláusula `inherits` é opcional.

Uma classe pode ter zero features.

### 3.3 feature

```
feature ::= OBJECTID ( [ formal [[ , formal ]]* ] ) : TYPEID { expr }
          | OBJECTID : TYPEID [ <- expr ]
```

Único ponto da gramática que exige dois tokens de lookahead. As duas
alternativas começam com `OBJECTID`; o token seguinte decide:

- `(` → definição de método
- `:` → definição de atributo

### 3.4 formal

```
formal ::= OBJECTID : TYPEID
```

Parâmetro formal de método. Sem valor padrão.

---

## 4. Gramática — expressões

Existem 21 alternativas para `expr`. Agrupadas por
estrutura de reconhecimento:

### 4.1 Construções com palavra-chave inicial

O primeiro token identifica a regra sem ambiguidade. São as mais simples de
implementar.

```
if expr then expr else expr fi
while expr loop expr pool
case expr of [[ OBJECTID : TYPEID => expr ; ]]+ esac
let OBJECTID : TYPEID [ <- expr ] [[ , OBJECTID : TYPEID [ <- expr ] ]]* in expr
new TYPEID
isvoid expr
not expr
```

`case` exige ao menos um ramo. `let` exige ao menos uma declaração.

### 4.2 Bloco

```
{ [[ expr ; ]]+ }
```

Ao menos uma expressão. O ponto e vírgula é terminador, não separador: a última expressão também o exige.

### 4.3 Operadores binários

```
expr + expr     expr - expr     expr * expr     expr / expr
expr < expr     expr <= expr    expr = expr
```

Escritos com recursão à esquerda no manual.

### 4.4 Operadores unários

```
~expr           not expr        isvoid expr
```

`~` é complemento aritmético sobre `Int`; `not` é complemento booleano sobre
`Bool`.

### 4.5 Despacho

Três formas:

```
expr . OBJECTID ( [ expr [[ , expr ]]* ] )          dinâmico
expr @ TYPEID . OBJECTID ( [ expr [[ , expr ]]* ] ) estático
OBJECTID ( [ expr [[ , expr ]]* ] )                 abreviado (self implícito)
```

### 4.6 Atribuição

```
OBJECTID <- expr
```

Associativa à direita e de menor precedência que todos os operadores.

### 4.7 Átomos

```
( expr )        OBJECTID        INT_CONST
STR_CONST       true            false
```

Os parênteses não geram nó. Servem para determinar a forma da árvore e
desaparecem dela — é a "abstração" no nome da AST.

---

## 5. Transformações sobre a gramática do manual

A gramática da Figura 1 não é diretamente implementável por descida
recursiva. Três transformações foram necessárias.

### 5.1 Eliminação da recursão à esquerda

Uma regra da forma `expr ::= expr + term` transcrita literalmente produziria
uma função cuja primeira ação é chamar a si mesma sem consumir token nenhum —
recursão infinita.

A reescrita padrão troca a recursão por um laço:

```
regra ::= subregra [[ operador subregra ]]*
```

A cada iteração, o nó acumulado até então torna-se o filho esquerdo do
novo nó. Isso é o que produz associatividade à esquerda: `1 - 2 - 3` monta
`(1-2)-3`. Inverter a ordem dos filhos produziria `1-(2-3)`, resultado
numericamente diferente.

### 5.2 Precedência codificada por encadeamento de regras

Não há tabela de precedência no parser. A precedência resulta da ordem em que
as regras se referem umas às outras: operadores de menor precedência ficam
nas regras mais externas, e portanto mais próximos da raiz da árvore. Como
a avaliação de uma árvore ocorre de baixo para cima, o que está mais interno é
avaliado primeiro.

Tabela do manual (seção 11.1), da maior para a menor precedência, mapeada nas
regras correspondentes:

| Nível | Operadores | Regra |
|---|---|---|
| 1 (mais forte) | `.` `@` | `dispatch` |
| 2 | `~` | `unary_neg` |
| 3 | `isvoid` | `isvoid_expr` |
| 4 | `*` `/` | `term` |
| 5 | `+` `-` | `arith` |
| 6 | `<=` `<` `=` | `comparison` |
| 7 | `not` | `not_expr` |
| 8 (mais fraca) | `<-` | `expr` |
