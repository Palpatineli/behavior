import numpy as np


def solve_line(x0, x1):
    a = (x1 - x0).T
    a[0], a[1] = -a[1], a[0]
    return a, a @ x0


def solve_rectangle(points):
    """calculates the lines of four edges of a box from its points
    for point x, Ax - b > 0 gives location relative to the box. [T, F, F, F]^T means
    outside the first edge. [F, F, F, F]^T means inside the box
    """
    point_no = 4  # it's a rect
    a = np.empty((4, 2))
    b = np.empty((4,))
    points = np.array(points)
    for idx1 in range(point_no):
        idx2 = 0 if idx1 + 1 == point_no else idx1 + 1
        ref_idx = 0 if idx2 + 1 == point_no else idx2 + 1
        temp_a, temp_b = solve_line(points[idx1, :], points[idx2, :])
        if temp_a @ points[ref_idx, :] - temp_b > 0:
            a[idx1, :] = -temp_a
            b[idx1] = -temp_b
        else:
            a[idx1, :] = temp_a
            b[idx1] = temp_b
    return a, b


def arm_id(trace, a, b):
    is_in_arm = np.greater((a @ trace.T).T - b, 0)
    double_cross = next(iter(np.nonzero(np.greater(is_in_arm.sum(1), 1))))
    for idx in double_cross:
        if is_in_arm[idx - 1, :].any():
            is_in_arm[idx, :] = is_in_arm[idx - 1, :]
        else:
            raise ValueError('mouse running through corner from center platform!', idx)
    location = is_in_arm @ np.arange(1, 5)
    return location


def main():
    points = np.array([[0, 2], [2, 2], [2, 0], [0, 0]])
    return solve_rectangle(points)


if __name__ == '__main__':
    main()
