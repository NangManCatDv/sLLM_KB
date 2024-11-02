%
parent(john, mary).
parent(john, sam).
parent(mary, anna).
parent(sam, tom).

%
sibling(X, Y) :- parent(Z, X), parent(Z, Y), X \= Y.

%
grandparent(X, Y) :- parent(X, Z), parent(Z, Y).
