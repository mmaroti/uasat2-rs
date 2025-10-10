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

import math
from typing import Any, List, Sequence, Optional, Tuple
from uasat import Solver, BitVec, Constant, Relation, Operation


class Algebra:
    def __init__(self, size: int, length: int, signature: List[int]):
        assert size >= 1 and length >= 0
        self.size = size
        self.length = length
        assert all(arity >= 0 for arity in signature)
        self.signature = signature

    def apply(self, op: int, args: List[BitVec]) -> BitVec:
        assert len(args) == self.signature[op]
        assert all(len(arg) == self.length for arg in args)
        raise NotImplementedError()

    def decode_elem(self, elem: BitVec) -> Any:
        assert len(elem) == self.length
        return NotImplementedError()


class SmallAlg(Algebra):
    def __init__(self, operations: List[Operation]):
        super().__init__(operations[0].size, operations[0].size,
                         [op.arity for op in operations])
        self.operations = operations

    @staticmethod
    def unknown(solver: Solver, size: int, signature: List[int]) -> 'SmallAlg':
        assert size >= 1 and all(arity >= 0 for arity in signature)
        operations = [Operation(size, arity, solver) for arity in signature]
        return SmallAlg(operations)

    def apply(self, op: int, args: List[BitVec]) -> BitVec:
        assert len(args) == self.signature[op]
        hack = self.operations[op]
        hack = Operation(hack.size, hack.arity, hack.table)
        elems = [Operation(self.size, 0, arg) for arg in args]
        res = hack.compose(elems)
        assert res.length == self.size
        return res.table

    def element(self, index: int) -> BitVec:
        assert 0 <= index < self.size
        return Operation.new_const(self.size, index).table

    def decode_elem(self, elem: BitVec) -> Any:
        return Operation(self.size, 0, elem.get_value()).decode()[0]

    def solution(self) -> 'SmallAlg':
        return SmallAlg([op.solution() for op in self.operations])

    def __repr__(self) -> str:
        result = "SmallAlg([\n"
        for op in self.operations:
            result += f"    {op},\n"
        result += "]),"
        return result


class ProductAlg(Algebra):
    def __init__(self, factors: Sequence[Algebra]):
        size = math.prod(a.size for a in factors)
        length = sum(a.length for a in factors)
        assert all(a.signature == factors[0].signature for a in factors)
        super().__init__(size, length, factors[0].signature)
        self.factors = list(factors)

    def apply(self, op: int, args: List[BitVec]) -> BitVec:
        solver = Solver.CALC
        literals = []
        start = 0
        for alg in self.factors:
            subargs = [arg.slice(start, start + alg.length) for arg in args]
            part = alg.apply(op, subargs)
            solver |= part.solver
            literals.extend(part.literals)
            start += alg.length
        assert start == self.length
        return BitVec(solver, literals)

    def combine(self, parts: List[BitVec]) -> BitVec:
        assert len(parts) == len(self.factors)
        solver = Solver.CALC
        literals = []
        for part in parts:
            solver |= part.solver
            literals += part.literals
        assert len(literals) == self.length
        return BitVec(solver, literals)

    def takeapart(self, elem: BitVec) -> List[BitVec]:
        assert len(elem) == self.length
        parts = []
        start = 0
        for alg in self.factors:
            parts.append(elem.slice(start, start + alg.length))
            start += alg.length
        return parts

    def decode_elem(self, elem: BitVec) -> List[Any]:
        result = []
        start = 0
        for alg in self.factors:
            part = elem.slice(start, start + alg.length)
            result.append(alg.decode_elem(part))
            start += alg.length
        return result


class Generator:
    def __init__(self, arity: int, algs: List[SmallAlg]):
        for alg in algs:
            assert alg.signature == [arity, 0, 0, 0]

        self.solver = Solver()

        assert arity >= 3
        self.arity = arity
        self.alg = ProductAlg(algs)
        elem0 = self.alg.combine([alg.operations[1].table for alg in algs])
        elem1 = self.alg.combine([alg.operations[2].table for alg in algs])
        elem2 = self.alg.combine([alg.operations[3].table for alg in algs])

        self.rel = ProductAlg([self.alg, self.alg])
        self.tuples = []
        self.tuples.append(self.rel.combine([elem0, elem1]))
        self.tuples.append(self.rel.combine([elem1, elem0]))
        self.tuples.append(self.rel.combine([elem1, elem2]))
        self.tuples.append(self.rel.combine([elem2, elem0]))

        self.steps: List[List[Constant]] = []

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

    def add_step(self):
        sels = []
        args = []
        for _ in range(self.arity):
            sel = Constant(len(self.tuples), self.solver)
            sels.append(sel)

            arg = Generator.choice(sel, self.tuples)
            args.append(arg)

        out = self.rel.apply(0, args)
        assert len(out) == self.rel.length

        self.tuples.append(out)
        self.steps.append(sels)

    def final_loop(self):
        last = self.rel.takeapart(self.tuples[-1])
        assert len(last) == 2
        last[0].comp_eq(last[1]).ensure_all()

    def decode(self) -> Optional[List[List[int]]]:
        if False:
            print("Tuples:")
            for t in self.tuples:
                print(self.rel.decode_elem(t))

        print("Steps:")
        steps = []
        for old_step in self.steps:
            step = [s.solution().decode()[0] for s in old_step]
            steps.append(step)
            print(f"{step},")
        return steps


def find_term(arity: int, algs: List[SmallAlg], num_steps: int) -> Optional[List[List[int]]]:
    gen = Generator(arity, algs)
    for _ in range(num_steps):
        gen.add_step()
    gen.final_loop()
    if gen.solver.solve():
        return gen.decode()
    else:
        print("Term not solvable")


def find_algebra(size: int, gens: Tuple[int, int, int], arity: int, multi_steps: List[List[List[int]]]) -> Optional[SmallAlg]:
    solver = Solver()
    alg = SmallAlg([
        Operation(size, arity, solver),
        Operation.new_const(size, gens[0]),
        Operation.new_const(size, gens[1]),
        Operation.new_const(size, gens[2]),
    ])

    op = alg.operations[0]

    # near unanimity
    for idx in range(arity):
        new_vars = [0] * idx + [1] + [0] * (arity - idx - 1)
        op.polymer(new_vars).comp_eq(
            Operation.new_proj(size, 2, 0)).ensure_all()

    rel = Relation(size, 2, solver)

    # preservation
    test = op.as_relation()
    for idx in range(1, arity + 1):
        test = test.polymer_swap(idx, 0)
        test = test.polymer_insert(1)
        test &= rel.polymer([0, 1], arity + 2)
        test = test.fold_any(1)
        test = test.polymer_swap(idx, 0)
    test = test.polymer_insert(1)
    test &= op.as_relation().polymer_insert(0)
    test = test.polymer_rotate(-2)
    test = test.fold_any(arity)
    (~test | rel).table.ensure_all()

    # special elements
    elem0 = alg.operations[1].table
    elem1 = alg.operations[2].table
    elem2 = alg.operations[3].table

    # generators in relation
    for (a, b) in [(elem0, elem1), (elem1, elem0), (elem1, elem2), (elem2, elem0)]:
        a = Relation(size, 1, a).polymer([0], 2)
        b = Relation(size, 1, b).polymer([1], 2)
        (~a | ~b | rel).table.ensure_all()

    # at most one diagonal
    # rel.polymer([0, 0]).table.ensure_one()

    # calculating generated pair
    def term(steps, e0, e1, e2, e3):
        e = [e0, e1, e2, e3]
        for step in steps:
            e.append(alg.apply(0, [e[s] for s in step]))
        return e[-1]

    for steps in multi_steps:
        # generated pair not equal
        tup0 = term(steps, elem0, elem1, elem1, elem2)
        tup1 = term(steps, elem1, elem0, elem2, elem0)

        a = Relation(size, 1, tup0).polymer([0], 2)
        b = Relation(size, 1, tup0).polymer([1], 2)
        test0 = (~a | ~b | ~rel).fold_all().table

        a = Relation(size, 1, tup1).polymer([0], 2)
        b = Relation(size, 1, tup1).polymer([1], 2)
        test1 = (~a | ~b | ~rel).fold_all().table

        (test0 | test1).ensure_all()

    if solver.solve():
        solution = alg.solution()
        print(solution)
        print(rel.solution())
        return solution
    else:
        print("Algebra not solvable")
        return None


ALGS3 = [
    SmallAlg([
        Operation(2, 3, [0, 0, 0, 1, 0, 1, 1, 1]),
        Operation(2, 0, [0]),
        Operation(2, 0, [0]),
        Operation(2, 0, [1]),
    ]),
    SmallAlg([
        Operation(2, 3, [0, 0, 0, 1, 0, 1, 1, 1]),
        Operation(2, 0, [0]),
        Operation(2, 0, [1]),
        Operation(2, 0, [0]),
    ]),
    SmallAlg([
        Operation(2, 3, [0, 0, 0, 1, 0, 1, 1, 1]),
        Operation(2, 0, [0]),
        Operation(2, 0, [1]),
        Operation(2, 0, [1]),
    ]),
    SmallAlg([
        Operation(4, 3, [0, 0, 0, 0, 0, 1, 2, 3, 0, 3, 2, 3, 0, 3, 3, 3, 0, 1, 3, 3, 1, 1, 1, 1, 3, 1, 2, 3, 3, 1,
                         3, 3, 0, 3, 2, 3, 3, 1, 2, 3, 2, 2, 2, 2, 3, 3, 2, 3, 0, 3, 3, 3, 3, 1, 3, 3, 3, 3, 2, 3, 3, 3, 3, 3]),
        Operation(4, 0, [0]),
        Operation(4, 0, [1]),
        Operation(4, 0, [2]),
    ]),
    SmallAlg([
        Operation(4, 3, [0, 0, 0, 0, 0, 1, 3, 3, 0, 3, 2, 3, 0, 3, 3, 3, 0, 1, 2, 3, 1, 1, 1, 1, 3, 1, 2, 3, 3, 1,
                         3, 3, 0, 2, 2, 3, 3, 1, 2, 3, 2, 2, 2, 2, 3, 3, 2, 3, 0, 3, 3, 3, 3, 1, 3, 3, 3, 3, 2, 3, 3, 3, 3, 3]),
        Operation(4, 0, [0]),
        Operation(4, 0, [1]),
        Operation(4, 0, [2]),
    ]),
    SmallAlg([
        Operation(4, 3, [0, 0, 0, 0, 0, 1, 3, 3, 0, 3, 2, 3, 0, 3, 3, 3, 0, 1, 3, 3, 1, 1, 1, 1, 3, 1, 2, 3, 3, 1,
                         3, 3, 0, 3, 2, 3, 2, 1, 2, 3, 2, 2, 2, 2, 3, 3, 2, 3, 0, 3, 3, 3, 3, 1, 3, 3, 3, 3, 2, 3, 3, 3, 3, 3]),
        Operation(4, 0, [0]),
        Operation(4, 0, [1]),
        Operation(4, 0, [2]),
    ]),
    SmallAlg([
        Operation(4, 3, [0, 0, 0, 0, 0, 1, 3, 3, 0, 3, 2, 3, 0, 3, 3, 3, 0, 1, 3, 3, 1, 1, 1, 1, 2, 1, 2, 3, 3, 1,
                         3, 3, 0, 3, 2, 3, 2, 1, 2, 3, 2, 2, 2, 2, 3, 3, 2, 3, 0, 3, 3, 3, 3, 1, 3, 3, 3, 3, 2, 3, 3, 3, 3, 3]),
        Operation(4, 0, [0]),
        Operation(4, 0, [1]),
        Operation(4, 0, [2]),
    ]),
]


ALGS4 = [
    SmallAlg([
        Operation(2, 4, [0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 1, 1, 1]),
        Operation(2, 0, [0]),
        Operation(2, 0, [0]),
        Operation(2, 0, [1]),
    ]),
    SmallAlg([
        Operation(2, 4, [0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 1, 1, 1, 1]),
        Operation(2, 0, [0]),
        Operation(2, 0, [1]),
        Operation(2, 0, [0]),
    ]),
    SmallAlg([
        Operation(2, 4, [0, 0, 0, 0, 0, 1, 0, 1, 0, 1, 0, 1, 1, 1, 1, 1]),
        Operation(2, 0, [0]),
        Operation(2, 0, [1]),
        Operation(2, 0, [1]),
    ]),
    SmallAlg([
        Operation(2, 4, [0, 0, 0, 1, 0, 0, 0, 1, 0, 1, 1, 1, 0, 1, 1, 1]),
        Operation(2, 0, [0]),
        Operation(2, 0, [1]),
        Operation(2, 0, [1]),
    ]),
    SmallAlg([
        Operation(2, 4, [0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 1, 1, 1, 1, 1]),
        Operation(2, 0, [0]),
        Operation(2, 0, [1]),
        Operation(2, 0, [0]),
    ]),
    SmallAlg([
        Operation(2, 4, [0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 1, 1, 1, 1, 1, 1]),
        Operation(2, 0, [0]),
        Operation(2, 0, [1]),
        Operation(2, 0, [1]),
    ]),
    SmallAlg([
        Operation(2, 4, [0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 1, 0, 1, 1, 1]),
        Operation(2, 0, [0]),
        Operation(2, 0, [1]),
        Operation(2, 0, [0]),
    ]),
    SmallAlg([
        Operation(2, 4, [0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 1, 0, 1, 1, 1]),
        Operation(2, 0, [0]),
        Operation(2, 0, [1]),
        Operation(2, 0, [0]),
    ]),
    SmallAlg([
        Operation(2, 4, [0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 1, 1, 1, 1, 1, 1]),
        Operation(2, 0, [0]),
        Operation(2, 0, [0]),
        Operation(2, 0, [1]),
    ]),
    SmallAlg([
        Operation(2, 4, [0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 1, 1, 1]),
        Operation(2, 0, [0]),
        Operation(2, 0, [1]),
        Operation(2, 0, [0]),
    ]),
    SmallAlg([
        Operation(3, 4, [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 1, 0, 0, 0, 0, 0, 1, 2, 0, 2, 2, 0, 0, 0, 0, 1, 1, 0, 1, 2, 0, 1,
                         1, 1, 1, 1, 1, 1, 1, 0, 1, 2, 1, 1, 1, 2, 1, 2, 0, 0, 0, 0, 1, 2, 0, 2, 2, 0, 1, 2, 1, 1, 1, 2, 0, 2, 0, 2, 2, 2, 1, 2, 2, 2, 2]),
        Operation(3, 0, [0]),
        Operation(3, 0, [1]),
        Operation(3, 0, [2]),
    ]),
    SmallAlg([
        Operation(3, 4, [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 2, 0, 1, 2, 1, 1, 2, 1, 1, 2, 0, 0, 0, 0, 1, 1, 1, 1, 2, 1, 1,
                         1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 2, 1, 1, 2, 0, 0, 0, 0, 1, 1, 0, 1, 2, 0, 1, 2, 1, 1, 1, 1, 1, 2, 0, 1, 2, 2, 1, 2, 2, 2, 2]),
        Operation(3, 0, [0]),
        Operation(3, 0, [1]),
        Operation(3, 0, [2]),
    ]),
    SmallAlg([
        Operation(3, 4, [0, 0, 0, 0, 1, 1, 0, 1, 1, 0, 1, 1, 1, 1, 1, 0, 1, 1, 0, 1, 0, 1, 1, 1, 1, 1, 2, 0, 1, 0, 1, 1, 1, 0, 1, 2, 0, 1,
                         1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 2, 0, 0, 0, 0, 1, 2, 0, 1, 2, 0, 1, 1, 1, 1, 1, 1, 2, 2, 0, 1, 2, 1, 1, 2, 2, 2, 2]),
        Operation(3, 0, [0]),
        Operation(3, 0, [1]),
        Operation(3, 0, [2]),
    ]),
    SmallAlg([
        Operation(3, 4, [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 2, 0, 0, 0, 0, 0, 0, 0, 0, 2, 0, 1, 0, 0, 1, 1, 0, 0, 2, 1, 1,
                         0, 1, 1, 1, 0, 1, 2, 0, 0, 0, 0, 1, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 0, 2, 0, 0, 0, 0, 1, 0, 0, 1, 2, 0, 2, 2, 0, 0, 2, 2, 2, 2]),
        Operation(3, 0, [0]),
        Operation(3, 0, [1]),
        Operation(3, 0, [2]),
    ]),
    SmallAlg([
        Operation(3, 4, [0, 0, 0, 0, 0, 0, 0, 0, 2, 0, 0, 0, 0, 1, 1, 0, 0, 2, 0, 0, 0, 0, 1, 0, 2, 0, 2, 0, 0, 0, 1, 1, 1, 0, 1, 0, 0, 1,
                         1, 1, 1, 1, 1, 1, 0, 0, 1, 2, 1, 1, 0, 2, 0, 2, 0, 0, 0, 0, 1, 0, 0, 0, 2, 0, 0, 0, 1, 1, 0, 0, 0, 2, 0, 0, 2, 0, 1, 2, 2, 2, 2]),
        Operation(3, 0, [0]),
        Operation(3, 0, [1]),
        Operation(3, 0, [2]),
    ]),
    SmallAlg([
        Operation(3, 4, [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 1, 0, 1, 1, 0, 1, 1, 0, 1, 1, 0, 1, 1, 0, 1, 2, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
                         1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 2, 1, 1, 1, 1, 2, 0, 1, 1, 1, 1, 2, 1, 1, 2, 0, 1, 1, 1, 1, 1, 2, 1, 2, 0, 1, 2, 2, 1, 2, 2, 2, 2]),
        Operation(3, 0, [0]),
        Operation(3, 0, [1]),
        Operation(3, 0, [2]),
    ]),
    SmallAlg([
        Operation(3, 4, [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 0, 2, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1,
                         0, 1, 1, 1, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 2, 0, 0, 0, 0, 1, 0, 0, 0, 2, 0, 1, 0, 0, 1, 0, 2, 1, 2, 0, 0, 2, 2, 0, 2, 2, 2, 2]),
        Operation(3, 0, [0]),
        Operation(3, 0, [1]),
        Operation(3, 0, [2]),
    ]),
    SmallAlg([
        Operation(3, 4, [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 1, 2, 0, 0, 2, 0, 0, 0, 0, 2, 2, 0, 0, 0, 0, 1, 1, 0, 0, 0, 1, 1,
                         0, 1, 1, 1, 0, 1, 0, 0, 0, 0, 1, 1, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 0, 2, 0, 0, 0, 0, 1, 0, 0, 0, 2, 0, 0, 2, 0, 0, 2, 2, 2, 2]),
        Operation(3, 0, [0]),
        Operation(3, 0, [1]),
        Operation(3, 0, [2]),
    ]),
    SmallAlg([
        Operation(3, 4, [0, 0, 0, 0, 0, 0, 0, 0, 2, 0, 1, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1,
                         1, 1, 1, 1, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 2, 0, 0, 0, 0, 1, 0, 0, 0, 2, 0, 0, 0, 0, 1, 0, 0, 0, 2, 0, 0, 2, 0, 0, 2, 2, 2, 2]),
        Operation(3, 0, [0]),
        Operation(3, 0, [1]),
        Operation(3, 0, [2]),
    ]),
    SmallAlg([
        Operation(3, 4, [0, 0, 0, 0, 1, 1, 0, 1, 2, 0, 1, 1, 1, 1, 1, 0, 1, 1, 0, 1, 1, 0, 1, 2, 0, 1, 2, 0, 1, 0, 0, 1, 1, 0, 1, 1, 0, 1,
                         1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 2, 0, 0, 0, 0, 1, 2, 0, 1, 2, 0, 1, 1, 1, 1, 2, 1, 1, 2, 0, 2, 2, 1, 1, 2, 2, 2, 2]),
        Operation(3, 0, [0]),
        Operation(3, 0, [1]),
        Operation(3, 0, [2]),
    ]),
    SmallAlg([
        Operation(3, 4, [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 1, 1, 1, 1, 1, 2, 0, 0, 0, 1, 1, 2, 1, 1, 2, 0, 0, 1, 1, 1, 1, 0, 2, 2, 1, 1,
                         1, 1, 1, 1, 1, 1, 1, 0, 1, 2, 1, 1, 1, 2, 1, 2, 0, 0, 0, 0, 1, 2, 0, 1, 2, 0, 1, 1, 1, 1, 1, 1, 1, 2, 0, 2, 2, 1, 1, 2, 2, 2, 2]),
        Operation(3, 0, [0]),
        Operation(3, 0, [1]),
        Operation(3, 0, [2]),
    ]),
    SmallAlg([
        Operation(3, 4, [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 1, 2, 0, 0, 0, 0, 0, 2, 0, 2, 2, 0, 0, 0, 0, 1, 0, 0, 1, 0, 1, 1,
                         1, 1, 1, 1, 1, 1, 0, 0, 0, 2, 0, 1, 0, 2, 0, 2, 0, 0, 0, 0, 0, 2, 0, 2, 2, 0, 0, 0, 1, 1, 0, 2, 0, 2, 0, 2, 2, 2, 2, 2, 2, 2, 2]),
        Operation(3, 0, [0]),
        Operation(3, 0, [1]),
        Operation(3, 0, [2]),
    ]),
    SmallAlg([
        Operation(3, 4, [0, 0, 0, 0, 1, 2, 0, 2, 2, 0, 0, 0, 2, 1, 2, 2, 2, 2, 0, 0, 0, 2, 1, 2, 2, 2, 2, 0, 1, 0, 1, 1, 1, 2, 1, 2, 0, 1,
                         2, 1, 1, 1, 2, 1, 2, 0, 1, 2, 1, 1, 1, 2, 1, 2, 0, 0, 2, 2, 1, 2, 2, 2, 2, 0, 2, 2, 2, 1, 2, 2, 2, 2, 0, 2, 2, 2, 1, 2, 2, 2, 2]),
        Operation(3, 0, [0]),
        Operation(3, 0, [1]),
        Operation(3, 0, [2]),
    ]),
    SmallAlg([
        Operation(3, 4, [0, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 1, 0, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 1,
                         0, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 0, 2, 0, 0, 0, 0, 1, 0, 0, 0, 2, 0, 0, 2, 0, 0, 2, 2, 2, 2]),
        Operation(3, 0, [0]),
        Operation(3, 0, [1]),
        Operation(3, 0, [2]),
    ]),
    SmallAlg([
        Operation(3, 4, [0, 0, 0, 0, 1, 0, 0, 0, 2, 0, 1, 0, 1, 1, 1, 0, 1, 0, 0, 0, 2, 0, 1, 0, 0, 2, 2, 0, 1, 0, 1, 1, 1, 0, 1, 2, 1, 1,
                         0, 1, 1, 1, 0, 1, 0, 0, 1, 0, 1, 1, 1, 0, 1, 2, 0, 0, 2, 0, 1, 0, 0, 2, 2, 0, 1, 0, 1, 1, 1, 2, 1, 2, 0, 0, 2, 0, 1, 2, 2, 2, 2]),
        Operation(3, 0, [0]),
        Operation(3, 0, [1]),
        Operation(3, 0, [2]),
    ]),
    SmallAlg([
        Operation(3, 4, [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 0, 2, 0, 0, 0, 0, 1, 0, 0, 0, 2, 1, 1,
                         0, 1, 1, 1, 0, 1, 0, 0, 0, 0, 1, 1, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0, 2, 0, 2, 0, 1, 0, 0, 1, 0, 0, 0, 2, 0, 0, 2, 0, 0, 2, 2, 2, 2]),
        Operation(3, 0, [0]),
        Operation(3, 0, [1]),
        Operation(3, 0, [2]),
    ]),
    SmallAlg([
        Operation(3, 4, [0, 0, 0, 0, 0, 0, 0, 0, 2, 0, 0, 0, 0, 1, 0, 0, 1, 2, 0, 0, 0, 0, 0, 0, 0, 2, 2, 0, 1, 0, 0, 1, 1, 0, 1, 2, 0, 1,
                         0, 1, 1, 1, 1, 1, 0, 0, 1, 2, 1, 1, 0, 2, 0, 2, 0, 0, 0, 0, 1, 2, 0, 0, 2, 0, 0, 2, 0, 1, 2, 2, 0, 2, 0, 0, 2, 0, 1, 2, 2, 2, 2]),
        Operation(3, 0, [0]),
        Operation(3, 0, [1]),
        Operation(3, 0, [2]),
    ]),
    SmallAlg([
        Operation(3, 4, [0, 0, 0, 0, 1, 1, 0, 1, 1, 0, 1, 0, 1, 1, 1, 1, 1, 2, 0, 0, 0, 1, 1, 1, 2, 1, 2, 0, 0, 1, 1, 1, 1, 0, 1, 1, 0, 1,
                         1, 1, 1, 1, 1, 1, 1, 0, 1, 2, 1, 1, 1, 1, 1, 2, 0, 0, 0, 0, 1, 2, 0, 2, 2, 0, 1, 2, 1, 1, 1, 1, 1, 2, 0, 1, 2, 2, 1, 2, 2, 2, 2]),
        Operation(3, 0, [0]),
        Operation(3, 0, [1]),
        Operation(3, 0, [2]),
    ]),
    SmallAlg([
        Operation(3, 4, [0, 0, 0, 0, 1, 0, 0, 0, 2, 0, 1, 0, 0, 1, 1, 0, 1, 2, 0, 0, 0, 0, 1, 0, 0, 0, 2, 0, 0, 0, 0, 1, 0, 0, 0, 2, 0, 1,
                         0, 1, 1, 1, 0, 1, 2, 0, 1, 0, 0, 1, 0, 0, 1, 2, 0, 0, 0, 0, 1, 0, 0, 0, 2, 0, 0, 0, 1, 1, 0, 0, 0, 2, 0, 0, 2, 0, 1, 2, 2, 2, 2]),
        Operation(3, 0, [0]),
        Operation(3, 0, [1]),
        Operation(3, 0, [2]),
    ]),
    SmallAlg([
        Operation(3, 4, [0, 0, 0, 0, 1, 0, 0, 0, 2, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 0, 0, 2, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 1,
                         0, 1, 1, 1, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 0, 2, 0, 0, 0, 0, 1, 0, 0, 2, 2, 0, 0, 2, 0, 0, 2, 2, 2, 2]),
        Operation(3, 0, [0]),
        Operation(3, 0, [1]),
        Operation(3, 0, [2]),
    ]),
    SmallAlg([
        Operation(3, 4, [0, 0, 0, 0, 0, 0, 0, 0, 2, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 0, 1, 1, 0, 2, 2, 0, 1, 0, 0, 1, 1, 1, 1, 1, 1, 1,
                         1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 1, 1, 1, 1, 2, 2, 0, 0, 0, 1, 1, 1, 1, 1, 2, 1, 1, 1, 1, 1, 1, 1, 1, 2, 1, 1, 2, 1, 1, 2, 2, 2, 2]),
        Operation(3, 0, [0]),
        Operation(3, 0, [1]),
        Operation(3, 0, [2]),
    ]),
    SmallAlg([
        Operation(3, 4, [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 2, 0, 0, 0, 0, 1, 2, 0, 0, 2, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1,
                         0, 1, 1, 1, 0, 1, 2, 0, 0, 2, 0, 1, 0, 0, 1, 2, 0, 0, 2, 0, 0, 0, 0, 0, 2, 0, 0, 2, 0, 1, 0, 2, 0, 2, 0, 2, 2, 0, 1, 2, 2, 2, 2]),
        Operation(3, 0, [0]),
        Operation(3, 0, [1]),
        Operation(3, 0, [2]),
    ]),
    SmallAlg([
        Operation(3, 4, [0, 0, 0, 0, 0, 0, 0, 0, 2, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 0, 0, 0, 0, 1, 0, 0, 0, 2, 0, 1,
                         0, 1, 1, 1, 1, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 2, 0, 0, 2, 0, 0, 2, 0, 0, 2, 0, 0, 0, 1, 1, 0, 0, 0, 2, 0, 0, 2, 0, 0, 2, 2, 2, 2]),
        Operation(3, 0, [0]),
        Operation(3, 0, [1]),
        Operation(3, 0, [2]),
    ]),
    SmallAlg([
        Operation(4, 4, [0, 0, 0, 0, 0, 2, 2, 0, 0, 0, 3, 0, 0, 0, 0, 0, 0, 3, 2, 3, 1, 1, 1, 1, 2, 3, 2, 3, 3, 3, 3, 3, 0, 0, 3, 3, 2, 3, 2, 2, 3, 3, 2, 3, 3, 3, 3, 3, 0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 0, 0, 0, 0, 3, 1, 3, 3, 0, 3, 3, 3, 3, 3, 3, 3, 3, 1, 3, 3, 1, 1, 1, 1, 3, 1, 3, 3, 3, 1, 3, 3, 3, 3, 2, 3, 3, 1, 2, 3, 2, 2, 2, 3, 3, 3, 2, 3, 3, 3, 3, 3, 3, 1, 3, 3, 3, 3, 3, 3, 3, 3,
                         3, 3, 0, 0, 0, 0, 0, 3, 3, 3, 0, 3, 2, 3, 3, 3, 3, 3, 3, 3, 3, 3, 1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3, 3, 3, 2, 3, 2, 2, 2, 2, 2, 2, 2, 2, 3, 2, 2, 2, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 2, 3, 3, 3, 3, 3, 0, 0, 0, 0, 3, 3, 3, 3, 0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 1, 1, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 2, 3, 3, 3, 2, 2, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3]),
        Operation(4, 0, [0]),
        Operation(4, 0, [1]),
        Operation(4, 0, [2]),
    ]),
    SmallAlg([
        Operation(4, 4, [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 1, 3, 3, 2, 3, 2, 3, 3, 3, 3, 3, 0, 0, 0, 0, 2, 2, 2, 2, 3, 2, 2, 3, 3, 2, 3, 3, 0, 0, 0, 0, 3, 3, 3, 3, 3, 3, 2, 3, 3, 3, 3, 3, 0, 3, 3, 3, 1, 1, 1, 1, 3, 3, 3, 3, 3, 3, 3, 3, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 3, 3, 2, 3, 1, 1, 1, 1, 3, 3, 2, 2, 3, 3, 3, 3, 3, 3, 3, 3, 1, 1, 1, 1, 3, 3, 3, 3, 3, 3,
                         3, 3, 0, 3, 3, 3, 3, 3, 3, 3, 2, 2, 2, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 1, 3, 3, 3, 2, 2, 3, 3, 3, 2, 3, 3, 2, 2, 3, 3, 3, 2, 3, 2, 2, 2, 2, 3, 3, 2, 3, 3, 3, 3, 3, 3, 3, 2, 3, 3, 3, 2, 3, 3, 3, 3, 3, 0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 1, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 2, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 2, 3, 3, 3, 3, 3]),
        Operation(4, 0, [0]),
        Operation(4, 0, [1]),
        Operation(4, 0, [2]),
    ]),
    SmallAlg([
        Operation(4, 4, [0, 0, 0, 0, 0, 0, 0, 3, 0, 0, 0, 0, 0, 0, 0, 3, 0, 0, 0, 0, 3, 1, 3, 3, 3, 1, 3, 3, 3, 3, 3, 3, 0, 3, 0, 0, 2, 3, 3, 3, 3, 2, 2, 3, 0, 3, 3, 3, 0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 0, 3, 0, 3, 3, 1, 3, 3, 2, 3, 3, 3, 3, 3, 3, 3, 1, 1, 3, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 3, 1, 2, 3, 1, 1, 3, 1, 3, 1, 2, 3, 3, 1, 3, 3, 3, 3, 3, 3, 3, 1, 3, 3, 3, 3, 3, 3, 3, 3,
                         3, 3, 0, 2, 3, 3, 3, 2, 3, 3, 2, 2, 2, 2, 3, 3, 3, 3, 2, 3, 3, 3, 3, 1, 2, 3, 3, 2, 2, 3, 3, 3, 3, 3, 2, 2, 2, 2, 2, 2, 2, 3, 2, 2, 2, 2, 2, 2, 2, 2, 3, 3, 3, 3, 3, 3, 3, 3, 3, 2, 2, 3, 3, 3, 3, 3, 0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 1, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 2, 3, 3, 3, 3, 3, 3, 3, 3, 2, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3]),
        Operation(4, 0, [0]),
        Operation(4, 0, [1]),
        Operation(4, 0, [2]),
    ]),
    SmallAlg([
        Operation(4, 4, [0, 0, 0, 0, 0, 2, 3, 3, 0, 3, 3, 3, 0, 3, 3, 3, 0, 3, 3, 3, 2, 1, 3, 3, 3, 2, 3, 3, 3, 3, 3, 3, 0, 3, 3, 3, 3, 1, 3, 3, 3, 3, 2, 3, 3, 3, 2, 3, 0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 0, 3, 3, 3, 3, 1, 2, 3, 3, 3, 2, 3, 3, 3, 3, 3, 3, 1, 3, 3, 1, 1, 1, 1, 3, 1, 3, 3, 3, 1, 3, 3, 3, 3, 3, 3, 2, 1, 3, 3, 3, 3, 2, 2, 3, 3, 3, 3, 3, 3, 3, 3, 3, 1, 3, 3, 3, 3, 3, 3, 3, 3,
                         3, 3, 0, 3, 3, 3, 3, 1, 3, 3, 2, 3, 2, 2, 3, 3, 3, 3, 3, 2, 2, 3, 2, 1, 3, 3, 3, 3, 2, 3, 3, 3, 2, 3, 3, 3, 2, 3, 2, 3, 2, 3, 2, 2, 2, 2, 3, 3, 2, 3, 3, 3, 3, 3, 3, 3, 2, 3, 2, 3, 2, 3, 3, 3, 3, 3, 0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 2, 3, 3, 3, 3, 3, 3, 3, 3, 3, 1, 1, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 2, 3, 3, 3, 3, 3, 3, 3, 2, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3]),
        Operation(4, 0, [0]),
        Operation(4, 0, [1]),
        Operation(4, 0, [2]),
    ]),
    SmallAlg([
        Operation(4, 4, [0, 0, 0, 0, 0, 3, 3, 3, 0, 3, 3, 3, 0, 3, 3, 3, 0, 2, 3, 3, 1, 1, 3, 1, 2, 2, 3, 3, 3, 1, 3, 3, 0, 2, 2, 3, 3, 1, 3, 3, 2, 2, 2, 2, 3, 3, 3, 3, 0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 2, 3, 3, 3, 3, 3, 0, 3, 0, 3, 3, 1, 3, 3, 3, 2, 2, 3, 3, 3, 3, 3, 3, 1, 2, 3, 1, 1, 1, 1, 1, 1, 1, 3, 3, 1, 3, 3, 3, 3, 3, 3, 3, 1, 3, 3, 2, 3, 2, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 1, 3, 3, 3, 3, 3, 3, 3, 3,
                         3, 3, 0, 3, 3, 3, 3, 1, 3, 3, 3, 2, 2, 3, 3, 3, 3, 3, 3, 2, 3, 3, 1, 1, 3, 1, 3, 1, 2, 3, 3, 3, 3, 3, 2, 2, 2, 3, 3, 3, 2, 3, 2, 2, 2, 2, 2, 3, 2, 3, 3, 3, 3, 3, 3, 1, 3, 3, 3, 3, 2, 3, 3, 3, 3, 3, 0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 1, 1, 3, 1, 3, 3, 3, 3, 3, 3, 3, 3, 3, 2, 3, 3, 3, 3, 3, 3, 2, 3, 2, 2, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3]),
        Operation(4, 0, [0]),
        Operation(4, 0, [1]),
        Operation(4, 0, [2]),
    ]),
    SmallAlg([
        Operation(4, 4, [0, 0, 0, 0, 0, 3, 3, 3, 0, 3, 3, 3, 0, 3, 3, 3, 0, 0, 0, 0, 1, 1, 1, 1, 3, 3, 3, 3, 3, 3, 3, 3, 0, 0, 0, 0, 3, 3, 3, 3, 2, 3, 2, 3, 3, 3, 2, 3, 0, 0, 0, 0, 3, 3, 3, 3, 3, 3, 2, 3, 3, 3, 3, 3, 0, 0, 0, 0, 1, 1, 1, 1, 3, 3, 3, 3, 3, 3, 2, 3, 2, 1, 3, 3, 1, 1, 1, 1, 3, 1, 3, 3, 3, 1, 3, 3, 3, 3, 3, 3, 1, 1, 1, 1, 3, 2, 2, 2, 3, 3, 3, 3, 3, 3, 3, 3, 1, 1, 1, 1, 3, 3, 2, 3, 3, 3,
                         3, 3, 0, 0, 0, 0, 2, 3, 2, 2, 2, 2, 2, 3, 3, 2, 3, 3, 3, 3, 2, 3, 1, 1, 1, 1, 3, 3, 2, 3, 3, 3, 3, 3, 3, 3, 2, 3, 2, 3, 2, 3, 2, 2, 2, 2, 3, 3, 2, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 2, 3, 3, 3, 3, 3, 0, 0, 0, 0, 3, 3, 3, 3, 3, 3, 2, 3, 3, 3, 3, 3, 3, 3, 3, 3, 1, 1, 1, 1, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 2, 2, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 2, 3, 3, 3, 3, 3]),
        Operation(4, 0, [0]),
        Operation(4, 0, [1]),
        Operation(4, 0, [2]),
    ]),
    SmallAlg([
        Operation(4, 4, [0, 0, 0, 0, 0, 2, 3, 3, 0, 3, 3, 3, 0, 3, 3, 3, 0, 0, 0, 0, 3, 1, 3, 3, 2, 3, 3, 3, 3, 3, 3, 3, 0, 0, 0, 0, 3, 3, 3, 3, 3, 3, 2, 3, 3, 3, 2, 3, 0, 0, 0, 0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 0, 3, 3, 3, 1, 1, 1, 1, 3, 3, 2, 3, 3, 3, 3, 3, 3, 1, 3, 3, 1, 1, 1, 1, 3, 1, 3, 3, 3, 1, 3, 3, 3, 3, 2, 2, 1, 1, 1, 1, 2, 3, 2, 3, 3, 3, 3, 3, 3, 3, 2, 3, 1, 1, 1, 1, 3, 3, 2, 3, 3, 3,
                         3, 3, 0, 3, 3, 3, 3, 3, 3, 3, 2, 3, 2, 3, 3, 3, 3, 3, 3, 2, 2, 3, 2, 1, 3, 3, 2, 3, 2, 3, 3, 3, 3, 3, 3, 2, 2, 3, 3, 3, 2, 3, 2, 2, 2, 2, 3, 3, 2, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 2, 3, 3, 3, 3, 3, 0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 2, 3, 3, 3, 3, 3, 3, 3, 2, 3, 3, 1, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 2, 3, 3, 3, 3, 3, 3, 3, 2, 2, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3]),
        Operation(4, 0, [0]),
        Operation(4, 0, [1]),
        Operation(4, 0, [2]),
    ]),
    SmallAlg([
        Operation(4, 4, [0, 0, 0, 0, 0, 3, 2, 3, 0, 0, 3, 0, 0, 3, 3, 3, 0, 3, 0, 3, 2, 1, 3, 1, 0, 1, 2, 3, 3, 3, 3, 3, 0, 3, 2, 3, 3, 1, 3, 3, 3, 2, 2, 3, 3, 3, 3, 3, 0, 3, 0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 0, 3, 3, 3, 3, 1, 2, 3, 2, 3, 2, 3, 3, 3, 3, 3, 3, 1, 3, 3, 1, 1, 1, 1, 3, 1, 1, 3, 3, 1, 1, 3, 0, 3, 2, 3, 1, 1, 2, 1, 2, 3, 2, 3, 3, 3, 2, 3, 3, 3, 3, 3, 3, 1, 3, 3, 3, 3, 2, 3, 3, 3,
                         3, 3, 0, 3, 3, 3, 3, 3, 2, 3, 3, 2, 2, 3, 3, 3, 3, 3, 0, 3, 2, 3, 3, 1, 3, 3, 3, 3, 2, 3, 3, 3, 3, 3, 3, 3, 2, 3, 3, 2, 2, 3, 2, 2, 2, 2, 3, 3, 2, 3, 0, 3, 3, 3, 3, 1, 2, 3, 3, 3, 2, 3, 3, 3, 3, 3, 0, 3, 3, 3, 3, 3, 2, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 1, 1, 3, 3, 3, 3, 2, 3, 3, 3, 3, 3, 0, 3, 2, 3, 3, 1, 3, 3, 3, 3, 2, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3]),
        Operation(4, 0, [0]),
        Operation(4, 0, [1]),
        Operation(4, 0, [2]),
    ]),
    SmallAlg([
        Operation(4, 4, [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3, 3, 0, 0, 0, 0, 0, 3, 3, 3, 3, 1, 3, 3, 0, 3, 3, 3, 3, 3, 3, 3, 0, 2, 2, 3, 0, 3, 2, 3, 3, 3, 2, 3, 3, 3, 2, 3, 0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 0, 1, 2, 3, 0, 1, 3, 3, 0, 3, 3, 3, 0, 3, 3, 3, 1, 1, 3, 3, 1, 1, 1, 1, 3, 1, 1, 3, 1, 1, 1, 3, 3, 1, 2, 3, 3, 1, 3, 3, 2, 3, 2, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 1, 3, 3, 3, 3, 3, 3, 3, 3,
                         3, 3, 0, 0, 2, 3, 3, 2, 2, 3, 2, 2, 2, 2, 3, 3, 2, 3, 2, 1, 2, 3, 3, 1, 2, 3, 3, 3, 2, 3, 3, 3, 2, 3, 2, 2, 2, 3, 2, 2, 2, 3, 2, 2, 2, 2, 3, 3, 2, 3, 3, 3, 2, 3, 3, 3, 2, 3, 3, 3, 2, 3, 3, 3, 3, 3, 0, 3, 3, 3, 3, 3, 3, 3, 0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 1, 3, 3, 3, 1, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 2, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3]),
        Operation(4, 0, [0]),
        Operation(4, 0, [1]),
        Operation(4, 0, [2]),
    ]),
    SmallAlg([
        Operation(4, 4, [0, 0, 0, 0, 0, 3, 0, 3, 0, 0, 0, 0, 0, 3, 3, 3, 0, 0, 3, 3, 1, 1, 2, 1, 3, 2, 2, 3, 3, 3, 3, 3, 0, 3, 2, 3, 3, 3, 2, 3, 2, 2, 2, 2, 3, 3, 2, 3, 0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 0, 3, 0, 3, 3, 1, 1, 3, 3, 3, 3, 3, 3, 3, 3, 3, 1, 1, 3, 3, 1, 1, 1, 1, 1, 1, 2, 1, 3, 1, 3, 3, 0, 2, 3, 3, 1, 1, 3, 1, 3, 2, 2, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 1, 3, 3, 3, 3, 3, 3, 3, 3,
                         3, 3, 0, 3, 0, 3, 3, 3, 3, 3, 3, 2, 2, 3, 3, 3, 3, 3, 2, 1, 2, 3, 3, 1, 3, 3, 3, 1, 2, 3, 3, 3, 3, 3, 0, 2, 2, 3, 2, 3, 2, 2, 2, 2, 2, 2, 3, 3, 2, 3, 0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 2, 3, 3, 3, 3, 3, 0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 1, 3, 3, 3, 1, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 2, 2, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3]),
        Operation(4, 0, [0]),
        Operation(4, 0, [1]),
        Operation(4, 0, [2]),
    ]),
    SmallAlg([
        Operation(4, 4, [0, 0, 0, 0, 0, 1, 3, 3, 0, 3, 3, 3, 0, 3, 3, 3, 0, 3, 3, 3, 0, 1, 2, 3, 0, 3, 2, 3, 3, 3, 3, 3, 0, 3, 0, 3, 3, 3, 3, 3, 3, 3, 2, 3, 3, 3, 3, 3, 0, 3, 3, 3, 3, 1, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 0, 1, 2, 3, 1, 1, 2, 1, 3, 1, 3, 3, 3, 1, 2, 3, 3, 1, 3, 3, 1, 1, 1, 1, 3, 1, 3, 3, 3, 1, 3, 3, 0, 1, 3, 3, 2, 1, 3, 1, 3, 1, 2, 3, 3, 1, 3, 3, 3, 1, 3, 3, 1, 1, 3, 1, 3, 1, 3, 3, 3, 1,
                         3, 3, 0, 3, 3, 3, 2, 1, 3, 3, 2, 3, 2, 3, 3, 3, 2, 3, 3, 2, 2, 3, 3, 1, 2, 3, 3, 2, 2, 3, 3, 3, 2, 3, 3, 2, 2, 3, 2, 1, 2, 2, 2, 2, 2, 2, 3, 3, 2, 3, 3, 3, 3, 3, 2, 1, 2, 3, 2, 3, 2, 2, 3, 3, 3, 3, 0, 3, 3, 3, 3, 1, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 1, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 2, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 1, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3]),
        Operation(4, 0, [0]),
        Operation(4, 0, [1]),
        Operation(4, 0, [2]),
    ]),
    SmallAlg([
        Operation(4, 4, [0, 0, 0, 0, 0, 1, 0, 3, 0, 0, 0, 0, 0, 3, 0, 3, 0, 3, 3, 3, 0, 1, 3, 3, 0, 3, 2, 3, 0, 3, 3, 3, 0, 3, 2, 3, 0, 3, 3, 3, 2, 3, 2, 3, 0, 3, 3, 3, 0, 3, 3, 3, 0, 3, 3, 3, 0, 3, 3, 3, 3, 3, 3, 3, 0, 3, 3, 3, 3, 1, 2, 3, 0, 1, 2, 3, 3, 3, 3, 3, 3, 1, 3, 3, 1, 1, 1, 1, 3, 1, 2, 3, 3, 1, 3, 3, 3, 1, 3, 3, 1, 1, 1, 1, 3, 1, 2, 3, 3, 1, 3, 3, 3, 3, 3, 3, 3, 1, 1, 3, 3, 1, 3, 3, 3, 3,
                         3, 3, 0, 2, 2, 3, 2, 1, 2, 3, 0, 2, 2, 3, 3, 3, 2, 3, 0, 3, 2, 3, 1, 1, 1, 1, 3, 3, 2, 3, 3, 3, 3, 3, 3, 2, 2, 3, 2, 2, 2, 2, 2, 2, 2, 2, 3, 2, 2, 3, 3, 3, 2, 3, 2, 3, 3, 3, 3, 3, 2, 3, 3, 3, 3, 3, 0, 3, 3, 3, 0, 3, 3, 3, 0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 1, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 2, 3, 3, 3, 2, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3]),
        Operation(4, 0, [0]),
        Operation(4, 0, [1]),
        Operation(4, 0, [2]),
    ]),
    SmallAlg([
        Operation(4, 4, [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0, 1, 2, 3, 0, 1, 2, 3, 0, 1, 2, 3, 3, 3, 2, 3, 0, 0, 0, 0, 0, 1, 3, 3, 3, 3, 2, 3, 0, 3, 3, 3, 0, 3, 0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 0, 1, 3, 3, 3, 1, 3, 3, 0, 1, 2, 3, 3, 3, 3, 3, 3, 1, 3, 3, 1, 1, 1, 1, 1, 1, 1, 1, 3, 1, 1, 3, 3, 3, 2, 3, 3, 1, 2, 3, 3, 1, 2, 3, 3, 1, 2, 3, 3, 3, 3, 3, 3, 1, 3, 3, 3, 1, 3, 3, 3, 3,
                         3, 3, 0, 3, 2, 3, 0, 3, 2, 3, 3, 3, 2, 3, 3, 3, 2, 3, 3, 3, 3, 3, 2, 1, 3, 3, 2, 2, 2, 3, 3, 3, 2, 3, 2, 3, 2, 2, 2, 3, 2, 3, 2, 2, 2, 2, 2, 3, 2, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 2, 3, 3, 3, 2, 3, 0, 3, 3, 3, 3, 3, 3, 3, 0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 1, 3, 3, 3, 1, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 1, 3, 3, 3, 3, 2, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3]),
        Operation(4, 0, [0]),
        Operation(4, 0, [1]),
        Operation(4, 0, [2]),
    ]),
    SmallAlg([
        Operation(4, 4, [0, 0, 0, 0, 0, 3, 2, 3, 0, 3, 2, 3, 0, 3, 3, 3, 0, 3, 3, 3, 3, 1, 1, 3, 3, 3, 2, 3, 3, 3, 3, 3, 0, 3, 2, 3, 2, 1, 2, 3, 2, 2, 2, 3, 3, 3, 3, 3, 0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 0, 0, 0, 3, 3, 1, 2, 3, 3, 3, 2, 3, 0, 3, 3, 3, 0, 1, 1, 3, 1, 1, 1, 1, 3, 1, 1, 3, 3, 1, 3, 3, 0, 3, 2, 3, 2, 1, 2, 3, 2, 1, 2, 3, 3, 3, 2, 3, 0, 3, 3, 3, 3, 1, 3, 3, 3, 3, 3, 3, 3, 3,
                         3, 3, 0, 0, 3, 3, 0, 1, 2, 3, 3, 3, 2, 3, 0, 3, 2, 3, 0, 1, 3, 3, 1, 1, 1, 3, 3, 1, 2, 3, 3, 1, 3, 3, 0, 3, 2, 3, 2, 1, 2, 3, 2, 2, 2, 2, 2, 3, 2, 3, 0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 2, 3, 3, 3, 3, 3, 0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 2, 3, 3, 3, 3, 3, 0, 3, 3, 3, 3, 1, 3, 3, 3, 1, 3, 3, 3, 3, 3, 3, 0, 3, 2, 3, 3, 1, 3, 3, 3, 3, 2, 3, 3, 3, 3, 3, 0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3]),
        Operation(4, 0, [0]),
        Operation(4, 0, [1]),
        Operation(4, 0, [2]),
    ]),
    SmallAlg([
        Operation(4, 4, [0, 0, 0, 0, 0, 3, 3, 3, 0, 3, 0, 3, 0, 3, 3, 3, 0, 0, 3, 3, 3, 1, 2, 3, 0, 2, 3, 3, 3, 3, 3, 3, 0, 0, 0, 3, 3, 2, 3, 3, 3, 2, 2, 3, 3, 3, 3, 3, 0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 0, 1, 0, 3, 1, 1, 1, 1, 3, 2, 3, 3, 3, 3, 3, 3, 1, 1, 2, 3, 1, 1, 1, 1, 3, 1, 3, 3, 1, 1, 3, 3, 3, 1, 3, 3, 3, 1, 1, 3, 3, 1, 2, 3, 3, 3, 3, 3, 3, 3, 3, 3, 1, 1, 1, 1, 3, 1, 3, 3, 3, 3,
                         3, 3, 0, 3, 3, 3, 3, 2, 2, 3, 2, 2, 2, 3, 3, 3, 2, 3, 3, 2, 3, 3, 3, 1, 3, 3, 2, 3, 2, 3, 3, 3, 3, 3, 2, 2, 2, 3, 3, 2, 2, 3, 2, 2, 2, 2, 3, 3, 2, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 2, 3, 3, 3, 3, 3, 0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 1, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 2, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3]),
        Operation(4, 0, [0]),
        Operation(4, 0, [1]),
        Operation(4, 0, [2]),
    ]),
    SmallAlg([
        Operation(4, 4, [0, 0, 0, 0, 0, 3, 2, 3, 0, 3, 3, 3, 0, 3, 3, 3, 0, 2, 2, 3, 3, 1, 3, 3, 0, 2, 2, 3, 3, 3, 3, 3, 0, 2, 0, 0, 3, 1, 3, 3, 0, 2, 2, 3, 3, 3, 2, 3, 0, 3, 3, 3, 3, 1, 3, 3, 3, 3, 2, 3, 3, 3, 3, 3, 0, 3, 3, 3, 3, 1, 3, 3, 3, 1, 2, 3, 3, 3, 3, 3, 0, 1, 2, 3, 1, 1, 1, 1, 3, 1, 2, 3, 3, 1, 3, 3, 0, 1, 3, 3, 3, 1, 3, 3, 2, 1, 2, 3, 3, 3, 3, 3, 0, 3, 3, 3, 3, 1, 3, 3, 3, 1, 3, 3, 3, 3,
                         3, 3, 0, 0, 2, 0, 3, 1, 2, 3, 3, 3, 2, 3, 3, 3, 2, 3, 3, 3, 3, 3, 1, 1, 2, 3, 3, 1, 2, 3, 3, 3, 3, 3, 0, 3, 2, 3, 3, 1, 2, 3, 2, 2, 2, 2, 3, 3, 2, 3, 0, 3, 3, 3, 3, 3, 2, 3, 3, 3, 2, 3, 3, 3, 2, 3, 0, 3, 3, 3, 3, 1, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 1, 3, 3, 3, 1, 2, 3, 3, 3, 3, 3, 0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 2, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3]),
        Operation(4, 0, [0]),
        Operation(4, 0, [1]),
        Operation(4, 0, [2]),
    ]),
    SmallAlg([
        Operation(4, 4, [0, 0, 0, 0, 0, 3, 3, 3, 0, 3, 2, 3, 0, 3, 3, 3, 0, 3, 3, 3, 1, 1, 1, 1, 3, 3, 3, 3, 3, 3, 3, 3, 0, 0, 3, 3, 3, 3, 3, 3, 2, 2, 2, 3, 3, 3, 3, 3, 0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 0, 0, 0, 0, 3, 1, 3, 3, 2, 3, 3, 3, 3, 3, 3, 3, 3, 1, 3, 3, 1, 1, 1, 1, 3, 1, 3, 3, 3, 1, 3, 3, 3, 2, 3, 3, 2, 1, 2, 3, 3, 3, 2, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 1, 3, 3, 3, 3, 2, 3, 3, 3,
                         3, 3, 0, 0, 0, 0, 0, 3, 3, 3, 3, 3, 2, 3, 0, 3, 3, 3, 2, 3, 2, 3, 1, 1, 1, 1, 2, 2, 2, 3, 3, 3, 3, 3, 3, 2, 2, 3, 3, 3, 2, 3, 2, 2, 2, 2, 3, 3, 2, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 2, 3, 3, 3, 3, 3, 0, 0, 0, 0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 2, 3, 1, 1, 1, 1, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 2, 3, 2, 2, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 2, 3, 3, 3, 3, 3]),
        Operation(4, 0, [0]),
        Operation(4, 0, [1]),
        Operation(4, 0, [2]),
    ]),
    SmallAlg([
        Operation(4, 4, [0, 0, 0, 0, 0, 3, 2, 3, 0, 0, 3, 0, 0, 3, 3, 3, 0, 0, 3, 3, 1, 1, 2, 1, 2, 3, 3, 3, 3, 3, 3, 3, 0, 3, 3, 3, 2, 1, 3, 3, 0, 3, 2, 3, 3, 3, 3, 3, 0, 3, 3, 3, 0, 1, 2, 3, 3, 3, 3, 3, 3, 3, 3, 3, 0, 3, 3, 3, 1, 1, 1, 3, 3, 3, 2, 3, 3, 3, 3, 3, 3, 1, 3, 3, 1, 1, 1, 1, 3, 1, 2, 3, 3, 1, 3, 3, 0, 3, 2, 3, 3, 1, 1, 3, 3, 3, 2, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 1, 1, 3, 3, 3, 3, 3, 3, 3,
                         3, 3, 0, 3, 3, 3, 3, 1, 3, 3, 2, 2, 2, 3, 3, 3, 3, 3, 3, 3, 3, 3, 2, 1, 2, 1, 3, 2, 2, 3, 3, 3, 3, 3, 0, 3, 2, 3, 2, 1, 2, 3, 2, 2, 2, 2, 3, 3, 2, 3, 3, 3, 3, 3, 3, 1, 3, 3, 3, 3, 2, 3, 3, 3, 3, 3, 0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 1, 3, 1, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 1, 3, 3, 3, 3, 2, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 2, 3, 3, 3, 3, 3]),
        Operation(4, 0, [0]),
        Operation(4, 0, [1]),
        Operation(4, 0, [2]),
    ]),
    SmallAlg([
        Operation(4, 4, [0, 0, 0, 0, 0, 3, 3, 3, 0, 2, 3, 3, 0, 3, 3, 3, 0, 3, 3, 3, 1, 1, 1, 3, 2, 1, 2, 3, 3, 3, 3, 3, 0, 2, 3, 3, 3, 1, 3, 3, 3, 2, 2, 2, 3, 3, 3, 3, 0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 0, 0, 0, 3, 3, 1, 3, 3, 3, 2, 2, 3, 3, 3, 3, 3, 0, 1, 3, 3, 1, 1, 1, 1, 1, 1, 3, 3, 3, 1, 3, 3, 3, 3, 3, 3, 1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3, 3, 3, 3, 3, 3, 1, 3, 3, 3, 3, 3, 3, 3, 3,
                         3, 3, 0, 0, 0, 0, 0, 1, 3, 3, 2, 2, 2, 2, 3, 3, 3, 3, 3, 2, 3, 3, 3, 1, 1, 1, 3, 2, 2, 3, 3, 3, 3, 3, 3, 2, 2, 3, 3, 3, 2, 3, 2, 2, 2, 2, 3, 3, 2, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 2, 2, 3, 3, 3, 3, 3, 0, 3, 3, 3, 3, 3, 3, 3, 3, 2, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 1, 1, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 1, 3, 3, 2, 2, 2, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 2, 3, 3, 3, 3, 3]),
        Operation(4, 0, [0]),
        Operation(4, 0, [1]),
        Operation(4, 0, [2]),
    ]),
    SmallAlg([
        Operation(4, 4, [0, 0, 0, 0, 0, 3, 3, 3, 0, 3, 0, 3, 0, 3, 3, 3, 0, 3, 2, 3, 3, 1, 1, 3, 3, 3, 3, 3, 3, 3, 3, 3, 0, 3, 2, 3, 3, 3, 3, 3, 2, 2, 2, 2, 3, 3, 3, 3, 0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 0, 0, 0, 3, 0, 1, 1, 3, 2, 3, 3, 3, 3, 3, 3, 3, 1, 1, 2, 3, 1, 1, 1, 1, 2, 1, 1, 1, 3, 1, 1, 3, 2, 1, 2, 3, 3, 1, 1, 3, 2, 1, 2, 2, 3, 1, 3, 3, 3, 3, 3, 3, 3, 1, 1, 3, 2, 1, 2, 3, 3, 3,
                         3, 3, 0, 0, 0, 3, 0, 3, 2, 3, 2, 3, 2, 3, 0, 3, 3, 3, 0, 3, 3, 3, 1, 1, 1, 1, 2, 3, 2, 3, 3, 3, 3, 3, 0, 3, 2, 3, 3, 2, 2, 3, 2, 2, 2, 2, 3, 3, 2, 3, 0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 2, 3, 3, 3, 3, 3, 0, 3, 0, 0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 2, 3, 3, 1, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 2, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3]),
        Operation(4, 0, [0]),
        Operation(4, 0, [1]),
        Operation(4, 0, [2]),
    ]),
    SmallAlg([
        Operation(4, 4, [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3, 1, 1, 1, 3, 3, 2, 2, 3, 3, 3, 3, 3, 0, 3, 0, 0, 3, 1, 3, 3, 2, 2, 2, 2, 3, 3, 3, 3, 0, 0, 0, 0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 0, 0, 0, 0, 3, 1, 1, 3, 2, 2, 2, 2, 3, 3, 3, 3, 3, 1, 3, 3, 1, 1, 1, 1, 1, 1, 1, 1, 3, 1, 1, 3, 3, 2, 3, 3, 1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3, 3, 3, 3, 3, 3, 1, 1, 3, 3, 3, 3, 3, 3, 3,
                         3, 3, 0, 0, 0, 0, 3, 1, 3, 3, 2, 2, 2, 2, 3, 3, 3, 3, 3, 3, 3, 3, 1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 3, 3, 3, 3, 3, 3, 3, 3, 2, 2, 2, 3, 3, 3, 3, 3, 0, 0, 0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 1, 1, 3, 3, 1, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 2, 3, 2, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3]),
        Operation(4, 0, [0]),
        Operation(4, 0, [1]),
        Operation(4, 0, [2]),
    ]),
    SmallAlg([
        Operation(4, 4, [0, 0, 0, 0, 0, 1, 2, 3, 0, 2, 3, 3, 0, 3, 3, 3, 0, 3, 3, 3, 1, 1, 3, 1, 3, 3, 3, 2, 3, 3, 3, 3, 0, 3, 3, 3, 3, 1, 2, 3, 3, 2, 2, 3, 3, 3, 3, 3, 0, 3, 3, 3, 3, 1, 3, 3, 3, 2, 3, 3, 3, 3, 3, 3, 0, 3, 3, 3, 3, 1, 3, 3, 3, 2, 2, 3, 3, 3, 3, 3, 0, 1, 3, 3, 1, 1, 1, 1, 3, 1, 2, 3, 3, 1, 3, 3, 3, 3, 3, 3, 1, 1, 1, 1, 3, 3, 2, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 1, 1, 3, 3, 3, 3, 3, 3, 3,
                         3, 3, 0, 3, 3, 3, 2, 1, 3, 3, 2, 2, 2, 2, 3, 3, 3, 3, 3, 3, 3, 3, 1, 1, 2, 1, 3, 3, 2, 2, 3, 1, 3, 3, 0, 3, 2, 3, 3, 1, 2, 3, 2, 2, 2, 2, 3, 3, 2, 3, 3, 3, 3, 3, 3, 1, 3, 3, 2, 2, 2, 2, 3, 3, 3, 3, 0, 3, 3, 3, 3, 1, 3, 3, 3, 3, 2, 3, 3, 3, 3, 3, 3, 3, 3, 3, 1, 1, 3, 1, 2, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 1, 3, 3, 3, 2, 2, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 1, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3]),
        Operation(4, 0, [0]),
        Operation(4, 0, [1]),
        Operation(4, 0, [2]),
    ]),
    SmallAlg([
        Operation(4, 4, [0, 0, 0, 0, 0, 2, 0, 0, 0, 0, 3, 3, 0, 3, 3, 3, 0, 0, 0, 3, 3, 1, 2, 3, 0, 3, 3, 3, 3, 3, 3, 3, 0, 3, 3, 3, 0, 2, 2, 3, 0, 3, 2, 3, 0, 3, 3, 3, 0, 3, 3, 3, 3, 1, 2, 3, 0, 3, 3, 3, 3, 3, 3, 3, 0, 3, 0, 3, 3, 1, 1, 3, 3, 1, 3, 3, 3, 3, 3, 3, 3, 1, 3, 3, 1, 1, 1, 1, 3, 1, 3, 3, 3, 1, 3, 3, 3, 1, 3, 3, 1, 1, 1, 1, 3, 1, 2, 3, 3, 1, 3, 3, 3, 3, 3, 3, 3, 1, 1, 3, 3, 3, 3, 3, 3, 3,
                         3, 3, 0, 3, 0, 3, 2, 2, 2, 2, 2, 2, 2, 3, 3, 3, 3, 3, 3, 1, 3, 3, 3, 1, 1, 3, 3, 2, 2, 3, 3, 3, 3, 3, 3, 3, 2, 3, 2, 2, 2, 3, 2, 2, 2, 2, 3, 3, 2, 3, 3, 3, 3, 3, 3, 3, 2, 3, 3, 3, 2, 2, 3, 3, 3, 3, 0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 1, 1, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 2, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 1, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3]),
        Operation(4, 0, [0]),
        Operation(4, 0, [1]),
        Operation(4, 0, [2]),
    ]),
    SmallAlg([
        Operation(4, 4, [0, 0, 0, 0, 0, 3, 3, 3, 0, 3, 3, 3, 0, 3, 3, 3, 0, 1, 2, 3, 3, 1, 3, 3, 3, 2, 3, 3, 3, 3, 3, 3, 0, 0, 2, 0, 3, 2, 3, 3, 3, 2, 2, 3, 3, 3, 2, 3, 0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 0, 3, 0, 3, 3, 1, 3, 3, 0, 1, 3, 3, 3, 3, 3, 3, 1, 1, 3, 3, 1, 1, 1, 1, 1, 1, 2, 3, 1, 1, 3, 3, 0, 1, 3, 3, 3, 1, 2, 3, 2, 3, 2, 3, 3, 1, 3, 3, 3, 3, 3, 3, 3, 1, 3, 3, 3, 1, 3, 3, 3, 3,
                         3, 3, 0, 3, 2, 3, 3, 3, 2, 3, 0, 3, 2, 3, 3, 3, 3, 3, 3, 1, 2, 3, 1, 1, 1, 3, 3, 1, 2, 3, 3, 1, 2, 3, 0, 2, 2, 3, 2, 2, 2, 3, 2, 2, 2, 2, 3, 3, 2, 3, 3, 3, 2, 3, 3, 3, 3, 3, 3, 3, 2, 3, 3, 3, 2, 3, 0, 3, 0, 3, 3, 3, 3, 3, 0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 1, 3, 3, 3, 3, 2, 3, 3, 1, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 2, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3]),
        Operation(4, 0, [0]),
        Operation(4, 0, [1]),
        Operation(4, 0, [2]),
    ]),
    SmallAlg([
        Operation(4, 4, [0, 0, 0, 0, 0, 2, 3, 3, 0, 3, 2, 3, 0, 3, 3, 3, 0, 1, 3, 3, 1, 1, 1, 1, 3, 1, 3, 3, 3, 1, 3, 3, 0, 2, 2, 3, 3, 2, 3, 3, 2, 2, 2, 3, 3, 2, 2, 3, 0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 2, 3, 3, 3, 3, 3, 0, 0, 0, 0, 0, 1, 3, 3, 0, 3, 3, 3, 0, 3, 3, 3, 3, 1, 3, 3, 1, 1, 1, 1, 3, 1, 3, 3, 3, 1, 3, 3, 3, 3, 2, 3, 2, 1, 2, 3, 3, 2, 2, 3, 3, 3, 2, 3, 3, 3, 3, 3, 3, 1, 3, 3, 3, 3, 3, 3, 3, 3,
                         3, 3, 0, 0, 0, 0, 0, 2, 2, 3, 0, 3, 2, 3, 0, 3, 3, 3, 3, 1, 2, 2, 1, 1, 1, 1, 3, 1, 2, 3, 3, 1, 3, 3, 3, 3, 2, 2, 3, 3, 2, 3, 2, 2, 2, 2, 3, 3, 2, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 2, 3, 3, 3, 3, 3, 0, 0, 0, 0, 0, 3, 3, 3, 0, 3, 3, 3, 0, 3, 3, 3, 3, 1, 3, 3, 1, 1, 1, 1, 3, 1, 3, 3, 3, 1, 3, 3, 3, 3, 2, 3, 3, 3, 3, 3, 2, 3, 2, 2, 3, 3, 2, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3]),
        Operation(4, 0, [0]),
        Operation(4, 0, [1]),
        Operation(4, 0, [2]),
    ]),
    SmallAlg([
        Operation(4, 4, [0, 0, 0, 0, 0, 2, 2, 2, 0, 2, 2, 2, 0, 2, 2, 2, 0, 2, 2, 2, 2, 1, 3, 3, 2, 2, 2, 3, 2, 3, 2, 3, 0, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 0, 2, 2, 2, 2, 2, 3, 3, 2, 2, 2, 3, 2, 2, 2, 3, 0, 2, 2, 2, 3, 1, 2, 3, 2, 3, 2, 2, 2, 2, 2, 3, 3, 1, 3, 3, 1, 1, 1, 1, 2, 1, 2, 2, 2, 1, 2, 2, 2, 2, 2, 2, 2, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 3, 3, 3, 3, 2, 1, 3, 2, 2, 2, 2, 2, 2, 2,
                         2, 3, 0, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 3, 2, 1, 2, 2, 2, 2, 2, 3, 2, 3, 2, 3, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 3, 2, 3, 2, 3, 2, 2, 2, 2, 2, 3, 2, 3, 0, 2, 2, 2, 2, 3, 2, 2, 2, 3, 2, 2, 2, 3, 2, 3, 3, 3, 3, 3, 2, 1, 2, 3, 2, 2, 2, 3, 3, 3, 3, 3, 2, 2, 2, 2, 2, 2, 2, 2, 2, 3, 2, 3, 2, 3, 2, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 2, 3, 3, 3, 3, 3, 3]),
        Operation(4, 0, [0]),
        Operation(4, 0, [1]),
        Operation(4, 0, [2]),
    ]),
    SmallAlg([
        Operation(4, 4, [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 3, 3, 1, 3, 3, 3, 1, 2, 3, 3, 1, 3, 3, 0, 3, 2, 3, 3, 2, 3, 3, 3, 2, 2, 3, 3, 3, 3, 3, 0, 3, 0, 3, 3, 3, 3, 3, 3, 3, 2, 3, 3, 3, 3, 3, 0, 2, 0, 0, 3, 1, 2, 3, 3, 2, 3, 3, 3, 1, 3, 3, 3, 1, 1, 3, 1, 1, 1, 1, 1, 1, 1, 1, 3, 1, 1, 3, 3, 2, 3, 3, 3, 1, 3, 3, 3, 1, 2, 3, 3, 1, 3, 3, 3, 1, 3, 3, 3, 1, 3, 3, 3, 1, 3, 3, 3, 3,
                         3, 3, 0, 2, 2, 0, 0, 1, 3, 3, 3, 2, 2, 3, 3, 3, 3, 3, 3, 2, 3, 3, 3, 1, 3, 3, 3, 1, 2, 3, 3, 3, 3, 3, 2, 2, 2, 2, 2, 3, 2, 3, 2, 2, 2, 2, 3, 3, 2, 3, 3, 2, 3, 3, 3, 1, 3, 3, 3, 3, 2, 3, 3, 3, 3, 3, 0, 0, 0, 0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 1, 3, 3, 3, 1, 3, 3, 3, 1, 3, 3, 3, 1, 3, 3, 3, 3, 2, 3, 3, 1, 3, 3, 3, 3, 2, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3]),
        Operation(4, 0, [0]),
        Operation(4, 0, [1]),
        Operation(4, 0, [2]),
    ]),
    SmallAlg([
        Operation(4, 4, [0, 0, 0, 0, 0, 3, 3, 3, 0, 3, 2, 3, 0, 3, 3, 3, 0, 3, 2, 3, 3, 1, 3, 3, 3, 1, 3, 3, 3, 3, 3, 3, 0, 2, 2, 3, 0, 1, 2, 3, 0, 2, 2, 3, 3, 3, 3, 3, 0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 0, 1, 0, 3, 0, 1, 3, 3, 0, 3, 2, 3, 0, 3, 3, 3, 0, 1, 2, 3, 1, 1, 1, 1, 1, 1, 1, 1, 3, 1, 3, 3, 2, 2, 2, 2, 3, 1, 1, 3, 2, 1, 2, 2, 3, 3, 3, 3, 0, 3, 3, 3, 3, 1, 3, 3, 3, 1, 3, 3, 3, 3,
                         3, 3, 0, 0, 0, 0, 0, 3, 3, 3, 2, 3, 2, 3, 0, 3, 3, 3, 0, 1, 2, 3, 3, 1, 3, 3, 3, 1, 2, 3, 3, 1, 2, 3, 2, 2, 2, 3, 3, 3, 2, 3, 2, 2, 2, 2, 3, 3, 2, 3, 0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 2, 3, 3, 3, 3, 3, 0, 3, 0, 3, 0, 3, 3, 3, 0, 3, 3, 3, 0, 3, 3, 3, 0, 3, 2, 3, 3, 1, 3, 3, 3, 1, 3, 3, 3, 3, 3, 3, 0, 2, 3, 3, 3, 3, 3, 3, 3, 2, 2, 3, 3, 3, 3, 3, 0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3]),
        Operation(4, 0, [0]),
        Operation(4, 0, [1]),
        Operation(4, 0, [2]),
    ]),
    SmallAlg([
        Operation(4, 4, [0, 0, 0, 0, 0, 1, 3, 3, 0, 2, 2, 3, 0, 3, 3, 3, 0, 3, 2, 3, 3, 1, 3, 3, 3, 3, 2, 3, 3, 3, 3, 3, 0, 3, 3, 3, 3, 1, 3, 3, 3, 3, 2, 3, 3, 3, 3, 3, 0, 3, 3, 3, 3, 1, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 0, 2, 2, 3, 3, 1, 3, 3, 2, 3, 3, 3, 3, 3, 3, 3, 0, 1, 3, 3, 1, 1, 1, 1, 3, 1, 3, 3, 3, 1, 3, 3, 0, 3, 3, 3, 3, 1, 3, 3, 3, 2, 2, 2, 3, 3, 3, 3, 0, 3, 2, 3, 3, 1, 3, 3, 3, 3, 2, 3, 3, 3,
                         3, 3, 0, 2, 3, 3, 3, 1, 2, 3, 3, 3, 2, 3, 3, 3, 3, 3, 0, 3, 2, 2, 3, 1, 3, 3, 2, 2, 2, 3, 3, 3, 2, 3, 0, 3, 2, 3, 3, 1, 2, 3, 2, 2, 2, 2, 3, 3, 2, 3, 0, 2, 3, 3, 3, 1, 2, 3, 2, 2, 2, 2, 3, 3, 3, 3, 0, 3, 3, 3, 3, 1, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 0, 3, 3, 3, 3, 1, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 0, 3, 3, 3, 3, 1, 3, 3, 3, 2, 2, 3, 3, 3, 3, 3, 0, 3, 3, 3, 3, 1, 3, 3, 3, 3, 2, 3, 3, 3, 3, 3]),
        Operation(4, 0, [0]),
        Operation(4, 0, [1]),
        Operation(4, 0, [2]),
    ]),
    SmallAlg([
        Operation(4, 4, [0, 0, 0, 0, 0, 1, 3, 3, 0, 2, 3, 3, 0, 3, 3, 3, 0, 1, 2, 3, 0, 1, 3, 3, 0, 1, 3, 3, 0, 1, 3, 3, 0, 3, 3, 3, 0, 1, 2, 2, 0, 3, 2, 3, 0, 3, 2, 3, 0, 3, 3, 3, 0, 1, 3, 3, 0, 3, 3, 3, 0, 3, 3, 3, 0, 1, 3, 3, 0, 1, 2, 3, 0, 1, 3, 3, 0, 1, 3, 3, 0, 1, 3, 3, 1, 1, 1, 1, 2, 1, 2, 3, 3, 1, 3, 3, 0, 1, 2, 3, 3, 1, 3, 3, 2, 1, 2, 2, 3, 1, 3, 3, 0, 1, 3, 3, 3, 1, 3, 3, 3, 1, 3, 3, 3, 1,
                         3, 3, 0, 3, 3, 3, 0, 1, 3, 3, 0, 3, 2, 3, 0, 3, 3, 3, 0, 1, 3, 3, 3, 1, 3, 3, 3, 1, 2, 3, 3, 1, 2, 3, 0, 3, 2, 3, 3, 1, 2, 3, 2, 2, 2, 2, 3, 3, 2, 3, 0, 3, 3, 3, 3, 1, 3, 3, 3, 3, 2, 3, 3, 3, 3, 3, 0, 3, 3, 3, 0, 1, 3, 3, 0, 3, 2, 3, 0, 3, 3, 3, 0, 1, 3, 3, 3, 1, 3, 3, 3, 1, 3, 3, 3, 1, 3, 3, 0, 3, 3, 3, 3, 1, 2, 3, 3, 2, 2, 3, 3, 3, 3, 3, 0, 3, 3, 3, 3, 1, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3]),
        Operation(4, 0, [0]),
        Operation(4, 0, [1]),
        Operation(4, 0, [2]),
    ]),
    SmallAlg([
        Operation(4, 4, [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 3, 3, 2, 3, 3, 3, 0, 3, 3, 3, 0, 0, 0, 0, 0, 3, 3, 3, 0, 3, 2, 3, 0, 3, 3, 3, 0, 0, 0, 0, 3, 3, 3, 3, 0, 3, 3, 3, 3, 3, 3, 3, 0, 3, 3, 3, 1, 1, 1, 1, 2, 3, 2, 3, 3, 3, 3, 3, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 3, 2, 3, 3, 3, 1, 1, 3, 3, 3, 3, 2, 3, 3, 3, 3, 3, 3, 3, 3, 3, 1, 1, 3, 3, 3, 3, 3, 3, 3, 3,
                         3, 3, 0, 2, 2, 3, 2, 3, 3, 3, 2, 2, 2, 2, 3, 3, 3, 3, 3, 3, 2, 3, 2, 1, 2, 3, 2, 2, 2, 2, 3, 3, 3, 3, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 3, 3, 2, 3, 2, 3, 2, 3, 2, 2, 2, 2, 3, 3, 2, 3, 0, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 1, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 2, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3]),
        Operation(4, 0, [0]),
        Operation(4, 0, [1]),
        Operation(4, 0, [2]),
    ]),
    SmallAlg([
        Operation(4, 4, [0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 2, 2, 2, 2, 1, 1, 3, 2, 1, 2, 2, 2, 1, 2, 3, 0, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 0, 2, 2, 2, 2, 3, 2, 3, 2, 2, 2, 2, 2, 3, 2, 3, 0, 0, 0, 0, 0, 1, 3, 2, 0, 3, 2, 2, 0, 3, 2, 3, 2, 1, 3, 1, 1, 1, 1, 1, 2, 1, 3, 1, 3, 1, 3, 1, 2, 3, 2, 2, 3, 1, 3, 3, 2, 3, 2, 2, 2, 3, 2, 2, 2, 3, 3, 3, 3, 1, 3, 3, 2, 3, 3, 3, 3, 3,
                         3, 3, 0, 0, 0, 0, 0, 3, 2, 2, 0, 2, 2, 2, 0, 3, 2, 2, 2, 1, 2, 2, 1, 1, 1, 3, 2, 2, 2, 2, 2, 3, 2, 2, 2, 2, 2, 2, 2, 3, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 3, 2, 2, 2, 2, 2, 2, 2, 3, 0, 0, 0, 0, 0, 3, 2, 3, 0, 2, 2, 2, 0, 3, 2, 3, 2, 1, 2, 2, 1, 1, 1, 1, 2, 1, 2, 2, 3, 1, 3, 3, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 3, 2, 3, 2, 3, 2, 3, 3, 3, 2, 3, 2, 3, 2, 3, 3, 3, 3, 3]),
        Operation(4, 0, [0]),
        Operation(4, 0, [1]),
        Operation(4, 0, [2]),
    ]),
    SmallAlg([
        Operation(4, 4, [0, 0, 0, 0, 0, 3, 2, 2, 0, 2, 2, 2, 0, 2, 2, 2, 0, 2, 2, 2, 2, 1, 3, 2, 2, 2, 2, 2, 2, 2, 2, 2, 0, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 0, 2, 2, 2, 2, 3, 2, 3, 2, 2, 2, 3, 2, 3, 2, 3, 0, 2, 2, 2, 3, 1, 3, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 1, 2, 2, 1, 1, 1, 1, 2, 1, 2, 2, 3, 1, 2, 2, 2, 3, 2, 2, 2, 1, 2, 2, 2, 3, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 3, 1, 2, 2, 3, 3, 3, 2, 3, 2,
                         2, 3, 0, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 3, 1, 2, 2, 2, 2, 2, 2, 3, 2, 2, 2, 2, 2, 2, 2, 2, 3, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 3, 2, 3, 2, 2, 2, 3, 0, 2, 2, 2, 3, 3, 2, 3, 2, 2, 2, 2, 2, 3, 2, 3, 2, 2, 3, 2, 2, 1, 2, 3, 2, 3, 3, 2, 2, 3, 3, 3, 2, 2, 2, 3, 2, 2, 2, 2, 2, 2, 2, 2, 2, 3, 2, 3, 2, 3, 2, 3, 3, 3, 2, 3, 2, 3, 2, 3, 3, 3, 3, 3]),
        Operation(4, 0, [0]),
        Operation(4, 0, [1]),
        Operation(4, 0, [2]),
    ]),
]


def test0():
    alg = find_algebra(2, (0, 1, 0), 4, [])


def test1():
    algs = list(ALGS4)
    arity = 4
    num_steps = 4

    next_alg = None
    multi_steps = []
    while True:
        steps = find_term(arity,
                          algs + [next_alg] if next_alg else algs,
                          num_steps)
        if not steps:
            break

        multi_steps.append(steps)
        alg = find_algebra(4, (0, 1, 2), arity, multi_steps)
        if alg is None:
            break

        next_alg = alg

    print("Done")
    print(next_alg)


def test2():
    steps = [
        [2, 1, 0],
        [1, 0, 4],
        [3, 0, 4],
        [0, 5, 6],
    ]

    find_algebra(8, (0, 1, 2), 3, [steps])


if __name__ == '__main__':
    test1()
