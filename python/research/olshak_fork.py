from uasat import *


def test():
    solver = Solver()
    size = 4

    f1 = Operation(size, 4, solver)
    g1 = Operation(size, 4, solver)

    (Operation.projection(size, 2, 0) == f1.polymer([0, 0, 0, 1])).ensure_all()
    (f1.polymer([0, 0, 1, 1]) == g1.polymer([0, 0, 1, 1])).ensure_all()
    (f1.polymer([0, 1, 0, 1]) == g1.polymer([0, 1, 0, 1])).ensure_all()
    (g1.polymer([0, 0, 0, 1]) == Operation.projection(size, 2, 1)).ensure_all()


if __name__ == '__main__':
    test()
