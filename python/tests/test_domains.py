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


def test_bool():
    elem0 = BOOLEAN.bool_lift(True)
    elem1 = BOOLEAN.bool_lift(False)
    elem2 = BOOLEAN.bool_or(elem0, elem1)
    # elem3 = BOOLEAN.comp_eq(elem2, elem1)
    print(BOOLEAN.decode(elem2))


def test_product():
    solver = Solver()
    domain = Product(BOOLEAN, BOOLEAN, BOOLEAN)
    elem1 = BitVec(solver, [Solver.TRUE, Solver.FALSE, Solver.TRUE])
    print(domain.decode(elem1))
    elem2 = domain.contains(elem1)
    print(BOOLEAN.decode(elem2))


def test_power():
    solver = Solver()
    domain = Power(SmallSet(3), SmallSet(3))
    elem1 = BitVec(solver, [
        Solver.TRUE, Solver.FALSE, Solver.FALSE,
        Solver.FALSE, Solver.TRUE, Solver.FALSE,
        Solver.FALSE, Solver.FALSE, Solver.TRUE,
    ])
    print(domain.decode(elem1))
    elem2 = domain.contains(elem1)
    print(BOOLEAN.decode(elem2))


if __name__ == '__main__':
    test_power()
