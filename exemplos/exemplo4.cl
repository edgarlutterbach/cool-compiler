(*
 * Demonstração 4: erro de redefinição de método herdado
 *
 * Logger tenta acrescentar um parâmetro a out_string, herdado de IO.
 * Em COOL, um método redefinido precisa manter exatamente a mesma
 * assinatura (manual, seção 6). O analisador conhece as assinaturas
 * das classes básicas e detecta o erro na passada 2.
 *
 * Resultado esperado:
 * Erro semântico na linha 17: Método 'out_string' redefinido em
 * 'Logger' com 2 parâmetro(s), mas declarado em 'IO' com 1
 *)

class Logger inherits IO {
    prefixo: String <- "[log] ";

    out_string(s: String, nivel: Int): SELF_TYPE {
        self@IO.out_string(prefixo.concat(s))
    };
};

class Main {
    main(): Object { (new Logger).out_string("iniciando", 1) };
};
