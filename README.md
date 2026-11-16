# UASAT: a universal algebra calculator based on a SAT solver

This is a Python library to aid research in universal algebra by generating
simple examples and counterexamples. For example, you can work with finitary
relations and operations on a finite set and express various constraints
between them. The underlying SAT solver is CaDiCaL 1.9.5, which is an
incremental SAT solver. It can be used to enumerate and count examples.
All relations and operations are represented by multidimensional matrices
with literal entries. When operations are performed on these objects, new
literals and clauses are added automatically to the solver. The usual
operations on relations and operations are supported, as shown in the
following two small examples.


```python
from uasat import Solver, Relation, Operation

def test_number_of_posets():
    """
    Counting the number of labeled 3-element posets.
    """

    solver = Solver()

    rel = Relation.variable(3, 2, solver)
    rel.reflexive().ensure_true()
    rel.antisymm().ensure_true()
    rel.transitive().ensure_true()

    count = 0
    while solver.solve():
        val = rel.solution()
        print(val.decode())
        count += 1
        (rel ^ val).ensure_any()
    assert count == 19


def test_polymorphisms_of_c3():
    """
    Find all binary polymorphisms of the reflexive oriented 3-cycle.
    """

    rel = Relation.tuples(3, 2, [
        (0, 0), (0, 1), (1, 1), (1, 2), (2, 2), (2, 0),
    ])

    solver = Solver()

    op = Operation.variable(rel.size, 2, solver)
    op.preserves(rel).ensure_true()

    count = 0
    while solver.solve():
        val = op.solution()
        print(val.decode())
        count += 1
        (op.table ^ val.table).ensure_any()
    assert count == 9
```

## Installation

Use `pip install uasat` to install the package from PyPI, preferably in a virtual
environment. You do not need to download the source from GitHub or build the
library yourself, but you can certainly do that. The library's source code and
some research scripts are available in the
[GitHub repository](https://github.com/mmaroti/uasat2-rs).
You can check that the library is installed correctly with the following command:
`python3 -c "import uasat; help(uasat.Solver)"`.

## Development

Some of the library's functionality is implemented in Rust. The CaDiCaL
SAT solver is implemented in C++ and compiled as part of the Rust build. The Python
interfaces to the Rust objects are built using `maturin`. Set up a virtual
environment, then use `maturin develop` to compile the library on your machine.
Run `python3 -m pytest` to run the validation tests. Build
with `maturin build` and `maturin build --sdist`, and upload with
`twine upload -r testpypi target/wheels/*`.

With `uv`, run `uv run --reinstall-package uasat --extra tests python -m pytest`
from the repository root to install the test dependencies and run the tests
using the project environment.
