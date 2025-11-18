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
    rel.reflexive().ensure_true()
    rel.antisymm().ensure_true()
    rel.transitive().ensure_true()

    count = 0
    while solver.solve():
        val = rel.solution()
        print(val.decode())
        count += 1
        (rel ^ val).ensure_any()
    assert count == 19


def test_polymorphisms_of_c3():
    """
    Find all binary polymorphisms of the reflexive oriented 3-cycle.
    """

    rel = Relation.tuples(3, 2, [
        (0, 0), (0, 1), (1, 1), (1, 2), (2, 2), (2, 0),
    ])

    solver = Solver()

    op = Operation.variable(rel.size, 2, solver)
    op.preserves(rel).ensure_true()

    count = 0
    while solver.solve():
        val = op.solution()
        print(val.decode())
        count += 1
        (op.table ^ val.table).ensure_any()
    assert count == 9


if __name__ == '__main__':
    test_polymorphisms_of_c3()
