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

from typeguard import typechecked
from typing import List

from .domain import Domain


class Operator:
    @typechecked
    def __init__(self, domains: List[Domain], codomain: Domain):
        self.domains = domains
        self.codomain = codomain

    @property
    @typechecked
    def arity(self) -> int:
        return len(self.domains)

    @typechecked
    def __call__(self, *args: Domain):
        assert len(args) == self.arity
        for domain, arg in zip(self.domains, args):
            assert domain.length == len(arg)
        raise NotImplementedError()
