class Main {
    x: String <- "atributo";
    main(): Object {
        {
            let x: Int <- 1, y: Int <- x + 1 in y;
            let x: Int, x: String <- "oculta" in x;
            let p: SELF_TYPE <- self in p;
            let a: Object <- x in a;
            x;
        }
    };
};