from build123d import *

from math import sin, cos, tan, asin, acos, atan, atan2, pi, floor, sqrt, degrees

from util import circle_pivot_tangent_angle

# Profile of the element holder perpendicular to the axis of the boom.
# Two of such profiles will be generated, at the front and rear plane
# of the element holder.
# The profile will be a rectangle centered at (0, housing_center)
# with width (housing_width, 2 * housing_r)
# then tangentially extended to a circle centered at (0, 0)
# with radius base_r.
def element_housing_profile_xy(
        housing_width,  # Width of the housing along the element axis
        housing_r,      # Radius of the element
        housing_center, # Center of the element
        base_r):        # Radius touching the conical boom surface
    hx = housing_width / 2
    hy_top = housing_center + housing_r
    hy_bottom = housing_center - housing_r
    d_hbottom_center = sqrt(hx**2 + hy_bottom**2)
    alpha = acos(base_r / d_hbottom_center) - atan2(hy_bottom, hx)
    dent_depth = housing_r * 1.5
    c = Curve() + [
        arc := CenterArc(center=(0,0,0), radius=base_r - 0.5, start_angle=90, arc_size=-90-degrees(alpha)),
        Polyline([
            arc@1,
            (base_r * cos(alpha), - base_r * sin(alpha)),
            (hx, hy_bottom),
            (hx, hy_top),
            (dent_depth, hy_top),
            (0, hy_top - dent_depth)
        ]),
    ]
    return make_face(c + mirror(c, about=Plane.YZ))

# Profile perpendicular to the element, trimming the rectangular housing body
# with a circular / drop shape
def element_housing_profile_yz(
        housing_r: float, housing_center: float, base_r: float):
    c = Curve() + [
        arc := ThreePointArc((housing_r, housing_center), 
                (0, housing_center + housing_r),
                (-housing_r / sqrt(2), housing_center + housing_r / sqrt(2))),
        Polyline([
            arc@1,
            (-housing_r, housing_center + housing_r * sin(45 * pi / 360)),
            (-housing_r, -base_r),
            (housing_r, -base_r),
            (housing_r, housing_center)])
    ]
    return Plane.ZY * make_face(c)

def build_housing(
        element_housing_width, element_housing_r, element_height, 
        base_r1, base_r2):
    rmid = (base_r1 + base_r2)/2
    hmid = 0
    s1 = Pos(0, 0, hmid-element_housing_r) * element_housing_profile_xy(
        element_housing_width, element_housing_r, 
        element_height,
        base_r1)
    s2 = Pos(0, 0, hmid+element_housing_r) * element_housing_profile_xy(
        element_housing_width, element_housing_r, 
        element_height,
        base_r2)
    l = loft([s1, s2])
    # Round the housing around the length of the element.
    l2 = extrude(to_extrude = 
            Pos(-element_housing_width/2, 0) * 
                element_housing_profile_yz(
                    element_housing_r, element_height, rmid), 
            amount = -element_housing_width)
    res = Plane.ZY * (l & l2)
#        if not res.Solids():
#            show_object(cq.Workplane(l))
#            show_object(cq.Workplane(l2))
#            print("build failed!")
    return res
