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

use pyo3::exceptions::{PyAssertionError, PyIndexError, PyValueError};
use pyo3::prelude::*;

use super::PySolver;
use std::fmt::Write;

#[pyclass(frozen, sequence, name = "BitVec")]
pub struct PyBitVec {
    solver: Py<PySolver>,
    literals: Box<[i32]>,
}

#[pymethods]
impl PyBitVec {
    /// Creates a new bit vector with the associated solver and literals.
    #[new]
    pub fn new(solver: Py<PySolver>, literals: Vec<i32>) -> PyResult<Self> {
        if !solver.get().__bool__() {
            for &a in literals.iter() {
                if a != PySolver::TRUE && a != PySolver::FALSE {
                    return Err(PyValueError::new_err("invalid literal"));
                }
            }
        }

        let literals = literals.into_boxed_slice();
        Ok(PyBitVec { solver, literals })
    }

    /// Constructs a new bit vector of length length filled with fresh
    /// new literals from the solver.
    #[staticmethod]
    pub fn new_variable(solver: Py<PySolver>, count: u32) -> PyResult<Self> {
        if solver.get().__bool__() {
            let var = solver.get().add_variable(count);
            let literals = (var..(var + count as i32)).collect();
            Ok(PyBitVec { solver, literals })
        } else {
            Err(PyValueError::new_err("calculator instance"))
        }
    }

    /// Returns the associated solver for this bit vector. If the solver is
    /// `None``, then all literals are `TRUE`` or `FALSE``. Otherwise, the
    /// elements are literals of the solver and their value is not yet known.
    #[getter]
    pub fn get_solver(me: &Bound<'_, Self>) -> Py<PySolver> {
        me.get().solver.clone_ref(me.py())
    }

    /// Returns a copy of the list of literals.
    #[getter]
    pub fn get_literals(&self) -> Vec<i32> {
        self.literals.to_vec()
    }

    pub fn __repr__(&self) -> String {
        let mut res: String = "[".into();
        let mut iter = self.literals.iter();
        if let Some(a) = iter.next() {
            write!(&mut res, "{}", a).unwrap();
            for a in iter {
                write!(&mut res, ", {}", a).unwrap();
            }
        }
        write!(&mut res, "]").unwrap();
        res
    }

    pub fn __len__(&self) -> usize {
        self.literals.len()
    }

    pub fn __getitem__(&self, index: usize) -> PyResult<i32> {
        if index >= self.literals.len() {
            Err(PyIndexError::new_err("index out of range"))
        } else {
            Ok(self.literals[index])
        }
    }

    /// Returns a subslice of this vector.
    #[pyo3(signature = (start, stop, step=1))]
    pub fn slice(me: &Bound<'_, Self>, start: usize, stop: usize, step: usize) -> PyResult<Self> {
        let literals = &me.get().literals;
        if start <= stop && stop <= literals.len() && step >= 1 {
            let solver = me.get().solver.clone_ref(me.py());
            let literals: Vec<i32> = if step == 1 {
                literals[start..stop].to_vec()
            } else {
                (start..stop).step_by(step).map(|i| literals[i]).collect()
            };
            let literals = literals.into_boxed_slice();
            Ok(PyBitVec { solver, literals })
        } else {
            Err(PyIndexError::new_err("invalid slice parameters"))
        }
    }

    /// When this bit vector is backed by a solver and there exists a solution,
    /// then this method returns the value of these literals in the solution.
    pub fn get_value(me: &Bound<'_, Self>) -> PyResult<Self> {
        if !me.get().solver.get().__bool__() {
            Err(PyValueError::new_err("calculator instance"))
        } else if me.get().solver.get().status() != Some(true) {
            Err(PyValueError::new_err("instance not solved"))
        } else {
            let mut literals = Vec::with_capacity(me.get().literals.len());
            for lit in me.get().literals.iter() {
                let val = me.get().solver.get().get_value(*lit) == Some(true);
                literals.push(PySolver::bool_lift(val));
            }
            let solver = me.py().get_type::<PySolver>().getattr("CALC")?.extract()?;
            let literals = literals.into_boxed_slice();
            Ok(PyBitVec { solver, literals })
        }
    }

    pub fn __invert__(me: &Bound<'_, Self>) -> Self {
        let solver = me.get().solver.clone_ref(me.py());
        let literals = me
            .get()
            .literals
            .iter()
            .map(|&lit| PySolver::bool_not(lit))
            .collect();
        PyBitVec { solver, literals }
    }

    pub fn __and__(me: &Bound<'_, Self>, other: &Self) -> PyResult<Self> {
        let solver = PySolver::join(me.py(), &me.get().solver, &other.solver)?;
        if me.get().literals.len() != other.literals.len() {
            return Err(PyValueError::new_err("length mismatch"));
        }

        let mut literals = Vec::with_capacity(me.get().literals.len());
        for (&a, &b) in me.get().literals.iter().zip(other.literals.iter()) {
            literals.push(solver.get().bool_and(a, b)?);
        }

        let literals = literals.into_boxed_slice();
        Ok(PyBitVec { solver, literals })
    }

    pub fn __or__(me: &Bound<'_, Self>, other: &Self) -> PyResult<Self> {
        let solver = PySolver::join(me.py(), &me.get().solver, &other.solver)?;
        if me.get().literals.len() != other.literals.len() {
            return Err(PyValueError::new_err("length mismatch"));
        }

        let mut literals = Vec::with_capacity(me.get().literals.len());
        for (&a, &b) in me.get().literals.iter().zip(other.literals.iter()) {
            literals.push(solver.get().bool_or(a, b)?);
        }

        let literals = literals.into_boxed_slice();
        Ok(PyBitVec { solver, literals })
    }

    pub fn __xor__(me: &Bound<'_, Self>, other: &Self) -> PyResult<Self> {
        let solver = PySolver::join(me.py(), &me.get().solver, &other.solver)?;
        if me.get().literals.len() != other.literals.len() {
            return Err(PyValueError::new_err("length mismatch"));
        }

        let mut literals = Vec::with_capacity(me.get().literals.len());
        for (&a, &b) in me.get().literals.iter().zip(other.literals.iter()) {
            literals.push(solver.get().bool_xor(a, b)?);
        }

        let literals = literals.into_boxed_slice();
        Ok(PyBitVec { solver, literals })
    }

    pub fn comp_eq(me: &Bound<'_, Self>, other: &Self) -> PyResult<Self> {
        let solver = PySolver::join(me.py(), &me.get().solver, &other.solver)?;
        if me.get().literals.len() != other.literals.len() {
            return Err(PyValueError::new_err("length mismatch"));
        }

        let mut res = PySolver::TRUE;
        for (&a, &b) in me.get().literals.iter().zip(other.literals.iter()) {
            let c = solver.get().bool_equ(a, b)?;
            res = solver.get().bool_and(res, c)?;
        }

        let literals = vec![res].into_boxed_slice();
        Ok(PyBitVec { solver, literals })
    }

    pub fn comp_ne(me: &Bound<'_, Self>, other: &Self) -> PyResult<Self> {
        let mut res = Self::comp_eq(me, other)?;
        let lit = PySolver::bool_not(res.literals[0]);
        res.literals = vec![lit].into_boxed_slice();
        Ok(res)
    }

    pub fn comp_le(me: &Bound<'_, Self>, other: &Self) -> PyResult<Self> {
        let solver = PySolver::join(me.py(), &me.get().solver, &other.solver)?;
        if me.get().literals.len() != other.literals.len() {
            return Err(PyValueError::new_err("length mismatch"));
        }

        let mut res = PySolver::TRUE;
        for (&a, &b) in me.get().literals.iter().zip(other.literals.iter()) {
            let c = solver.get().bool_xor(a, b)?;
            res = solver.get().bool_iff(c, b, res)?;
        }

        let literals = vec![res].into_boxed_slice();
        Ok(PyBitVec { solver, literals })
    }

    pub fn comp_gt(me: &Bound<'_, Self>, other: &Self) -> PyResult<Self> {
        let mut res = Self::comp_le(me, other)?;
        let lit = PySolver::bool_not(res.literals[0]);
        res.literals = vec![lit].into_boxed_slice();
        Ok(res)
    }

    pub fn comp_ge(me: &Bound<'_, Self>, other: &Self) -> PyResult<Self> {
        let solver = PySolver::join(me.py(), &me.get().solver, &other.solver)?;
        if me.get().literals.len() != other.literals.len() {
            return Err(PyValueError::new_err("length mismatch"));
        }

        let mut res = PySolver::TRUE;
        for (&a, &b) in me.get().literals.iter().zip(other.literals.iter()) {
            let c = solver.get().bool_xor(a, b)?;
            res = solver.get().bool_iff(c, a, res)?;
        }

        let literals = vec![res].into_boxed_slice();
        Ok(PyBitVec { solver, literals })
    }

    pub fn comp_lt(me: &Bound<'_, Self>, other: &Self) -> PyResult<Self> {
        let mut res = Self::comp_ge(me, other)?;
        let lit = PySolver::bool_not(res.literals[0]);
        res.literals = vec![lit].into_boxed_slice();
        Ok(res)
    }

    pub fn fold_all(me: &Bound<'_, Self>) -> PyResult<Self> {
        let solver = me.get().solver.clone_ref(me.py());
        let mut res = PySolver::TRUE;
        for lit in me.get().literals.iter() {
            res = solver.get().bool_and(res, *lit)?;
            if res == PySolver::FALSE {
                break;
            }
        }
        let literals = vec![res].into_boxed_slice();
        Ok(PyBitVec { solver, literals })
    }

    pub fn fold_any(me: &Bound<'_, Self>) -> PyResult<Self> {
        let solver = me.get().solver.clone_ref(me.py());
        let mut res = PySolver::FALSE;
        for lit in me.get().literals.iter() {
            res = solver.get().bool_or(res, *lit)?;
            if res == PySolver::TRUE {
                break;
            }
        }
        let literals = vec![res].into_boxed_slice();
        Ok(PyBitVec { solver, literals })
    }

    pub fn fold_one(me: &Bound<'_, Self>) -> PyResult<Self> {
        let solver = me.get().solver.clone_ref(me.py());
        let mut min1 = PySolver::FALSE;
        let mut min2 = PySolver::FALSE;
        for lit in me.get().literals.iter() {
            let tmp = solver.get().bool_and(min1, *lit)?;
            min2 = solver.get().bool_or(min2, tmp)?;
            min1 = solver.get().bool_or(min1, *lit)?;
            if min2 == PySolver::TRUE {
                break;
            }
        }
        let res = solver.get().bool_and(min1, PySolver::bool_not(min2))?;
        let literals = vec![res].into_boxed_slice();
        Ok(PyBitVec { solver, literals })
    }

    pub fn fold_amo(me: &Bound<'_, Self>) -> PyResult<Self> {
        let solver = me.get().solver.clone_ref(me.py());
        let mut min1 = PySolver::FALSE;
        let mut min2 = PySolver::FALSE;
        for lit in me.get().literals.iter() {
            let tmp = solver.get().bool_and(min1, *lit)?;
            min2 = solver.get().bool_or(min2, tmp)?;
            min1 = solver.get().bool_or(min1, *lit)?;
            if min2 == PySolver::TRUE {
                break;
            }
        }
        let res = PySolver::bool_not(min2);
        let literals = vec![res].into_boxed_slice();
        Ok(PyBitVec { solver, literals })
    }

    pub fn ensure_all(me: &Bound<'_, Self>) -> PyResult<()> {
        if me.get().solver.get().__bool__() {
            for lit in me.get().literals.iter() {
                me.get().solver.get().add_clause1(*lit);
            }
        } else {
            for lit in me.get().literals.iter() {
                if *lit != PySolver::TRUE {
                    return Err(PyAssertionError::new_err("not all true"));
                }
            }
        }
        Ok(())
    }

    pub fn ensure_any(me: &Bound<'_, Self>) -> PyResult<()> {
        if me.get().solver.get().__bool__() {
            me.get().solver.get().add_clause(me.get().literals.to_vec());
            Ok(())
        } else {
            for lit in me.get().literals.iter() {
                if *lit != PySolver::TRUE {
                    return Ok(());
                }
            }
            Err(PyAssertionError::new_err("none are true"))
        }
    }

    pub fn ensure_one(me: &Bound<'_, Self>) -> PyResult<()> {
        let solver = me.get().solver.get();
        let mut min1 = PySolver::FALSE;
        let mut min2 = PySolver::FALSE;
        for lit in me.get().literals.iter() {
            let tmp = solver.bool_and(min1, *lit)?;
            min2 = solver.bool_or(min2, tmp)?;
            min1 = solver.bool_or(min1, *lit)?;
            if min2 == PySolver::TRUE {
                break;
            }
        }
        let res = solver.bool_and(min1, PySolver::bool_not(min2))?;
        solver.add_clause1(res);
        Ok(())
    }
}
