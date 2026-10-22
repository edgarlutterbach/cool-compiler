# 🧊 coolc — Compilador COOL em Python

> Implementação didática de um compilador para a linguagem **COOL** (*Classroom Object-Oriented Language*), escrita do zero em Python puro, com analisador léxico, analisador sintático por descida recursiva que produz uma árvore sintática abstrata (AST) e analisador semântico que verifica o programa e anota o tipo estático de cada expressão.

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![Dependências](https://img.shields.io/badge/depend%C3%AAncias-nenhuma-brightgreen)
![Status](https://img.shields.io/badge/status-em%20desenvolvimento-yellow)

---

## 📖 Sobre o projeto

COOL é uma linguagem orientada a objetos, pequena e fortemente tipada, criada para o ensino de construção de compiladores. Este projeto segue a especificação oficial do [Manual de Referência de COOL](https://theory.stanford.edu/~aiken/software/cool/cool-manual.pdf) e está organizado nas fases clássicas de um compilador:

| Fase | Módulo | Status |
|---|---|---|
| Análise léxica | `coolc/lexer.py` | ✅ Concluída |
| Análise sintática | `coolc/parser.py` | ✅ Concluída |
| Análise semântica | `coolc/semantic.py` | ✅ Concluída |
| Geração de código (BRIL) | — | 🚧 Planejada |

---

## ✨ Funcionalidades

### 🔤 Analisador léxico

- Reconhecimento das 17 palavras reservadas de COOL, insensíveis a maiúsculas (`class`, `CLASS` e `cLaSs` são o mesmo token).
- Tratamento de `true` e `false` como literais, e não como palavras reservadas: exigem apenas a primeira letra minúscula e são emitidos como `BOOL_CONST` com valor.
- Distinção entre `TYPEID` (inicial maiúscula) e `OBJECTID` (inicial minúscula).
- Literais inteiros armazenados já convertidos para `int`, com suporte a zeros à esquerda (`007`).
- Literais de string com escapes resolvidos na tokenização (`\b`, `\t`, `\n`, `\f` e a regra geral `\c` → `c`), incluindo strings multilinha com `\` + quebra de linha.
- Comentários de linha (`--`) e comentários de bloco (`(* ... *)`) com **aninhamento arbitrário**, controlado por contador de profundidade.
- *Maximal munch* para operadores conflitantes: `<-`, `<=`, `<`, `=>`, `=`.
- Contagem de linhas precisa, inclusive dentro de comentários e strings multilinha.
- Emissão de tokens `ERROR` com mensagem descritiva e número da linha, para:
  - caractere inválido;
  - identificador iniciado por `_`;
  - quebra de linha não escapada, caractere nulo ou EOF dentro de string;
  - string com mais de 1024 caracteres;
  - comentário de bloco não fechado ou `*)` sem abertura correspondente.

### 🌳 Analisador sintático

- Parser por **descida recursiva**, com uma função por regra da gramática.
- Lookahead de um token na maior parte da gramática e de dois tokens para distinguir atribuição (`x <- expr`) de outras expressões.
- Cobertura completa da gramática de expressões: `if`, `while`, `case`, `let`, blocos, `new`, `isvoid`, `not`, `~`, operadores aritméticos e relacionais, atribuição e os três tipos de despacho (dinâmico, estático com `@` e abreviado com `self` implícito).
- Precedência de operadores codificada pelo encadeamento das regras, conforme a seção 11.1 do manual.
- Associatividade à esquerda para operadores binários, obtida pela eliminação da recursão à esquerda (`1 - 2 - 3` → `(1 - 2) - 3`).
- Validação de restrições estruturais: programa vazio, bloco vazio, `case` sem ramos e `let` sem declarações são rejeitados.
- Mensagens de erro legíveis, com o token esperado e o encontrado (ex.: `Esperado 'else', encontrado 'fi'`).

### 🧠 Analisador semântico

- Análise em **três passadas** sobre a AST, o que permite usar uma classe antes de declará-la:
  1. **Classes:** tabela de classes, classes básicas, validação de herança, detecção de ciclos e exigência da classe `Main`.
  2. **Features:** atributos e métodos de cada classe, tipos declarados, redefinição de métodos herdados e exigência de `main()` em `Main`.
  3. **Expressões:** verificação de tipos de todas as expressões, segundo as regras formais da seção 12 do manual.
- Classes básicas `Object`, `IO`, `Int`, `String` e `Bool` disponíveis em todo programa, com as assinaturas da seção 8 do manual.
- Relação de **conformidade** (`A ≤ B`) e **join** (menor ancestral comum), usados em atribuições, argumentos, retornos, `if` e `case`.
- Tabela de símbolos com **escopos aninhados**, incluindo ocultamento de atributos por parâmetros, variáveis de `let` e variáveis de `case`.
- Tratamento completo de **`SELF_TYPE`**: usos permitidos e proibidos da seção 4.1 e regras especiais de conformidade, join e despacho. Em `(new B).clone()`, com `clone(): SELF_TYPE` declarado em uma classe ancestral, o tipo inferido é `B`.
- Travessia das expressões pelo padrão *visitor*, com uma regra de tipo para cada nó.
- Mensagens de erro com a linha mais próxima do problema e o motivo da rejeição (ex.: `Atribuição a 'b': tipo 'A' não conforma com o tipo declarado 'B'`).

### 🖨️ Visualização da AST

- Impressão indentada da árvore sintática, com número da linha de origem de cada construção relevante.
- Após a análise semântica, cada expressão exibe o seu **tipo estático** entre colchetes, como `[Int]`, distinto dos tipos declarados no código, que aparecem após `:`.

---

## 🛠️ Tecnologias utilizadas

| Tecnologia | Uso |
|---|---|
| 🐍 **Python 3.10+** | Linguagem de implementação |
| 📦 `dataclasses` | Definição dos tokens e dos nós da AST |
| 🏷️ `enum` | Enumeração dos tipos de token |
| 🔡 `string` | Conjuntos de caracteres do analisador léxico |

O projeto utiliza **somente a biblioteca padrão do Python**. Nenhum gerador de analisadores (como Flex, Bison, PLY ou ANTLR) foi usado: as três fases foram escritas manualmente.

---

## 📋 Pré-requisitos

- **Python 3.10 ou superior** — obrigatório, pois o código usa a sintaxe de união de tipos com `|` (ex.: `int | str | None`) nas anotações das dataclasses e o parâmetro `kw_only` de `dataclasses.field`.
- **Git** — para clonar o repositório.

Verifique sua versão do Python com:

```bash
python --version
```

---

## 🚀 Como rodar o projeto

### 1. Clonar o repositório

```bash
git clone https://github.com/edgarlutterbach/cool-compiler.git
cd cool-compiler
```

### 2. (Opcional) Criar um ambiente virtual

Como não há dependências externas, este passo é opcional, mas recomendado para manter o ambiente isolado.

```bash
python -m venv .venv

# Linux / macOS
source .venv/bin/activate

# Windows (PowerShell)
.venv\Scripts\Activate.ps1
```

### 3. Instalar dependências

Não há dependências a instalar. 🎉

### 4. Executar o compilador

O ponto de entrada é o módulo `coolc.main`, que recebe o caminho de um arquivo `.cl`. Execute a partir da raiz do repositório:

```bash
python -m coolc.main exemplos/teste_parser.cl
```

O arquivo passa pelas análises léxica, sintática e semântica, e a árvore é impressa com o tipo estático de cada expressão. Saída esperada:

```text
Program
  Class Main inherits Object  (linha 1)
    Attribute x: Int  (linha 2)
      Int 42  [Int]
    Attribute nome: String  (linha 3)
      String 'teste'  [String]
    Attribute flag: Bool  (linha 4)
    Method f(a: Int, b: Int): Int  (linha 5)
      Identifier a  [Int]
    Method g(): Object  (linha 6)
      Identifier flag  [Bool]
    Method main(): Object  (linha 7)
      Int 0  [Int]
  Class Segunda inherits Main  (linha 10)
    Method h(): Int  (linha 11)
      Int 1  [Int]
```

Duas marcas vêm da análise semântica: `inherits Object`, preenchido nas classes sem `inherits` explícito, e os tipos entre colchetes.

### 5. Demonstrações da análise semântica

Cinco exemplos reúnem as principais verificações da fase. O cabeçalho de cada arquivo descreve o que ele demonstra e o resultado esperado.

```bash
# Herança, redefinição, despacho dinâmico e estático, case, join e SELF_TYPE
python -m coolc.main exemplos/demo1_zoologico.cl

# Lista encadeada: tipo recursivo e uso de uma classe antes da sua declaração
python -m coolc.main exemplos/demo2_lista.cl

# Escopos: o mesmo nome como atributo, parâmetro, variável de let e de case
python -m coolc.main exemplos/demo3_escopos.cl

# Erro: redefinição de out_string, herdado de IO, com assinatura diferente
python -m coolc.main exemplos/demo4_erro_redefinicao.cl

# Erro: método com retorno SELF_TYPE que devolve new Conta
python -m coolc.main exemplos/demo5_erro_self_type.cl
```

### ⚠️ Tratamento de erros

Em caso de erro, o compilador informa a fase, a linha e a causa, encerrando com código de saída `1`. Cada fase só é executada se a anterior não encontrou erros.

```text
Erro léxico na linha 3: String não foi fechada
```

```text
Erro de sintaxe na linha 5: Esperado 'else', encontrado 'fi'
```

```text
Erro semântico na linha 6: Atribuição a 'b': tipo 'A' não conforma com o tipo declarado 'B'
```

Erros que não pertencem a uma linha específica são informados sem o número:

```text
Erro semântico: Programa sem classe 'Main'
```

---

## 🔐 Variáveis de ambiente

**Não aplicável.** O projeto não utiliza arquivo `.env` nem depende de variáveis de ambiente. Toda a entrada é fornecida pelo arquivo `.cl` passado na linha de comando.

---

## 📁 Estrutura do projeto

```text
cool-compiler/
├── coolc/
│   ├── tokens.py       # tipos de token, estrutura Token, tabela de reservadas
│   ├── lexer.py        # analisador léxico
│   ├── ast.py          # nós da árvore sintática abstrata
│   ├── parser.py       # analisador sintático
│   ├── semantic.py     # analisador semântico
│   ├── astprinter.py   # impressão indentada da árvore
│   └── main.py         # ponto de entrada da linha de comando
├── docs/
│   ├── tokens.md       # especificação léxica
│   ├── parser.md       # especificação sintática
│   └── semantic.md     # especificação semântica
└── exemplos/
    ├── demo*.cl        # demonstrações da análise semântica
    ├── erro_*.cl       # um programa para cada erro semântico
    └── *.cl            # programas válidos de teste
```

---

## 📚 Documentação

As decisões de projeto e as especificações de cada fase estão documentadas em detalhe:

- 📄 [`docs/tokens.md`](docs/tokens.md) — especificação léxica: tokens, literais, escapes, comentários e decisões registradas.
- 📄 [`docs/parser.md`](docs/parser.md) — especificação sintática: gramática, transformações aplicadas e tabela de precedência.
- 📄 [`docs/semantic.md`](docs/semantic.md) — especificação semântica: passadas, regras de tipo, `SELF_TYPE`, decisões registradas e tabela de erros.
- 🔗 [Manual de Referência de COOL (Stanford)](https://theory.stanford.edu/~aiken/software/cool/cool-manual.pdf) — especificação oficial da linguagem.