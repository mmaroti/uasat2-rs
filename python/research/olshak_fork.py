from uasat import Solver, Operation


def test():
    solver = Solver()
    size = 4

    f1 = Operation(size, 4, solver)
    g1 = Operation(size, 4, solver)

    Operation.projection(size, 2, 0).comp_eq(
        f1.polymer([0, 0, 0, 1])).ensure_all()
    f1.polymer([0, 0, 1, 1]).comp_eq(g1.polymer([0, 0, 1, 1])).ensure_all()
    f1.polymer([0, 1, 0, 1]).comp_eq(g1.polymer([0, 1, 0, 1])).ensure_all()
    g1.polymer([0, 0, 0, 1]).comp_eq(
        Operation.projection(size, 2, 1)).ensure_all()

    print(solver.solve())
    print(f1.solution().decode())


if __name__ == '__main__':
    test()
