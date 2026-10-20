class A {
    f(): Int { 1 };
};
class B inherits A { };

class Main {
    main(): Object { (new A)@B.f() };
};