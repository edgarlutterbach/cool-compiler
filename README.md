# 🧊 coolc — Compilador COOL em Python

> Implementação didática de um compilador para a linguagem **COOL** (*Classroom Object-Oriented Language*), escrita do zero em Python puro, com analisador léxico e analisador sintático por descida recursiva que produz uma árvore sintática abstrata (AST).

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
| Análise semântica | — | 🚧 Planejada |
| Geração de código | — | 🚧 Planejada |

---

## ✨ Funcionalidades

### 🔤 Analisador léxico

- Reconhecimento das 19 palavras reservadas de COOL, insensíveis a maiúsculas (`class`, `CLASS` e `cLaSs` são o mesmo token).
- Tratamento especial de `true` e `false`, que exigem apenas a primeira letra minúscula e são emitidos como `BOOL_CONST` com valor.
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

### 🖨️ Visualização da AST

- Impressão indentada da árvore sintática, com número da linha de origem de cada construção relevante.

---

## 🛠️ Tecnologias utilizadas

| Tecnologia | Uso |
|---|---|
| 🐍 **Python 3.10+** | Linguagem de implementação |
| 📦 `dataclasses` | Definição dos tokens e dos nós da AST |
| 🏷️ `enum` | Enumeração dos tipos de token |
| 🔡 `string` | Conjuntos de caracteres do analisador léxico |

O projeto utiliza **somente a biblioteca padrão do Python**. Nenhum gerador de analisadores (como Flex, Bison, PLY ou ANTLR) foi usado: léxico e sintático foram escritos manualmente.

---

## 📋 Pré-requisitos

- **Python 3.10 ou superior** — obrigatório, pois o código usa a sintaxe de união de tipos com `|` (ex.: `int | str | None`) nas anotações das dataclasses.
- **Git** — para clonar o repositório.

Verifique sua versão do Python com:

```bash
python --version
```

---

## 🚀 Como rodar o projeto

### 1. Clonar o repositório

```bash
git clone https://github.com/<seu-usuario>/cool-compiler.git
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

Saída esperada:

```text
Program
  Class Main  (linha 1)
    Attribute x: Int  (linha 2)
      Int 42
    Attribute nome: String  (linha 3)
      String 'teste'
    Attribute flag: Bool  (linha 4)
    Method f(a: Int, b: Int): Int  (linha 5)
      Identifier a
    Method g(): Object  (linha 6)
      Identifier flag
  Class Segunda inherits Main  (linha 9)
    Method h(): Int  (linha 10)
      Int 1
```

### 5. Outros exemplos

```bash
# Programa interativo clássico com let, blocos e despacho
python -m coolc.main exemplos/hello.cl

# Arquivo de cobertura: comentários aninhados, escapes, case, while, despacho estático
python -m coolc.main exemplos/cobertura.cl
```

### ⚠️ Tratamento de erros

Em caso de erro, o compilador informa a fase, a linha e a causa, encerrando com código de saída `1`:

```text
Erro léxico na linha 3: String não foi fechada
```

```text
Erro de sintaxe na linha 5: Esperado 'else', encontrado 'fi'
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
│   ├── astprinter.py   # impressão indentada da árvore
│   └── main.py         # ponto de entrada da linha de comando
├── docs/
│   ├── tokens.md       # especificação léxica
│   └── parser.md       # especificação sintática
├── exemplos/           # programas COOL de teste
└── tests/              # testes automatizados (em construção)
```

---

## 📚 Documentação

As decisões de projeto e as especificações de cada fase estão documentadas em detalhe:

- 📄 [`docs/tokens.md`](docs/tokens.md) — especificação léxica: tokens, literais, escapes, comentários e decisões registradas.
- 📄 [`docs/parser.md`](docs/parser.md) — especificação sintática: gramática, transformações aplicadas e tabela de precedência.
- 🔗 [Manual de Referência de COOL (Stanford)](https://theory.stanford.edu/~aiken/software/cool/cool-manual.pdf) — especificação oficial da linguagem.