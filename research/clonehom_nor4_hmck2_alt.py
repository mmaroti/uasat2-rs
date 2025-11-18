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

from typing import List, Optional
from uasat import Solver, BitVec, Constant, Relation, Operation, SmallAlg, ProductAlg


class Generator:
    def __init__(self, algs: List[SmallAlg]):
        self.solver = Solver()

        self.alg = ProductAlg(algs)
        elem0 = self.alg.combine([alg.encode_elem(0) for alg in algs])
        elem1 = self.alg.combine([alg.encode_elem(1) for alg in algs])

        self.rel = ProductAlg([self.alg, self.alg, self.alg])
        self.tuples = []
        self.tuples.append(self.rel.combine([elem0, elem0, elem1]))
        self.tuples.append(self.rel.combine([elem0, elem1, elem0]))
        self.tuples.append(self.rel.combine([elem1, elem0, elem0]))
        self.tuples.append(self.rel.combine([elem1, elem1, elem0]))

        self.steps = []

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
        sel_arg0 = Constant.variable(len(self.tuples), self.solver)
        sel_arg1 = Constant.variable(len(self.tuples), self.solver)
        sel_arg2 = Constant.variable(len(self.tuples), self.solver)
        sel_arg3 = Constant.variable(len(self.tuples), self.solver)

        arg0 = Generator.choice(sel_arg0, self.tuples)
        arg1 = Generator.choice(sel_arg1, self.tuples)
        arg2 = Generator.choice(sel_arg2, self.tuples)
        arg3 = Generator.choice(sel_arg3, self.tuples)

        sel_oper = len(self.steps) % 4
        out = self.rel.apply(sel_oper, [arg0, arg1, arg2, arg3])
        assert len(out) == self.rel.length

        self.tuples.append(out)
        self.steps.append([sel_oper, sel_arg0, sel_arg1, sel_arg2, sel_arg3])

    def final_loop(self):
        last = self.rel.splitup(self.tuples[-1])
        (~last[0] ^ last[1]).ensure_all()
        (~last[0] ^ last[2]).ensure_all()

    def decode(self) -> Optional[List[List[int]]]:
        if False:
            print("Tuples:")
            for t in self.tuples:
                print(self.rel.decode_elem(t))

        print("Steps:")
        steps = []
        for s in self.steps:
            sel_oper = s[0]
            sel_arg0 = s[1].solution().decode()
            sel_arg1 = s[2].solution().decode()
            sel_arg2 = s[3].solution().decode()
            sel_arg3 = s[4].solution().decode()
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

    alg = SmallAlg.variable(solver, size, [4, 4, 4, 4], partop=True)
    f1, g1, f2, g2 = alg.operations

    if True:
        mask = [Solver.FALSE for _ in range(size ** 4)]
        for i in range(size):
            for j in range(size):
                mask[(1 + size) * i + (size**2 + size**3) * j] = Solver.TRUE
                mask[(1 + size**2) * i + (size + size**3) * j] = Solver.TRUE
                mask[(1 + size + size**2) * i + (size**3) * j] = Solver.TRUE
        mask = Relation(size, 4, BitVec(Solver.CALC, mask))

        (f1.domain() ^ ~mask).ensure_all()
        (g1.domain() ^ ~mask).ensure_all()
        (f2.domain() ^ ~mask).ensure_all()
        (g2.domain() ^ ~mask).ensure_all()

    f1.polymer([0, 0, 1, 1]).comp_eq(g1.polymer([0, 0, 1, 1])).ensure_all()
    f1.polymer([0, 1, 0, 1]).comp_eq(g1.polymer([0, 1, 0, 1])).ensure_all()

    f2.polymer([0, 0, 1, 1]).comp_eq(g2.polymer([0, 0, 1, 1])).ensure_all()
    f2.polymer([0, 1, 0, 1]).comp_eq(g2.polymer([0, 1, 0, 1])).ensure_all()

    Operation.projection(alg.size, 2, 0).comp_eq(
        f1.polymer([0, 0, 0, 1])).ensure_all()
    g1.polymer([0, 0, 0, 1]).comp_eq(
        f2.polymer([0, 0, 0, 1])).ensure_all()
    g2.polymer([0, 0, 0, 1]).comp_eq(
        Operation.projection(alg.size, 2, 1)).ensure_all()

    elem0 = alg.encode_elem(0)
    elem1 = alg.encode_elem(1)

    def term(steps, e0, e1, e2, e3):
        e = [e0, e1, e2, e3]
        for s in steps:
            e.append(
                alg.apply(s[0], [e[s[1]], e[s[2]], e[s[3]], e[s[4]]], partop=True))
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
    SmallAlg([
        Operation(2, 4, [0, None, None, 1, None, 0, None,
                         1, 0, None, 1, None, 0, None, None, 1]),
        Operation(2, 4, [0, None, None, 1, None, 0, None,
                         1, 1, None, 1, None, 0, None, None, 1]),
        Operation(2, 4, [0, None, None, 0, None, 0, None,
                         1, 1, None, 1, None, 1, None, None, 1]),
        Operation(2, 4, [0, None, None, 0, None, 0, None,
                         0, 1, None, 1, None, 1, None, None, 1]),
    ]),
    SmallAlg([
        Operation(2, 4, [0, None, None, 0, None, 1, None,
                         1, 0, None, 0, None, 0, None, None, 1]),
        Operation(2, 4, [0, None, None, 0, None, 1, None,
                         1, 0, None, 0, None, 0, None, None, 1]),
        Operation(2, 4, [0, None, None, 1, None, 1, None,
                         1, 0, None, 0, None, 1, None, None, 1]),
        Operation(2, 4, [0, None, None, 1, None, 1, None,
                         0, 1, None, 0, None, 1, None, None, 1]),
    ]),
    SmallAlg([
        Operation(2, 4, [0, None, None, 1, None, 1, None,
                         1, 0, None, 0, None, 0, None, None, 1]),
        Operation(2, 4, [0, None, None, 1, None, 1, None,
                         1, 0, None, 0, None, 0, None, None, 1]),
        Operation(2, 4, [0, None, None, 0, None, 0, None,
                         1, 0, None, 1, None, 1, None, None, 1]),
        Operation(2, 4, [0, None, None, 0, None, 0, None,
                         0, 1, None, 1, None, 1, None, None, 1]),
    ]),
    SmallAlg([
        Operation(2, 4, [0, None, None, 1, None, 1, None,
                         1, 0, None, 0, None, 0, None, None, 1]),
        Operation(2, 4, [0, None, None, 1, None, 1, None,
                         1, 0, None, 0, None, 0, None, None, 1]),
        Operation(2, 4, [0, None, None, 1, None, 0, None,
                         1, 0, None, 1, None, 0, None, None, 1]),
        Operation(2, 4, [0, None, None, 1, None, 0, None,
                         0, 1, None, 1, None, 0, None, None, 1]),
    ]),
    SmallAlg([
        Operation(2, 4, [0, None, None, 1, None, 0, None,
                         1, 0, None, 1, None, 0, None, None, 1]),
        Operation(2, 4, [0, None, None, 1, None, 0, None,
                         1, 0, None, 1, None, 0, None, None, 1]),
        Operation(2, 4, [0, None, None, 0, None, 1, None,
                         1, 0, None, 0, None, 1, None, None, 1]),
        Operation(2, 4, [0, None, None, 0, None, 1, None,
                         0, 1, None, 0, None, 1, None, None, 1]),
    ]),
    SmallAlg([
        Operation(2, 4, [0, None, None, 0, None, 1, None,
                         1, 0, None, 0, None, 1, None, None, 1]),
        Operation(2, 4, [0, None, None, 0, None, 1, None,
                         1, 0, None, 0, None, 1, None, None, 1]),
        Operation(2, 4, [0, None, None, 1, None, 0, None,
                         1, 0, None, 1, None, 1, None, None, 1]),
        Operation(2, 4, [0, None, None, 1, None, 0, None,
                         0, 1, None, 1, None, 1, None, None, 1]),
    ]),
    SmallAlg([
        Operation(2, 4, [0, None, None, 1, None, 1, None,
                         1, 0, None, 0, None, 0, None, None, 1]),
        Operation(2, 4, [0, None, None, 1, None, 1, None,
                         1, 0, None, 0, None, 0, None, None, 1]),
        Operation(2, 4, [0, None, None, 0, None, 1, None,
                         1, 0, None, 1, None, 1, None, None, 1]),
        Operation(2, 4, [0, None, None, 0, None, 1, None,
                         0, 1, None, 1, None, 1, None, None, 1]),
    ]),
    SmallAlg([
        Operation(2, 4, [0, None, None, 1, None, 1, None,
                         1, 0, None, 1, None, 0, None, None, 1]),
        Operation(2, 4, [0, None, None, 1, None, 1, None,
                         1, 1, None, 1, None, 0, None, None, 1]),
        Operation(2, 4, [0, None, None, 0, None, 1, None,
                         1, 1, None, 0, None, 0, None, None, 1]),
        Operation(2, 4, [0, None, None, 0, None, 1, None,
                         0, 1, None, 0, None, 0, None, None, 1]),
    ]),
    SmallAlg([
        Operation(2, 4, [0, None, None, 1, None, 0, None,
                         1, 0, None, 1, None, 0, None, None, 1]),
        Operation(2, 4, [0, None, None, 1, None, 0, None,
                         0, 1, None, 1, None, 0, None, None, 1]),
        Operation(2, 4, [0, None, None, 0, None, 0, None,
                         0, 1, None, 1, None, 1, None, None, 1]),
        Operation(2, 4, [0, None, None, 0, None, 0, None,
                         0, 1, None, 1, None, 1, None, None, 1]),
    ]),
    SmallAlg([
        Operation(2, 4, [0, None, None, 1, None, 1, None,
                         1, 0, None, 0, None, 0, None, None, 1]),
        Operation(2, 4, [0, None, None, 1, None, 1, None,
                         1, 0, None, 0, None, 0, None, None, 1]),
        Operation(2, 4, [0, None, None, 1, None, 0, None,
                         1, 0, None, 1, None, 1, None, None, 1]),
        Operation(2, 4, [0, None, None, 1, None, 0, None,
                         0, 1, None, 1, None, 1, None, None, 1]),
    ]),
    SmallAlg([
        Operation(2, 4, [0, None, None, 0, None, 1, None,
                         1, 0, None, 1, None, 1, None, None, 1]),
        Operation(2, 4, [0, None, None, 0, None, 1, None,
                         0, 1, None, 1, None, 1, None, None, 1]),
        Operation(2, 4, [0, None, None, 0, None, 0, None,
                         0, 1, None, 1, None, 1, None, None, 1]),
        Operation(2, 4, [0, None, None, 0, None, 0, None,
                         0, 1, None, 1, None, 1, None, None, 1]),
    ]),
    SmallAlg([
        Operation(2, 4, [0, None, None, 1, None, 0, None,
                         1, 0, None, 0, None, 1, None, None, 1]),
        Operation(2, 4, [0, None, None, 1, None, 0, None,
                         0, 0, None, 0, None, 1, None, None, 1]),
        Operation(2, 4, [0, None, None, 1, None, 1, None,
                         0, 0, None, 0, None, 1, None, None, 1]),
        Operation(2, 4, [0, None, None, 1, None, 1, None,
                         0, 1, None, 0, None, 1, None, None, 1]),
    ]),
    SmallAlg([
        Operation(2, 4, [0, None, None, 0, None, 0, None,
                         1, 0, None, 1, None, 1, None, None, 1]),
        Operation(2, 4, [0, None, None, 0, None, 0, None,
                         0, 1, None, 1, None, 1, None, None, 1]),
        Operation(2, 4, [0, None, None, 0, None, 0, None,
                         0, 1, None, 1, None, 1, None, None, 1]),
        Operation(2, 4, [0, None, None, 0, None, 0, None,
                         0, 1, None, 1, None, 1, None, None, 1]),
    ]),
    SmallAlg([
        Operation(2, 4, [0, None, None, 0, None, 1, None,
                         1, 0, None, 0, None, 1, None, None, 1]),
        Operation(2, 4, [0, None, None, 0, None, 1, None,
                         0, 1, None, 0, None, 1, None, None, 1]),
        Operation(2, 4, [0, None, None, 0, None, 0, None,
                         0, 1, None, 1, None, 1, None, None, 1]),
        Operation(2, 4, [0, None, None, 0, None, 0, None,
                         0, 1, None, 1, None, 1, None, None, 1]),
    ]),
    SmallAlg([
        Operation(2, 4, [0, None, None, 1, None, 0, None,
                         1, 0, None, 0, None, 1, None, None, 1]),
        Operation(2, 4, [0, None, None, 1, None, 0, None,
                         0, 1, None, 0, None, 1, None, None, 1]),
        Operation(2, 4, [0, None, None, 0, None, 1, None,
                         0, 1, None, 0, None, 1, None, None, 1]),
        Operation(2, 4, [0, None, None, 0, None, 1, None,
                         0, 1, None, 0, None, 1, None, None, 1]),
    ]),
    SmallAlg([
        Operation(2, 4, [0, None, None, 0, None, 0, None,
                         1, 0, None, 0, None, 0, None, None, 1]),
        Operation(2, 4, [0, None, None, 0, None, 0, None,
                         1, 1, None, 0, None, 0, None, None, 1]),
        Operation(2, 4, [0, None, None, 0, None, 1, None,
                         1, 1, None, 1, None, 0, None, None, 1]),
        Operation(2, 4, [0, None, None, 0, None, 1, None,
                         0, 1, None, 1, None, 0, None, None, 1]),
    ]),
    SmallAlg([
        Operation(2, 4, [0, None, None, 0, None, 0, None,
                         1, 0, None, 0, None, 0, None, None, 1]),
        Operation(2, 4, [0, None, None, 0, None, 0, None,
                         1, 0, None, 0, None, 0, None, None, 1]),
        Operation(2, 4, [0, None, None, 1, None, 0, None,
                         1, 0, None, 0, None, 1, None, None, 1]),
        Operation(2, 4, [0, None, None, 1, None, 0, None,
                         0, 1, None, 0, None, 1, None, None, 1]),
    ]),
    SmallAlg([
        Operation(2, 4, [0, None, None, 0, None, 1, None,
                         1, 0, None, 1, None, 1, None, None, 1]),
        Operation(2, 4, [0, None, None, 0, None, 1, None,
                         0, 0, None, 1, None, 1, None, None, 1]),
        Operation(2, 4, [0, None, None, 1, None, 1, None,
                         0, 0, None, 1, None, 0, None, None, 1]),
        Operation(2, 4, [0, None, None, 1, None, 1, None,
                         0, 1, None, 1, None, 0, None, None, 1]),
    ]),
    SmallAlg([
        Operation(2, 4, [0, None, None, 0, None, 0, None,
                         1, 0, None, 0, None, 0, None, None, 1]),
        Operation(2, 4, [0, None, None, 0, None, 0, None,
                         1, 0, None, 0, None, 0, None, None, 1]),
        Operation(2, 4, [0, None, None, 1, None, 0, None,
                         1, 0, None, 1, None, 1, None, None, 1]),
        Operation(2, 4, [0, None, None, 1, None, 0, None,
                         0, 1, None, 1, None, 1, None, None, 1]),
    ]),
    SmallAlg([
        Operation(2, 4, [0, None, None, 0, None, 0, None,
                         1, 0, None, 0, None, 1, None, None, 1]),
        Operation(2, 4, [0, None, None, 0, None, 0, None,
                         0, 1, None, 0, None, 1, None, None, 1]),
        Operation(2, 4, [0, None, None, 1, None, 1, None,
                         0, 1, None, 0, None, 0, None, None, 1]),
        Operation(2, 4, [0, None, None, 1, None, 1, None,
                         0, 1, None, 0, None, 0, None, None, 1]),
    ]),
    SmallAlg([
        Operation(2, 4, [0, None, None, 0, None, 0, None,
                         1, 0, None, 1, None, 1, None, None, 1]),
        Operation(2, 4, [0, None, None, 0, None, 0, None,
                         1, 1, None, 1, None, 1, None, None, 1]),
        Operation(2, 4, [0, None, None, 0, None, 0, None,
                         1, 1, None, 1, None, 1, None, None, 1]),
        Operation(2, 4, [0, None, None, 0, None, 0, None,
                         0, 1, None, 1, None, 1, None, None, 1]),
    ]),
    SmallAlg([
        Operation(2, 4, [0, None, None, 1, None, 0, None,
                         1, 0, None, 0, None, 1, None, None, 1]),
        Operation(2, 4, [0, None, None, 1, None, 0, None,
                         1, 1, None, 0, None, 1, None, None, 1]),
        Operation(2, 4, [0, None, None, 0, None, 0, None,
                         1, 1, None, 1, None, 0, None, None, 1]),
        Operation(2, 4, [0, None, None, 0, None, 0, None,
                         0, 1, None, 1, None, 0, None, None, 1]),
    ]),
    SmallAlg([
        Operation(2, 4, [0, None, None, 1, None, 0, None,
                         1, 0, None, 1, None, 1, None, None, 1]),
        Operation(2, 4, [0, None, None, 1, None, 0, None,
                         0, 1, None, 1, None, 1, None, None, 1]),
        Operation(2, 4, [0, None, None, 1, None, 0, None,
                         0, 1, None, 1, None, 0, None, None, 1]),
        Operation(2, 4, [0, None, None, 1, None, 0, None,
                         0, 1, None, 1, None, 0, None, None, 1]),
    ]),
    SmallAlg([
        Operation(2, 4, [0, None, None, 1, None, 0, None,
                         1, 0, None, 0, None, 0, None, None, 1]),
        Operation(2, 4, [0, None, None, 1, None, 0, None,
                         0, 1, None, 0, None, 0, None, None, 1]),
        Operation(2, 4, [0, None, None, 1, None, 0, None,
                         0, 1, None, 1, None, 1, None, None, 1]),
        Operation(2, 4, [0, None, None, 1, None, 0, None,
                         0, 1, None, 1, None, 1, None, None, 1]),
    ]),
    SmallAlg([
        Operation(2, 4, [0, None, None, 1, None, 0, None,
                         1, 0, None, 1, None, 1, None, None, 1]),
        Operation(2, 4, [0, None, None, 1, None, 0, None,
                         0, 0, None, 1, None, 1, None, None, 1]),
        Operation(2, 4, [0, None, None, 0, None, 1, None,
                         0, 0, None, 1, None, 1, None, None, 1]),
        Operation(2, 4, [0, None, None, 0, None, 1, None,
                         0, 1, None, 1, None, 1, None, None, 1]),
    ]),
    SmallAlg([
        Operation(2, 4, [0, None, None, 0, None, 1, None,
                         1, 0, None, 1, None, 1, None, None, 1]),
        Operation(2, 4, [0, None, None, 0, None, 1, None,
                         1, 0, None, 1, None, 1, None, None, 1]),
        Operation(2, 4, [0, None, None, 0, None, 0, None,
                         1, 0, None, 1, None, 1, None, None, 1]),
        Operation(2, 4, [0, None, None, 0, None, 0, None,
                         0, 1, None, 1, None, 1, None, None, 1]),
    ]),
    SmallAlg([
        Operation(2, 4, [0, None, None, 0, None, 1, None,
                         1, 0, None, 1, None, 1, None, None, 1]),
        Operation(2, 4, [0, None, None, 0, None, 1, None,
                         0, 0, None, 1, None, 1, None, None, 1]),
        Operation(2, 4, [0, None, None, 0, None, 1, None,
                         0, 0, None, 0, None, 1, None, None, 1]),
        Operation(2, 4, [0, None, None, 0, None, 1, None,
                         0, 1, None, 0, None, 1, None, None, 1]),
    ]),
    SmallAlg([
        Operation(2, 4, [0, None, None, 0, None, 0, None,
                         1, 0, None, 1, None, 0, None, None, 1]),
        Operation(2, 4, [0, None, None, 0, None, 0, None,
                         1, 1, None, 1, None, 0, None, None, 1]),
        Operation(2, 4, [0, None, None, 0, None, 0, None,
                         1, 1, None, 1, None, 0, None, None, 1]),
        Operation(2, 4, [0, None, None, 0, None, 0, None,
                         0, 1, None, 1, None, 0, None, None, 1]),
    ]),
    SmallAlg([
        Operation(2, 4, [0, None, None, 0, None, 1, None,
                         1, 0, None, 0, None, 0, None, None, 1]),
        Operation(2, 4, [0, None, None, 0, None, 1, None,
                         1, 1, None, 0, None, 0, None, None, 1]),
        Operation(2, 4, [0, None, None, 0, None, 1, None,
                         1, 1, None, 0, None, 1, None, None, 1]),
        Operation(2, 4, [0, None, None, 0, None, 1, None,
                         0, 1, None, 0, None, 1, None, None, 1]),
    ]),
    SmallAlg([
        Operation(2, 4, [0, None, None, 1, None, 0, None,
                         1, 0, None, 1, None, 1, None, None, 1]),
        Operation(2, 4, [0, None, None, 1, None, 0, None,
                         1, 1, None, 1, None, 1, None, None, 1]),
        Operation(2, 4, [0, None, None, 0, None, 0, None,
                         1, 1, None, 0, None, 1, None, None, 1]),
        Operation(2, 4, [0, None, None, 0, None, 0, None,
                         0, 1, None, 0, None, 1, None, None, 1]),
    ]),
    SmallAlg([
        Operation(2, 4, [0, None, None, 1, None, 0, None,
                         1, 0, None, 1, None, 1, None, None, 1]),
        Operation(2, 4, [0, None, None, 1, None, 0, None,
                         0, 1, None, 1, None, 1, None, None, 1]),
        Operation(2, 4, [0, None, None, 0, None, 0, None,
                         0, 1, None, 1, None, 1, None, None, 1]),
        Operation(2, 4, [0, None, None, 0, None, 0, None,
                         0, 1, None, 1, None, 1, None, None, 1]),
    ]),
    SmallAlg([
        Operation(2, 4, [0, None, None, 0, None, 1, None,
                         1, 0, None, 0, None, 0, None, None, 1]),
        Operation(2, 4, [0, None, None, 0, None, 1, None,
                         0, 1, None, 0, None, 0, None, None, 1]),
        Operation(2, 4, [0, None, None, 1, None, 0, None,
                         0, 1, None, 1, None, 1, None, None, 1]),
        Operation(2, 4, [0, None, None, 1, None, 0, None,
                         0, 1, None, 1, None, 1, None, None, 1]),
    ]),
    SmallAlg([
        Operation(2, 4, [0, None, None, 1, None, 0, None,
                         1, 0, None, 0, None, 0, None, None, 1]),
        Operation(2, 4, [0, None, None, 1, None, 0, None,
                         1, 0, None, 0, None, 0, None, None, 1]),
        Operation(2, 4, [0, None, None, 0, None, 1, None,
                         1, 0, None, 1, None, 0, None, None, 1]),
        Operation(2, 4, [0, None, None, 0, None, 1, None,
                         0, 1, None, 1, None, 0, None, None, 1]),
    ]),
    SmallAlg([
        Operation(2, 4, [0, None, None, 1, None, 0, None,
                         1, 0, None, 1, None, 1, None, None, 1]),
        Operation(2, 4, [0, None, None, 1, None, 0, None,
                         0, 0, None, 1, None, 1, None, None, 1]),
        Operation(2, 4, [0, None, None, 1, None, 0, None,
                         0, 0, None, 1, None, 1, None, None, 1]),
        Operation(2, 4, [0, None, None, 1, None, 0, None,
                         0, 1, None, 1, None, 1, None, None, 1]),
    ]),
    SmallAlg([
        Operation(2, 4, [0, None, None, 0, None, 1, None,
                         1, 0, None, 0, None, 0, None, None, 1]),
        Operation(2, 4, [0, None, None, 0, None, 1, None,
                         0, 1, None, 0, None, 0, None, None, 1]),
        Operation(2, 4, [0, None, None, 0, None, 1, None,
                         0, 1, None, 1, None, 1, None, None, 1]),
        Operation(2, 4, [0, None, None, 0, None, 1, None,
                         0, 1, None, 1, None, 1, None, None, 1]),
    ]),
    SmallAlg([
        Operation(2, 4, [0, None, None, 0, None, 1, None,
                         1, 0, None, 0, None, 1, None, None, 1]),
        Operation(2, 4, [0, None, None, 0, None, 1, None,
                         1, 0, None, 0, None, 1, None, None, 1]),
        Operation(2, 4, [0, None, None, 0, None, 1, None,
                         1, 0, None, 0, None, 1, None, None, 1]),
        Operation(2, 4, [0, None, None, 0, None, 1, None,
                         0, 1, None, 0, None, 1, None, None, 1]),
    ]),
    SmallAlg([
        Operation(2, 4, [0, None, None, 1, None, 1, None,
                         1, 0, None, 0, None, 1, None, None, 1]),
        Operation(2, 4, [0, None, None, 1, None, 1, None,
                         0, 1, None, 0, None, 1, None, None, 1]),
        Operation(2, 4, [0, None, None, 0, None, 0, None,
                         0, 1, None, 1, None, 1, None, None, 1]),
        Operation(2, 4, [0, None, None, 0, None, 0, None,
                         0, 1, None, 1, None, 1, None, None, 1]),
    ]),
    SmallAlg([
        Operation(2, 4, [0, None, None, 0, None, 0, None,
                         1, 0, None, 1, None, 1, None, None, 1]),
        Operation(2, 4, [0, None, None, 0, None, 0, None,
                         1, 0, None, 1, None, 1, None, None, 1]),
        Operation(2, 4, [0, None, None, 1, None, 0, None,
                         1, 0, None, 0, None, 0, None, None, 1]),
        Operation(2, 4, [0, None, None, 1, None, 0, None,
                         0, 1, None, 0, None, 0, None, None, 1]),
    ]),
    SmallAlg([
        Operation(2, 4, [0, None, None, 1, None, 0, None,
                         1, 0, None, 1, None, 1, None, None, 1]),
        Operation(2, 4, [0, None, None, 1, None, 0, None,
                         0, 0, None, 1, None, 1, None, None, 1]),
        Operation(2, 4, [0, None, None, 0, None, 0, None,
                         0, 0, None, 1, None, 1, None, None, 1]),
        Operation(2, 4, [0, None, None, 0, None, 0, None,
                         0, 1, None, 1, None, 1, None, None, 1]),
    ]),
    SmallAlg([
        Operation(2, 4, [0, None, None, 1, None, 1, None,
                         1, 0, None, 0, None, 0, None, None, 1]),
        Operation(2, 4, [0, None, None, 1, None, 1, None,
                         1, 1, None, 0, None, 0, None, None, 1]),
        Operation(2, 4, [0, None, None, 1, None, 0, None,
                         1, 1, None, 0, None, 1, None, None, 1]),
        Operation(2, 4, [0, None, None, 1, None, 0, None,
                         0, 1, None, 0, None, 1, None, None, 1]),
    ]),
    SmallAlg([
        Operation(2, 4, [0, None, None, 1, None, 0, None,
                         1, 0, None, 0, None, 1, None, None, 1]),
        Operation(2, 4, [0, None, None, 1, None, 0, None,
                         0, 1, None, 0, None, 1, None, None, 1]),
        Operation(2, 4, [0, None, None, 0, None, 0, None,
                         0, 1, None, 1, None, 1, None, None, 1]),
        Operation(2, 4, [0, None, None, 0, None, 0, None,
                         0, 1, None, 1, None, 1, None, None, 1]),
    ]),
    SmallAlg([
        Operation(2, 4, [0, None, None, 0, None, 0, None,
                         1, 0, None, 1, None, 1, None, None, 1]),
        Operation(2, 4, [0, None, None, 0, None, 0, None,
                         1, 0, None, 1, None, 1, None, None, 1]),
        Operation(2, 4, [0, None, None, 0, None, 1, None,
                         1, 0, None, 1, None, 1, None, None, 1]),
        Operation(2, 4, [0, None, None, 0, None, 1, None,
                         0, 1, None, 1, None, 1, None, None, 1]),
    ]),
    SmallAlg([
        Operation(2, 4, [0, None, None, 0, None, 1, None,
                         1, 0, None, 0, None, 0, None, None, 1]),
        Operation(2, 4, [0, None, None, 0, None, 1, None,
                         0, 1, None, 0, None, 0, None, None, 1]),
        Operation(2, 4, [0, None, None, 1, None, 1, None,
                         0, 1, None, 1, None, 0, None, None, 1]),
        Operation(2, 4, [0, None, None, 1, None, 1, None,
                         0, 1, None, 1, None, 0, None, None, 1]),
    ]),
    SmallAlg([
        Operation(2, 4, [0, None, None, 0, None, 0, None,
                         1, 0, None, 0, None, 1, None, None, 1]),
        Operation(2, 4, [0, None, None, 0, None, 0, None,
                         1, 1, None, 0, None, 1, None, None, 1]),
        Operation(2, 4, [0, None, None, 1, None, 0, None,
                         1, 1, None, 1, None, 0, None, None, 1]),
        Operation(2, 4, [0, None, None, 1, None, 0, None,
                         0, 1, None, 1, None, 0, None, None, 1]),
    ]),
    SmallAlg([
        Operation(2, 4, [0, None, None, 1, None, 1, None,
                         1, 0, None, 0, None, 0, None, None, 1]),
        Operation(2, 4, [0, None, None, 1, None, 1, None,
                         0, 1, None, 0, None, 0, None, None, 1]),
        Operation(2, 4, [0, None, None, 0, None, 0, None,
                         0, 1, None, 0, None, 1, None, None, 1]),
        Operation(2, 4, [0, None, None, 0, None, 0, None,
                         0, 1, None, 0, None, 1, None, None, 1]),
    ]),
    SmallAlg([
        Operation(2, 4, [0, None, None, 0, None, 0, None,
                         1, 0, None, 0, None, 0, None, None, 1]),
        Operation(2, 4, [0, None, None, 0, None, 0, None,
                         0, 1, None, 0, None, 0, None, None, 1]),
        Operation(2, 4, [0, None, None, 1, None, 0, None,
                         0, 1, None, 1, None, 1, None, None, 1]),
        Operation(2, 4, [0, None, None, 1, None, 0, None,
                         0, 1, None, 1, None, 1, None, None, 1]),
    ]),
    SmallAlg([
        Operation(2, 4, [0, None, None, 1, None, 1, None,
                         1, 0, None, 1, None, 0, None, None, 1]),
        Operation(2, 4, [0, None, None, 1, None, 1, None,
                         1, 1, None, 1, None, 0, None, None, 1]),
        Operation(2, 4, [0, None, None, 0, None, 0, None,
                         1, 1, None, 1, None, 0, None, None, 1]),
        Operation(2, 4, [0, None, None, 0, None, 0, None,
                         0, 1, None, 1, None, 0, None, None, 1]),
    ]),
    SmallAlg([
        Operation(2, 4, [0, None, None, 0, None, 1, None,
                         1, 0, None, 1, None, 0, None, None, 1]),
        Operation(2, 4, [0, None, None, 0, None, 1, None,
                         0, 1, None, 1, None, 0, None, None, 1]),
        Operation(2, 4, [0, None, None, 0, None, 0, None,
                         0, 1, None, 1, None, 1, None, None, 1]),
        Operation(2, 4, [0, None, None, 0, None, 0, None,
                         0, 1, None, 1, None, 1, None, None, 1]),
    ]),
]


def test1():
    algs = list(ALGS2)

    next_alg = None
    multi_steps = []
    while True:
        steps = find_term(algs + [next_alg] if next_alg else algs, 16)
        if not steps:
            break

        multi_steps.append(steps)

        alg = find_algebra(multi_steps, 2)
        if alg is None:
            break

        next_alg = alg

    print("Done")
    print(next_alg)


def test2():
    steps = [
        [1, 3, 1, 3, 1],
        [1, 3, 2, 3, 0],
        [1, 3, 2, 3, 2],
        [1, 3, 1, 6, 5],
        [0, 3, 1, 6, 5],
        [1, 7, 8, 7, 8],
        [1, 3, 3, 4, 9],
        [1, 7, 7, 9, 10],
    ]

    find_algebra([steps], 7)


if __name__ == '__main__':
    test1()
