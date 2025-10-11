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
from typing import List

from ._uasat import Solver, BitVec


class Domain:
    def __init__(self, length: int, size: int):
        self.length = length
        self.size = size

    def contains(self, elem: BitVec) -> BitVec:
        assert len(elem) == self.length
        raise NotImplementedError()

    def decode(self, elem: BitVec) -> str:
        assert len(elem) == self.length
        raise NotImplementedError()

    def bool_iff(self, elem0: BitVec, elem1: BitVec, elem2: BitVec) -> BitVec:
        assert len(elem0) == 1 and len(elem1) == len(elem2) == self.length
        solver = elem0.solver or elem1.solver or elem2.solver
        test = elem0.literals[0]
        lits = [solver.bool_iff(test, l1, l2)
                for l1, l2 in zip(elem1.literals, elem2.literals)]
        return BitVec(elem0.solver, lits)


class Product(Domain):
    def __init__(self, *domains: Domain):
        length = sum(domain.length for domain in domains)
        size = math.prod(domain.size for domain in domains)
        super().__init__(length, size)
        self.domains = domains

    def parts(self, elem: BitVec) -> List[BitVec]:
        assert len(elem) == self.length
        result = []
        start = 0
        for domain in self.domains:
            result.append(elem.slice(start, start + domain.length))
            start += domain.length
        return result

    def contains(self, elem: BitVec) -> BitVec:
        result = BOOLEAN.TRUE
        for dom, part in zip(self.domains, self.parts(elem)):
            result = BOOLEAN.bool_and(result, dom.contains(part))
        return result

    def decode(self, elem: BitVec) -> str:
        result = "["
        first = True
        for dom, part in zip(self.domains, self.parts(elem)):
            if first:
                first = False
            else:
                result += ","
            result += dom.decode(part)
        result += "]"
        return result


class Power(Domain):
    def __init__(self, codomain: Domain, domain: Domain):
        length = codomain.length * domain.size
        size = codomain.size ** domain.size
        super().__init__(length, size)
        self.codomain = codomain
        self.domain = domain

    def parts(self, elem: BitVec) -> List[BitVec]:
        assert len(elem) == self.length
        result = []
        for start in range(0, self.length, self.codomain.length):
            result.append(elem.slice(start, start + self.codomain.length))
        return result

    def contains(self, elem: BitVec) -> BitVec:
        result = BOOLEAN.TRUE
        for part in self.parts(elem):
            result = BOOLEAN.bool_and(result, self.codomain.contains(part))
        return result

    def decode(self, elem: BitVec) -> str:
        result = "["
        first = True
        for part in self.parts(elem):
            if first:
                first = False
            else:
                result += ","
            result += self.codomain.decode(part)
        result += "]"
        return result


class Boolean(Domain):
    def __init__(self):
        super().__init__(1, 2)

    TRUE = BitVec(Solver.CALC, [Solver.TRUE])
    FALSE = BitVec(Solver.CALC, [Solver.FALSE])

    def contains(self, elem: BitVec) -> BitVec:
        assert len(elem) == self.length
        return Boolean.TRUE

    def decode(self, elem: BitVec) -> str:
        assert len(elem) == self.length
        lit = elem[0]
        if lit == Solver.TRUE:
            return "1"
        elif lit == Solver.FALSE:
            return "0"
        else:
            raise ValueError("invalid elem")

    def bool_lift(self, value: bool) -> BitVec:
        return Boolean.TRUE if value else Boolean.FALSE

    def bool_not(self, elem: BitVec) -> BitVec:
        assert len(elem) == self.length
        return ~elem

    def bool_or(self, elem0: BitVec, elem1: BitVec) -> BitVec:
        assert len(elem0) == len(elem1) == self.length
        return elem0 | elem1

    def bool_and(self, elem0: BitVec, elem1: BitVec) -> BitVec:
        assert len(elem0) == len(elem1) == self.length
        return elem0 & elem1

    def bool_imp(self, elem0: BitVec, elem1: BitVec) -> BitVec:
        assert len(elem0) == len(elem1) == self.length
        return ~elem0 | elem1

    def bool_xor(self, elem0: BitVec, elem1: BitVec) -> BitVec:
        assert len(elem0) == len(elem1) == self.length
        return elem0 ^ elem1

    def bool_equ(self, elem0: BitVec, elem1: BitVec) -> BitVec:
        assert len(elem0) == len(elem1) == self.length
        return ~elem0 ^ elem1


BOOLEAN = Boolean()


class SmallSet(Domain):
    def __init__(self, size: int):
        super().__init__(size, size)

    def contains(self, elem: BitVec) -> BitVec:
        assert len(elem) == self.length
        lit = elem.solver.fold_one(elem.literals)
        return BitVec(elem.solver, [lit])

    def decode(self, elem: BitVec) -> str:
        assert len(elem) == self.length
        val = None
        for i in range(self.size):
            if elem.literals[i] == Solver.TRUE:
                assert val is None
                val = i
            else:
                assert elem.literals[i] == Solver.FALSE
        if val is None:
            raise ValueError("invalid elem")
        return str(val)


class Operator:
    def __init__(self, domains: List[Domain], codomain: Domain):
        self.domains = domains
        self.codomain = codomain

    @property
    def arity(self) -> int:
        return len(self.domains)

    def __call__(self, *args: Domain):
        assert len(args) == self.arity
        for domain, arg in zip(self.domains, args):
            assert domain.length == len(args)
        raise NotImplementedError()
