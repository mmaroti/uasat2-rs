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
use std::sync::atomic::{AtomicU32, Ordering};
use std::sync::Mutex;

/// The CaDiCaL incremental SAT solver. The literals are unwrapped positive
/// and negative integers, exactly as in the DIMACS format.
#[pyclass(frozen)]
pub struct Solver {
    solver: Mutex<cadical::Solver>,
    num_vars: AtomicU32,
}

#[pymethods]
impl Solver {
    #[new]
    /// Constructs a new solver instance. The literal 1 is always added
    /// by default to the solver and serves as the true value.
    pub fn new() -> Self {
        let mut solver = cadical::Solver::new();
        solver.add_clause([1]);
        Self {
            solver: Mutex::new(solver),
            num_vars: AtomicU32::new(1),
        }
    }

    /// Constructs a new solver with one of the following pre-defined
    /// configurations of advanced internal options:
    /// * `default`: set default advanced internal options
    /// * `plain`: disable all internal preprocessing options
    /// * `sat`: set internal options to target satisfiable instances
    /// * `unsat`: set internal options to target unsatisfiable instances
    #[staticmethod]
    pub fn with_config(config: &str) -> Self {
        let mut solver = cadical::Solver::with_config(config).unwrap();
        solver.add_clause(vec![1].into_iter());
        Self {
            solver: Mutex::new(solver),
            num_vars: AtomicU32::new(1),
        }
    }

    /// Returns the name and version of the CaDiCaL library.
    pub fn signature(&self) -> String {
        self.solver.lock().unwrap().signature().into()
    }

    /// Adds a new variable to the solver and returns the corresponding
    /// literal as an integer.
    pub fn add_variable(&self) -> i32 {
        let val = self.num_vars.fetch_add(1, Ordering::Relaxed);
        debug_assert!(val < i32::MAX as u32);
        (val + 1) as i32
    }

    /// Adds the given clause to the solver. Negated literals are negative
    /// integers, positive literals are positive ones. All literals must be
    /// non-zero.
    pub fn add_clause(&self, literals: Vec<i32>) {
        debug_assert!(literals.iter().all(|&l| l != 0));
        self.solver.lock().unwrap().add_clause(literals.into_iter());
    }

    /// Runs the solver and returns true if a solution is available.
    pub fn solve(&self) -> bool {
        self.solver.lock().unwrap().solve().unwrap()
    }

    /// Solves the formula defined by the set of clauses under the given
    /// assumptions.
    pub fn solve_with(&self, literals: Vec<i32>) -> bool {
        self.solver
            .lock()
            .unwrap()
            .solve_with(literals.into_iter())
            .unwrap()
    }

    /// Returns the value of the literal in the found model.
    pub fn get_value(&self, literal: i32) -> bool {
        self.solver.lock().unwrap().value(literal) == Some(true)
    }

    /// Returns the number of variables in the solver.
    pub fn num_variables(&self) -> u32 {
        self.num_vars.load(Ordering::Relaxed)
    }

    /// Returns the number of clauses in the solver.
    pub fn num_clauses(&self) -> usize {
        self.solver.lock().unwrap().num_clauses()
    }

    /// Returns the logical true element.
    pub fn bool_true(&self) -> i32 {
        1
    }

    /// Returns the logical true element.
    pub fn bool_false(&self) -> i32 {
        -1
    }

    /// Returns the always true or false literal.
    pub fn bool_lift(&self, elem: bool) -> i32 {
        if elem {
            1
        } else {
            -1
        }
    }

    /// Returns the logical or of a pair of elements.
    pub fn bool_or(&self, elem1: i32, elem2: i32) -> i32 {
        if elem1 == 1 || elem2 == 1 || elem1 == -elem2 {
            1
        } else if elem1 == -1 || elem1 == elem2 {
            elem2
        } else if elem2 == -1 {
            elem1
        } else {
            let elem3 = self.add_variable();
            self.add_clause(vec![-elem1, elem3]);
            self.add_clause(vec![-elem2, elem3]);
            self.add_clause(vec![elem1, elem2, -elem3]);
            elem3
        }
    }

    /// Returns the logical and of a pair of elements.
    pub fn bool_and(&self, elem1: i32, elem2: i32) -> i32 {
        -self.bool_or(-elem1, -elem2)
    }

    /// Returns the logical implication of a pair of elements.
    pub fn bool_imp(&self, elem1: i32, elem2: i32) -> i32 {
        self.bool_or(-elem1, elem2)
    }

    /// Returns the exclusive or of a pair of elements.
    pub fn bool_xor(&self, elem1: i32, elem2: i32) -> i32 {
        if elem1 == -1 {
            elem2
        } else if elem1 == 1 {
            -elem2
        } else if elem2 == -1 {
            elem1
        } else if elem2 == 1 {
            -elem1
        } else if elem1 == elem2 {
            -1
        } else if elem1 == -elem2 {
            1
        } else {
            let elem3 = self.add_variable();
            self.add_clause(vec![-elem1, elem2, elem3]);
            self.add_clause(vec![elem1, -elem2, elem3]);
            self.add_clause(vec![elem1, elem2, -elem3]);
            self.add_clause(vec![-elem1, -elem2, -elem3]);
            elem3
        }
    }

    /// Returns the logical equivalence of a pair of elements.
    pub fn bool_equ(&self, elem1: i32, elem2: i32) -> i32 {
        self.bool_xor(-elem1, elem2)
    }

    /// Returns the majority of the given values.
    fn bool_maj(&self, elem1: i32, elem2: i32, elem3: i32) -> i32 {
        let tmp1 = self.bool_and(elem1, elem2);
        let tmp2 = self.bool_and(elem1, elem3);
        let tmp3 = self.bool_and(elem2, elem3);
        let tmp4 = self.bool_or(tmp1, tmp2);
        self.bool_or(tmp3, tmp4)
    }

    /// Computes the conjunction of the elements.
    pub fn bool_fold_all(&self, elems: Vec<i32>) -> i32 {
        let mut result = self.bool_true();
        for elem in elems {
            result = self.bool_and(result, elem);
        }
        result
    }

    /// Computes the conjunction of the elements.
    pub fn bool_fold_any(&self, elems: Vec<i32>) -> i32 {
        let mut result = self.bool_false();
        for elem in elems {
            result = self.bool_or(result, elem);
        }
        result
    }

    /// Computes the boolean sum of the elements.
    pub fn bool_fold_xor(&self, elems: Vec<i32>) -> i32 {
        let mut result = self.bool_false();
        for elem in elems {
            result = self.bool_xor(result, elem);
        }
        result
    }

    /// Computes the exactly one predicate over the given elements.
    fn bool_fold_one(&self, elems: Vec<i32>) -> i32 {
        let mut min1 = self.bool_false();
        let mut min2 = self.bool_false();
        for elem in elems {
            let tmp = self.bool_and(min1, elem);
            min2 = self.bool_or(min2, tmp);
            min1 = self.bool_or(min1, elem);
        }
        self.bool_and(min1, -min2)
    }

    /// Computes the at most one predicate over the given elements.
    fn bool_fold_amo(&self, elems: Vec<i32>) -> i32 {
        let mut min1 = self.bool_false();
        let mut min2 = self.bool_false();
        for elem in elems {
            let tmp = self.bool_and(min1, elem);
            min2 = self.bool_or(min2, tmp);
            min1 = self.bool_or(min1, elem);
        }
        -min2
    }

    /// Returns true if the two sequences are equal.
    fn bool_cmp_equ(&self, elems1: Vec<i32>, elems2: Vec<i32>) -> i32 {
        assert_eq!(elems1.len(), elems2.len());
        let mut result = self.bool_true();
        for (a, b) in elems1.into_iter().zip(elems2.into_iter()) {
            let c = self.bool_equ(a, b);
            result = self.bool_and(result, c);
        }
        result
    }

    /// Returns true if the two sequences are not equal.
    fn bool_cmp_neq(&self, elems1: Vec<i32>, elems2: Vec<i32>) -> i32 {
        -self.bool_cmp_equ(elems1, elems2)
    }
}
