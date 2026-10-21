# Especificação semântica — COOL

Documento de referência do analisador semântico.

---

## 1. Visão geral

| Item | Escolha |
|------|---------|
| Técnica | Três passadas sobre a AST, escritas manualmente |
| Entrada | Árvore sintática abstrata (`ast.Program`) produzida pelo parser |
| Saída | A mesma AST, com o tipo estático de cada expressão em `expr_type`, e a tabela de classes |
| Travessia das expressões | Padrão *visitor*, com despacho pelo nome do nó |
| Tratamento de erro | Aborta no primeiro erro, lançando `SemanticError` |

A análise sintática verifica se o programa está **bem escrito**. A análise
semântica verifica se ele **faz sentido**: se as classes referenciadas
existem, se a herança forma uma árvore, se os tipos das expressões combinam
com os tipos declarados.

O analisador só recebe árvores completas: `main.py` encerra antes da fase
semântica se houver erro léxico ou sintático.

Toda a fase está em `coolc/semantic.py`, organizada em três partes:

| Parte | Conteúdo |
|-------|----------|
| Módulo | `SemanticError`, constantes, `basic_classes()`, `SymbolTable` |
| `SemanticAnalyzer`, passadas 1 e 2 | Verificações sobre classes e features |
| `SemanticAnalyzer`, ferramentas e passada 3 | `conforms`, `join`, `lookup_method` e as regras `visit_*` |

---

## 2. Estrutura em passadas

COOL permite usar uma classe antes de declará-la. Em

```text
class A inherits B { f(): C { new C }; };
class B { };
class C { };
```

uma travessia única não saberia, ao chegar em `A`, se `B` e `C` existem. A
análise é dividida em passadas, e cada uma só consulta o que as anteriores
já registraram por completo.

| Passada | Métodos | Produz | Depende de |
|---------|---------|--------|------------|
| 1. Classes | `register_classes`, `check_parents`, `check_cycles`, `check_main` | Tabela de classes e grafo de herança válido | nada |
| 2. Features | `collect_features`, `check_feature_types`, `check_inheritance`, `check_main_method` | Tabelas de atributos e métodos por classe | passada 1 |
| 3. Expressões | `check_expressions` e as regras `visit_*` | Tipo estático de cada expressão | passadas 1 e 2 |

A ordem **dentro** de cada passada também é obrigatória. Cada verificação
depende de uma garantia da anterior:

| Verificação | Garantia de que depende |
|-------------|-------------------------|
| `check_parents` | Todas as classes já estão na tabela |
| `check_cycles` | Todo pai existe e nenhum é `None`, exceto o de `Object` |
| `check_main` | Roda por último, para que os exemplos de erro sem `Main` reportem o próprio erro |
| `check_inheritance` | Os tipos das features já foram validados |
| Toda a passada 3 | Sem ciclos: toda subida pela herança termina em `Object` |

---

## 3. Classes básicas

`Object`, `IO`, `Int`, `String` e `Bool` não aparecem no arquivo-fonte, mas
precisam estar na tabela de classes desde o início (manual, 8). Elas são
construídas por `basic_classes()` como nós `ast.Class` sintéticos, iguais aos
que o parser produziria.

| Classe | Pai | Métodos |
|--------|-----|---------|
| `Object` | nenhum | `abort(): Object`, `type_name(): String`, `copy(): SELF_TYPE` |
| `IO` | `Object` | `out_string(x: String): SELF_TYPE`, `out_int(x: Int): SELF_TYPE`, `in_string(): String`, `in_int(): Int` |
| `Int` | `Object` | nenhum |
| `String` | `Object` | `length(): Int`, `concat(s: String): String`, `substr(i: Int, l: Int): String` |
| `Bool` | `Object` | nenhum |

Convenções dos nós sintéticos:

| Campo | Valor | Motivo |
|-------|-------|--------|
| `line` | `BUILTIN_LINE`, igual a `0` | Não vêm do arquivo-fonte |
| `body` dos métodos | `None` | A implementação será escrita na geração de código |
| `parent` | `None` apenas em `Object` | `Object` é a raiz da hierarquia |

Com isso, as passadas tratam uma classe básica e uma classe do usuário com o
mesmo código. A busca de `out_string` em uma subclasse de `IO`, por exemplo,
não tem caso especial.

---

## 4. Passada 1 — classes

### 4.1 Tabela de classes

`self.classes` mapeia o nome de cada classe para o seu nó `ast.Class`. As
classes básicas entram primeiro, e as do programa em seguida, na ordem do
arquivo.

A tabela pertence ao analisador, e não à AST: a árvore continua
representando apenas o que está no arquivo-fonte.

### 4.2 Verificações

| Verificação | Regra | Seção do manual |
|-------------|-------|-----------------|
| Nome `SELF_TYPE` | Nenhuma classe pode se chamar `SELF_TYPE` | 4.1 |
| Redefinição de básica | `class Int { ... }` é proibido | 8 |
| Duplicata | Cada nome de classe é declarado uma única vez | 3 |
| Pai implícito | Sem `inherits`, o pai é `Object` | 3 |
| Pai proibido | Não se herda de `Int`, `String`, `Bool` nem `SELF_TYPE` | 3, 8 e 4.1 |
| Pai inexistente | O pai precisa estar na tabela | 3 |
| Ciclo | A herança precisa formar uma árvore com raiz em `Object` | 3 |
| Classe `Main` | Todo programa tem uma classe `Main` | 9 |

### 4.3 Detecção de ciclos

Para cada classe, `check_cycles` sobe a cadeia de pais anotando as classes
visitadas. Chegar a `Object` encerra a subida sem ciclo. Encontrar uma classe
já visitada indica ciclo.

```text
C → A → B → A      (A repetida: ciclo)
D → IO → Object    (chegou à raiz: sem ciclo)
```

O erro acusa a **primeira classe repetida**, e não a classe em que a subida
começou. No exemplo acima, `C` apenas herda de uma classe do ciclo, sem
pertencer a ele. A primeira classe repetida é a entrada do ciclo, e por isso
sempre faz parte dele.

---

## 5. Passada 2 — features

### 5.1 Tabelas de features

| Tabela | Conteúdo |
|--------|----------|
| `self.attributes[classe]` | Nome do atributo → nó `ast.Attribute` |
| `self.methods[classe]` | Nome do método → nó `ast.Method` |

São duas tabelas porque atributos e métodos ocupam espaços de nomes
distintos: `valor: Int` e `valor(): Int` podem coexistir na mesma classe
(manual, 3.1).

As tabelas guardam apenas as features **declaradas** em cada classe. Features
herdadas são encontradas por busca na cadeia de pais, e nunca copiadas. Essa
separação é o que permite distinguir "declarado aqui" de "herdado" nas
regras de redefinição e na exigência de `main`.

### 5.2 Verificações

| Verificação | Regra | Seção do manual |
|-------------|-------|-----------------|
| Atributo duplicado | Um nome de atributo por classe | 3.1 |
| Método duplicado | Um nome de método por classe | 3.1 |
| Atributo `self` | Nenhum atributo pode se chamar `self` | 7.2 |
| Tipo de atributo | Classe registrada ou `SELF_TYPE` | 4.1 |
| Tipo de retorno | Classe registrada ou `SELF_TYPE` | 4.1 |
| Parâmetro `self` | Nenhum parâmetro pode se chamar `self` | 7.2 |
| Parâmetro duplicado | Nomes de parâmetros distintos no mesmo método | 6 |
| Tipo de parâmetro | Classe registrada; `SELF_TYPE` é proibido | 4.1 |
| Atributo herdado | Um atributo herdado não pode ser redeclarado, nem com o mesmo tipo | 3.2 e 5 |
| Método redefinido | Mesma quantidade de parâmetros, mesmos tipos e mesmo retorno | 6 |
| Método `main` | `Main` **declara** `main()`, sem parâmetros; herdá-lo não basta | 9 |

### 5.3 Redefinição de métodos

A assinatura de um método redefinido é comparada com a do ancestral **mais
próximo** que o declara. A comparação com os ancestrais mais distantes vem
por transitividade.

| Item comparado | Exigência |
|----------------|-----------|
| Quantidade de parâmetros | Igual, testada antes do `zip` |
| Tipo de cada parâmetro | Igual, na mesma posição |
| Tipo de retorno | Igual |
| Nomes dos parâmetros | Livres |

A exigência existe por causa do despacho dinâmico: a passada 3 tipa `x.f()`
pela assinatura de `f` no tipo estático de `x`, mas a execução chama o `f`
da classe real do objeto. Assinaturas idênticas garantem que as duas visões
sejam compatíveis.

---

## 6. Ferramentas de tipo

São funções de consulta usadas pela passada 3. Todas sobem a cadeia de
herança, e todas dependem da ausência de ciclos garantida pela passada 1.

| Função | Pergunta que responde | Seção do manual |
|--------|----------------------|-----------------|
| `conforms(a, b)` | `a ≤ b`? Um valor do tipo `a` pode ser usado onde se espera `b`? | 4 |
| `join(a, b)` | Qual é o menor tipo do qual `a` e `b` são subtipos? | 7.5 |
| `lookup_method(tipo, nome)` | Qual é a definição de `nome` mais próxima, a partir do próprio tipo? | 7.4 |
| `find_inherited(tabela, classe, nome)` | O que a classe herda com esse nome, a partir do pai? | 5 e 6 |

### 6.1 Conformidade

```text
A ≤ A                                  (reflexiva)
se C herda de P, então C ≤ P           (herança direta)
se A ≤ C e C ≤ P, então A ≤ P          (transitiva)        (manual, 4)
```

As três regras se reduzem a uma subida: `a ≤ b` se `b` aparece na cadeia de
pais de `a`, incluindo o próprio `a`. A relação **não é simétrica**:
`conforms(a, b)` pergunta se `a` cabe onde se espera `b`.

### 6.2 Join

O join de dois tipos é o primeiro ancestral de `b` que também é ancestral de
`a`. Como a subida parte de `b` em direção à raiz, o primeiro encontro é o
**menor** ancestral comum.

```text
        Object
       /      \
      A        Main         D ⊔ C    = A
     / \                    D ⊔ B    = B
    B   C                   D ⊔ Main = Object
    |
    D
```

### 6.3 Busca de método

`lookup_method` testa primeiro o próprio tipo e, se não encontrar, delega a
subida a `find_inherited`. A única diferença entre as duas funções é o ponto
de partida, e ela é essencial: se `C` redefine `f`, `lookup_method("C", "f")`
encontra o `f` de `C`, enquanto `find_inherited` encontraria o do pai.

### 6.4 Tabela de símbolos

`SymbolTable` implementa o ambiente de objetos `O` das regras formais
(manual, 12.1) como uma pilha de dicionários.

| Operação | Efeito | Na notação do manual |
|----------|--------|----------------------|
| `enter_scope()` | Empilha um escopo vazio | |
| `add(nome, tipo)` | Declara no escopo do topo | `O[T/x]` |
| `lookup(nome)` | Busca do topo para a base | `O(x)` |
| `exit_scope()` | Desempilha, descartando as declarações | Volta ao ambiente anterior |

A busca do topo para a base implementa o ocultamento sem caso especial: o
nome mais interno sempre vence. Redeclarar um nome em escopo interno é legal
em COOL, por isso a tabela não detecta duplicatas.

---

## 7. Passada 3 — expressões

### 7.1 Notação das regras

As regras de tipo do manual (seção 12.2) têm a forma `O, M, C ⊢ e : T`: no
ambiente de objetos `O`, de métodos `M` e na classe corrente `C`, a
expressão `e` tem tipo `T`.

| Notação | Implementação |
|---------|---------------|
| `O` | `self.symbols` |
| `M` | `self.methods` e `lookup_method` |
| `C` | `self.current_class` |
| `⊢ e : T` | `self.visit(e)` devolve `T` e grava `e.expr_type` |

O tipo é um **atributo sintetizado**: cada regra visita primeiro os filhos e
só depois decide o tipo do nó.

### 7.2 Travessia e escopos

`check_expressions` percorre as classes do programa e monta os escopos na
ordem das regras de visibilidade (manual, 6 e 7.2):

```text
escopo da classe   self : SELF_TYPE, atributos declarados e herdados
  inicializadores de atributo      (veem só esse escopo)
  escopo do método   parâmetros formais, que ocultam atributos
    corpo do método
```

`visit` escolhe a regra pelo nome da classe do nó, com
`getattr(self, f"visit_{type(node).__name__}")`. É a mesma convenção do
`ast.NodeVisitor` da biblioteca padrão. Acrescentar uma regra é escrever um
método novo, sem alterar os existentes.

Os 14 nós de expressão têm regra própria. `visit_default` lança
`NotImplementedError`: chegar a ele é um bug do compilador, e não um erro do
programa COOL.

### 7.3 Regras por construção

| Construção | Regra | Exigências | Tipo resultante |
|------------|-------|------------|-----------------|
| `123` | `[Int]` | | `Int` |
| `"abc"` | `[String]` | | `String` |
| `true`, `false` | `[True]`, `[False]` | | `Bool` |
| `x` | `[Var]` | `x` declarado em algum escopo visível | Tipo declarado de `x` |
| `e1 + e2`, `-`, `*`, `/` | `[Arith]` | Os dois operandos `Int` | `Int` |
| `e1 < e2`, `<=` | `[Compare]` | Os dois operandos `Int` | `Bool` |
| `e1 = e2` | `[Equal]` | Se um lado é `Int`, `String` ou `Bool`, o outro tem o mesmo tipo | `Bool` |
| `~e` | `[Neg]` | Operando `Int` | `Int` |
| `not e` | `[Not]` | Operando `Bool` | `Bool` |
| `isvoid e` | `[Isvoid]` | Operando bem tipado, de qualquer tipo | `Bool` |
| `new T` | `[New]` | `T` existe ou é `SELF_TYPE` | `T` |
| `{ e1; ...; en; }` | `[Sequence]` | | Tipo de `en` |
| `x <- e` | `[ASSIGN]` | `x` declarado, `x ≠ self`, `tipo(e) ≤ tipo(x)` | Tipo de `e` |
| `if c then e1 else e2 fi` | `[If]` | `c` do tipo `Bool` | `tipo(e1) ⊔ tipo(e2)` |
| `while c loop e pool` | `[Loop]` | `c` do tipo `Bool` | `Object` |
| `let x : T <- e1 in e2` | `[Let-Init]` | `T` válido, `x ≠ self`, `tipo(e1) ≤ T` | Tipo de `e2` |
| `case e of x : T => ...; esac` | `[Case]` | Tipos dos ramos distintos, existentes e diferentes de `SELF_TYPE`; `x ≠ self` | Join dos corpos dos ramos |
| `e0.f(e1, ...)` | `[Dispatch]` | `f` existe no tipo de `e0`; argumentos em mesma quantidade e conformes | Retorno de `f`, ou tipo de `e0` se o retorno é `SELF_TYPE` |
| `e0@T.f(e1, ...)` | `[StaticDispatch]` | `T` existe e não é `SELF_TYPE`; `tipo(e0) ≤ T`; `f` existe em `T` | Retorno de `f`, ou tipo de `e0` se o retorno é `SELF_TYPE` |

Duas regras verificam features, e não expressões, e ficam em
`check_expressions`:

| Feature | Regra | Exigência |
|---------|-------|-----------|
| Atributo `x : T <- e` | `[Attr-Init]` | `tipo(e) ≤ T` |
| Método `f(...) : T { e }` | `[Method]` | `tipo(e) ≤ T` |

### 7.4 O `let`

O inicializador de cada variável é tipado **antes** de a variável ser
declarada, e cada variável abre o próprio escopo. Isso traduz a equivalência
do manual entre um `let` com várias variáveis e `let`s aninhados (manual,
12.2):

```text
let x : Int <- 1, y : Int <- x + 1 in y
  é tipado como
let x : Int <- 1 in (let y : Int <- x + 1 in y)
```

Consequências:

| Expressão | Resultado |
|-----------|-----------|
| `let x : Int <- x + 1 in x` | Erro, se não houver outro `x` visível |
| `let x : Int <- 1, y : Int <- x + 1 in y` | Válida: `y` enxerga o `x` do `let` |
| `let x : Int, x : String in x` | Válida: o segundo `x` oculta o primeiro (manual, 7.8) |

### 7.5 O `case`

Cada ramo abre e fecha o próprio escopo, então as variáveis de ramos
diferentes nunca se enxergam. O tipo da expressão examinada não precisa ter
relação com os tipos dos ramos: a escolha do ramo acontece em tempo de
execução, e a ausência de ramo compatível é um erro de execução (manual,
7.9).

### 7.6 Despacho

As três formas usam a mesma regra. O despacho abreviado `f(args)` não tem
caso especial, porque o parser já o transformou em `self.f(args)`.

O retorno `SELF_TYPE` é o que justifica a existência de `SELF_TYPE` (manual,
7.4). Com `B` herdando de `A`:

```text
class A { clone(): SELF_TYPE { new SELF_TYPE }; };

(new B).clone()        tipo B, e não A
(new B)@A.clone()      tipo B: o resultado é o tipo do receptor, e não o T do @
```

---

## 8. SELF_TYPE

`SELF_TYPE` representa a classe do objeto em tempo de execução, que pode ser
qualquer subclasse da classe em que aparece. O manual o define por uma lista
fechada de usos permitidos:

```text
SELF_TYPE may be used in the following places: new SELF_TYPE, as the
return type of a method, as the declared type of a let variable, or as
the declared type of an attribute. No other uses of SELF_TYPE are
permitted.                                                  (manual, 4.1)
```

### 8.1 Posições da gramática

| Posição | Permitido | Onde é verificado |
|---------|-----------|-------------------|
| Nome de classe | Não | `register_classes` |
| `inherits` | Não | `check_parents` |
| Tipo de atributo | Sim | `check_feature_types` |
| Retorno de método | Sim | `check_method_types` |
| Tipo de parâmetro | Não | `check_method_types` |
| Variável de `let` | Sim | `visit_Let` |
| Ramo de `case` | Não | `visit_Case` |
| `new` | Sim | `visit_New` |
| `e@T.f()` | Não | `visit_Dispatch` |

Os quatro usos permitidos passam por `is_valid_type`.

### 8.2 Regras de tipo

| Regra | Comportamento | Implementação |
|-------|---------------|---------------|
| `self` | Tipo `SELF_TYPE_C` | Escopo da classe |
| Conformidade | `SELF_TYPE_C ≤ P` se `C ≤ P`; `T ≤ SELF_TYPE` sempre falso para uma classe `T` | `conforms` |
| Join | `SELF_TYPE_C ⊔ T = C ⊔ T`; `SELF_TYPE_C ⊔ SELF_TYPE_C = SELF_TYPE_C` | `join` |
| Despacho com receptor `SELF_TYPE_C` | O método é procurado em `C` | `visit_Dispatch` |
| Retorno `SELF_TYPE` | O resultado tem o tipo do receptor | `visit_Dispatch` |

`T ≤ SELF_TYPE` ser sempre falso é a regra mais contraintuitiva: em
`p : SELF_TYPE`, atribuir `new Main` é rejeitado mesmo dentro de `Main`,
porque em tempo de execução `self` pode ser uma subclasse de `Main`.

---

## 9. Saída: a AST decorada

Depois da análise, todo nó de expressão tem `expr_type` preenchido. O campo
vem da classe base `Expression`, em `ast.py`, declarado com `kw_only=True`
para não alterar os construtores usados pelo parser.

`print_tree` mostra o tipo inferido entre colchetes, para não confundi-lo
com os tipos **declarados**, que aparecem depois de `:`:

```text
    Method main(): Object  (linha 25)
      Block  (linha 26)  [Int]
        Dispatch .so_b  (linha 27)  [Int]
          receiver:
            Dispatch .clone  (linha 27)  [B]
              receiver:
                New B  (linha 27)  [B]
```

Sobre uma árvore não analisada, `print_tree` produz a mesma saída da fase
sintática, sem colchetes.

---

## 10. Decisões de projeto registradas

**Três passadas.** Elimina o problema da referência adiantada: cada passada
só consulta o que as anteriores registraram por completo.

**Classes básicas como nós sintéticos.** Uniformidade: as passadas tratam
`IO` e uma classe do usuário com o mesmo código (manual, 8).

**Pai implícito gravado na AST.** Classes sem `inherits` passam a ter
`parent = "Object"`, o que elimina o caso `None` de todas as subidas pela
herança. Efeito visível: a árvore impressa mostra `inherits Object`.
Decisão própria.

**Tabelas no analisador, e não na AST.** A AST representa o arquivo-fonte;
as tabelas representam o que a análise concluiu sobre ele.

**Features herdadas por busca, e não por cópia.** Mantém a distinção entre
"declarado aqui" e "herdado", necessária para redefinições e para `main`.

**Ciclo atribuído à classe de entrada.** O manual não define qual classe
reportar. A primeira classe repetida pertence ao ciclo, e a classe de origem
pode não pertencer. Decisão própria.

**Erro de `Main` ausente sem linha.** A ausência de uma classe não ocorre em
nenhuma linha do arquivo. `SemanticError` aceita `line=None`, e `main.py`
omite a linha nesse caso. Decisão própria.

**Mensagem específica para `main` herdado.** O manual exige `main` declarado
em `Main` (manual, 9). Quem herda `main` de outra classe recebe uma mensagem
que explica isso, em vez de "não declara o método".

**Redefinição com nomes de parâmetros diferentes aceita.** O manual exige
quantidade, tipos e retorno iguais (manual, 6), e não menciona os nomes.
Interpretação.

**Visitor por nome.** Substitui a cascata de `isinstance` usada no
`astprinter`, que é anterior a esta decisão e foi mantida.

**Campo `expr_type`, e não `static_type`.** `Dispatch` já tem um campo
`static_type`, que guarda o `T` de `e@T.f()`.

**Um escopo por variável de `let`.** Tradução literal da equivalência com
`let`s aninhados (manual, 12.2).

**`SELF_TYPE` implementado de forma antecipada.** O planejamento previa uma
etapa isolada. Na prática, cada regra de `SELF_TYPE` entrou quando a regra
que a usava foi implementada, porque sem ela programas válidos derrubariam o
compilador. A etapa prevista virou uma revisão da seção 4.1.

**Construção incremental com tolerância temporária.** Durante a
implementação da passada 3, nós ainda sem regra recebiam tipo `None`, e as
verificações sobre `None` eram puladas. A tolerância foi removida quando a
última regra ficou pronta.

**Linha reportada nos erros.** Operando inválido: linha do operando.
Igualdade: linha do operador. Corpo ou inicializador de feature: linha da
feature. Argumento: linha do próprio argumento. Em cada caso, é a linha mais
próxima do problema.

**Aborta no primeiro erro.** Mesma política da análise sintática.

---

## 11. Erros semânticos

Todo erro é um `SemanticError(mensagem, linha)`. `main.py` o imprime como
`Erro semântico na linha N: mensagem`, ou `Erro semântico: mensagem` quando
não há linha. O código de saída é `1`.

Os exemplos estão em `exemplos/`, um arquivo por erro.

### 11.1 Passada 1 — classes

| Situação | Mensagem | Exemplo |
|----------|----------|---------|
| Classe chamada `SELF_TYPE` | `'SELF_TYPE' não pode ser usado como nome de classe` | `erro_classe_self_type.cl` |
| Redefinição de classe básica | `Classe básica 'Int' não pode ser redefinida` | `erro_classe_redefinida.cl` |
| Classe duplicada | `Classe 'A' já foi declarada na linha N` | `erro_classe_duplicada.cl` |
| Pai proibido | `Classe 'A' não pode herdar de 'Bool'` | `erro_pai_proibido.cl`, `erro_pai_self_type.cl` |
| Pai inexistente | `Classe 'A' herda de 'X', que não foi declarada` | `erro_pai_inexistente.cl` |
| Ciclo de herança | `Herança cíclica: a classe 'A' herda de si mesma` | `erro_heranca_ciclica.cl`, `erro_heranca_propria.cl` |
| Sem classe `Main` | `Programa sem classe 'Main'` (sem linha) | `erro_sem_main.cl` |

### 11.2 Passada 2 — features

| Situação | Mensagem | Exemplo |
|----------|----------|---------|
| Método duplicado | `Método 'f' já foi declarado na classe 'A', na linha N` | `erro_metodo_duplicado.cl` |
| Atributo duplicado | `Atributo 'x' já foi declarado na classe 'A', na linha N` | `erro_atributo_duplicado.cl` |
| Atributo `self` | `Atributo não pode se chamar 'self' (classe 'A')` | `erro_atributo_self.cl` |
| Tipo de atributo inexistente | `Atributo 'x' da classe 'A' tem tipo inexistente 'X'` | `erro_tipo_atributo.cl` |
| Tipo de retorno inexistente | `Método 'f' da classe 'A' tem tipo de retorno inexistente 'X'` | `erro_tipo_retorno.cl` |
| Parâmetro `self` | `Parâmetro não pode se chamar 'self' (método 'f')` | `erro_parametro_self.cl` |
| Parâmetro duplicado | `Parâmetro 'a' declarado mais de uma vez no método 'f'` | `erro_parametro_duplicado.cl` |
| Parâmetro `SELF_TYPE` | `Parâmetro 'a' do método 'f' não pode ter tipo 'SELF_TYPE'` | `erro_parametro_self_type.cl` |
| Tipo de parâmetro inexistente | `Parâmetro 'a' do método 'f' tem tipo inexistente 'X'` | `erro_parametro_tipo.cl` |
| Atributo herdado redeclarado | `Atributo 'x' da classe 'B' redefine atributo herdado de 'A'` | `erro_atributo_herdado.cl` |
| Redefinição: quantidade | `Método 'f' redefinido em 'B' com N parâmetro(s), mas declarado em 'A' com M` | `erro_redefinicao_aridade.cl` |
| Redefinição: tipo de parâmetro | `Parâmetro 'x' do método 'f' tem tipo 'T1' em 'B', mas 'T2' em 'A'` | `erro_redefinicao_parametro.cl` |
| Redefinição: retorno | `Método 'f' redefinido em 'B' com retorno 'T1', mas declarado em 'A' com retorno 'T2'` | `erro_redefinicao_retorno.cl`, `erro_redefinicao_usuario.cl` |
| `Main` sem `main` | `Classe 'Main' não declara o método 'main'` | `erro_main_sem_metodo.cl` |
| `main` herdado | `Classe 'Main' herda 'main' de 'A', mas precisa declará-lo` | `erro_main_herdado.cl` |
| `main` com parâmetros | `Método 'main' da classe 'Main' não pode ter parâmetros (declarado com N)` | `erro_main_parametros.cl` |

### 11.3 Passada 3 — expressões e features

| Situação | Mensagem | Exemplo |
|----------|----------|---------|
| Identificador não declarado | `Identificador 'x' não foi declarado` | `erro_identificador_nao_declarado.cl`, `erro_identificador_fora_de_escopo.cl`, `erro_identificador_em_operacao.cl` |
| Operando aritmético ou de comparação | `Operando esquerdo de '+' deve ser do tipo 'Int', mas tem tipo 'T'` | `erro_aritmetica_tipo.cl`, `erro_comparacao_tipo.cl` |
| Igualdade entre tipos incompatíveis | `Comparação '=' entre tipos incompatíveis 'Int' e 'String'` | `erro_igualdade_tipo.cl` |
| Operando de `~` ou `not` | `Operando de '~' deve ser do tipo 'Int', mas tem tipo 'T'` | `erro_negacao_tipo.cl`, `erro_not_tipo.cl` |
| Tipo inexistente em `new` | `Tipo inexistente 'X' em 'new'` | `erro_new_tipo.cl` |
| Atribuição a `self` | `Não é possível atribuir a 'self'` | `erro_atribuicao_self.cl` |
| Atribuição de tipo incompatível | `Atribuição a 'x': tipo 'T1' não conforma com o tipo declarado 'T2'` | `erro_atribuicao_tipo.cl`, `erro_atribuicao_supertipo.cl`, `erro_atribuicao_self_type.cl` |
| Predicado não `Bool` | `Predicado do 'if' deve ser do tipo 'Bool', mas tem tipo 'T'` | `erro_if_predicado.cl`, `erro_while_predicado.cl` |
| Tipo inexistente em `let` | `Variável 'x' do 'let' tem tipo inexistente 'X'` | `erro_let_tipo.cl` |
| `self` em `let` | `'self' não pode ser declarado em 'let'` | `erro_let_self.cl` |
| Inicializador de `let` incompatível | `Variável 'x' do 'let': tipo do inicializador 'T1' não conforma com o tipo declarado 'T2'` | `erro_let_inicializador.cl` |
| `self` em `case` | `'self' não pode ser declarado em ramo de 'case'` | `erro_case_self.cl` |
| Ramo `SELF_TYPE` | `Ramo 'x' do 'case' não pode ter tipo 'SELF_TYPE'` | `erro_case_self_type.cl` |
| Tipo de ramo inexistente | `Ramo 'x' do 'case' tem tipo inexistente 'X'` | `erro_case_tipo_inexistente.cl` |
| Tipo de ramo repetido | `Tipo 'T' repetido em ramos do 'case' (primeiro na linha N)` | `erro_case_tipo_repetido.cl` |
| Despacho estático com `SELF_TYPE` | `Despacho estático não pode usar 'SELF_TYPE'` | `erro_despacho_estatico_self_type.cl` |
| Tipo inexistente no despacho estático | `Tipo inexistente 'X' em despacho estático` | |
| Receptor incompatível com o `@T` | `Despacho estático: tipo do receptor 'T1' não conforma com 'T2'` | `erro_despacho_estatico_receptor.cl` |
| Método inexistente | `Método 'f' não existe na classe 'A'` | `erro_despacho_metodo_inexistente.cl`, `erro_despacho_metodo_basico.cl` |
| Quantidade de argumentos | `Método 'f' espera N argumento(s), mas recebeu M` | `erro_despacho_aridade.cl` |
| Argumento incompatível | `Argumento 'x' de 'f': tipo 'T1' não conforma com 'T2'` | `erro_despacho_argumento.cl` |
| Inicializador de atributo incompatível | `Atributo 'x': tipo do inicializador 'T1' não conforma com o tipo declarado 'T2'` | `erro_atributo_inicializador.cl` |
| Corpo de método incompatível | `Método 'f': tipo do corpo 'T1' não conforma com o retorno declarado 'T2'` | `erro_metodo_retorno.cl`, `erro_metodo_retorno_if.cl`, `erro_metodo_retorno_self_type.cl` |

### 11.4 Programas válidos de referência

| Exemplo | O que demonstra |
|---------|-----------------|
| `escopos.cl` | Parâmetro ocultando atributo herdado |
| `atributo_metodo_mesmo_nome.cl` | Espaços de nomes separados para atributos e métodos |
| `redefinicao_valida.cl` | Redefinição com nomes de parâmetros diferentes |
| `operadores.cl`, `operadores_unarios.cl` | Operadores, incluindo `=` entre objetos e `isvoid 42` |
| `atribuicao.cl` | Atribuição a supertipo e com `SELF_TYPE` |
| `condicionais.cl` | Join entre ramos do `if`, incluindo ramos `Int` e `String` |
| `let.cl` | Variáveis encadeadas e ocultamento em `let` |
| `case.cl` | Join entre ramos do `case` e ocultamento por variável de ramo |
| `despacho.cl` | As três formas de despacho e o retorno `SELF_TYPE` |
| `features_validas.cl` | Inicializadores e retornos que conformam por herança |
| `self_type.cl` | Os quatro usos permitidos de `SELF_TYPE`, consumidos por uma subclasse |