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

from uasat import Solver, Relation, Operation


def test_number_of_posets():
    """
    Counting the number of labeled 3-element posets.
    """

    solver = Solver()
    rel = Relation.variable(3, 2, solver)
    rel.reflexive().ensure_all()
    rel.antisymm().ensure_all()
    rel.transitive().ensure_all()

    count = 0
    while solver.solve() is True:
        val = rel.solution()
        print(val.decode())
        count += 1
        (rel ^ val).ensure_any()
    assert count == 19


def test_evaluate_n1():
    for arity in range(1, 4):
        solver = Solver()

        rel = Relation.variable(2, arity, solver)
        opers = [Relation.variable(2, 1, solver) for _ in range(arity)]

        out0 = rel._evaluate_n1(opers)
        out1 = rel._evaluate_nm(opers)
        out0.comp_ne(out1).ensure_all()

        if solver.solve():
            print(rel.solution())
            for op in opers:
                print(op.solution())
            print(out0.solution())
            print(out1.solution())
            assert False


def test_evaluate_n2():
    for arity in range(1, 4):
        solver = Solver()

        rel = Relation.variable(2, arity, solver)
        opers = [Relation.variable(2, 2, solver) for _ in range(arity)]

        out0 = rel._evaluate_n2(opers)
        out1 = rel._evaluate_nm(opers)
        out0.comp_ne(out1).ensure_all()

        if solver.solve():
            print(rel.solution())
            for op in opers:
                print(op.solution())
            print(out0.solution())
            print(out1.solution())
            assert False


def test_evaluate_n3():
    for arity in range(1, 4):
        solver = Solver()

        rel = Relation.variable(2, arity, solver)
        opers = [Relation.variable(2, 3, solver) for _ in range(arity)]

        out0 = rel._evaluate_n3(opers)
        out1 = rel._evaluate_nm(opers)
        out0.comp_ne(out1).ensure_all()

        if solver.solve():
            print(rel.solution())
            for op in opers:
                print(op.solution())
            print(out0.solution())
            print(out1.solution())
            assert False


def test_evaluate_1m():
    for arity in range(1, 4):
        solver = Solver()

        rel = Relation.variable(2, 1, solver)
        oper = Relation.variable(2, arity, solver)

        out0 = rel._evaluate_1m(oper)
        out1 = rel._evaluate_nm([oper])
        out0.comp_ne(out1).ensure_all()

        if solver.solve():
            print(rel.solution())
            print(oper.solution())
            print(out0.solution())
            print(out1.solution())
            assert False


def test_evaluate_2m():
    for arity in range(1, 4):
        solver = Solver()

        rel = Relation.variable(2, 2, solver)
        oper0 = Relation.variable(2, arity, solver)
        oper1 = Relation.variable(2, arity, solver)

        out0 = rel._evaluate_2m(oper0, oper1)
        out1 = rel._evaluate_nm([oper0, oper1])
        out0.comp_ne(out1).ensure_all()

        if solver.solve():
            print(rel.solution())
            print(oper0.solution())
            print(oper1.solution())
            print(out0.solution())
            print(out1.solution())
            assert False


def test_evaluate_3m():
    for arity in range(1, 4):
        solver = Solver()

        rel = Relation.variable(2, 3, solver)
        oper0 = Relation.variable(2, arity, solver)
        oper1 = Relation.variable(2, arity, solver)
        oper2 = Relation.variable(2, arity, solver)

        out0 = rel._evaluate_3m(oper0, oper1, oper2)
        out1 = rel._evaluate_nm([oper0, oper1, oper2])
        out0.comp_ne(out1).ensure_all()

        if solver.solve():
            print(rel.solution())
            print(oper0.solution())
            print(oper1.solution())
            print(oper2.solution())
            print(out0.solution())
            print(out1.solution())
            assert False


if __name__ == '__main__':
    test_evaluate_3m()
