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
from uasat import *


def test_signature():
    """
    Making sure that the rust library can be loaded and works.
    """

    solver = Solver()
    assert solver.signature == "cadical-1.9.5"


def test_join():
    solver = Solver()
    assert solver.join(Solver.STATIC) is solver
    assert Solver.STATIC.join(solver) is solver
    assert solver.join(solver) is solver
    assert Solver.STATIC.join(Solver.STATIC) is Solver.STATIC

    other = Solver()
    try:
        solver.join(other)
        assert False
    except ValueError:
        pass


def test_static():
    solver = Solver()
    calc = Solver.STATIC

    for a in [Solver.FALSE, Solver.TRUE]:
        assert solver.bool_not(a) == calc.bool_not(a)
        for b in [Solver.FALSE, Solver.TRUE]:
            assert solver.bool_and(a, b) == calc.bool_and(a, b)
            assert solver.bool_or(a, b) == calc.bool_or(a, b)
            assert solver.bool_imp(a, b) == calc.bool_imp(a, b)
            assert solver.bool_xor(a, b) == calc.bool_xor(a, b)
            assert solver.bool_equ(a, b) == calc.bool_equ(a, b)
            for c in [Solver.FALSE, Solver.TRUE]:
                assert solver.bool_maj(a, b, c) == calc.bool_maj(a, b, c)
                assert solver.bool_iff(a, b, c) == calc.bool_iff(a, b, c)
                assert solver.fold_all([a, b, c]) == calc.fold_all([a, b, c])
                assert solver.fold_any([a, b, c]) == calc.fold_any([a, b, c])
                assert solver.fold_one([a, b, c]) == calc.fold_one([a, b, c])
                assert solver.fold_amo([a, b, c]) == calc.fold_amo([a, b, c])
                for d in [Solver.FALSE, Solver.TRUE]:
                    assert solver.comp_eq(
                        [a, b], [c, d]) == calc.comp_eq([a, b], [c, d])
                    assert solver.comp_ne(
                        [a, b], [c, d]) == calc.comp_ne([a, b], [c, d])
                    assert solver.comp_le(
                        [a, b], [c, d]) == calc.comp_le([a, b], [c, d])
                    assert solver.comp_lt(
                        [a, b], [c, d]) == calc.comp_lt([a, b], [c, d])
                    assert solver.comp_ge(
                        [a, b], [c, d]) == calc.comp_ge([a, b], [c, d])
                    assert solver.comp_gt(
                        [a, b], [c, d]) == calc.comp_gt([a, b], [c, d])


def test_bitvec():
    """
    We are checking if the operations defined in the Solver and those defined
    in the BitVec when solver is None do match.
    """

    solver = Solver()
    v1 = BitVec(solver, [-1, -1, 1, 1])
    v2 = BitVec(None, [-1, -1, 1, 1])
    v3 = BitVec(None, [-1, 1, -1, 1])

    def check(u: BitVec, v: BitVec):
        assert u.solver == solver and v.solver is None
        assert u.literals == v.literals

    check(v1, v2)
    check(~v1, ~v2)
    check(v1 & v3, v2 & v3)
    check(v1 | v3, v2 | v3)
    check(v1 ^ v3, v2 ^ v3)

    def bits(a: int) -> List[int]:
        return [
            Solver.bool_lift((a & 1) != 0),
            Solver.bool_lift((a & 2) != 0),
            Solver.bool_lift((a & 4) != 0),
        ]

    for a in range(8):
        v1 = BitVec(solver, bits(a))
        v2 = BitVec(None, v1.literals)
        for b in range(8):
            v3 = BitVec(None, bits(b))

            check(v1 == v3, v2 == v3)
            check(v1 != v3, v2 != v3)
            check(v1 != v3, ~(v2 == v3))
            check(v1 <= v3, v2 <= v3)
            check(v1 > v3, v2 > v3)
            check(v1 > v3, ~(v2 <= v3))
            check(v1 < v3, v2 < v3)
            check(v1 >= v3, v2 >= v3)
            check(v1 >= v3, ~(v2 < v3))
