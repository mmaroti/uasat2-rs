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

from typing import List, Tuple, Dict, Any
import cotengra

from .relation import Relation

OPTIMIZER = None


def contract_pair(rel1: Relation,
                  var1: Tuple[Any, ...],
                  rel2: Relation,
                  var2: Tuple[Any, ...],
                  var3: Tuple[Any, ...]) -> Relation:
    assert rel1.arity == len(var1)
    assert rel2.arity == len(var2)

    extra = set()
    extra.update(var1)
    extra.update(var2)
    assert extra.issuperset(var3)
    extra.difference_update(var3)
    extra = list(extra)
    total = extra + list(var3)

    rel1 = rel1.polymer([total.index(a) for a in var1], len(total))
    rel2 = rel2.polymer([total.index(a) for a in var2], len(total))
    rel3 = rel1 & rel2
    if len(extra) != 0:
        rel3 = rel3.fold_any(len(extra))
    return rel3


def contract(inputs: List[Tuple[Relation, Tuple[Any, ...]]],
             output: Tuple[Any, ...]) -> Relation:
    global OPTIMIZER
    if OPTIMIZER is None:
        OPTIMIZER = cotengra.ReusableHyperOptimizer()

    size_dict: Dict[Any, int] = dict()
    data = dict()
    input_vars = []
    for idx, (rel, var) in enumerate(inputs):
        for v in var:
            if v in size_dict:
                assert size_dict[v] == rel.size
            else:
                size_dict[v] = rel.size
        input_vars.append(var)
        data[frozenset({idx})] = rel

    # print(input_vars, output, size_dict)
    tree = OPTIMIZER.search(input_vars, output, size_dict)

    for a, b, c in tree.traverse():
        var1 = tuple(tree.get_legs(b))
        var2 = tuple(tree.get_legs(c))
        if tree.root == a:
            var3 = output
        else:
            var3 = tuple(tree.get_legs(a))

        rel1 = data[b]
        del data[b]
        rel2 = data[c]
        del data[c]
        assert var3 not in data
        data[a] = contract_pair(rel1, var1, rel2, var2, var3)

    assert len(data) == 1
    return data[tree.root]
