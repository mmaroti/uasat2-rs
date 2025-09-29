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

from typing import List
from uasat import Solver, BitVec, Relation, Operation


class Algebra:
    def __init__(self, opers: List[Operation]):
        self.opers = opers
        assert all(o.size == opers[0].size for o in opers)

    @staticmethod
    def unknown(solver: Solver, size: int):
        assert size >= 1
        return Algebra([
            Operation(size, 4, solver),
            Operation(size, 4, solver),
        ])

    @property
    def size(self) -> int:
        return self.opers[0].size

    def check_axioms(self):
        assert len(self.opers) == 2
        self.opers[0].polymer([0, 0, 1, 1]).comp_eq(
            self.opers[1].polymer([0, 0, 1, 1])).ensure_all()
        self.opers[0].polymer([0, 1, 0, 1]).comp_eq(
            self.opers[1].polymer([0, 1, 0, 1])).ensure_all()

        Operation.projection(self.size, 2, 0).comp_eq(
            self.opers[0].polymer([0, 0, 0, 1])).ensure_all()
        self.opers[1].polymer([0, 0, 0, 1]).comp_eq(
            Operation.projection(self.size, 2, 1)).ensure_all()

    def solution(self) -> 'Algebra':
        return Algebra([oper.solution() for oper in self.opers])

    def decode(self) -> str:
        result = "Algebra([\n"
        for oper in self.opers:
            result += f"    Operation({oper.size}, {oper.arity}, {oper.decode()}),\n"
        result += "])"
        return result

    def evaluate_tuple(self, oper: int, args: List[Operation]) -> List[Operation]:
        op = self.opers[oper]
        assert op.arity == len(args) and all(
            len(arg) == len(args[0]) for arg in args)

        result = []
        for idx in range(len(args[0])):
            result.append(op.evaluate([arg[idx] for arg in args]))
        return result


ALGEBRAS = [
    Algebra([
        Operation(2, 4, [0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1]),
        Operation(2, 4, [0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1]),
    ])
]


class Generator:
    def __init__(self, solver: Solver, steps: int):
        self.solver = solver
        self.tuples = [
            self.constant_entry([0, 0, 1]),
            self.constant_entry([0, 1, 0]),
            self.constant_entry([1, 0, 0]),
            self.constant_entry([1, 1, 0]),
        ]

    def select(self, entries):
        pass

    def constant_entry(self, values: List[int]) -> List[Operation]:
        result = []
        for alg in ALGEBRAS:
            for value in values:
                result.append(Operation.constant(alg.size, value))
        return result

    def select_oper(self) -> BitVec:
        var = BitVec.new_variable(self.solver, 2)
        var.ensure_one()
        return var

    def evaluate_entry(self, oper: BitVec, args: List[List[Operation]]) -> List[Operation]:
        num = len(args[0]) // len(ALGEBRAS)
        assert all(len(arg) == num * len(ALGEBRAS) for arg in args)
        assert all(len(alg.opers) == len(oper) for alg in ALGEBRAS)

        result = []
        for idx, alg in enumerate(ALGEBRAS):
            for pos in range(num):
                args2 = [arg[idx * num + pos] for arg in args]
                res = Relation.empty_relation(alg.size, 1)
                for op in range(len(oper)):
                    val = alg.opers[op].evaluate(args2).graph
                    val &= Relation.const_relation(
                        val.size, val.arity, oper.solver, oper[op])
                    res |= val
                result.append(Operation(alg.size, 0, res.table))
        return result


def find_algebra():
    solver = Solver()

    algebra = Algebra.unknown(solver, 2)
    algebra.check_axioms()
    if solver.solve():
        print(algebra.solution().decode())


def find_term():
    solver = Solver()
    generator = Generator(solver, 1)

    a0 = generator.constant_entry([0, 0, 1])
    a1 = generator.constant_entry([0, 1, 0])
    a2 = generator.constant_entry([1, 0, 0])
    a3 = generator.constant_entry([1, 1, 0])
    oper = generator.select_oper()
    a4 = generator.evaluate_entry(oper, [a0, a1, a2, a3])
    print(solver.solve())
    print([v.solution().decode() for v in a4])
    print(oper.get_value())


if __name__ == '__main__':
    find_term()
