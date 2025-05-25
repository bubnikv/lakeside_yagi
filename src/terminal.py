from build123d import *

from math import sin, cos, tan, asin, acos, atan, atan2, pi, floor, sqrt, degrees
from dataclasses import dataclass
from util import circle_pivot_tangent_angle, tangent_pos

from ocp_vscode import *

@dataclass
class ChocoTerminal:
    # Outer diameter of the brass terminal
    outer_diameter: float
    # Inner diameter of the brass terminal (hole)
    inner_diameter: float
    # Length of the brass terminal
    length: float
    # Height of the brass terminal
    height: float
    # Width of the flat (screw) side of the terminal
    flat_width: float
    # Bevel of the flat side of the terminal
    flat_bevel: float
    # Diameter of the screw shaft
    screw_diameter: float
    # Distance of the screw center from the center of the terminal
    screw_offset_from_center: float
    # Diameter of the center through hole
    center_hole_diameter: float

    @classmethod
    def make_terminal_10mm2(cls):
        return cls(outer_diameter=4.3, inner_diameter=3.4, length=12., height=5.8, 
                   flat_width=3.55, flat_bevel=0.2,
                   screw_diameter=3., screw_offset_from_center=4.,
                   center_hole_diameter=3.)

    # Create terminal outer contour in XY plane with the flat side pointing up,
    # terminal hole centered at (0, 0).
    def outer_profile(self, offset=0):
        r2 = self.outer_diameter / 2
        top = self.height - r2
        c = Curve() + [
            line := Line((0, top), (self.flat_width / 2, top)),
            arc := JernArc(start=(0, -r2), tangent=(1, 0), radius=r2, 
                    arc_size=90. + self.tangent_angle()),
            Line(line@1, arc@1)
        ]
        c = c + mirror(c, about=Plane.YZ)
        w = Wire(c).fillet_2d(radius=self.flat_bevel, vertices=c.vertices().group_by(Axis.Y)[-1])
        if offset > 0:
            w = w.offset_2d(offset)
        return make_face(w)

    def hole(self):
        return Circle(self.inner_diameter / 2)

    # Create terminal outer contour in XY plane with the flat side pointing up, drill the hole.
    def profile(self):
        return self.outer_profile() - self.hole()
    
    # Create terminal outer contour in XY plane with the flat side pointing up,
    # tilted so that the right side is vertical and the left side has a 45 degree taper to the top.
    def teardrop_profile(self, offset):
        profile = Rotation(0, 0, -self.tangent_angle()) * self.outer_profile(offset)
        edges = profile.edges()
        teardrop_pos = tangent_pos(edges, tangent_angle=45, max_dir=Vector(-1, 1))
        assert(teardrop_pos is not None)
        max_x = tangent_pos(edges, tangent_angle=90, max_dir=Vector(-1, 0))
        assert(max_x is not None)
        l = IntersectingLine(teardrop_pos, (-1., -1.), other = Line(max_x, (max_x.X, max_x.Y + 100)))
        profile = make_face(Wire.make_convex_hull(edges + ShapeList([l])))
#        show_object(profile, name="teardrop_pos")
#        exit(0)
        return profile

    # Length of the terminal is aligned with the Z axis, centered along Z.
    def body(self, drill_screw_holes: bool = True):
        b = Location([0, 0, - self.length / 2]) * \
            extrude(self.profile(), self.length)
        if drill_screw_holes:
            h = Cylinder(self.screw_diameter / 2, self.height, rotation = (-90., 0., 0.), 
                             align=(Align.CENTER, Align.CENTER, Align.MIN))
            b = (b - Location([0, 0, - self.screw_offset_from_center]) * h
                   - Location([0, 0, + self.screw_offset_from_center]) * h
                   - Cylinder(self.center_hole_diameter / 2, self.height*2, rotation = (-90., 0., 0.)))
        return b

    def tangent_angle(self):
        r2 = self.outer_diameter / 2
        top = self.height - r2
        return 90 - circle_pivot_tangent_angle(r2, top, self.flat_width / 2)
