class A {
    f(): Int { 1 };
    clone(): SELF_TYPE { self };
};
class B inherits A {
    f(): Int { 2 };
};

class Main inherits IO {
    b: B <- new B;
    main(): Object {
        {
            out_string("ola");
            out_string("a").out_int(1);
            b.f();
            b@A.f();
            b.clone();
            "abc".concat("d").length();
            self.copy();
            b.type_name();
        }
    };
};