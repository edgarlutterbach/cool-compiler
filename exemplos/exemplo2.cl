(*
 * Demonstração 2: estrutura recursiva e referência adiantada
 *
 * Mostra: a classe Lista usa No antes de No ser declarada, o que só é
 * possível porque a análise é feita em passadas; tipos recursivos;
 * while, not, let e atribuição com subtipo.
 *
 * Resultado esperado: árvore impressa, sem erro.
 *)

class Lista {
    vazia(): Bool { true };

    cabeca(): Int { { abort(); 0; } };

    cauda(): Lista { { abort(); self; } };

    -- No é usada aqui, mas só é declarada abaixo
    adicionar(i: Int): Lista { (new No).iniciar(i, self) };
};

class No inherits Lista {
    valor: Int;
    proximo: Lista;

    vazia(): Bool { false };

    cabeca(): Int { valor };

    cauda(): Lista { proximo };

    iniciar(i: Int, resto: Lista): Lista {
        {
            valor <- i;
            proximo <- resto;
            self;
        }
    };
};

class Main inherits IO {
    soma(l: Lista): Int {
        let total: Int <- 0,
            atual: Lista <- l
        in
            {
                while not atual.vazia() loop
                    {
                        total <- total + atual.cabeca();
                        atual <- atual.cauda();
                    }
                pool;
                total;
            }
    };

    main(): Object {
        let numeros: Lista <- (new Lista).adicionar(3).adicionar(2).adicionar(1) in
            out_int(soma(numeros))
    };
};
