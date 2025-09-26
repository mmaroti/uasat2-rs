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

from uasat import *
from uasat.structure import *


def test_posets():
    solver = Solver()

    rel = Relation(2, 2, solver)
    solver.add_clause(rel.reflexive().literals)
    solver.add_clause(rel.symmetric().literals)

    while solver.solve() is True:
        val = rel.get_value()
        print(val, val.decode())

        solver.add_clause(rel.table ^ val.table)


def test_commutative_ops():
    solver = Solver()

    oper = Operation(2, 2, solver)
    test = (oper == oper.polymer([1, 0]))
    solver.add_clause(test.literals)

    while solver.solve() is True:
        oper2 = oper.get_value()
        print(oper2, oper2.decode())

        solver.add_clause(oper.table ^ oper2.table)


if __name__ == '__main__':
    test_posets()
