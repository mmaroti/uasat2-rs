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

from uasat import Solver, Relation, Operation, BitVec


def functional(rel: Relation) -> BitVec:
    assert rel.arity >= 2
    rel0 = rel.polymer_insert(rel.arity - 1)
    rel1 = rel.polymer_insert(rel.arity)
    rel2 = (rel0 & rel1).fold_any(rel.arity - 1)
    rel3 = (~rel2 | Relation.diagonal(rel.size))
    return rel3.table.fold_all()


def abelian(rel: Relation) -> BitVec:
    assert rel.arity == 4
    rel1 = rel.polymer([0, 0, 1, 2]).fold_any(1)
    rel2 = (~rel1 | Relation.diagonal(rel.size))
    return rel2.table.fold_all()


def test(size: int = 2):
    solver = Solver()

    oper = Operation.variable(size, 3, solver)
    oper.idempotent().ensure_true()

    rel0 = Relation.tuples(size, 4, [
        (0, 0, 0, 0),
        (0, 1, 1, 0),
        (1, 1, 0, 0),
        (0, 0, 1, 1),
        (1, 0, 0, 1),
        (1, 1, 1, 1),
    ])

    rel1 = oper.apply(rel0)
    # rel2 = oper.apply(rel1)

    abelian(rel1).ensure_true()
    functional(rel1).ensure_false()

    if solver.solve():
        print(oper.solution().decode())
        print(rel1.solution().decode_tuples())
    else:
        print(None)


if __name__ == '__main__':
    test(5)
