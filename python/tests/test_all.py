import pytest
import uasat


def test_cadical_signature():
    # solver = uasat.Solver.with_config("unsat")
    solver = uasat.Solver()
    assert solver.signature() == "cadical-1.3.0"
