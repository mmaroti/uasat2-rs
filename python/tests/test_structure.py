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


def test_number_of_posets():
    """
    Counting the number of labeled 3-element posets.
    """

    solver = Solver()
    rel = Relation(3, 2, solver)
    rel.reflexive().ensure_all()
    rel.antisymmetric().ensure_all()
    rel.transitive().ensure_all()

    count = 0
    while solver.solve() is True:
        val = rel.get_value()
        print(val.decode())
        count += 1
        solver.add_clause(rel.table ^ val.table)
    assert count == 19


def test_commutative_ops():
    solver = Solver()

    oper = Operation(2, 2, solver)
    test = (oper == oper.polymer([1, 0]))
    solver.add_clause(test.literals)

    while solver.solve() is True:
        oper2 = oper.get_value()
        print(oper2.decode())

        solver.add_clause(oper.table ^ oper2.table)


if __name__ == '__main__':
    test_number_of_posets()
