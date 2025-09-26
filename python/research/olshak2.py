import uasat
import numpy


SOLVER = uasat.Solver()


def create_term(solver: uasat.Solver) -> numpy.ndarray:
    term = numpy.empty((6, 6, 3), dtype=numpy.int32)
    for i in range(6):
        for j in range(6):
            for k in range(3):
                term[i, j, k] = solver.add_variable()
            solver.add_clause([term[i, j, 0], term[i, j, 1], term[i, j, 2]])
            solver.add_clause([-term[i, j, 0], -term[i, j, 1]])
            solver.add_clause([-term[i, j, 0], -term[i, j, 2]])
            solver.add_clause([-term[i, j, 1], -term[i, j, 2]])
    return term


def decode_term(solver: uasat.Solver, term: numpy.ndarray) -> numpy.ndarray:
    result = numpy.empty((6, 6), dtype=numpy.int32)
    for i in range(6):
        for j in range(6):
            for k in range(3):
                if solver.get_value(term[i, j, k]):
                    result[i, j] = k
    return result


def equality_yxxxyy_xyxyxy(solver: uasat.Solver, term1: numpy.ndarray, term2: numpy.ndarray) -> int:
    assert term1.shape == term2.shape and term1.shape[0] == 6
    term1 = term1.reshape((6, -1))
    term2 = term2.reshape((6, -1))

    return solver.fold_all([
        solver.comp_eq(term1[0], term1[4]),
        solver.comp_eq(term1[0], term1[5]),
        solver.comp_eq(term1[0], term2[1]),
        solver.comp_eq(term1[0], term2[3]),
        solver.comp_eq(term1[0], term2[5]),
        solver.comp_eq(term1[1], term1[2]),
        solver.comp_eq(term1[1], term1[3]),
        solver.comp_eq(term1[1], term2[0]),
        solver.comp_eq(term1[1], term2[2]),
        solver.comp_eq(term1[1], term2[4]),
    ])


def equality_yxxxyy_xxyyyx(solver: uasat.Solver, term1: numpy.ndarray, term2: numpy.ndarray) -> int:
    assert term1.shape == term2.shape and term1.shape[0] == 6
    term1 = term1.reshape((6, -1))
    term2 = term2.reshape((6, -1))

    return solver.fold_all([
        solver.comp_eq(term1[0], term1[4]),
        solver.comp_eq(term1[0], term1[5]),
        solver.comp_eq(term1[0], term2[2]),
        solver.comp_eq(term1[0], term2[3]),
        solver.comp_eq(term1[0], term2[4]),
        solver.comp_eq(term1[1], term1[2]),
        solver.comp_eq(term1[1], term1[3]),
        solver.comp_eq(term1[1], term2[0]),
        solver.comp_eq(term1[1], term2[1]),
        solver.comp_eq(term1[1], term2[5]),
    ])


def equality_xyxyxy_xxyyyx(solver: uasat.Solver, term1: numpy.ndarray, term2: numpy.ndarray) -> int:
    assert term1.shape == term2.shape and term1.shape[0] == 6
    term1 = term1.reshape((6, -1))
    term2 = term2.reshape((6, -1))

    return solver.fold_all([
        solver.comp_eq(term1[0], term1[2]),
        solver.comp_eq(term1[0], term1[4]),
        solver.comp_eq(term1[0], term2[0]),
        solver.comp_eq(term1[0], term2[1]),
        solver.comp_eq(term1[0], term2[5]),
        solver.comp_eq(term1[1], term1[3]),
        solver.comp_eq(term1[1], term1[5]),
        solver.comp_eq(term1[1], term2[2]),
        solver.comp_eq(term1[1], term2[3]),
        solver.comp_eq(term1[1], term2[4]),
    ])


def equality_olshak(solver: uasat.Solver, term1: numpy.ndarray, term2: numpy.ndarray) -> int:
    assert term1.shape == term2.shape and term1.shape[0] == 6

    return solver.fold_any([
        equality_yxxxyy_xyxyxy(solver, term1, term2),
        equality_yxxxyy_xxyyyx(solver, term1, term2),
        equality_xyxyxy_xxyyyx(solver, term1, term2),
        equality_yxxxyy_xyxyxy(solver, term2, term1),
        equality_yxxxyy_xxyyyx(solver, term2, term1),
        equality_xyxyxy_xxyyyx(solver, term2, term1),
    ])


def equality_reversed(solver: uasat.Solver, term1: numpy.ndarray, term2: numpy.ndarray) -> int:
    assert term1.shape == term2.shape and term1.shape[0] == 6

    return solver.fold_all([
        equality_olshak(solver, term1[i], term2[i]) for i in range(6)
    ])


def equality_idempotent(solver: uasat.Solver, term1: numpy.ndarray, term2: numpy.ndarray) -> int:
    assert term1.shape == term2.shape and term1.shape[:2] == (6, 6)

    term1 = term1.reshape((6, -1))
    term2 = term2.swapaxes(0, 1).reshape((6, -1))

    return solver.fold_all([
        solver.comp_eq(term1[0], term1[1]),
        solver.comp_eq(term1[0], term1[2]),
        solver.comp_eq(term1[0], term1[3]),
        solver.comp_eq(term1[0], term1[4]),
        solver.comp_eq(term1[0], term1[5]),
        solver.comp_eq(term1[0], term2[0]),
        solver.comp_eq(term1[0], term2[1]),
        solver.comp_eq(term1[0], term2[2]),
        solver.comp_eq(term1[0], term2[3]),
        solver.comp_eq(term1[0], term2[4]),
        solver.comp_eq(term1[0], term2[5]),
    ])


def equality(solver: uasat.Solver, term1: numpy.ndarray, term2: numpy.ndarray) -> int:
    assert term1.shape == term2.shape

    return solver.fold_any([
        solver.comp_eq(term1.flatten(), term2.flatten()),
        equality_olshak(solver, term1, term2),
        equality_reversed(solver, term1, term2),
        # equality_idempotent(solver, term1, term2),
    ])


def disjoint(solver: uasat.Solver, term1: numpy.ndarray, term2: numpy.ndarray) -> int:
    assert term1.shape == term2.shape
    term1 = term1.reshape((-1, 3))
    term2 = term2.reshape((-1, 3))

    return solver.fold_all([
        solver.comp_ne(term1[i], term2[i]) for i in range(term1.shape[0])
    ])


def add_edge(solver: uasat.Solver, term1: numpy.ndarray, term2: numpy.ndarray):
    term3 = create_term(solver)
    term4 = create_term(solver)
    solver.add_clause([equality(solver, term1, term3)])
    solver.add_clause([disjoint(solver, term3, term4)])
    solver.add_clause([equality(solver, term4, term2)])


def test():

    solver = uasat.Solver()
    terms = []
    for _ in range(7):
        terms.append(create_term(solver))

    for i in range(len(terms)):
        for j in range(i + 1, len(terms)):
            add_edge(solver, terms[i], terms[j])

    if solver.solve():
        for term in terms:
            print(decode_term(solver, term))


if __name__ == '__main__':
    test()
