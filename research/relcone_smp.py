# Copyright (C) 2026, Miklos Maroti
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

from uasat import Relation, Operation
from uasat.clones import find_new_relation
from uasat.critical_rels import CriticalRels


def test_smp_relcone():
    plus = Operation(4, 2, [
        0, 1, 2, 3,
        1, 0, 3, 2,
        2, 3, 0, 1,
        3, 2, 1, 0,
    ])

    prod = Operation(4, 2, [
        0, 0, 0, 0,
        0, 0, 0, 0,
        0, 0, 1, 1,
        0, 0, 1, 1,
    ])

    relations = [
        Relation(4, 1, [True, True, False, False]),
        Relation(4, 1, [True, False, False, False]),
        Relation(4, 2, [True, True, False, False,
                        True, True, False, False,
                        False, False, True, True,
                        False, False, True, True]),
        Relation(4, 2, [True, False, False, False,
                        False, True, False, False,
                        False, False, False, True,
                        False, False, True, False]),
        Relation(4, 2, [True, True, False, False,
                        False, False, True, True,
                        False, False, False, False,
                        False, False, False, False]),
        Relation(4, 3, [True, True, False, False,
                        False, False, True, True,
                        False, False, False, False,
                        False, False, False, False,

                        False, False, True, True,
                        True, True, False, False,
                        False, False, False, False,
                        False, False, False, False,

                        False, False, False, False,
                        False, False, False, False,
                        True, True, False, False,
                        False, False, True, True,

                        False, False, False, False,
                        False, False, False, False,
                        False, False, True, True,
                        True, True, False, False]),
    ]

    for r in relations:
        print(r.decode_tuples())

    new_rel = find_new_relation(
        4, [plus, prod], 4, relations, 3)
    print(new_rel)


def test_critical_rels():
    plus = Operation(4, 2, [
        0, 1, 2, 3,
        1, 0, 3, 2,
        2, 3, 0, 1,
        3, 2, 1, 0,
    ])

    prod = Operation(4, 2, [
        0, 0, 0, 0,
        0, 0, 0, 0,
        0, 0, 1, 1,
        0, 0, 1, 1,
    ])

    crit = CriticalRels(4, [plus, prod], 5)

    for rel in [
        Relation(4, 1, [True, True, False, False]),
        Relation(4, 1, [True, False, False, False]),
        Relation(4, 1, [False, False, False, False]),

        Relation(4, 2, [True, True, False, False,
                        True, True, False, False,
                        False, False, True, True,
                        False, False, True, True]),
        Relation(4, 2, [True, True, False, False,
                        False, False, True, True,
                        False, False, False, False,
                        False, False, False, False]),
        Relation(4, 2, [True, False, False, False,
                        False, True, False, False,
                        False, False, False, True,
                        False, False, True, False]),
        Relation(4, 2, [True, False, False, False,
                        False, True, False, False,
                        False, False, True, False,
                        False, False, False, True]),

        Relation(4, 3, [True, True, False, False, True, True, False, False, False, False, True, True, False, False, True, True, False, False, True, True, False, False, True, True, True, True, False, False, True, True, False, False,
                 False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False]),
        Relation(4, 3, [True, True, False, False, False, False, True, True, False, False, False, False, False, False, False, False, False, False, True, True, True, True, False, False, False, False, False, False, False, False, False,
                 False, False, False, False, False, False, False, False, False, True, True, False, False, False, False, True, True, False, False, False, False, False, False, False, False, False, False, True, True, True, True, False, False]),
        Relation(4, 3, [True, False, False, False, True, False, False, False, False, True, False, False, False, True, False, False, False, True, False, False, False, True, False, False, True, False, False, False, True, False, False,
                 False, False, False, False, True, False, False, False, True, False, False, True, False, False, False, True, False, False, False, True, False, False, False, True, False, False, False, False, True, False, False, False, True]),
        Relation(4, 3, [True, True, False, False, True, True, False, False, False, False, True, True, False, False, True, True, True, True, False, False, True, True, False, False, False, False, True, True, False, False, True,
                 True, False, False, True, True, False, False, True, True, True, True, False, False, True, True, False, False, False, False, True, True, False, False, True, True, True, True, False, False, True, True, False, False]),
        Relation(4, 3, [True, False, False, False, False, True, False, False, False, False, False, False, False, False, False, False, False, True, False, False, True, False, False, False, False, False, False, False, False, False, False,
                 False, False, False, False, False, False, False, False, False, True, False, False, False, False, True, False, False, False, False, False, False, False, False, False, False, False, True, False, False, True, False, False, False]),
        Relation(4, 3, [True, False, False, False, False, True, False, False, False, False, False, False, False, False, False, False, False, True, False, False, True, False, False, False, False, False, False, False, False, False, False,
                 False, False, False, False, True, False, False, True, False, False, False, False, False, False, False, False, False, False, False, True, False, False, False, False, True, False, False, False, False, False, False, False, False]),

        Relation(4, 4, [True, True, False, False, True, True, False, False, False, False, True, True, False, False, True, True, True, True, False, False, True, True, False, False, False, False, True, True, False, False, True, True, False, False, True, True, False, False, True, True, True, True, False, False, True, True, False, False, False, False, True, True, False, False, True, True, True, True, False, False, True, True, False, False, False, False, True, True, False, False, True, True, True, True, False, False, True, True, False, False, False, False, True, True, False, False, True, True, True, True, False, False, True, True, False, False, True, True, False, False, True, True, False, False, False, False, True, True, False, False, True, True, True, True, False, False, True, True, False, False, False, False, True, True, False, False, True, True, False, False, False, False,
                 False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False]),
        Relation(4, 4, [True, True, False, False, False, False, True, True, False, False, False, False, False, False, False, False, True, True, False, False, False, False, True, True, False, False, False, False, False, False, False, False, False, False, True, True, True, True, False, False, False, False, False, False, False, False, False, False, False, False, True, True, True, True, False, False, False, False, False, False, False, False, False, False, False, False, True, True, True, True, False, False, False, False, False, False, False, False, False, False, False, False, True, True, True, True, False, False, False, False, False, False, False, False, False, False, True, True, False, False, False, False, True, True, False, False, False, False, False, False, False, False, True, True, False, False, False, False, True, True, False, False, False, False, False, False, False,
                 False, False, False, False, False, False, False, False, False, False, False, True, True, True, True, False, False, False, False, False, False, False, False, False, False, False, False, True, True, True, True, False, False, False, False, False, False, False, False, False, False, True, True, False, False, False, False, True, True, False, False, False, False, False, False, False, False, True, True, False, False, False, False, True, True, False, False, False, False, False, False, False, False, True, True, False, False, False, False, True, True, False, False, False, False, False, False, False, False, True, True, False, False, False, False, True, True, False, False, False, False, False, False, False, False, False, False, True, True, True, True, False, False, False, False, False, False, False, False, False, False, False, False, True, True, True, True, False, False]),
        Relation(4, 4, [True, True, False, False, False, False, True, True, False, False, False, False, False, False, False, False, False, False, True, True, True, True, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, True, True, False, False, False, False, True, True, False, False, False, False, False, False, False, False, False, False, True, True, True, True, False, False, False, False, True, True, True, True, False, False, False, False, False, False, False, False, False, False, True, True, False, False, False, False, True, True, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, True, True, True, True, False, False, False, False, False, False, False, False, False, False, True, True, False, False, False, False, True, True, False,
                 False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False]),
        Relation(4, 4, [True, True, False, False, False, False, True, True, False, False, False, False, False, False, False, False, True, True, False, False, False, False, True, True, False, False, False, False, False, False, False, False, False, False, True, True, True, True, False, False, False, False, False, False, False, False, False, False, False, False, True, True, True, True, False, False, False, False, False, False, False, False, False, False, False, False, True, True, True, True, False, False, False, False, False, False, False, False, False, False, False, False, True, True, True, True, False, False, False, False, False, False, False, False, False, False, True, True, False, False, False, False, True, True, False, False, False, False, False, False, False, False, True, True, False, False, False, False, True, True, False, False, False, False, False, False, False,
                 False, False, False, False, False, False, False, False, False, True, True, False, False, False, False, True, True, False, False, False, False, False, False, False, False, True, True, False, False, False, False, True, True, False, False, False, False, False, False, False, False, False, False, True, True, True, True, False, False, False, False, False, False, False, False, False, False, False, False, True, True, True, True, False, False, False, False, False, False, False, False, False, False, False, False, True, True, True, True, False, False, False, False, False, False, False, False, False, False, False, False, True, True, True, True, False, False, False, False, False, False, False, False, False, False, True, True, False, False, False, False, True, True, False, False, False, False, False, False, False, False, True, True, False, False, False, False, True, True]),
        Relation(4, 4, [True, True, False, False, False, False, True, True, False, False, False, False, False, False, False, False, False, False, True, True, True, True, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, True, True, True, True, False, False, False, False, False, False, False, False, False, False, True, True, False, False, False, False, True, True, False, False, True, True, True, True, False, False, False, False, False, False, False, False, False, False, True, True, False, False, False, False, True, True, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, True, True, False, False, False, False, True, True, False, False, False, False, False, False, False, False, False, False, True, True, True, True, False, False, False,
                 False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False]),
        Relation(4, 4, [True, True, False, False, True, True, False, False, False, False, True, True, False, False, True, True, True, True, False, False, True, True, False, False, False, False, True, True, False, False, True, True, False, False, True, True, False, False, True, True, True, True, False, False, True, True, False, False, False, False, True, True, False, False, True, True, True, True, False, False, True, True, False, False, True, True, False, False, True, True, False, False, False, False, True, True, False, False, True, True, True, True, False, False, True, True, False, False, False, False, True, True, False, False, True, True, False, False, True, True, False, False, True, True, True, True, False, False, True, True, False, False, False, False, True, True, False, False, True, True, True, True, False, False, True, True, False,
                 False, False, False, True, True, False, False, True, True, True, True, False, False, True, True, False, False, False, False, True, True, False, False, True, True, True, True, False, False, True, True, False, False, True, True, False, False, True, True, False, False, False, False, True, True, False, False, True, True, True, True, False, False, True, True, False, False, False, False, True, True, False, False, True, True, False, False, True, True, False, False, True, True, True, True, False, False, True, True, False, False, False, False, True, True, False, False, True, True, True, True, False, False, True, True, False, False, True, True, False, False, True, True, False, False, False, False, True, True, False, False, True, True, True, True, False, False, True, True, False, False, False, False, True, True, False, False, True, True]),
        Relation(4, 4, [True, False, False, False, False, True, False, False, False, False, True, False, False, False, False, True, False, True, False, False, True, False, False, False, False, False, False, True, False, False, True, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, True, False, False, True, False, False, False, False, False, False, True, False, False, True, False, True, False, False, False, False, True, False, False, False, False, True, False, False, False, False, True, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False,
                 False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, True, False, False, True, False, False, False, False, False, False, True, False, False, True, False, True, False, False, False, False, True, False, False, False, False, True, False, False, False, False, True, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, True, False, False, False, False, True, False, False, False, False, True, False, False, False, False, True, False, True, False, False, True, False, False, False, False, False, False, True, False, False, True, False]),
        Relation(4, 4, [True, False, False, False, False, True, False, False, False, False, True, False, False, False, False, True, False, True, False, False, True, False, False, False, False, False, False, True, False, False, True, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, True, False, False, True, False, False, False, False, False, False, True, False, False, True, False, True, False, False, False, False, True, False, False, False, False, True, False, False, False, False, True, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False,
                 False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, True, False, False, False, False, True, False, False, False, False, True, False, False, False, False, True, False, True, False, False, True, False, False, False, False, False, False, True, False, False, True, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, True, False, False, True, False, False, False, False, False, False, True, False, False, True, False, True, False, False, False, False, True, False, False, False, False, True, False, False, False, False, True]),
        Relation(4, 4, [True, False, False, False, False, True, False, False, False, False, False, False, False, False, False, False, False, True, False, False, True, False, False, False, False, False, False, False, False, False, False, False, False, False, False, True, False, False, True, False, False, False, False, False, False, False, False, False, False, False, True, False, False, False, False, True, False, False, False, False, False, False, False, False, False, True, False, False, True, False, False, False, False, False, False, False, False, False, False, False, True, False, False, False, False, True, False, False, False, False, False, False, False, False, False, False, False, False, True, False, False, False, False, True, False, False, False, False, False, False, False, False, False, False, False, True, False, False, True, False, False, False, False, False, False, False, False,
                 False, False, False, False, False, False, False, False, False, False, True, False, False, True, False, False, False, False, False, False, False, False, False, False, False, True, False, False, False, False, True, False, False, False, False, False, False, False, False, False, False, False, False, True, False, False, False, False, True, False, False, False, False, False, False, False, False, False, False, False, True, False, False, True, False, False, False, False, False, False, False, False, False, True, False, False, False, False, True, False, False, False, False, False, False, False, False, False, False, False, True, False, False, True, False, False, False, False, False, False, False, False, False, False, False, False, False, False, True, False, False, True, False, False, False, False, False, False, False, False, False, False, False, True, False, False, False, False, True]),
    ]:
        crit.add_relation(rel)

    while True:
        rel = crit.find_next()
        print(rel)
        if rel is None:
            break


if __name__ == '__main__':
    # test_smp_relcone()
    test_critical_rels()
