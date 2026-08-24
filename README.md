# Compilador COOL

Compilador para a linguagem COOL (*Classroom Object-Oriented Language*),
desenvolvido em Python para a disciplina de Compiladores da UFF.

O objetivo final é traduzir código COOL para BRIL (*Big Red Intermediate
Language*), uma representação intermediária que permite execução e otimização
do programa original.

---

## Como executar

Requer Python 3.10 ou superior. O projeto não possui dependências externas.

```bash
python -m coolc.main exemplos/hello.cl
```

A saída é a lista de tokens reconhecidos, um por bloco, no formato:

```
TYPEID
     Valor: 'Main'
     Linha: 1
```

Tokens que não carregam valor (palavras reservadas, operadores, separadores)
omitem a linha `Valor`.

---

## Estrutura do projeto

```
cool-compiler/
├── coolc/
│   ├── tokens.py    # tipos de token, estrutura Token, tabela de reservadas
│   ├── lexer.py     # o analisador léxico
│   └── main.py      # ponto de entrada da linha de comando
├── docs/
│   └── tokens.md    # especificação léxica completa
├── exemplos/        # programas COOL de teste
└── tests/
```

### `tokens.py`

Define o vocabulário do analisador. Três elementos:

- **`TokenType`** — enum com os 43 tipos de token..
- **`Token`** — `dataclass` imutável (`frozen=True`) com tipo, linha e valor
  opcional.
- **`KEYWORDS`** — dicionário das 17 palavras reservadas que geram token sem
  valor, mapeando o lexema em minúsculas para o tipo correspondente.

### `lexer.py`

Analisador léxico escrito manualmente, sem gerador de parser. A classe `Lexer`
mantém três campos de estado — o texto, a posição e a linha atual — mais um
campo auxiliar com a linha de início do token corrente.

Quatro primitivas de navegação isolam todo o acesso à posição:

| Primitiva | Função |
|---|---|
| `at_end()` | A posição ultrapassou o fim do texto? |
| `peek(offset)` | Olha um caractere adiante sem consumir |
| `advance()` | Consome e devolve o caractere atual |
| `match(char)` | Consome apenas se o caractere for o esperado |

Nenhum outro método toca a posição diretamente. Isso garante duas invariantes:
a contagem de linhas nunca dessincroniza, e o retrocesso é impossível por
construção.

O ponto de entrada é `next_token()`, que descarta espaço em branco e
comentários, registra a linha inicial e despacha para uma de quatro
sub-rotinas conforme o primeiro caractere. `tokenize()` roda esse ciclo até o
token `EOF`.

---

## Decisões de projeto

A especificação léxica completa, conferida linha a linha contra o *Cool
Reference Manual* de Alex Aiken, está em [`docs/tokens.md`](docs/tokens.md).
As decisões abaixo são as que exigiram julgamento além do que o manual define.

### Booleanos são literais, não palavras reservadas

O manual lista 19 palavras reservadas, incluindo `true` e `false`. Este
projeto emite apenas 17 tokens de palavra reservada; os dois booleanos geram
`BOOL_CONST` carregando o valor `True` ou `False`.

Justificativa: na gramática do manual, `true` e `false` aparecem
como alternativas de `expr`, na mesma lista que `integer` e `string` — nunca
como marcação estrutural equivalente a `if` ou `class`. Um único token com
valor evita duplicar regras na análise sintática.

A regra especial de maiúsculas dos booleanos é preservada: apenas a primeira
letra precisa ser minúscula, de modo que `tRuE` é um booleano e `True` é um
identificador de tipo.

### Strings são armazenadas já interpretadas

As sequências de escape são resolvidas no momento da tokenização. O literal
`"a\nb"` produz um valor de três caracteres, com quebra de linha real.

Justificativa: os escapes precisam ser resolvidos em algum ponto antes da
geração de código. Adiar significa reprocessar a string mais tarde, quando o
contexto de posição no arquivo já se perdeu e erros de escape não podem mais
ser localizados.

Como consequência, o limite de 1024 caracteres é aferido sobre o texto
interpretado, não sobre o texto bruto.

### Recuperação de erro em vez de aborto

O analisador não interrompe a execução no primeiro erro léxico. Ele emite um
token `ERROR` com mensagem e linha, avança até um ponto de retomada seguro e
continua, permitindo relatar vários problemas em uma única execução.

Internamente, os pontos de falha levantam uma exceção `LexicalError`,
capturada em `next_token()`. Isso mantém o caminho normal livre de
verificações e concentra o tratamento em um único lugar.

Os pontos de retomada variam conforme o erro, porque erros diferentes indicam
intenções diferentes:

| Erro | Retomada |
|---|---|
| Caractere inválido | O caractere já foi consumido |
| Identificador iniciado por `_` | O lexema já foi consumido |
| Comentário ou string não fechados | Fim do arquivo |
| Caractere nulo ou limite de tamanho em string | Descarta até a aspa de fechamento |
| Quebra de linha não escapada em string | **Não descarta nada** |

O último caso é deliberado: uma quebra de linha não escapada quase sempre
significa aspa de fechamento esquecida, e o texto seguinte é código válido.
Descartá-lo até a próxima aspa engoliria programa legítimo.

### Ambiguidade do caractere nulo

O manual afirma que uma string não pode conter the null (character `\0`), o
que admite duas leituras: o byte nulo literal ou a sequência de escape `\0`.
Pela regra geral do próprio manual, `\0` deveria produzir o caractere `0`.

Decisão adotada: apenas o byte nulo literal é erro; a sequência `\0` segue a
regra geral.

### Fechamento de comentário sem abertura

O manual não define o comportamento de um `*)` isolado. Este projeto o trata
como erro léxico, por decisão própria.

---

## Pontos técnicos de destaque

**Comentários de bloco aninhados.** COOL permite aninhamento em `(* ... *)`,
diferente de C. Uma busca ingênua pelo primeiro `*)` quebraria em
`(* a (* b *) c *)`, deixando ` c *)` como código. A implementação mantém um
contador de profundidade, encerrando apenas quando ele retorna a zero.

**Contagem de linha centralizada.** O incremento de `self.line` ocorre
exclusivamente dentro de `advance()`. Como todo consumo de caractere passa por
ali — inclusive dentro de comentários e de strings multilinha — a contagem
permanece correta sem verificações espalhadas pelo código.

**Maximal munch.** Sempre se reconhece o maior lexema possível a partir da
posição atual. Isso é implementado pela separação entre `peek` (inspeciona) e
`advance` (consome), permitindo decidir antes de se comprometer. Resolve os
conflitos `<` / `<-` / `<=`, `=` / `=>`, `-` / `--`, `(` / `(*` e `*` / `*)`.

O mesmo princípio explica por que o identificador é consumido por completo
antes de consultar a tabela de palavras reservadas: `CLASS_maiusculo` é um
identificador de tipo, não a palavra `class` seguida de `_maiusculo`.

---

## Abordagem manual

É permitido tanto a implementação manual quanto o uso de geradores
automáticos de parser (da família lex/yacc, cujos equivalentes em Python são
PLY, SLY, Lark e ANTLR).

Este projeto adota a implementação manual. A justificativa é que a gramática
declarativa transfere o reconhecimento para uma tabela LALR gerada — um
artefato que não se lê e cujos conflitos são difíceis de diagnosticar sem
teoria de parsing. Escrever o autômato à mão custa mais digitação, mas mantém
controle total sobre mensagens de erro, recuperação e formato da saída.

---

## Próximas fases

| Fase | Estado |
|---|---|
| Análise léxica | Concluída |
| Análise sintática | Pendente |
| Análise semântica | Pendente |
| Geração de código BRIL | Pendente |

---

## Referências

- Aiken, A. *The Cool Reference Manual*.