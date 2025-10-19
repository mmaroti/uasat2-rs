# Copyright (C) 2025, Miklos Maroti
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import numpy
from uasat import BitVec, Solver, Relation
from typing import List, Optional


class Term:
    def __init__(self, size: int, arity: int, depth: int, table: BitVec):
        assert size >= 1 and arity >= 3 and depth >= 0
        assert len(table) == size * (arity ** depth)

        self.size = size
        self.arity = arity
        self.depth = depth
        self.table = table

    @staticmethod
    def constant(size: int, arity: int, value: int) -> 'Term':
        assert 0 <= value < size and arity >= 3

        table = [Solver.FALSE for _ in range(size)]
        table[value] = Solver.TRUE
        return Term(size, arity, 0, BitVec(Solver.CALC, table))

    @staticmethod
    def variable(size: int, arity: int, depth: int, solver: Solver) -> 'Term':
        assert size >= 1 and arity >= 3 and depth >= 0
        table = BitVec.variable(solver, size * (arity ** depth))
        for start in range(0, len(table), size):
            table.slice(start, start + size).ensure_one()
        return Term(size, arity, depth, table)

    def solution(self) -> 'Term':
        return Term(self.size, self.arity, self.depth, self.table.solution())

    def decode(self) -> numpy.ndarray:
        result = numpy.empty([self.arity ** self.depth], dtype=int)

        table = self.table.solution()
        for i in range(len(result)):
            for j in range(self.size):
                if table[i * self.size + j] == Solver.TRUE:
                    result[i] = j
                    break
            else:
                raise ValueError()

        return result.reshape([self.arity for _ in range(self.depth)])

    def subterms(self) -> List['Term']:
        assert self.depth >= 1
        sublen = len(self.table) // self.arity
        return [Term(self.size,
                     self.arity,
                     self.depth - 1,
                     self.table.slice(start, start + sublen))
                for start in range(0, len(self.table), sublen)]

    @staticmethod
    def combine(subterms: List['Term']) -> 'Term':
        arity = len(subterms)
        assert arity >= 3
        size = subterms[0].size
        depth = subterms[0].depth

        solver = Solver.CALC
        literals = []
        for sub in subterms:
            assert sub.size == size and sub.depth == depth
            literals.extend(sub.table.literals)
            solver |= sub.table.solver

        return Term(size, arity, depth + 1, BitVec(solver, literals))

    def enlarge(self) -> 'Term':
        literals = self.table.literals
        enlarged = []
        for start in range(0, len(literals), self.size):
            for _ in range(self.arity):
                enlarged.extend(literals[start:start + self.size])
        return Term(self.size, self.arity, self.depth + 1,
                    BitVec(self.table.solver, enlarged))

    @staticmethod
    def choice(selector: BitVec, choices: List['Term']) -> 'Term':
        assert len(selector) == len(choices) and len(choices) >= 1

        size = choices[0].size
        arity = choices[0].arity
        depth = choices[0].depth
        solver = Solver.CALC
        for c in choices:
            solver |= c.table.solver
            assert c.size == size and c.arity == arity and c.depth == depth

        literals = []
        for i in range(len(choices[0].table)):
            values = BitVec(solver, [c.table[i] for c in choices])
            values &= selector
            literals.append(values.fold_any()[0])

        table = BitVec(solver, literals)
        for i in range(0, len(table), size):
            table.slice(i, i + size).ensure_one()

        return Term(size, arity, depth, table)

    def rewrite(self) -> 'Term':
        if self.depth == 0:
            return self

        subterms = [s.rewrite() for s in self.subterms()]
        assert len(subterms) == self.arity and self.arity >= 3

        option0 = subterms[0].enlarge()
        option1 = subterms[1].enlarge()
        option2 = Term.combine(subterms)

        equalities = []
        for i in range(self.arity):
            a = subterms[i].table
            b = subterms[(i + 1) % self.arity].table
            equalities.append(a.comp_eq(b))

        test0 = BitVec(Solver.CALC, [Solver.FALSE])
        test1 = test0
        for i in range(self.arity):
            t = BitVec(Solver.CALC, [Solver.TRUE])
            for j in range(self.arity - 2):
                t &= equalities[(i + j) % self.arity]
            if i == 1:
                test1 = t & ~equalities[0]
            else:
                test0 |= t
        test2 = ~test0 & ~test1

        selector = BitVec(self.table.solver, [test0[0], test1[0], test2[0]])
        selector.ensure_one()
        return Term.choice(selector, [option0, option1, option2])


def ensure_generators(relation: Relation, terms: List[Term]):
    assert relation.arity == len(terms) and len(terms) >= 1
    assert all(relation.size == t.size for t in terms)

    tables = [t.table for t in terms]
    for start in range(0, len(tables[0]), relation.size):
        rel = relation
        for i, t in enumerate(tables):
            r = Relation(relation.size, 1, t.slice(
                start, start + relation.size))
            rel &= r.polymer([i], relation.arity)
        rel.ensure_any()


class Lookup:
    def __init__(self, depth: int):
        assert depth >= 0
        self.depth = depth
        self.terms: List[Term] = []

    def get(self, term: Term, add: bool = False) -> Optional[int]:
        assert not term.table.solver and term.depth <= self.depth
        while term.depth < self.depth:
            term = term.enlarge()

        for i, t in enumerate(self.terms):
            len(t.table)
            assert len(t.table) == len(term.table)
            if term.table.comp_eq(t.table).value():
                return i

        return None

    def add(self, term: Term) -> int:
        i = self.get(term)
        if i is None:
            i = len(self.terms)
            while term.depth < self.depth:
                term = term.enlarge()
            self.terms.append(term)
        return i


def decode_generation(terms: List[Term]):
    lookup = Lookup(max(t.depth for t in terms))
    for i in range(terms[0].size):
        lookup.add(Term.constant(terms[0].size, terms[0].arity, i))

    values = set()

    def decode(terms: List[Term]):
        subterms = []
        if terms[0].depth > 0:
            subterms = [t.subterms() for t in terms]
            for subs in zip(*subterms):
                decode(subs)  # type: ignore

        value = tuple(lookup.add(t.rewrite()) for t in terms)
        if value not in values:
            if terms[0].depth == 0:
                print(value, "generator")
            else:
                args = []
                for sub in zip(*subterms):
                    args.append(tuple(lookup.get(t.rewrite()) for t in sub))
                print(value, "apply", args)

            values.add(value)

    decode(terms)


def find_siggers6():
    arity = 9
    depth = 4
    rel = Relation.tuples(
        3, 2, [(0, 1), (1, 0), (1, 2), (2, 1), (2, 0), (0, 2)])

    solver = Solver()
    term0 = Term.variable(3, arity, depth, solver)
    term1 = Term.variable(3, arity, depth, solver)

    ensure_generators(rel, [term0, term1])
    term2 = term0.rewrite()
    term3 = term1.rewrite()
    (~term2.table ^ term3.table).ensure_all()

    if solver.solve():
        term0 = term0.solution()
        term1 = term1.solution()
        # print(term0.decode())
        # print(term1.decode())
        decode_generation([term0, term1])
    else:
        print("No solution")


def find_siggers4():
    arity = 4
    depth = 5
    rel = Relation.tuples(3, 2, [(0, 1), (1, 0), (1, 2), (2, 0)])

    solver = Solver()
    term0 = Term.variable(3, arity, depth, solver)
    term1 = Term.variable(3, arity, depth, solver)

    ensure_generators(rel, [term0, term1])
    term2 = term0.rewrite()
    term3 = term1.rewrite()
    (~term2.table ^ term3.table).ensure_all()

    if solver.solve():
        term0 = term0.solution()
        term1 = term1.solution()
        decode_generation([term0, term1])
    else:
        print("No solution")


if __name__ == '__main__':
    find_siggers6()
