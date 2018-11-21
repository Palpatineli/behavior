import numpy as np
from ..geometry import solve_line, solve_rectangle, arm_id


def test_solve_line():
    a_mat, b = solve_line(np.array([0.0, 0.0]), np.array([1.0, 1.0]))
    print(a_mat, b)
    assert a_mat.dot(np.array([0.5, 0.6])) + b > 0
    assert a_mat.dot(np.array([0.8, 0.7])) + b < 0
    assert a_mat.dot(np.array([1.1, 1.1])) + b == 0
    a_mat, b = solve_line(np.array([-1.0, -1.0]), np.array([-2.0, -1.5]))
    assert a_mat.dot(np.array([1.0, 0.5])) + b < 0
    assert a_mat.dot(np.array([-2.5, -2])) + b > 0
    assert a_mat.dot(np.array([-3, -2])) + b == 0


def test_solve_rectangle():
    points = np.array([[2, 2], [2.5, 1], [1, 0.5], [1.25, 1.75]])
    a_mat, b = solve_rectangle(points)


def test_arm_id():
            s
