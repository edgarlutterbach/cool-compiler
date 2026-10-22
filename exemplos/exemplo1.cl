(*
 * Demonstração 1: herança, redefinição e despacho
 *
 * Mostra: hierarquia de classes, redefinição de métodos com a mesma
 * assinatura, despacho dinâmico e estático (@), case por tipo, join
 * entre ramos do if e métodos que retornam SELF_TYPE.
 *
 * Resultado esperado: árvore impressa, sem erro.
 *)

class Animal inherits IO {
    nome: String <- "animal";

    -- Retorna SELF_TYPE: chamado sobre um Cachorro, devolve um Cachorro
    nomear(n: String): SELF_TYPE {
        {
            nome <- n;
            self;
        }
    };

    som(): String { "..." };

    apresentar(): SELF_TYPE {
        out_string(nome.concat(" faz ").concat(som()).concat("\n"))
    };
};

class Cachorro inherits Animal {
    -- Redefinição com assinatura idêntica à de Animal
    som(): String { "au" };

    buscar(): String { "bolinha" };
};

class Gato inherits Animal {
    som(): String { "miau" };
};

class Main inherits IO {
    -- O ramo escolhido depende do tipo dinâmico de a
    descrever(a: Animal): String {
        case a of
            c: Cachorro => "um cachorro que busca a ".concat(c.buscar());
            g: Gato => "um gato";
            x: Animal => "um animal qualquer";
        esac
    };

    main(): Object {
        let rex: Cachorro <- (new Cachorro).nomear("Rex"),
            mia: Gato <- (new Gato).nomear("Mia"),
            -- Cachorro ⊔ Gato = Animal
            escolhido: Animal <- if rex.som() = "au" then rex else mia fi
        in
            {
                rex.apresentar();
                mia.apresentar();
                out_string(descrever(escolhido).concat("\n"));
                -- Despacho estático: usa o som() de Animal, e não o de Cachorro
                out_string(rex@Animal.som().concat("\n"));
            }
    };
};
