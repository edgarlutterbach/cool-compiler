(*
 *        Object
 *       /      \
 *      A        Main
 *     / \
 *    B   C
 *    |
 *    D
 *)

class A { };
class B inherits A { };
class C inherits A { };
class D inherits B { };

class Main {
    main(): Object { 0 };
};