/*
* Copyright (C) 2019-2025, Miklos Maroti
*
* This program is free software: you can redistribute it and/or modify
* it under the terms of the GNU General Public License as published by
* the Free Software Foundation, either version 3 of the License, or
* (at your option) any later version.
*
* This program is distributed in the hope that it will be useful,
* but WITHOUT ANY WARRANTY; without even the implied warranty of
* MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
* GNU General Public License for more details.
*
* You should have received a copy of the GNU General Public License
* along with this program.  If not, see <http://www.gnu.org/licenses/>.
*/

use pyo3::prelude::*;
use std::sync::Mutex;
use std::time::{Duration, SystemTime};

/// Helper structure to check for python signals.
struct CheckSig {
    last: SystemTime,
}

impl CheckSig {
    fn new() -> Self {
        Self {
            last: SystemTime::now(),
        }
    }
}

impl cadical::Callbacks for CheckSig {
    fn terminate(&mut self) -> bool {
        let now = SystemTime::now();
        if now
            .duration_since(self.last)
            .is_ok_and(|v| v < Duration::from_millis(5))
        {
            return false;
        }

        self.last = now;
        Python::with_gil(|py| py.check_signals()).is_err()
    }
}

/// The CaDiCaL incremental SAT solver. The literals are unwrapped positive
/// and negative integers, exactly as in the DIMACS format.
pub struct Solver {
    solver: cadical::Solver<CheckSig>,
    num_vars: i32,
}

impl Solver {
    /// Constructs a new solver instance. The literal 1 is always added
    /// by default to the solver and serves as the true value.
    pub fn new() -> Self {
        let mut solver = cadical::Solver::new();
        solver.set_callbacks(Some(CheckSig::new()));
        solver.add_clause([1]);
        Self {
            solver,
            num_vars: 1,
        }
    }

    /// Constructs a new solver with one of the following pre-defined
    /// configurations of advanced internal options:
    /// * `default`: set default advanced internal options
    /// * `plain`: disable all internal preprocessing options
    /// * `sat`: set internal options to target satisfiable instances
    /// * `unsat`: set internal options to target unsatisfiable instances
    pub fn with_config(config: &str) -> Self {
        let mut solver = cadical::Solver::with_config(config).unwrap();
        solver.set_callbacks(Some(CheckSig::new()));
        solver.add_clause([1]);
        Self {
            solver,
            num_vars: 1,
        }
    }

    /// Returns the name and version of the CaDiCaL library.
    #[inline]
    pub fn signature(&self) -> &str {
        self.solver.signature()
    }

    /// Adds a new variable to the solver and returns the corresponding
    /// literal as an integer.
    #[inline]
    pub fn add_variable(&mut self) -> i32 {
        self.num_vars += 1;
        self.num_vars
    }

    /// Returns the number of variables in the solver.
    #[inline]
    pub fn num_variables(&self) -> usize {
        self.num_vars as usize
    }

    /// Adds the given clause to the solver. Negated literals are negative
    /// integers, positive literals are positive ones. All literals must be
    /// non-zero.
    #[inline]
    pub fn add_clause<ITER>(&mut self, clause: ITER)
    where
        ITER: Iterator<Item = i32>,
    {
        self.solver.add_clause(clause)
    }

    /// Adds the unary clause to the solver.
    #[inline]
    pub fn add_clause1(&mut self, lit0: i32) {
        self.solver.add_clause([lit0])
    }

    /// Adds the binary clause to the solver.
    #[inline]
    pub fn add_clause2(&mut self, lit0: i32, lit1: i32) {
        self.solver.add_clause([lit0, lit1])
    }

    /// Adds the ternary clause to the solver.
    #[inline]
    pub fn add_clause3(&mut self, lit0: i32, lit1: i32, lit2: i32) {
        self.solver.add_clause([lit0, lit1, lit2])
    }

    /// Adds the quaternary clause to the solver.
    #[inline]
    pub fn add_clause4(&mut self, lit0: i32, lit1: i32, lit2: i32, lit3: i32) {
        self.solver.add_clause([lit0, lit1, lit2, lit3])
    }

    /// Returns the number of clauses in the solver.
    #[inline]
    pub fn num_clauses(&self) -> usize {
        self.solver.num_clauses()
    }

    /// Solves the formula defined by the added clauses. If the formula is
    /// satisfiable, then `Some(true)` is returned. If the formula is
    /// unsatisfiable, then `Some(false)` is returned. If the solver runs out
    /// of resources or was terminated, then `None` is returned.
    #[inline]
    pub fn solve(&mut self) -> Option<bool> {
        self.solver.solve()
    }

    /// Solves the formula defined by the set of clauses under the given
    /// assumptions.
    #[inline]
    pub fn solve_with<ITER>(&mut self, assumptions: ITER) -> Option<bool>
    where
        ITER: Iterator<Item = i32>,
    {
        self.solver.solve_with(assumptions)
    }

    /// Returns the value of the given literal in the last solution. The
    /// state of the solver must be `Some(true)`. The returned value is
    /// `None` if the formula is satisfied regardless of the value of the
    /// literal.
    #[inline]
    pub fn get_value(&self, literal: i32) -> Option<bool> {
        self.solver.value(literal)
    }

    /// The always true literal.
    pub const TRUE: i32 = 1;

    /// The always false literal.
    pub const FALSE: i32 = -1;

    /// Returns the negated literal.
    #[inline]
    pub fn bool_not(lit: i32) -> i32 {
        -lit
    }

    /// Returns the always true or false literal.
    #[inline]
    pub fn bool_lift(val: bool) -> i32 {
        if val {
            Solver::TRUE
        } else {
            Solver::FALSE
        }
    }

    /// Returns the disjunction of a pair of elements.
    pub fn bool_or(&mut self, lit0: i32, lit1: i32) -> i32 {
        if lit0 == Solver::TRUE || lit1 == Solver::TRUE || lit0 == Solver::bool_not(lit1) {
            Solver::TRUE
        } else if lit0 == Solver::FALSE || lit0 == lit1 {
            lit1
        } else if lit1 == Solver::FALSE {
            lit0
        } else {
            let lit2 = self.add_variable();
            self.add_clause2(Solver::bool_not(lit0), lit2);
            self.add_clause2(Solver::bool_not(lit1), lit2);
            self.add_clause3(lit0, lit1, Solver::bool_not(lit2));
            lit2
        }
    }

    /// Returns the conjunction of a pair of elements.
    #[inline]
    pub fn bool_and(&mut self, lit0: i32, lit1: i32) -> i32 {
        Solver::bool_not(self.bool_or(Solver::bool_not(lit0), Solver::bool_not(lit1)))
    }

    /// Returns the logical implication of a pair of elements.
    #[inline]
    pub fn bool_imp(&mut self, lit0: i32, lit1: i32) -> i32 {
        self.bool_or(Solver::bool_not(lit0), lit1)
    }

    /// Returns the exclusive or of a pair of elements.
    pub fn bool_xor(&mut self, lit0: i32, lit1: i32) -> i32 {
        if lit0 == Solver::FALSE {
            lit1
        } else if lit0 == Solver::TRUE {
            Solver::bool_not(lit1)
        } else if lit1 == Solver::FALSE {
            lit0
        } else if lit1 == Solver::TRUE {
            Solver::bool_not(lit0)
        } else if lit0 == lit1 {
            Solver::FALSE
        } else if lit0 == Solver::bool_not(lit1) {
            Solver::TRUE
        } else {
            let lit2 = self.add_variable();
            self.add_clause3(Solver::bool_not(lit0), lit1, lit2);
            self.add_clause3(lit0, Solver::bool_not(lit1), lit2);
            self.add_clause3(lit0, lit1, Solver::bool_not(lit2));
            self.add_clause3(
                Solver::bool_not(lit0),
                Solver::bool_not(lit1),
                Solver::bool_not(lit2),
            );
            lit2
        }
    }

    /// Returns the logical equivalence of a pair of elements.
    #[inline]
    pub fn bool_equ(&mut self, lit0: i32, lit1: i32) -> i32 {
        self.bool_xor(Solver::bool_not(lit0), lit1)
    }

    /// Computes the conjunction of the elements.
    #[inline]
    pub fn fold_all<ITER>(&mut self, lits: ITER) -> i32
    where
        ITER: Iterator<Item = i32>,
    {
        let mut result = Solver::TRUE;
        for lit in lits {
            result = self.bool_and(result, lit);
        }
        result
    }

    /// Computes the disjunction of the elements.
    #[inline]
    pub fn fold_any<ITER>(&mut self, lits: ITER) -> i32
    where
        ITER: Iterator<Item = i32>,
    {
        let mut result = Solver::FALSE;
        for lit in lits {
            result = self.bool_or(result, lit);
        }
        result
    }

    /// Computes the exactly one predicate over the given elements.
    pub fn fold_one<ITER>(&mut self, lits: ITER) -> i32
    where
        ITER: Iterator<Item = i32>,
    {
        let mut min1 = Solver::FALSE;
        let mut min2 = Solver::FALSE;
        for lit in lits {
            let tmp = self.bool_and(min1, lit);
            min2 = self.bool_or(min2, tmp);
            min1 = self.bool_or(min1, lit);
        }
        self.bool_and(min1, Solver::bool_not(min2))
    }

    /// Computes the at most one predicate over the given elements.
    pub fn fold_amo<ITER>(&mut self, lits: ITER) -> i32
    where
        ITER: Iterator<Item = i32>,
    {
        let mut min1 = Solver::FALSE;
        let mut min2 = Solver::FALSE;
        for lit in lits {
            let tmp = self.bool_and(min1, lit);
            min2 = self.bool_or(min2, tmp);
            min1 = self.bool_or(min1, lit);
        }
        Solver::bool_not(min2)
    }

    /// Returns true if the two sequences are equal.
    pub fn comp_equ<ITER>(&mut self, lits0: ITER, lits1: ITER) -> i32
    where
        ITER: Iterator<Item = i32>,
    {
        let mut result = Solver::TRUE;
        for (a, b) in lits0.into_iter().zip(lits1.into_iter()) {
            let c = self.bool_equ(a, b);
            result = self.bool_and(result, c);
        }
        result
    }

    /// Returns true if the two sequences are not equal.
    pub fn comp_neq<ITER>(&mut self, lits0: ITER, lits1: ITER) -> i32
    where
        ITER: Iterator<Item = i32>,
    {
        Solver::bool_not(self.comp_equ(lits0, lits1))
    }
}

/// The CaDiCaL incremental SAT solver. The literals are unwrapped positive
/// and negative integers, exactly as in the DIMACS format.
#[pyclass(frozen, name = "Solver")]
pub struct PySolver(Mutex<Solver>);

#[pymethods]
impl PySolver {
    /// Constructs a new solver instance. The literal 1 is always added
    /// by default to the solver and serves as the true value.
    #[new]
    pub fn new() -> Self {
        Self(Mutex::new(Solver::new()))
    }

    /// Constructs a new solver with one of the following pre-defined
    /// configurations of advanced internal options:
    /// * `default`: set default advanced internal options
    /// * `plain`: disable all internal preprocessing options
    /// * `sat`: set internal options to target satisfiable instances
    /// * `unsat`: set internal options to target unsatisfiable instances
    #[staticmethod]
    pub fn with_config(config: &str) -> Self {
        Self(Mutex::new(Solver::with_config(config)))
    }

    /// Returns the name and version of the CaDiCaL library.
    pub fn signature(&self) -> String {
        self.0.lock().unwrap().signature().into()
    }

    /// Adds a new variable to the solver and returns the corresponding
    /// literal as an integer.
    pub fn add_variable(&self) -> i32 {
        self.0.lock().unwrap().add_variable()
    }

    /// Returns the number of variables in the solver.
    pub fn num_variables(&self) -> usize {
        self.0.lock().unwrap().num_variables()
    }

    /// Adds the given clause to the solver. Negated literals are negative
    /// integers, positive literals are positive ones. All literals must be
    /// non-zero.
    pub fn add_clause(&self, clause: Vec<i32>) {
        self.0.lock().unwrap().add_clause(clause.into_iter())
    }

    /// Adds the unary clause to the solver.
    pub fn add_clause1(&self, lit0: i32) {
        self.0.lock().unwrap().add_clause1(lit0)
    }

    /// Adds the binary clause to the solver.
    pub fn add_clause2(&self, lit0: i32, lit1: i32) {
        self.0.lock().unwrap().add_clause2(lit0, lit1)
    }

    /// Adds the ternary clause to the solver.
    pub fn add_clause3(&self, lit0: i32, lit1: i32, lit2: i32) {
        self.0.lock().unwrap().add_clause3(lit0, lit1, lit2)
    }

    /// Adds the quaternary clause to the solver.
    pub fn add_clause4(&self, lit0: i32, lit1: i32, lit2: i32, lit3: i32) {
        self.0.lock().unwrap().add_clause4(lit0, lit1, lit2, lit3)
    }

    /// Returns the number of clauses in the solver.
    pub fn num_clauses(&self) -> usize {
        self.0.lock().unwrap().num_clauses()
    }

    /// Solves the formula defined by the added clauses. If the formula is
    /// satisfiable, then `Some(true)` is returned. If the formula is
    /// unsatisfiable, then `Some(false)` is returned. If the solver runs out
    /// of resources or was terminated, then `None` is returned.
    pub fn solve(&self) -> Option<bool> {
        self.0.lock().unwrap().solve()
    }

    /// Solves the formula defined by the set of clauses under the given
    /// assumptions.
    pub fn solve_with(&self, assumptions: Vec<i32>) -> Option<bool> {
        self.0.lock().unwrap().solve_with(assumptions.into_iter())
    }

    /// Returns the value of the given literal in the last solution. The
    /// state of the solver must be `Some(true)`. The returned value is
    /// `None` if the formula is satisfied regardless of the value of the
    /// literal.
    pub fn get_value(&self, literal: i32) -> Option<bool> {
        self.0.lock().unwrap().get_value(literal)
    }

    /// The always true literal.
    #[classattr]
    pub const TRUE: i32 = Solver::TRUE;

    /// The always false literal.
    #[classattr]
    pub const FALSE: i32 = Solver::FALSE;

    /// Returns the negated literal.
    #[staticmethod]
    pub fn bool_not(lit: i32) -> i32 {
        Solver::bool_not(lit)
    }

    /// Returns the always true or false literal.
    #[staticmethod]
    pub fn bool_lift(val: bool) -> i32 {
        Solver::bool_lift(val)
    }

    /// Returns the disjunction of a pair of elements.
    pub fn bool_or(&self, lit0: i32, lit1: i32) -> i32 {
        self.0.lock().unwrap().bool_or(lit0, lit1)
    }

    /// Computes the disjunction of the elements.
    pub fn bool_and(&self, lit0: i32, lit1: i32) -> i32 {
        self.0.lock().unwrap().bool_and(lit0, lit1)
    }

    /// Returns the logical implication of a pair of elements.
    pub fn bool_imp(&self, lit0: i32, lit1: i32) -> i32 {
        self.0.lock().unwrap().bool_imp(lit0, lit1)
    }

    /// Returns the exclusive or of a pair of elements.
    pub fn bool_xor(&self, lit0: i32, lit1: i32) -> i32 {
        self.0.lock().unwrap().bool_xor(lit0, lit1)
    }

    /// Returns the logical equivalence of a pair of elements.
    pub fn bool_equ(&self, lit0: i32, lit1: i32) -> i32 {
        self.0.lock().unwrap().bool_equ(lit0, lit1)
    }

    /// Computes the conjunction of the elements.
    pub fn fold_all(&self, lits: Vec<i32>) -> i32 {
        self.0.lock().unwrap().fold_all(lits.into_iter())
    }

    /// Computes the disjunction of the elements.
    pub fn fold_any(&self, lits: Vec<i32>) -> i32 {
        self.0.lock().unwrap().fold_any(lits.into_iter())
    }

    /// Computes the exactly one predicate over the given elements.
    pub fn fold_one(&self, lits: Vec<i32>) -> i32 {
        self.0.lock().unwrap().fold_one(lits.into_iter())
    }

    /// Computes the at most one predicate over the given elements.
    pub fn fold_amo(&self, lits: Vec<i32>) -> i32 {
        self.0.lock().unwrap().fold_amo(lits.into_iter())
    }

    /// Returns true if the two sequences are equal.
    pub fn comp_equ(&self, lits0: Vec<i32>, lits1: Vec<i32>) -> i32 {
        assert_eq!(lits0.len(), lits1.len());
        self.0
            .lock()
            .unwrap()
            .comp_equ(lits0.into_iter(), lits1.into_iter())
    }

    /// Returns true if the two sequences are not equal.
    pub fn comp_neq(&self, lits0: Vec<i32>, lits1: Vec<i32>) -> i32 {
        assert_eq!(lits0.len(), lits1.len());
        self.0
            .lock()
            .unwrap()
            .comp_neq(lits0.into_iter(), lits1.into_iter())
    }
}
