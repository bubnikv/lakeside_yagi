from math import sin, cos, tan, asin, acos, atan, atan2, pi, floor, sqrt, degrees

from build123d import *

def circle_pivot_tangent_angle(r: float, x: float, y: float) -> float:
    """Calculate angle of a top tangent line from a circle at (0, 0) to a point (x, y).
       returns angle in degrees.
    """
    return degrees(acos(r / sqrt(x**2 + y**2)) + atan(y / x))

def tangent_pos(edges, tangent_angle, max_dir: Vector):
   tangent_pos = None
   max_xy = -1e10
   for edge in edges:
      params = edge.find_tangent(angle=tangent_angle)
      assert(len(params) <= 1)
      if len(params) == 1:
            pos = edge @ params[0]
            xy = pos.dot(max_dir)
            if xy > max_xy:
               max_xy = xy
               tangent_pos = pos
   return tangent_pos
