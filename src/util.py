from math import sin, cos, tan, asin, acos, atan, atan2, pi, floor, sqrt, degrees

def circle_pivot_tangent_angle(r: float, x: float, y: float) -> float:
    """Calculate angle of a top tangent line from a circle at (0, 0) to a point (x, y).
       returns angle in degrees.
    """
    return degrees(acos(r / sqrt(x**2 + y**2)) + atan(y / x))
