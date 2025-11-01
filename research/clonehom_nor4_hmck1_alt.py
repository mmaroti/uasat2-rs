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

from typing import List, Optional, Sequence
from uasat import Solver, BitVec, Constant, Relation, Operation, SmallAlg, Algebra


class Step:
    def __init__(self, oper: int, sels: List[Constant]):
        self.oper = oper
        self.sels = sels

    @staticmethod
    def variable(solver: Solver, oper: int, arity: int, size: int):
        sels = [Constant.variable(size, solver) for _ in range(arity)]
        return Step(oper, sels)

    def solution(self) -> 'Step':
        return Step(self.oper, [s.solution() for s in self.sels])

    def __repr__(self):
        return f"Step({self.oper}, {self.sels})"


class Term:
    def __init__(self, steps: List[Step]):
        self.steps = steps

    @staticmethod
    def variable(solver: Solver, signature: List[int], num_gens: int, num_steps: int):
        steps = []
        for oper in range(num_steps):
            oper %= len(signature)
            arity = signature[oper]
            step = Step.variable(solver, oper, arity, num_gens + len(steps))
            steps.append(step)
        return Term(steps)

    def solution(self) -> 'Term':
        return Term([s.solution() for s in self.steps])

    def __repr__(self) -> str:
        return f"Term({self.steps})"

    def evaluate(self, algebra: Algebra, gens: Sequence[BitVec], partop: bool = False) -> BitVec:
        elems = list(gens)
        for s in self.steps:
            assert len(s.sels) == algebra.signature[s.oper]
            assert all(c.size == len(elems) for c in s.sels)
            args = [Term.choice(c, elems) for c in s.sels]
            elems.append(algebra.apply(s.oper, args, partop=partop))
        return elems[-1]

    @staticmethod
    def choice(selector: Constant, choices: List[BitVec]) -> BitVec:
        assert selector.size == len(choices) and selector.arity == 0

        length = len(choices[0])
        solver = selector.solver
        for choice in choices:
            assert len(choice) == length
            solver |= choice.solver

        literals = []
        for idx in range(length):
            val = BitVec(solver, [choice[idx] for choice in choices])
            val &= selector.table
            literals.append(val.fold_any()[0])

        assert len(literals) == length
        return BitVec(solver, literals)


def find_algebra(terms: List[Term], size: int) -> Optional[SmallAlg]:
    solver = Solver()

    alg = SmallAlg.variable(solver, size, [4, 4])

    f1, g1 = alg.operations

    f1.polymer([0, 0, 1, 1]).comp_eq(g1.polymer([0, 0, 1, 1])).ensure_all()
    f1.polymer([0, 1, 0, 1]).comp_eq(g1.polymer([0, 1, 0, 1])).ensure_all()

    Operation.projection(alg.size, 2, 0).comp_eq(
        f1.polymer([0, 0, 0, 1])).ensure_all()
    g1.polymer([0, 0, 0, 1]).comp_eq(
        Operation.projection(alg.size, 2, 1)).ensure_all()

    rel = Relation.variable(size, 3, solver)
    (~Relation.tuples(size, 3, [[0, 0, 1], [0, 1, 0], [
     1, 0, 0], [1, 1, 0]]) | rel).ensure_all()

    for oper in alg.operations:
        oper.preserves(rel).ensure_all()

    diag = rel.polymer([0, 0, 0])
    for term in terms:
        val = term.evaluate(alg, [alg.encode_elem(0), alg.encode_elem(1)])
        (~val | ~diag.table).ensure_all()

    if solver.solve():
        alg = alg.solution()
        print(alg)
        print(diag.solution())
        return alg
    else:
        print("Algebra not solvable")


def find_diag(alg: SmallAlg) -> Relation:
    rel = Relation.tuples(
        alg.size, 3, [[0, 0, 1], [0, 1, 0], [1, 0, 0], [1, 1, 0]])
    while True:
        rel2 = rel
        for oper in alg.operations:
            rel |= oper.apply(rel2)

        if rel2.comp_eq(rel).value():
            return rel.polymer([0, 0, 0])


def find_term(algs: Sequence[SmallAlg], depth: int) -> Optional[Term]:
    solver = Solver()

    term = Term.variable(solver, [4, 4], 2, depth)

    for alg in algs:
        diag = find_diag(alg)

        val = term.evaluate(alg, [alg.encode_elem(0), alg.encode_elem(1)])
        (~val | diag.table).ensure_all()

    if solver.solve():
        term = term.solution()
        print(term)
        return term
    else:
        print("Term not solvable")


ALGS = [
    SmallAlg([
        Operation(2, 4, [0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 1, 0, 1, 1, 1, 1]),
        Operation(2, 4, [0, 0, 0, 0, 0, 1, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1]),
    ]),
    SmallAlg([
        Operation(2, 4, [0, 0, 0, 0, 1, 0, 1, 1, 0, 0, 0, 0, 1, 1, 1, 1]),
        Operation(2, 4, [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 1, 1, 1, 1, 1]),
    ]),
    SmallAlg([
        Operation(2, 4, [0, 1, 1, 1, 1, 0, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1]),
        Operation(2, 4, [0, 1, 1, 1, 1, 0, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1]),
    ]),
    SmallAlg([
        Operation(2, 4, [0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 1, 0, 1, 1]),
        Operation(2, 4, [0, 0, 0, 1, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1]),
    ]),
    SmallAlg([
        Operation(3, 4, [0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 2, 2, 1, 1, 1, 2, 2, 2, 2, 2, 2, 1, 1, 1, 2, 2, 2, 0, 2, 2, 1, 1, 1, 2, 2, 2, 1, 2,
                         2, 1, 1, 1, 2, 2, 1, 2, 2, 2, 1, 1, 1, 2, 2, 2, 0, 2, 2, 1, 1, 1, 2, 2, 2, 2, 2, 2, 1, 1, 1, 2, 2, 2, 2, 2, 2, 1, 1, 1, 2, 2, 2]),
        Operation(3, 4, [0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 2, 2, 2, 0, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
                         1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 1, 2, 2, 2, 2]),
    ]),
    SmallAlg([
        Operation(2, 4, [0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 1, 0, 1, 0, 1, 1]),
        Operation(2, 4, [0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 1, 0, 0, 1]),
    ]),
]


def test1():
    algs = list(ALGS)

    next_alg = None
    terms = []
    while True:
        term = find_term(algs + [next_alg] if next_alg else algs, 2)
        if not term:
            break

        terms.append(term)
        alg = find_algebra(terms, 4)
        if alg is None:
            break

        next_alg = alg

    print("Done")
    print(next_alg)


if __name__ == '__main__':
    test1()
