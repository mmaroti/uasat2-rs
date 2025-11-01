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

import math
from typing import Any, List, Sequence, Optional

from ._uasat import BitVec, Solver
from .operation import Operation, Constant


class Algebra:
    def __init__(self, size: int, length: int, signature: List[int]):
        assert size >= 1 and length >= 0
        self.size = size
        self.length = length
        assert all(arity >= 0 for arity in signature)
        self.signature = signature

    def apply(self, op: int, args: List[BitVec], partop: bool = False) -> BitVec:
        assert len(args) == self.signature[op]
        assert all(len(arg) == self.length for arg in args)
        raise NotImplementedError()

    def encode_elem(self, elem: Any) -> BitVec:
        raise NotImplementedError()

    def decode_elem(self, elem: BitVec) -> Any:
        assert len(elem) == self.length
        raise NotImplementedError()

    def solution(self) -> 'Algebra':
        raise NotImplementedError()


class SmallAlg(Algebra):
    def __init__(self, operations: List[Operation]):
        super().__init__(operations[0].size, operations[0].size,
                         [op.arity for op in operations])
        self.operations = operations

    @staticmethod
    def variable(solver: Solver, size: int, signature: List[int], partop: bool = False) -> 'SmallAlg':
        assert size >= 1 and all(arity >= 0 for arity in signature)
        operations = [Operation.variable(size, arity, solver, partop=partop)
                      for arity in signature]
        return SmallAlg(operations)

    def apply(self, op: int, args: List[BitVec], partop: bool = False) -> BitVec:
        assert len(args) == self.signature[op]
        elems = [Constant(self.size, arg) for arg in args]
        res = self.operations[op].compose(elems, partop)
        assert res.length == self.size
        return res.table

    def encode_elem(self, elem: int) -> BitVec:
        assert 0 <= elem < self.size
        return Constant.constant(self.size, elem).table

    def decode_elem(self, elem: BitVec) -> Any:
        return Constant(self.size, elem.solution()).decode()

    def solution(self) -> 'SmallAlg':
        return SmallAlg([op.solution() for op in self.operations])

    def __repr__(self) -> str:
        result = "SmallAlg([\n"
        for op in self.operations:
            result += f"    {op},\n"
        result += "]),"
        return result


class ProductAlg(Algebra):
    def __init__(self, factors: Sequence[Algebra], signature: Optional[List[int]] = None):
        size = math.prod(a.size for a in factors)
        length = sum(a.length for a in factors)

        if signature is None:
            signature = factors[0].signature
        assert all(a.signature == signature for a in factors)
        super().__init__(size, length, signature)
        self.factors = list(factors)

    def apply(self, op: int, args: List[BitVec], partop: bool = False) -> BitVec:
        solver = Solver.CALC
        literals = []
        start = 0
        for alg in self.factors:
            subargs = [arg.slice(start, start + alg.length) for arg in args]
            part = alg.apply(op, subargs, partop)
            solver |= part.solver
            literals.extend(part.literals)
            start += alg.length
        assert start == self.length
        return BitVec(solver, literals)

    def combine(self, parts: Sequence[BitVec]) -> BitVec:
        assert len(parts) == len(self.factors)
        solver = Solver.CALC
        literals = []
        for part in parts:
            solver |= part.solver
            literals += part.literals
        assert len(literals) == self.length
        return BitVec(solver, literals)

    def splitup(self, elem: BitVec) -> List[BitVec]:
        assert len(elem) == self.length
        parts = []
        start = 0
        for alg in self.factors:
            parts.append(elem.slice(start, start + alg.length))
            start += alg.length
        return parts

    def encode_elem(self, elem: List[Any]) -> BitVec:
        assert len(elem) == len(self.factors)
        return self.combine([f.encode_elem(e) for f, e in zip(self.factors, elem)])

    def decode_elem(self, elem: BitVec) -> List[Any]:
        assert len(elem) == self.length
        return [f.decode_elem(e) for f, e in zip(self.factors, self.splitup(elem))]

    def solution(self) -> 'ProductAlg':
        return ProductAlg([f.solution() for f in self.factors])
