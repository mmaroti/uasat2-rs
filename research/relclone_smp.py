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
from uasat.clones import FunClone, FindRelClone
from uasat.critical_rels import CriticalRels
from typing import Tuple


def print_forks(relation: Relation):
    def transform(tup: Tuple[int, ...]):
        return tuple([a // 2 for a in tup] + [a % 2 for a in tup])

    tups = [transform(tup) for tup in relation.decode_tuples()]
    tups = sorted(tups)

    def is_fork(tup: Tuple[int, ...], pos: int) -> bool:
        for i in range(pos):
            if tup[i] != 0:
                return False
        return tup[pos] == 1

    for pos in range(2 * relation.arity):
        for tup in tups:
            if is_fork(tup, pos):
                print(pos, tup)
                break


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

    fun_clone = FunClone(4, [plus, prod])
    find_rel_clone = FindRelClone(fun_clone)

    if True:
        find_rel_clone.find_relations(3, 4, select="min", debug=True)
    else:
        find_rel_clone.add_relations([
            Relation(4, 1, [True, False, False, False]),

            Relation(4, 1, [True, True, False, False]),

            Relation(4, 2, [True, True, False, False,
                            False, False, True, True,
                            False, False, False, False,
                            False, False, False, False]),

            Relation(4, 2, [True, False, False, False,
                            False, True, False, False,
                            False, False, False, True,
                            False, False, True, False]),

            Relation(4, 3, [True, True, False, False,
                            True, True, False, False,
                            False, False, True, True,
                            False, False, True, True,

                            False, False, True, True,
                            False, False, True, True,
                            True, True, False, False,
                            True, True, False, False,

                            False, False, False, False,
                            False, False, False, False,
                            False, False, False, False,
                            False, False, False, False,

                            False, False, False, False,
                            False, False, False, False,
                            False, False, False, False,
                            False, False, False, False]),

            Relation(4, 3, [True, False, False, False,
                            False, True, False, False,
                            False, False, False, False,
                            False, False, False, False,

                            False, True, False, False,
                            True, False, False, False,
                            False, False, False, False,
                            False, False, False, False,

                            False, False, False, False,
                            False, False, False, False,
                            False, True, False, False,
                            True, False, False, False,

                            False, False, False, False,
                            False, False, False, False,
                            True, False, False, False,
                            False, True, False, False]),
        ])

    rel = find_rel_clone.find_relation(4, 3)
    print(rel)


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

    if False:
        rels = [
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
        ]

        for rel in rels:
            print(rel)
            print_forks(rel)

    rels = [
    ]

    crit = CriticalRels(4, [plus, prod], 3)

    for rel in rels:
        crit.add_relation(rel)

    while True:
        rel = crit.find_next(True)
        print(rel)
        if rel is None:
            break
        else:
            print_forks(rel)


if __name__ == '__main__':
    test_smp_relcone()
    # test_smp_relcone()
    # test_critical_rels()
