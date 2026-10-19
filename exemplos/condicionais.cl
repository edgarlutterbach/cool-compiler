class A { };
class B inherits A { };
class C inherits A { };

class Main {
    flag: Bool;
    n: Int;
    a: A;

    ramos(): Object {
        {
            if flag then new B else new C fi;
            if flag then 1 else 2 fi;
            if flag then 1 else "um" fi;
            if flag then self else self fi;
            if flag then self else new Main fi;
            while n < 10 loop n <- n + 1 pool;
        }
    };

    escolhe(): A { a <- if flag then new B else new C fi };

    main(): Object { 0 };
};