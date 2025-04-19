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

from .uasat import Solver


class Element:
    def __init__(self, domain: 'Domain', solver: Solver, literals: List[int]):
        self.domain = domain
        self.solver = solver
        self.literals = literals

    @property
    def length(self):
        return len(self.literals)


class Domain:
    def __init__(self, length: int):
        self.length = length

    def compatible(self, elem: Element) -> bool:
        return elem.domain == self and elem.length == self.length

    def contains(self, elem: Element) -> Element:
        assert self.compatible(elem)
        raise NotImplementedError()


class Operator:
    def __init__(self, domains: List[Domain], codomain: Domain):
        self.domains = domains
        self.codomain = codomain

    @property
    def arity(self):
        return len(self.domains)

    def evaluate(self, elements: List[Element]) -> Element:
        assert len(elements) == len(self.domains)
        assert all(d.compatible(e) for (d, e) in zip(self.domains, elements))


class Boolean:
    def __init__(self):
        super().__init__(1)

    def contains(self, elem: Element) -> Element:
        assert self.compatible(elem)
        return [elem.solver.bool_true()]

    def bool_and(self, elem0: Element, elem1: Element) -> Element:
        assert self.compatible(elem0) and self.compatible(elem1) \
            and elem0.solver == elem1.solver
        elem2 = elem0.solver.bool_and(elem0.literals[0], elem1.literals[0])
        return Element(self, elem0.solver, [elem2])


class Fixed(Domain):
    def __init__(self, size: int):
        super().__init__(size)

    def contains(self, elem: Element) -> Element:
        return [elem.solver.fold_one(elem.literals)]


class Product(Domain):
    def __init__(self, factors: List[Domain]):
        super().__init__(sum(f.length for f in factors))
        self.factors = factors


class Power(Domain):
    def __init__(self, base: Domain, exponent: Domain):
        super().__init__(base.num_bits ** exponent.num_bits)
        self.base = base
        self.exponent = exponent
