(*
 * Demonstração 5: erro de tipo com SELF_TYPE
 *
 * abrir() declara retorno SELF_TYPE, mas devolve new Conta. Dentro de
 * Conta isso parece correto, mas em uma subclasse ContaPoupanca o
 * método prometeria uma ContaPoupanca e entregaria uma Conta. Por isso
 * T <= SELF_TYPE é sempre falso (manual, seção 4.1).
 *
 * Correção: trocar new Conta por new SELF_TYPE.
 *
 * Resultado esperado:
 * Erro semântico na linha 26: Método 'abrir': tipo do corpo 'Conta'
 * não conforma com o retorno declarado 'SELF_TYPE'
 *)

class Conta {
    saldo: Int <- 0;

    depositar(v: Int): SELF_TYPE {
        {
            saldo <- saldo + v;
            self;
        }
    };

    abrir(): SELF_TYPE { new Conta };
};

class ContaPoupanca inherits Conta {
    rendimento(): Int { 1 };
};

class Main {
    main(): Object { (new ContaPoupanca).abrir().rendimento() };
};
