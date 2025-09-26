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

use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use std::sync::{Mutex, MutexGuard};
use std::time::{Duration, SystemTime};

/// Helper structure to check for python signals.
struct CheckSignal {
    last: SystemTime,
}

impl CheckSignal {
    fn new() -> Self {
        Self {
            last: SystemTime::now(),
        }
    }
}

impl cadical::Callbacks for CheckSignal {
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
#[pyclass(frozen, name = "Solver")]
pub struct PySolver(Option<Mutex<cadical::Solver<CheckSignal>>>);

impl PySolver {
    fn get_solver(&self) -> MutexGuard<'_, cadical::Solver<CheckSignal>> {
        self.0
            .as_ref()
            .expect("calculator instance")
            .lock()
            .unwrap()
    }

    pub fn join(py: Python<'_>, first: &Py<Self>, second: &Py<Self>) -> PyResult<Py<Self>> {
        if second.get().0.is_none() {
            Ok(first.clone_ref(py))
        } else if first.get().0.is_none() || first.is(second) {
            Ok(second.clone_ref(py))
        } else {
            Err(PyValueError::new_err("not joinable"))
        }
    }
}

#[allow(clippy::new_without_default)]
#[pymethods]
impl PySolver {
    /// Constructs a new solver instance. The literal 1 is always added
    /// by default to the solver and serves as the true value.
    #[new]
    pub fn new() -> Self {
        let mut solver = cadical::Solver::new();
        solver.set_callbacks(Some(CheckSignal::new()));
        solver.reserve(1);
        solver.add_clause([1]);
        Self(Some(Mutex::new(solver)))
    }

    /// Constructs a new solver with one of the following pre-defined
    /// configurations of advanced internal options:
    /// * `default`: set default advanced internal options
    /// * `plain`: disable all internal preprocessing options
    /// * `sat`: set internal options to target satisfiable instances
    /// * `unsat`: set internal options to target unsatisfiable instances
    #[staticmethod]
    pub fn with_config(config: &str) -> PyResult<Self> {
        let mut solver =
            cadical::Solver::with_config(config).map_err(|e| PyValueError::new_err(e.msg))?;
        solver.set_callbacks(Some(CheckSignal::new()));
        solver.reserve(1);
        solver.add_clause([1]);
        Ok(Self(Some(Mutex::new(solver))))
    }

    /// The unique calculator instance that can do all calculations with
    /// TRUE and FALSE values, but cannot do any SAT solving.
    #[classattr]
    pub const CALC: PySolver = PySolver(None);

    /// Returns the name and version of the CaDiCaL library.
    #[getter]
    pub fn signature(&self) -> String {
        if let Some(s) = self.0.as_ref() {
            let s = s.lock().unwrap();
            s.signature().into()
        } else {
            "calculator".into()
        }
    }

    /// Retruns TRUE if this is a real solver instance, and FALSE
    /// if this is just the calculator instance.
    #[inline]
    pub fn __bool__(&self) -> bool {
        self.0.is_some()
    }

    /// Returns a pointer to either this or the other solver, whichever is
    /// not the calculator instance. If neither is static and they are different
    /// then an error is returned.
    pub fn __or__(me: &Bound<'_, Self>, other: Py<Self>) -> PyResult<Py<Self>> {
        if me.get().0.is_none() || me.is(&other) {
            Ok(other)
        } else if other.get().0.is_none() {
            Ok(me.clone().unbind())
        } else {
            Err(PyValueError::new_err("not joinable"))
        }
    }

    /// Adds a new variable to the solver and returns the corresponding
    /// literal as an integer.
    pub fn add_variable(&self) -> i32 {
        let mut solver = self.get_solver();
        let var = solver.max_variable() + 1;
        solver.reserve(var);
        var
    }

    /// Returns the number of variables in the solver.
    #[getter]
    pub fn num_variables(&self) -> usize {
        self.get_solver().max_variable() as usize
    }

    /// Adds the given clause to the solver. Negated literals are negative
    /// integers, positive literals are positive ones. All literals must be
    /// non-zero.
    pub fn add_clause(&self, clause: Vec<i32>) {
        self.get_solver().add_clause(clause);
    }

    /// Adds the unary clause to the solver.
    pub fn add_clause1(&self, lit0: i32) {
        self.get_solver().add_clause([lit0]);
    }

    /// Adds the binary clause to the solver.
    pub fn add_clause2(&self, lit0: i32, lit1: i32) {
        self.get_solver().add_clause([lit0, lit1]);
    }

    /// Adds the ternary clause to the solver.
    pub fn add_clause3(&self, lit0: i32, lit1: i32, lit2: i32) {
        self.get_solver().add_clause([lit0, lit1, lit2]);
    }

    /// Adds the quaternary clause to the solver.
    pub fn add_clause4(&self, lit0: i32, lit1: i32, lit2: i32, lit3: i32) {
        self.get_solver().add_clause([lit0, lit1, lit2, lit3]);
    }

    /// Returns the number of clauses in the solver.
    #[getter]
    pub fn num_clauses(&self) -> usize {
        self.get_solver().num_clauses()
    }

    /// Solves the formula defined by the added clauses. If the formula is
    /// satisfiable, then `Some(true)` is returned. If the formula is
    /// unsatisfiable, then `Some(false)` is returned. If the solver runs out
    /// of resources or was terminated, then `None` is returned.
    pub fn solve(&self) -> Option<bool> {
        self.get_solver().solve()
    }

    /// Solves the formula defined by the set of clauses under the given
    /// assumptions.
    pub fn solve_with(&self, assumptions: Vec<i32>) -> Option<bool> {
        self.get_solver().solve_with(assumptions)
    }

    /// Returns the value of the given literal in the last solution. The
    /// state of the solver must be `Some(true)`. The returned value is
    /// `None` if the formula is satisfied regardless of the value of the
    /// literal.
    pub fn get_value(&self, literal: i32) -> Option<bool> {
        self.get_solver().value(literal)
    }

    /// The always true literal.
    #[classattr]
    pub const TRUE: i32 = 1;

    /// The always false literal.
    #[classattr]
    pub const FALSE: i32 = -1;

    /// Returns the negated literal.
    #[inline]
    #[staticmethod]
    pub fn bool_not(lit: i32) -> i32 {
        -lit
    }

    /// Returns the always true or false literal.
    #[inline]
    #[staticmethod]
    pub fn bool_lift(val: bool) -> i32 {
        if val {
            Self::TRUE
        } else {
            Self::FALSE
        }
    }

    /// Returns the disjunction of a pair of elements.
    pub fn bool_or(&self, lit0: i32, lit1: i32) -> PyResult<i32> {
        if lit0 == Self::TRUE || lit1 == Self::TRUE || lit0 == Self::bool_not(lit1) {
            Ok(Self::TRUE)
        } else if lit0 == Self::FALSE || lit0 == lit1 {
            Ok(lit1)
        } else if lit1 == Self::FALSE {
            Ok(lit0)
        } else if let Some(s) = self.0.as_ref() {
            let mut s = s.lock().unwrap();
            let lit2 = s.max_variable() + 1;
            s.add_clause([Self::bool_not(lit0), lit2]);
            s.add_clause([Self::bool_not(lit1), lit2]);
            s.add_clause([lit0, lit1, Self::bool_not(lit2)]);
            Ok(lit2)
        } else {
            Err(PyValueError::new_err("calculator instance"))
        }
    }

    /// Returns the conjunction of a pair of elements.
    #[inline]
    pub fn bool_and(&self, lit0: i32, lit1: i32) -> PyResult<i32> {
        self.bool_or(Self::bool_not(lit0), Self::bool_not(lit1))
            .map(Self::bool_not)
    }

    /// Returns the logical implication of a pair of elements.
    #[inline]
    pub fn bool_imp(&self, lit0: i32, lit1: i32) -> PyResult<i32> {
        self.bool_or(Self::bool_not(lit0), lit1)
    }

    /// Returns the exclusive or of a pair of elements.
    pub fn bool_xor(&self, lit0: i32, lit1: i32) -> PyResult<i32> {
        if lit0 == Self::FALSE {
            Ok(lit1)
        } else if lit0 == Self::TRUE {
            Ok(Self::bool_not(lit1))
        } else if lit1 == Self::FALSE {
            Ok(lit0)
        } else if lit1 == Self::TRUE {
            Ok(Self::bool_not(lit0))
        } else if lit0 == lit1 {
            Ok(Self::FALSE)
        } else if lit0 == Self::bool_not(lit1) {
            Ok(Self::TRUE)
        } else if let Some(s) = self.0.as_ref() {
            let mut s = s.lock().unwrap();
            let lit2 = s.max_variable() + 1;
            s.add_clause([Self::bool_not(lit0), lit1, lit2]);
            s.add_clause([lit0, Self::bool_not(lit1), lit2]);
            s.add_clause([lit0, lit1, Self::bool_not(lit2)]);
            s.add_clause([
                Self::bool_not(lit0),
                Self::bool_not(lit1),
                Self::bool_not(lit2),
            ]);
            Ok(lit2)
        } else {
            Err(PyValueError::new_err("calculator instance"))
        }
    }

    /// Returns the logical equivalence of a pair of elements.
    #[inline]
    pub fn bool_equ(&self, lit0: i32, lit1: i32) -> PyResult<i32> {
        self.bool_xor(Self::bool_not(lit0), lit1)
    }

    /// Returns the majority of three elements.
    pub fn bool_maj(&self, lit0: i32, lit1: i32, lit2: i32) -> PyResult<i32> {
        if lit0 == lit1 || lit0 == lit2 || lit1 == Self::bool_not(lit2) {
            Ok(lit0)
        } else if lit1 == lit2 || lit0 == Self::bool_not(lit2) {
            Ok(lit1)
        } else if lit0 == Self::bool_not(lit1) {
            Ok(lit2)
        } else if lit0 == Self::FALSE {
            self.bool_and(lit1, lit2)
        } else if lit0 == Self::TRUE {
            self.bool_or(lit1, lit2)
        } else if lit1 == Self::FALSE {
            self.bool_and(lit0, lit2)
        } else if lit1 == Self::TRUE {
            self.bool_or(lit0, lit2)
        } else if lit2 == Self::FALSE {
            self.bool_and(lit0, lit1)
        } else if lit2 == Self::TRUE {
            self.bool_or(lit0, lit1)
        } else if let Some(s) = self.0.as_ref() {
            let mut s = s.lock().unwrap();
            let lit3 = s.max_variable() + 1;
            s.add_clause([lit0, lit1, Self::bool_not(lit3)]);
            s.add_clause([lit0, lit2, Self::bool_not(lit3)]);
            s.add_clause([lit1, lit2, Self::bool_not(lit3)]);
            s.add_clause([Self::bool_not(lit0), Self::bool_not(lit1), lit3]);
            s.add_clause([Self::bool_not(lit0), Self::bool_not(lit2), lit3]);
            s.add_clause([Self::bool_not(lit1), Self::bool_not(lit2), lit3]);
            Ok(lit3)
        } else {
            Err(PyValueError::new_err("calculator instance"))
        }
    }

    /// Returns 'lit1' if 'lit0' is true, otherwise 'lit2' is returned.
    pub fn bool_iff(&self, lit0: i32, lit1: i32, lit2: i32) -> PyResult<i32> {
        if lit1 == lit2 || lit0 == Self::TRUE {
            Ok(lit1)
        } else if lit0 == Self::FALSE {
            Ok(lit2)
        } else if lit1 == Self::bool_not(lit2) {
            self.bool_xor(lit0, lit2)
        } else if lit0 == lit1 || lit1 == Self::TRUE {
            self.bool_or(lit0, lit2)
        } else if lit0 == Self::bool_not(lit1) || lit1 == Self::FALSE {
            self.bool_and(Self::bool_not(lit0), lit2)
        } else if lit0 == Self::bool_not(lit2) || lit2 == Self::TRUE {
            self.bool_or(Self::bool_not(lit0), lit1)
        } else if lit0 == lit2 || lit2 == Self::FALSE {
            self.bool_and(lit0, lit1)
        } else if let Some(s) = self.0.as_ref() {
            let mut s = s.lock().unwrap();
            let lit3 = s.max_variable() + 1;
            s.add_clause([Self::bool_not(lit0), Self::bool_not(lit1), lit3]);
            s.add_clause([Self::bool_not(lit0), lit1, Self::bool_not(lit3)]);
            s.add_clause([lit0, Self::bool_not(lit2), lit3]);
            s.add_clause([lit0, lit2, Self::bool_not(lit3)]);
            Ok(lit3)
        } else {
            Err(PyValueError::new_err("calculator instance"))
        }
    }

    /// Computes the conjunction of the elements.
    pub fn fold_all(&self, lits: Bound<'_, PyAny>) -> PyResult<i32> {
        let mut res = Self::TRUE;
        for lit in lits.try_iter()? {
            let lit = lit?.extract::<i32>()?;
            res = self.bool_and(res, lit)?;
            if res == Self::FALSE {
                return Ok(Self::FALSE);
            }
        }
        Ok(res)
    }

    /// Computes the disjunction of the elements.
    pub fn fold_any(&self, lits: Bound<'_, PyAny>) -> PyResult<i32> {
        let mut res = Self::FALSE;
        for lit in lits.try_iter()? {
            let lit = lit?.extract::<i32>()?;
            res = self.bool_or(res, lit)?;
            if res == Self::TRUE {
                return Ok(Self::TRUE);
            }
        }
        Ok(res)
    }

    /// Computes the exactly one predicate over the given elements.
    pub fn fold_one(&self, lits: Bound<'_, PyAny>) -> PyResult<i32> {
        let mut min1 = Self::FALSE;
        let mut min2 = Self::FALSE;
        for lit in lits.try_iter()? {
            let lit = lit?.extract::<i32>()?;
            let tmp = self.bool_and(min1, lit)?;
            min2 = self.bool_or(min2, tmp)?;
            min1 = self.bool_or(min1, lit)?;
            if min2 == Self::TRUE {
                return Ok(Self::FALSE);
            }
        }
        self.bool_and(min1, Self::bool_not(min2))
    }

    /// Computes the at most one predicate over the given elements.
    pub fn fold_amo(&self, lits: Bound<'_, PyAny>) -> PyResult<i32> {
        let mut min1 = Self::FALSE;
        let mut min2 = Self::FALSE;
        for lit in lits.try_iter()? {
            let lit = lit?.extract::<i32>()?;
            let tmp = self.bool_and(min1, lit)?;
            min2 = self.bool_or(min2, tmp)?;
            min1 = self.bool_or(min1, lit)?;
            if min2 == Self::TRUE {
                return Ok(Self::FALSE);
            }
        }
        Ok(Self::bool_not(min2))
    }

    /// Returns true if the two sequences are equal. The two sequences
    /// must have the same length.
    pub fn comp_eq(&self, lits0: Bound<'_, PyAny>, lits1: Bound<'_, PyAny>) -> PyResult<i32> {
        let mut res = Self::TRUE;

        let mut lits0 = lits0.try_iter()?;
        let mut lits1 = lits1.try_iter()?;
        loop {
            let a = lits0.next();
            let b = lits1.next();

            if a.is_none() && b.is_none() {
                return Ok(res);
            } else if a.is_none() || b.is_none() {
                return Err(PyValueError::new_err("length mismatch"));
            }

            let a = a.unwrap()?.extract::<i32>()?;
            let b = b.unwrap()?.extract::<i32>()?;

            let c = self.bool_equ(a, b)?;
            res = self.bool_and(res, c)?;

            if res == Self::FALSE {
                return Ok(Self::FALSE);
            }
        }
    }

    /// Returns true if the two sequences are not equal. The two sequences
    /// must have the same length.
    pub fn comp_ne(&self, lits0: Bound<'_, PyAny>, lits1: Bound<'_, PyAny>) -> PyResult<i32> {
        self.comp_eq(lits0, lits1).map(Self::bool_not)
    }

    /// Returns true if the first sequence is smaller than or equal to the
    /// second one as a binary number when the least significant digit is
    /// the first one. So [TRUE, FALSE] = 1 is smaller than [FALSE, TRUE] = 2.
    /// The two sequences must have the same length.
    pub fn comp_le(&self, lits0: Bound<'_, PyAny>, lits1: Bound<'_, PyAny>) -> PyResult<i32> {
        let mut res = Self::TRUE;

        let mut lits0 = lits0.try_iter()?;
        let mut lits1 = lits1.try_iter()?;
        loop {
            let a = lits0.next();
            let b = lits1.next();

            if a.is_none() && b.is_none() {
                return Ok(res);
            } else if a.is_none() || b.is_none() {
                return Err(PyValueError::new_err("length mismatch"));
            }

            let a = a.unwrap()?.extract::<i32>()?;
            let b = b.unwrap()?.extract::<i32>()?;

            let c = self.bool_xor(a, b)?;
            res = self.bool_iff(c, b, res)?;
        }
    }

    /// Returns true if the first sequence is smaller than the second one
    /// as a binary number hen the least significant digit is the first one.
    /// The two sequences must have the same length.
    pub fn comp_lt(&self, lits0: Bound<'_, PyAny>, lits1: Bound<'_, PyAny>) -> PyResult<i32> {
        self.comp_le(lits1, lits0).map(Self::bool_not)
    }

    /// Returns true if the first sequence is greater than or equal to the
    /// second one as a binary number when the least significant digit is
    /// the first one. The two sequences must have the same length.
    pub fn comp_ge(&self, lits0: Bound<'_, PyAny>, lits1: Bound<'_, PyAny>) -> PyResult<i32> {
        self.comp_le(lits1, lits0)
    }

    /// Returns true if the first sequence is greater than the second one
    /// as a binary number hen the least significant digit is the first one.
    /// The two sequences must have the same length.
    pub fn comp_gt(&self, lits0: Bound<'_, PyAny>, lits1: Bound<'_, PyAny>) -> PyResult<i32> {
        self.comp_le(lits0, lits1).map(Self::bool_not)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn bool_op2(op: for<'a> fn(&'a PySolver, i32, i32) -> PyResult<i32>, table: [bool; 4]) {
        let lits = [1, -1, 2, -2, 3, -3];
        for a in lits {
            for b in lits {
                let solver = PySolver::new();
                assert_eq!(solver.add_variable(), 2);
                assert_eq!(solver.add_variable(), 3);
                let c = op(&solver, a, b).unwrap();
                solver.add_clause1(2);
                solver.add_clause1(3);
                assert_eq!(solver.solve(), Some(true));
                let a = solver.get_value(a).unwrap();
                let b = solver.get_value(b).unwrap();
                let c = solver.get_value(c).unwrap();
                assert_eq!(c, table[2 * (a as usize) + (b as usize)]);
            }
        }
    }

    fn bool_op3(op: for<'a> fn(&'a PySolver, i32, i32, i32) -> PyResult<i32>, table: [bool; 8]) {
        let lits = [1, -1, 2, -2, 3, -3, 4, -4];
        for a in lits {
            for b in lits {
                for c in lits {
                    let solver = PySolver::new();
                    assert_eq!(solver.add_variable(), 2);
                    assert_eq!(solver.add_variable(), 3);
                    assert_eq!(solver.add_variable(), 4);
                    let d = op(&solver, a, b, c).unwrap();
                    solver.add_clause1(2);
                    solver.add_clause1(3);
                    solver.add_clause1(4);
                    assert_eq!(solver.solve(), Some(true));
                    let a = solver.get_value(a).unwrap();
                    let b = solver.get_value(b).unwrap();
                    let c = solver.get_value(c).unwrap();
                    let d = solver.get_value(d).unwrap();
                    assert_eq!(d, table[4 * (a as usize) + 2 * (b as usize) + (c as usize)]);
                }
            }
        }
    }

    #[test]
    fn bool_ops() {
        bool_op2(PySolver::bool_or, [false, true, true, true]);
        bool_op2(PySolver::bool_and, [false, false, false, true]);
        bool_op2(PySolver::bool_imp, [true, true, false, true]);
        bool_op2(PySolver::bool_xor, [false, true, true, false]);
        bool_op2(PySolver::bool_equ, [true, false, false, true]);
        bool_op3(
            PySolver::bool_maj,
            [false, false, false, true, false, true, true, true],
        );
        bool_op3(
            PySolver::bool_iff,
            [false, true, false, true, false, false, true, true],
        );
    }
}
