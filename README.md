# Compilador COOL

Compilador para a linguagem COOL, desenvolvido em Python para a disciplina de 
Compiladores da UFF — Campus de Rio das Ostras.

O objetivo final é traduzir código COOL para BRIL, uma representação intermediária 
que permite execução e otimização do programa original.

---

## Como executar

Requer Python 3.10 ou superior. O projeto não possui dependências externas.

```bash
python -m coolc.main exemplos/cobertura.cl
```

A saída é a árvore sintática abstrata em formato indentado, com dois espaços
por nível de aninhamento:

```
Program
  Class Cobertura inherits IO  (linha 7)
    Method aritmetica(): Int  (linha 24)
      BinOp '-'
        BinOp '+'
          Identifier zero
          Identifier normal
        BinOp '/'
          BinOp '*'
            Identifier com_zeros
            Int 2
          Int 1
```

Erros léxicos são relatados antes da análise sintática e interrompem a
execução: não faz sentido montar uma árvore a partir de tokens inválidos.

---

## Estrutura do projeto

```
cool-compiler/
├── coolc/
│   ├── tokens.py       # tipos de token, estrutura Token, tabela de reservadas
│   ├── lexer.py        # analisador léxico
│   ├── ast.py          # nós da árvore sintática abstrata
│   ├── parser.py       # analisador sintático
│   ├── astprinter.py   # impressão indentada da árvore
│   └── main.py         # ponto de entrada da linha de comando
├── docs/
│   ├── tokens.md       # especificação léxica
│   └── parser.md       # especificação sintática
├── exemplos/           # programas COOL de teste
└── tests/
```

---

## Fase 1 — Análise léxica

### `tokens.py`

Define o vocabulário do analisador:

- **`TokenType`** — enum com os 43 tipos de token.
- **`Token`** — `dataclass` imutável (`frozen=True`) com tipo, linha e valor
  opcional.
- **`KEYWORDS`** — dicionário das 17 palavras reservadas que geram token sem
  valor.
- **`describe`** — converte um tipo de token em texto legível para mensagens
  de erro, exibindo `';'` em vez de `SEMI`.

### `lexer.py`

Analisador escrito manualmente, sem gerador. A classe `Lexer` mantém três
campos de estado — texto, posição e linha — mais a linha de início do token
corrente.

Quatro primitivas isolam todo o acesso à posição:

| Primitiva | Função |
|---|---|
| `at_end()` | A posição ultrapassou o fim do texto? |
| `peek(offset)` | Olha um caractere adiante **sem consumir** |
| `advance()` | Consome e devolve o caractere atual |
| `match(char)` | Consome apenas se o caractere for o esperado |

Nenhum outro método toca a posição diretamente. Isso garante duas invariantes:
a contagem de linhas nunca dessincroniza, e o retrocesso é impossível por
construção.

### Pontos técnicos

**Comentários de bloco aninhados.** COOL permite aninhamento em `(* ... *)`,
diferente de C. Uma busca ingênua pelo primeiro `*)` quebraria em
`(* a (* b *) c *)`. A implementação mantém um contador de profundidade,
encerrando apenas quando ele retorna a zero.

**Contagem de linha centralizada.** O incremento ocorre exclusivamente dentro
de `advance()`. Como todo consumo de caractere passa por ali — inclusive
dentro de comentários e de strings multilinha — a contagem permanece correta
sem verificações espalhadas pelo código.

**Maximal munch.** Reconhece-se sempre o maior lexema possível a partir da
posição atual, implementado pela separação entre `peek` e `advance`. Resolve
os conflitos `<` / `<-` / `<=`, `=` / `=>`, `-` / `--`, `(` / `(*` e
`*` / `*)`. O mesmo princípio explica por que o identificador é consumido por
completo antes da consulta à tabela de reservadas: `CLASS_maiusculo` é um
identificador de tipo, não `class` seguido de `_maiusculo`.

---

## Fase 2 — Análise sintática

Implementada por **descida recursiva**, mantendo a abordagem manual da fase
anterior. Cada regra da gramática corresponde a um método, e a recursão mútua
entre eles reproduz a estrutura da gramática.

### `ast.py`

Dezoito tipos de nó, todos `dataclass` sem comportamento.

### `parser.py`

A classe `Parser` mantém a lista de tokens e a posição. As primitivas são
análogas às do lexer, um nível acima — operam sobre tokens em vez de
caracteres:

| Primitiva | Função |
|---|---|
| `peek(offset)` | Token atual ou adiante, **sem consumir** |
| `advance()` | Consome e devolve o token atual |
| `check(tipo)` | O token atual é deste tipo? |
| `expect(tipo)` | Consome o token exigido, ou falha |

A divisão entre `check` e `expect` é deliberada: `check` **pergunta**, para
escolher entre alternativas ou detectar construções opcionais; `expect`
**exige**, nas partes que a gramática determina como fixas.

### Cadeia de precedência

Não há tabela de precedência no código. A precedência resulta do
encadeamento das regras: operadores mais fracos ficam nas regras mais externas
e, portanto, mais próximos da raiz da árvore. Como a avaliação ocorre de baixo
para cima, o que está mais interno é avaliado primeiro.

```
parse_expr                      <-              (mais fraco)
  parse_not                     not
    parse_comparison            < <= =
      parse_arith               + -
        parse_term              * /
          parse_isvoid          isvoid
            parse_neg           ~
              parse_dispatch    . @   (mais forte)
                parse_atom
```

### Transformações sobre a gramática do manual

Três ajustes foram necessários:

**Eliminação da recursão à esquerda.** Regras como `expr ::= expr + term`
produziriam uma função cuja primeira ação é chamar a si mesma sem consumir
token algum. A reescrita troca a recursão por um laço, e o nó acumulado
torna-se o filho esquerdo do novo nó — é isso que produz associatividade à
esquerda.

**Comparações não associam.** O manual determina que `<`, `<=` e `=` não
associam, então `1 < 2 < 3` é inválido. A regra correspondente usa `if` em vez
de `while`.

**Fatoração à esquerda em `feature`.** As duas alternativas — método e
atributo — começam com `OBJECTID`. Consumindo o prefixo comum antes da
decisão, o lookahead de dois tokens vira um teste simples sobre o token
seguinte.

### A ambiguidade do `let`

O manual determina que o corpo de um `let` se estende o mais à direita
possível. Em `let x: Int <- 1 in let y: Int <- 2 in x + y`, o corpo do
primeiro `let` é o segundo por inteiro.

**Na descida recursiva resolve-se sozinho**: a função que trata o corpo
chama a regra de expressão mais externa, que naturalmente consome o 
máximo possível.

---

## Decisões de projeto

As especificações completas estão em [`docs/tokens.md`](docs/tokens.md) e
[`docs/parser.md`](docs/parser.md). As decisões abaixo são as que exigiram
julgamento além do que o manual define.

### Booleanos são literais, não palavras reservadas

O manual lista 19 palavras reservadas, incluindo `true` e `false`. Este
projeto emite 17 tokens de reservada; os booleanos geram `BOOL_CONST`
carregando o valor.

Justificativa: na Figura 1 do manual, `true` e `false` aparecem como
alternativas de `expr`, ao lado de `integer` e `string` — como valores, não
como estrutura. Um token com valor evita duplicar regras na análise sintática.

A regra especial de maiúsculas é preservada: apenas a primeira letra precisa
ser minúscula, de modo que `tRuE` é booleano e `True` é identificador de tipo.

### Strings são armazenadas já interpretadas

As sequências de escape são resolvidas na tokenização. O literal `"a\nb"`
produz um valor de três caracteres.

Justificativa: adiar significa reprocessar a string quando o contexto de
posição no arquivo já se perdeu e erros de escape não podem mais ser
localizados. Como consequência, o limite de 1024 caracteres é aferido sobre o
texto interpretado — o manual não esclarece qual dos dois vale.

### Um nó para todas as operações binárias

`BinOperation` carrega o operador como campo, em vez de sete classes
distintas. As regras de tipo são idênticas dentro de cada grupo, e separá-las
duplicaria código na análise semântica e na geração de código.

### Despacho abreviado na AST

`metodo(a, b)` é registrado como despacho dinâmico com `self` como receptor,
conforme o manual define. A alternativa obrigaria as fases seguintes a
tratar dois casos equivalentes.

### Parênteses não geram nó

`(1 + 2) * 3` e `1 + 2 * 3` produzem árvores diferentes, mas em nenhuma delas
existe um nó de parêntese: a diferença está na forma, não no conteúdo.

### Políticas de erro distintas por fase

**Léxico: recuperação.** O analisador não interrompe no primeiro erro. Emite
um token `ERROR` com mensagem e linha, avança até um ponto de retomada seguro
e continua, permitindo relatar vários problemas por execução. Os pontos de
retomada variam conforme o erro:

| Erro | Retomada |
|---|---|
| Caractere inválido | O caractere já foi consumido |
| Identificador iniciado por `_` | O lexema já foi consumido |
| Comentário ou string não fechados | Fim do arquivo |
| Caractere nulo ou limite de tamanho em string | Descarta até a aspa de fechamento |
| Quebra de linha não escapada em string | Não descarta nada |

**Sintático: aborto no primeiro erro.**

### Ambiguidade do caractere nulo

O manual afirma que uma string não pode conter *the null (character `\0`)*, o
que admite duas leituras: o byte nulo literal ou a sequência de escape. Pela
regra geral do próprio manual, `\0` produziria o caractere `0`.

Decisão adotada: apenas o byte nulo literal é erro. Ponto a confirmar.

### Fechamento de comentário sem abertura

O manual não define o comportamento de um `*)` isolado. Tratado como erro
léxico, por decisão própria.

---

## Abordagem manual

Este projeto adota a implementação manual nas duas fases. A gramática
declarativa transfere o reconhecimento para uma tabela LALR gerada — um
artefato que não se lê e cujos conflitos são difíceis de diagnosticar sem
teoria de parsing. Escrever o reconhecedor à mão custa mais digitação, mas
mantém controle sobre mensagens de erro, recuperação e formato da saída.

---

## Referências

- Aiken, A. *The Cool Reference Manual*.