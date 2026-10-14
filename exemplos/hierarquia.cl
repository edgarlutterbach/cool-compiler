(*
 *        Object
 *       /      \
 *      A        Main
 *     / \
 *    B   C
 *    |
 *    D
 *)

class A {
    f(): Int { 0 };
};
class B inherits A { };
class C inherits A {
    f(): Int { 1 };
};
class D inherits B { };

class Main {
    main(): Object { 0 };
};