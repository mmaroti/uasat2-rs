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
from typing import Any, List, Sequence, Optional
from uasat import Solver, BitVec, Operation


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
                         [oper.arity for oper in operations])
        self.operations = operations

    @staticmethod
    def unknown(solver: Solver, size: int, signature: List[int]) -> 'SmallAlg':
        assert size >= 1 and all(arity >= 0 for arity in signature)
        operations = [Operation(size, arity, solver) for arity in signature]
        return SmallAlg(operations)

    def apply(self, op: int, args: List[BitVec]) -> BitVec:
        assert len(args) == self.signature[op]
        opers = [Operation(self.size, 0, arg) for arg in args]
        res = self.operations[op].compose(opers)
        assert res.length == self.size
        return res.table

    def element(self, index: int) -> BitVec:
        assert 0 <= index < self.size
        return Operation.constant(self.size, index).table

    def decode_elem(self, elem: BitVec) -> Any:
        return Operation(self.size, 0, elem.get_value()).decode()[0]

    def solution(self) -> 'SmallAlg':
        return SmallAlg([op.solution() for op in self.operations])

    def __repr__(self) -> str:
        result = "SmallAlg([\n"
        for op in self.operations:
            result += f"    Operation({op.size}, {op.arity}, {op.decode()}),\n"
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
    def __init__(self, algs: List[SmallAlg]):
        self.solver = Solver()

        self.alg = ProductAlg(algs)
        elem0 = self.alg.combine([alg.element(0) for alg in algs])
        elem1 = self.alg.combine([alg.element(1) for alg in algs])

        self.rel = ProductAlg([self.alg, self.alg, self.alg])
        self.tuples = []
        self.tuples.append(self.rel.combine([elem0, elem0, elem1]))
        self.tuples.append(self.rel.combine([elem0, elem1, elem0]))
        self.tuples.append(self.rel.combine([elem1, elem0, elem0]))
        self.tuples.append(self.rel.combine([elem1, elem1, elem0]))

        self.steps = []

    @staticmethod
    def choice(selector: Operation, choices: List[BitVec]) -> BitVec:
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
        sel_arg0 = Operation(len(self.tuples), 0, self.solver)
        sel_arg1 = Operation(len(self.tuples), 0, self.solver)
        sel_arg2 = Operation(len(self.tuples), 0, self.solver)
        sel_arg3 = Operation(len(self.tuples), 0, self.solver)

        arg0 = Generator.choice(sel_arg0, self.tuples)
        arg1 = Generator.choice(sel_arg1, self.tuples)
        arg2 = Generator.choice(sel_arg2, self.tuples)
        arg3 = Generator.choice(sel_arg3, self.tuples)

        out0 = self.rel.apply(0, [arg0, arg1, arg2, arg3])
        out1 = self.rel.apply(1, [arg0, arg1, arg2, arg3])

        sel_oper = Operation(2, 0, self.solver)
        out = Generator.choice(sel_oper, [out0, out1])
        assert len(out) == self.rel.length

        self.tuples.append(out)
        self.steps.append([sel_oper, sel_arg0, sel_arg1, sel_arg2, sel_arg3])

    def final_loop(self):
        last = self.rel.takeapart(self.tuples[-1])
        last[0].comp_eq(last[1]).ensure_all()
        last[0].comp_eq(last[2]).ensure_all()

    def decode(self) -> Optional[List[List[int]]]:
        if False:
            print("Tuples:")
            for t in self.tuples:
                print(self.rel.decode_elem(t))

        print("Steps:")
        steps = []
        for s in self.steps:
            sel_oper = s[0].solution().decode()[0]
            sel_arg0 = s[1].solution().decode()[0]
            sel_arg1 = s[2].solution().decode()[0]
            sel_arg2 = s[3].solution().decode()[0]
            sel_arg3 = s[4].solution().decode()[0]
            steps.append([sel_oper, sel_arg0, sel_arg1, sel_arg2, sel_arg3])
            print(f"[{sel_oper}, {sel_arg0}, {sel_arg1}, {sel_arg2}, {sel_arg3}],")
        return steps


def find_term(algs: List[SmallAlg], num_steps: int) -> Optional[List[List[int]]]:
    gen = Generator(algs)
    for _ in range(num_steps):
        gen.add_step()
    gen.final_loop()
    if gen.solver.solve():
        return gen.decode()
    else:
        print("Term not solvable")


def find_algebra(multi_steps: List[List[List[int]]], size: int = 2) -> Optional[SmallAlg]:
    solver = Solver()
    alg = SmallAlg([
        Operation(size, 4, solver),
        Operation(size, 4, solver),
    ])

    assert alg.signature == [4, 4]
    f1, g1 = alg.operations

    f1.polymer([0, 0, 1, 1]).comp_eq(
        g1.polymer([0, 0, 1, 1])).ensure_all()
    f1.polymer([0, 1, 0, 1]).comp_eq(
        g1.polymer([0, 1, 0, 1])).ensure_all()

    Operation.projection(alg.size, 2, 0).comp_eq(
        f1.polymer([0, 0, 0, 1])).ensure_all()
    Operation.projection(alg.size, 2, 1).comp_eq(
        g1.polymer([0, 0, 0, 1])).ensure_all()

    elem0 = alg.element(0)
    elem1 = alg.element(1)

    def term(steps, e0, e1, e2, e3):
        e = [e0, e1, e2, e3]
        for s in steps:
            e.append(alg.apply(s[0], [e[s[1]], e[s[2]], e[s[3]], e[s[4]]]))
        return e[-1]

    for steps in multi_steps:
        tup0 = term(steps, elem0, elem0, elem1, elem1)
        tup1 = term(steps, elem0, elem1, elem0, elem1)
        tup2 = term(steps, elem1, elem0, elem0, elem0)
        (tup0.comp_ne(tup1) | tup1.comp_ne(tup2)).ensure_all()

    if solver.solve():
        solution = alg.solution()
        print(solution)
        return solution
    else:
        print("Algebra not solvable")
        return None


ALGS2 = [
    # x+y+z and u
    SmallAlg([
        Operation(2, 4, [0, 1, 1, 0, 1, 0, 0, 1, 0, 1, 1, 0, 1, 0, 0, 1]),
        Operation(2, 4, [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1]),
    ]),
    # maj(y,z,u) and u
    SmallAlg([
        Operation(2, 4, [0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 1, 1, 1, 1, 1, 1]),
        Operation(2, 4, [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1]),
    ]),
    # x and y+z+u
    SmallAlg([
        Operation(2, 4, [0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1]),
        Operation(2, 4, [0, 0, 1, 1, 1, 1, 0, 0, 1, 1, 0, 0, 0, 0, 1, 1]),
    ]),

    # 2nd step
    SmallAlg([
        Operation(2, 4, [0, 0, 0, 1, 0, 0, 0, 1, 0, 1, 1, 0, 1, 0, 0, 1]),
        Operation(2, 4, [0, 1, 0, 1, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 0, 1]),
    ]),

    # 3rd step
    SmallAlg([
        Operation(2, 4, [0, 0, 1, 0, 1, 1, 1, 1, 0, 0, 0, 0, 1, 0, 1, 1]),
        Operation(2, 4, [0, 0, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 1, 1]),
    ]),
    SmallAlg([
        Operation(2, 4, [0, 1, 0, 0, 1, 1, 0, 1, 0, 0, 1, 1, 1, 1, 1, 1]),
        Operation(2, 4, [0, 0, 0, 0, 0, 1, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1]),
    ]),
    SmallAlg([
        Operation(2, 4, [0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 1, 1, 0, 1, 0, 1]),
        Operation(2, 4, [0, 1, 1, 0, 1, 1, 0, 0, 1, 0, 1, 0, 0, 0, 1, 1]),
    ]),

    # 4th step
    SmallAlg([
        Operation(2, 4, [0, 1, 1, 1, 1, 0, 1, 1, 0, 0, 1, 1, 0, 0, 0, 1]),
        Operation(2, 4, [0, 1, 1, 1, 0, 0, 0, 0, 1, 0, 1, 1, 0, 0, 1, 1]),
    ]),
    SmallAlg([
        Operation(2, 4, [0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1]),
        Operation(2, 4, [0, 1, 1, 1, 0, 0, 0, 0, 1, 1, 1, 1, 0, 1, 1, 1]),
    ]),
    SmallAlg([
        Operation(2, 4, [0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 1, 0, 1, 1]),
        Operation(2, 4, [0, 0, 0, 1, 0, 0, 0, 0, 1, 1, 1, 0, 1, 1, 1, 1]),
    ]),
    SmallAlg([
        Operation(2, 4, [0, 0, 1, 0, 1, 1, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1]),
        Operation(2, 4, [0, 0, 0, 0, 0, 1, 0, 0, 1, 1, 1, 1, 0, 0, 1, 1]),
    ]),
    SmallAlg([
        Operation(2, 4, [0, 1, 0, 0, 1, 1, 0, 1, 0, 0, 0, 1, 1, 1, 0, 1]),
        Operation(2, 4, [0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 1, 0, 0, 1]),
    ]),

    # 5th step
    SmallAlg([
        Operation(2, 4, [0, 0, 1, 0, 0, 0, 1, 1, 0, 0, 1, 0, 1, 1, 1, 1]),
        Operation(2, 4, [0, 1, 1, 0, 1, 0, 0, 0, 1, 1, 1, 0, 1, 1, 0, 1]),
    ]),
    SmallAlg([
        Operation(2, 4, [0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0, 1, 1, 1, 1]),
        Operation(2, 4, [0, 1, 0, 0, 0, 1, 0, 0, 1, 1, 0, 1, 1, 1, 0, 1]),
    ]),
    SmallAlg([
        Operation(2, 4, [0, 0, 0, 0, 1, 1, 0, 1, 0, 1, 1, 1, 1, 0, 1, 1]),
        Operation(2, 4, [0, 0, 0, 0, 1, 1, 1, 0, 1, 0, 1, 1, 1, 0, 0, 1]),
    ]),
    SmallAlg([
        Operation(2, 4, [0, 1, 0, 0, 1, 0, 0, 1, 0, 1, 0, 1, 1, 1, 0, 1]),
        Operation(2, 4, [0, 0, 1, 0, 1, 0, 1, 0, 1, 0, 0, 1, 1, 0, 1, 1]),
    ]),
    SmallAlg([
        Operation(2, 4, [0, 1, 0, 1, 1, 0, 0, 1, 0, 1, 0, 0, 0, 0, 1, 1]),
        Operation(2, 4, [0, 1, 1, 1, 0, 0, 0, 0, 1, 1, 0, 0, 0, 1, 1, 1]),
    ]),

    # 6th step
    SmallAlg([
        Operation(2, 4, [0, 0, 1, 0, 1, 0, 1, 1, 0, 0, 1, 0, 1, 1, 0, 1]),
        Operation(2, 4, [0, 0, 0, 0, 1, 0, 1, 0, 1, 0, 1, 1, 1, 1, 1, 1]),
    ]),
    SmallAlg([
        Operation(2, 4, [0, 0, 1, 0, 0, 1, 0, 1, 0, 1, 1, 0, 1, 1, 0, 1]),
        Operation(2, 4, [0, 1, 1, 0, 0, 1, 1, 0, 1, 1, 1, 1, 1, 0, 0, 1]),
    ]),
    SmallAlg([
        Operation(2, 4, [0, 0, 1, 1, 0, 0, 1, 1, 0, 1, 1, 0, 1, 1, 0, 1]),
        Operation(2, 4, [0, 1, 1, 1, 0, 0, 1, 0, 1, 1, 1, 0, 1, 1, 0, 1]),
    ]),
    SmallAlg([
        Operation(2, 4, [0, 1, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 0, 1]),
        Operation(2, 4, [0, 0, 0, 1, 0, 0, 1, 0, 1, 1, 1, 1, 0, 1, 1, 1]),
    ]),
    SmallAlg([
        Operation(2, 4, [0, 1, 0, 0, 1, 0, 1, 1, 0, 0, 1, 1, 1, 0, 0, 1]),
        Operation(2, 4, [0, 1, 1, 0, 0, 0, 0, 0, 1, 0, 1, 1, 1, 1, 1, 1]),
    ]),
    SmallAlg([
        Operation(2, 4, [0, 1, 1, 0, 1, 0, 1, 1, 0, 1, 1, 0, 1, 0, 1, 1]),
        Operation(2, 4, [0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 1, 0, 1, 1, 0, 1]),
    ]),
    SmallAlg([
        Operation(2, 4, [0, 1, 1, 1, 0, 0, 1, 1, 0, 0, 0, 1, 1, 0, 0, 1]),
        Operation(2, 4, [0, 0, 0, 1, 1, 0, 1, 0, 1, 0, 0, 0, 1, 0, 0, 1]),
    ]),
    SmallAlg([
        Operation(2, 4, [0, 0, 0, 0, 1, 1, 1, 1, 0, 1, 0, 0, 0, 0, 1, 1]),
        Operation(2, 4, [0, 1, 1, 0, 1, 1, 1, 0, 1, 0, 0, 1, 0, 0, 0, 1]),
    ]),
    SmallAlg([
        Operation(2, 4, [0, 0, 0, 1, 1, 1, 0, 1, 0, 0, 1, 0, 0, 0, 0, 1]),
        Operation(2, 4, [0, 0, 1, 1, 1, 1, 1, 0, 1, 0, 1, 0, 0, 0, 0, 1]),
    ]),
    SmallAlg([
        Operation(2, 4, [0, 0, 0, 1, 1, 0, 1, 1, 0, 0, 1, 0, 0, 0, 1, 1]),
        Operation(2, 4, [0, 0, 0, 1, 1, 0, 0, 0, 1, 1, 1, 1, 0, 1, 0, 1]),
    ]),

    # not sovable by any 2-element algebra:
    # [0, 3, 2, 1, 0],
    # [1, 3, 2, 1, 0],
    # [1, 5, 4, 5, 3],
    # [0, 6, 4, 6, 4],
    # [1, 6, 6, 4, 5],
    # [1, 8, 8, 4, 7],
]


def test1():
    algs = list(ALGS2)

    next_alg = None
    multi_steps = []
    while True:
        steps = find_term(algs + [next_alg] if next_alg else algs, 6)
        if not steps:
            break

        multi_steps.append(steps)
        alg = find_algebra(multi_steps, 3)
        if alg is None:
            break

        next_alg = alg

    print("Done")
    print(next_alg)


def test2():
    steps = [
        [0, 3, 2, 1, 0],
        [1, 3, 2, 1, 0],
        [1, 5, 4, 5, 3],
        [0, 6, 4, 6, 4],
        [1, 6, 6, 4, 5],
        [1, 8, 8, 4, 7],
    ]

    find_algebra([steps], 3)


if __name__ == '__main__':
    test1()
