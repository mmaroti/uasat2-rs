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

from uasat import Operation, Solver, Relation
from uasat.clones import MaximalClones


def retract(oper: Operation, ret: List[int]):
    sub = []
    for i, a in enumerate(ret):
        assert ret[a] == a
        if i == a:
            sub.append(i)
    assert oper.size == len(sub)

    map = [sub.index(a) for a in ret]


class Maximal3Perm(MaximalClones):
    def __init__(self, size: int, max_relation_arity, max_operation_arity):
        MaximalClones.__init__(
            self, size, max_relation_arity, max_operation_arity)

        maltsev2 = Operation(2, 3, [0, 1, 1, 0, 1, 0, 0, 1])

        retracts = []

    def maltsev_condition(self, solver: Solver) -> List[Operation]:
        oper1 = Operation.variable(self.size, 3, solver)
        oper2 = Operation.variable(self.size, 3, solver)

        oper1.polymer([0, 1, 1]).comp_eq(
            Operation.projection(self.size, 2, 0)).ensure_true()
        oper1.polymer([0, 0, 1]).comp_eq(
            oper2.polymer([0, 1, 1])).ensure_true()
        oper2.polymer([0, 0, 1]).comp_eq(
            Operation.projection(self.size, 2, 1)).ensure_true()

        return [oper1, oper2]

    def relation_condition(self, solver: Solver) -> List[Relation]:
        relations = []

        for i in range(self.size):
            relations.append(Relation.singleton(self.size, [i]))

        relations.append(Relation.variable(self.size, 2, solver))
        relations[-1].reflexive().ensure_true()

        return relations


def test():
    clones = Maximal3Perm(3, 3, 3)
    while clones.find_maximal([]):
        pass


if __name__ == '__main__':
    test()
