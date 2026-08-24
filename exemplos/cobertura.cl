-- Comentario de linha no inicio do arquivo

(* Comentario de bloco simples *)

(* Comentario (* aninhado (* em tres niveis *) de volta *) fechando *)

class Cobertura inherits IO {

    zero: Int <- 0;
    normal: Int <- 42;
    com_zeros: Int <- 007;

    verdadeiro: Bool <- true;
    falso: Bool <- false;
    misto: Bool <- tRuE;
    tipo_nao_bool: Object; -- True seria TYPEID, nao BOOL_CONST

    com_aspas: String <- "ele disse \"ola\" e saiu";
    com_escapes: String <- "tab:\t barra:\\ fim:\n";
    escape_generico: String <- "\q vira apenas q";
    multilinha: String <- "primeira parte \
segunda parte";

    aritmetica(): Int {
        zero + normal - com_zeros * 2 / 1
    };

    unarios(): Int {
        ~normal
    };

    comparacoes(): Bool {
        if zero < normal then
            if normal <= 100 then
                zero = 0
            else
                not true
            fi
        else
            false
        fi
    };

    laco(): Object {
        while zero < 10 loop
            zero <- zero + 1
        pool
    };

    selecao(x: Object): String {
        case x of
            i: Int => "inteiro";
            s: String => "string";
            o: Object => "outro";
        esac
    };

    despacho(): Object {
        {
            self.aritmetica();
            self@Cobertura.unarios();
            new Cobertura;
            isvoid tipo_nao_bool;
        }
    };

    CLASS_maiusculo(): Int { 1 };  -- reservada em maiusculo ainda e reservada
    com_sublinhado_meio_1: Int <- 5;

};

(* comentario de bloco
   ocupando varias linhas
   para testar a contagem *)

class Segunda {
    metodo(a: Int, b: Int): Int { a + b };
};
