class A { };
class B inherits A { };

class Main {
    a: A;
    o: Object;
    n: Int;
    main(): Object {
        {
            a <- new B;
            o <- self;
            n <- 1 + 2;
            o <- new SELF_TYPE;
        }
    };
};