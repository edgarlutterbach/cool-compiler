# Especificação léxica — COOL

Documento de referência do analisador léxico.

---

## 1. Palavras reservadas

COOL define 19 palavras reservadas: `class`, `else`, `false`, `fi`, `if`,
`in`, `inherits`, `isvoid`, `let`, `loop`, `pool`, `then`, `while`, `case`,
`esac`, `new`, `of`, `not`, `true`.

Destas, 17 produzem tokens sem valor e estão na tabela abaixo. As outras duas
(`true` e `false`) são classificadas como literais neste projeto.

Exceto `true` e `false`, as palavras reservadas são
insensíveis a maiúsculas. `class`, `CLASS` e `cLaSs` são o mesmo token.

Implementação: consumir o identificador completo, converter para minúsculas e
só então consultar esta tabela. Se não estiver aqui, é identificador.

| Nome       | Padrão     | Valor armazenado | Observações |
|------------|------------|------------------|-------------|
| `CLASS`    | `class`    | nenhum           | |
| `ELSE`     | `else`     | nenhum           | |
| `FI`       | `fi`       | nenhum           | Fecha o `if ... then ... else` |
| `IF`       | `if`       | nenhum           | |
| `IN`       | `in`       | nenhum           | Separa declarações do corpo no `let` |
| `INHERITS` | `inherits` | nenhum           | |
| `ISVOID`   | `isvoid`   | nenhum           | Operador prefixo |
| `LET`      | `let`      | nenhum           | |
| `LOOP`     | `loop`     | nenhum           | |
| `POOL`     | `pool`     | nenhum           | Fecha o `while ... loop` |
| `THEN`     | `then`     | nenhum           | |
| `WHILE`    | `while`    | nenhum           | |
| `CASE`     | `case`     | nenhum           | |
| `ESAC`     | `esac`     | nenhum           | Fecha o `case ... of` |
| `NEW`      | `new`      | nenhum           | |
| `OF`       | `of`       | nenhum           | |
| `NOT`      | `not`      | nenhum           | Complemento booleano; não confundir com `~` |

---

## 2. Identificadores

Identificadores são cadeias (que não sejam palavras
reservadas) formadas por letras, dígitos e sublinhado. Identificadores de tipo
começam com maiúscula; identificadores de objeto começam com minúscula.

| Nome       | Padrão                | Valor armazenado  | Observações |
|------------|-----------------------|-------------------|-------------|
| `TYPEID`   | `[A-Z][A-Za-z0-9_]*`  | texto do lexema   | Nomes de classe e de tipo |
| `OBJECTID` | `[a-z][A-Za-z0-9_]*`  | texto do lexema   | Variáveis, atributos, métodos |

### 2.1 `self` e `SELF_TYPE`

`self` é um `OBJECTID` comum e `SELF_TYPE` é um `TYPEID`
comum. Nenhuma linha extra na tabela de reservadas.

---

## 3. Literais

| Nome         | Padrão        | Valor armazenado      | Observações |
|--------------|---------------|-----------------------|-------------|
| `INT_CONST`  | `[0-9]+`      | `int` já convertido   | Sem sinal; zeros à esquerda permitidos |
| `STR_CONST`  | ver 3.2       | texto já interpretado | Escapes resolvidos na tokenização |
| `BOOL_CONST` | `true`/`false`| `True` / `False` (bool) | Primeira letra obrigatoriamente minúscula |

### 3.1 Inteiros

`-5` produz dois tokens: `MINUS` seguido de `INT_CONST(5)`. O manual
cita `007` como constante válida, logo zeros à esquerda são aceitos.

### 3.2 Literais de string

Delimitados por aspas duplas. O conteúdo é definido por exclusão: qualquer
caractere é permitido, salvo as restrições listadas adiante.

A regra geral é que `\c` denota o caractere `c`. Existem quatro
exceções, e só quatro:

| Sequência | Produz |
|-----------|--------|
| `\b`      | backspace |
| `\t`      | tab |
| `\n`      | quebra de linha |
| `\f`      | formfeed |

Todo o resto decorre da regra geral, e não são casos especiais:

| Sequência | Produz | Por quê |
|-----------|--------|---------|
| `\"`      | `"`    | Regra geral; é o que permite aspas dentro da string |
| `\\`      | `\`    | Regra geral |
| `\q`      | `q`    | Regra geral; não é erro |
| `\` + quebra de linha real | quebra de linha | Regra geral; permite string multilinha |

### 3.3 Regra de maiúsculas de `true` e `false`

Diferente das demais reservadas: apenas a primeira letra precisa ser 
minúscula; as seguintes podem ser maiúsculas ou minúsculas.

- `true`, `tRUE`, `tRuE` → `BOOL_CONST(True)`
- `True`, `TRUE` → `TYPEID` (começam com maiúscula)

Implementação: testar antes da consulta genérica à tabela de reservadas,
verificando o lexema em minúsculas e que o primeiro caractere é minúsculo.

---

## 4. Operadores

| Nome     | Padrão | Valor armazenado | Observações |
|----------|--------|------------------|-------------|
| `PLUS`   | `+`    | nenhum           | Soma |
| `MINUS`  | `-`    | nenhum           | Subtração. Conflita com `--`; exige maximal munch |
| `TIMES`  | `*`    | nenhum           | Multiplicação. Conflita com `*)`; exige maximal munch |
| `DIVIDE` | `/`    | nenhum           | Divisão inteira |
| `NEG`    | `~`    | nenhum           | Complemento aritmético*(`Int` → `Int`) |
| `LT`     | `<`    | nenhum           | Conflita com `<-` e `<=`; exige maximal munch |
| `LE`     | `<=`   | nenhum           | Menor ou igual |
| `EQ`     | `=`    | nenhum           | Igualdade. Conflita com `=>`; exige maximal munch |
| `ASSIGN` | `<-`   | nenhum           | Atribuição |
| `DOT`    | `.`    | nenhum           | Despacho dinâmico: `obj.metodo()` |
| `AT`     | `@`    | nenhum           | Despacho estático: `obj@Classe.metodo()` |

COOL não possui `>`, `>=` nem operador de desigualdade. Comparações nesses
sentidos são escritas invertendo os operandos ou combinando com `not`.

---

## 5. Separadores e pontuação

| Nome     | Padrão | Valor armazenado | Observações |
|----------|--------|------------------|-------------|
| `LBRACE` | `{`    | nenhum           | |
| `RBRACE` | `}`    | nenhum           | |
| `LPAREN` | `(`    | nenhum           | Conflita com `(*`; exige maximal munch |
| `RPAREN` | `)`    | nenhum           | |
| `COLON`  | `:`    | nenhum           | |
| `SEMI`   | `;`    | nenhum           | Terminador, não separador |
| `COMMA`  | `,`    | nenhum           | |
| `DARROW` | `=>`   | nenhum           | Ramo de `case` |

---

## 6. Tokens de controle

| Nome    | Padrão  | Valor armazenado    | Observações |
|---------|---------|---------------------|-------------|
| `EOF`   | nenhum  | nenhum              | Token sintético, emitido uma única vez ao fim do texto |
| `ERROR` | nenhum  | mensagem descritiva | Emitido em qualquer falha léxica |

Situações que geram `ERROR`:

| Situação | Origem |
|----------|--------|
| Caractere inválido fora de string e de comentário | manual (não está na Figura 1) |
| Identificador iniciado por `_` ou dígito | manual, 10.1 |
| Quebra de linha não escapada em string | manual, 10.2 |
| EOF dentro de string | manual, 10.2 |
| Byte nulo em string | manual, 10.2 |
| String com mais de 1024 caracteres | manual, 7.1 |
| EOF dentro de comentário de bloco | manual, 10.3 |
| `*)` sem `(*` correspondente | **decisão própria** — o manual não define |

---

## 7. Decisões de projeto registradas

Booleanos são literais, não palavras reservadas.
`true` e `false` produzem `BOOL_CONST` com valor, e não tokens `TRUE`/`FALSE`
sem valor. Motivo: na gramática do manual, `true` e `false`
aparecem como alternativas de `expr`, exatamente no mesmo lugar que `integer`
e `string` — nunca como marcação estrutural igual a `if` ou `class`. Um único
token com valor evita duplicar regras na gramática. 

Inteiros são armazenados já convertidos para `int`.
A conversão é trivial e barata aqui, e evita que a análise semântica e a
geração de código a repitam.

Strings são armazenadas já interpretadas.
`"a\nb"` é armazenado como três caracteres, com a quebra de linha real, e não
como quatro com a barra invertida literal. Motivo: se as escapes não forem
resolvidas agora, teriam de ser resolvidas na geração de código, quando o
contexto léxico já se perdeu. Resolver uma vez, onde a informação está, é mais
barato e mais fácil de testar. O comprimento de 1024 é contado sobre o texto
interpretado, não sobre o texto bruto — decisão própria; o manual não
esclarece.

Palavras reservadas, operadores e separadores não armazenam valor.
O tipo do token já identifica o lexema univocamente.

A linha é armazenada em todos os tokens.
Necessária para mensagens de erro em todas as fases seguintes.

Recuperação de erro em vez de abortar.
Escolha própria; o manual não trata de tratamento de erro do compilador.

---

## 8. Elementos que não geram token

### 8.1 Espaço em branco

| Caractere | ASCII | Nome |
|-----------|-------|------|
| `' '`     | 32    | espaço |
| `\t`      | 9     | tab horizontal |
| `\n`      | 10    | quebra de linha |
| `\v`      | 11    | tab vertical |
| `\f`      | 12    | formfeed |
| `\r`      | 13    | carriage return |

Note que `\b` (backspace) não é espaço em branco em COOL. Ele só existe
como sequência de escape dentro de strings.

### 8.2 Comentário de linha

Inicia em `--` e termina na quebra de linha ou no fim do arquivo. 
O manual é explícito ao permitir o segundo caso, portanto EOF dentro
de comentário de linha não é erro.

### 8.3 Comentário de bloco

Delimitado por `(*` e `*)`.

Implementação: manter um contador de profundidade. Incrementar a cada `(*`,
decrementar a cada `*)`, encerrar quando chegar a zero. Uma busca ingênua pelo
primeiro `*)` quebraria em `(* a (* b *) c *)`, deixando ` c *)` como código.

Comentários não podem cruzar fronteiras de arquivo, logo EOF com contador
maior que zero é erro.

### 8.4 Contagem de linhas

O contador deve ser incrementado em todo consumo de `\n`, inclusive dentro
de comentários de bloco e de strings multilinha escapadas. Incrementar apenas
no laço principal produz números errados de forma silenciosa a partir do
primeiro comentário longo.