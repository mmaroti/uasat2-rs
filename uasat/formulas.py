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

from typing import Callable, List, Optional, Set


class Domain:
    def __init__(self, name: str, size: Optional[int]):
        self.name = name
        self.size = size

    def forall(self, callable: Callable[..., 'Formula'],
               num_vars: Optional[int] = None) -> 'Formula':
        if num_vars is None:
            num_vars = callable.__code__.co_argcount

        vars = [Variable(self, Variable.next_index + i)
                for i in range(num_vars)]
        Variable.next_index += num_vars
        formula = callable(*vars)
        Variable.next_index -= num_vars

        if isinstance(formula, ForAll):
            return ForAll(vars + formula.variables, formula.formula)
        else:
            return ForAll(vars, formula)

    def exists(self, callable: Callable[..., 'Formula'],
               num_vars: Optional[int] = None) -> 'Formula':
        if num_vars is None:
            num_vars = callable.__code__.co_argcount

        vars = [Variable(self, Variable.next_index + i)
                for i in range(num_vars)]
        Variable.next_index += num_vars
        formula = callable(*vars)
        Variable.next_index -= num_vars

        if isinstance(formula, Exists):
            return Exists(vars + formula.variables, formula.formula)
        else:
            return Exists(vars, formula)


class Variable:
    next_index: int = 0

    def __init__(self, domain: Domain, index: int):
        self.domain = domain
        self.index = index

    def __str__(self) -> str:
        return "X" + str(self.index)

    def __eq__(self, other: 'Variable') -> 'Formula':
        return Equ(self, other)


class Relation:
    def __init__(self, name: str, domains: List[Domain]):
        self.name = name
        self.domains = domains

    @property
    def arity(self) -> int:
        return len(self.domains)

    def __call__(self, *variables: Variable) -> 'Formula':
        assert len(variables) == self.arity
        return Atomic(self, list(variables))

    def functional(self) -> 'Formula':
        assert len(self.domains) >= 1

        def build(vars, pos: int) -> 'Formula':
            if pos + 1 < len(self.domains):
                return self.domains[pos].forall(
                    lambda x: build(vars + [x], pos + 1))
            else:
                return self.domains[-1].forall(
                    lambda x, y: ~self(*vars, x) | ~self(*vars, y) | (x == y))

        return build([], 0)

    def existential(self) -> 'Formula':
        assert len(self.domains) >= 1

        def build(vars, pos: int) -> 'Formula':
            if pos + 1 < len(self.domains):
                return self.domains[pos].forall(
                    lambda x: build(vars + [x], pos + 1))
            else:
                return self.domains[-1].exists(
                    lambda x: self(*vars, x))

        return build([], 0)


class Formula:
    @property
    def free_variables(self) -> Set[Variable]:
        raise NotImplementedError()

    def __invert__(self) -> 'Formula':
        return Not(self)

    def __and__(self, other: 'Formula') -> 'Formula':
        if isinstance(self, And):
            formulas = list(self.formulas)
        else:
            formulas = [self]

        if isinstance(other, And):
            formulas.extend(other.formulas)
        else:
            formulas.append(other)

        return And(*formulas)

    def __or__(self, other: 'Formula') -> 'Formula':
        if isinstance(self, Or):
            formulas = list(self.formulas)
        else:
            formulas = [self]

        if isinstance(other, Or):
            formulas.extend(other.formulas)
        else:
            formulas.append(other)

        return Or(*formulas)

    def __xor__(self, other: 'Formula') -> 'Formula':
        if isinstance(self, Xor):
            formulas = list(self.formulas)
        else:
            formulas = [self]

        if isinstance(other, Xor):
            formulas.extend(other.formulas)
        else:
            formulas.append(other)

        return Xor(*formulas)

    def __str__(self) -> str:
        raise NotImplementedError()


class Atomic(Formula):
    def __init__(self, relation: Relation, variables: List[Variable]):
        assert relation.domains == [var.domain for var in variables]
        self.symbol = relation
        self.variables = variables

    @property
    def free_variables(self) -> Set[Variable]:
        return set(self.variables)

    def __str__(self) -> str:
        return self.symbol.name + "(" \
            + ",".join(str(v) for v in self.variables) + ")"


class ForAll(Formula):
    def __init__(self, variables: List[Variable], formula: Formula):
        assert all(isinstance(var, Variable) for var in variables)
        assert isinstance(formula, Formula)
        self.variables = variables
        self.formula = formula

    def __str__(self) -> str:
        return "![" + ",".join(str(v) for v in self.variables) + "]: " \
            + str(self.formula)

    @property
    def free_variables(self) -> Set[Variable]:
        vars = self.formula.free_variables
        vars.difference_update(self.variables)
        return vars


class Exists(Formula):
    def __init__(self, variables: List[Variable], formula: Formula):
        assert all(isinstance(var, Variable) for var in variables)
        assert isinstance(formula, Formula)
        self.variables = variables
        self.formula = formula

    def __str__(self) -> str:
        return "?[" + ",".join(str(v) for v in self.variables) + "]: " \
            + str(self.formula)

    @property
    def free_variables(self) -> Set[Variable]:
        vars = self.formula.free_variables
        vars.difference_update(self.variables)
        return vars


class Not(Formula):
    def __init__(self, formula: Formula):
        assert isinstance(formula, Formula)
        self.formula = formula

    def __invert__(self) -> 'Formula':
        return self.formula

    def __str__(self) -> str:
        return "~" + str(self.formula)

    @property
    def free_variables(self) -> Set[Variable]:
        return self.formula.free_variables


class And(Formula):
    def __init__(self, *formulas: Formula):
        assert all(isinstance(fml, Formula) for fml in formulas)
        self.formulas = formulas

    def __str__(self) -> str:
        return "(" + " & ".join(str(f) for f in self.formulas) + ")"

    @property
    def free_variables(self) -> Set[Variable]:
        vars = set()
        for formula in self.formulas:
            vars.update(formula.free_variables)
        return vars


class Or(Formula):
    def __init__(self, *formulas: Formula):
        assert all(isinstance(fml, Formula) for fml in formulas)
        self.formulas = formulas

    def __str__(self) -> str:
        return "(" + " | ".join(str(f) for f in self.formulas) + ")"

    @property
    def free_variables(self) -> Set[Variable]:
        vars = set()
        for formula in self.formulas:
            vars.update(formula.free_variables)
        return vars


class Xor(Formula):
    def __init__(self, *formulas: Formula):
        self.formulas = formulas

    def __str__(self) -> str:
        return "(" + " ^ ".join(str(f) for f in self.formulas) + ")"

    @property
    def free_variables(self) -> Set[Variable]:
        vars = set()
        for formula in self.formulas:
            vars.update(formula.free_variables)
        return vars


class Equ(Formula):
    def __init__(self, var1: Variable, var2: Variable):
        assert isinstance(var1, Variable) and isinstance(var2, Variable)
        self.var1 = var1
        self.var2 = var2

    def __str__(self) -> str:
        return str(self.var1) + "=" + str(self.var2)

    @property
    def free_variables(self) -> Set[Variable]:
        return set((self.var1, self.var2))
