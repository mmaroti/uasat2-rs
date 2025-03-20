use pyo3::prelude::*;

/// Formats the sum of two numbers as string.
#[pyfunction]
fn sum_as_string(_a: usize, _b: usize) -> PyResult<String> {
    let solver: cadical::Solver = cadical::Solver::with_config("unsat").unwrap();
    Ok(solver.signature().into())
}

/// A Python module implemented in Rust.
#[pymodule]
fn uasat(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(sum_as_string, m)?)?;
    Ok(())
}
