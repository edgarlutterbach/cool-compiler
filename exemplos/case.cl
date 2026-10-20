class A { };
class B inherits A { };
class C inherits A { };

class Main {
    x: Object;
    main(): Object {
        {
            case x of
                b: B => b;
                c: C => c;
            esac;
            case x of
                i: Int => i;
                s: String => s;
            esac;
            case x of
                a: A => a;
                x: Int => x + 1;
            esac;
        }
    };
};