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
