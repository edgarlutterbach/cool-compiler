(*
 * Demonstração 3: escopos e ocultamento
 *
 * Mostra: o mesmo nome x declarado como atributo, parâmetro, variável
 * de let e variável de case. Em cada uso, vale a declaração mais
 * interna. Os tipos entre colchetes na árvore impressa mostram qual
 * x foi usado em cada ponto.
 *
 * Resultado esperado: árvore impressa, sem erro.
 *)

class Main inherits IO {
    -- Atributo: visível em toda a classe
    x: String <- "atributo";

    -- O parâmetro x: Int oculta o atributo
    dobro(x: Int): Int { x * 2 };

    -- Sem parâmetro x: aqui x é o atributo String
    tamanho(): Int { x.length() };

    exemplo(o: Object): Object {
        {
            -- O inicializador de y ainda vê o atributo; o corpo vê o x do let
            let y: Int <- x.length(), x: Bool <- y < 10 in
                if x then "curto" else "longo" fi;

            -- A variável de cada ramo só existe dentro do próprio ramo
            case o of
                x: Int => x + 1;
                s: String => s.length();
                outro: Object => 0;
            esac;

            -- Fora do let e do case, x volta a ser o atributo
            x.concat("!");
        }
    };

    main(): Object { out_int(dobro(tamanho())) };
};
