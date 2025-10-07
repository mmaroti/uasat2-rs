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

import uasat


def test_number_of_posets():
    """
    Counting the number of labeled 3-element posets.
    """

    solver = uasat.Solver()
    rel = uasat.Relation(3, 2, solver)
    rel.reflexive().ensure_all()
    rel.antisymm().ensure_all()
    rel.transitive().ensure_all()

    count = 0
    while solver.solve() is True:
        val = rel.solution()
        print(val.decode())
        count += 1
        solver.add_clause((rel.table ^ val.table).literals)
    assert count == 19


def test_commutative_ops():
    solver = uasat.Solver()

    oper = uasat.Operation(2, 2, solver)
    test = oper.comp_eq(oper.polymer([1, 0]))
    solver.add_clause(test.literals)

    while solver.solve() is True:
        val = oper.solution()
        print(val.decode())

        solver.add_clause((oper.table ^ val.table).literals)


if __name__ == '__main__':
    test_number_of_posets()
