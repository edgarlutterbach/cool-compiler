class A { };
class B inherits A { };

class Main {
    a: A <- new B;
    o: Object <- 42;
    proprio: SELF_TYPE <- self;
    f(): A { new B };
    g(): SELF_TYPE { self };
    h(): Object { if true then 1 else "um" fi };
    main(): Object { 0 };
};