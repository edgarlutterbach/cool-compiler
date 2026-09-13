class Main {
    x: Int <- 42;
    nome: String <- "teste";
    flag: Bool;
    f(a: Int, b: Int): Int { a };
    g(): Object { flag };
};

class Segunda inherits Main {
    h(): Int { 1 };
};