class Main {
    a: Int <- ~5;
    b: Bool <- not (a < 0);
    c: Bool <- isvoid self;
    d: Bool <- isvoid 42;
    e: Int <- ~~a + 1;
    main(): Object { not not b };
};