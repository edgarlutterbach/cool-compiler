class A {
    -- Atributo do tipo SELF_TYPE
    proprio: SELF_TYPE;

    -- Retorno SELF_TYPE e new SELF_TYPE
    clone(): SELF_TYPE { new SELF_TYPE };

    -- Variável de let do tipo SELF_TYPE
    eu(): SELF_TYPE { let x: SELF_TYPE <- self in x };

    -- Atribuição entre valores SELF_TYPE
    guarda(): SELF_TYPE {
        {
            proprio <- clone();
            proprio;
        }
    };
};

class B inherits A {
    so_b(): Int { 1 };
};

class Main {
    main(): Object {
        {
            (new B).clone().so_b();
            (new B).eu().so_b();
            (new B).copy().so_b();
            (new B)@A.clone().so_b();
        }
    };
};