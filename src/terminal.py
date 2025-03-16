from build123d import *

from math import sin, cos, tan, asin, acos, atan, atan2, pi, floor, sqrt, degrees
from dataclasses import dataclass

from util import circle_pivot_tangent_angle

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

    # Create terminal outer contour in XY plane with the flat side pointing up.
    def outer_profile(self):
        r2 = self.outer_diameter / 2
        top = self.height - r2
        c = Curve() + [
            line := Line((0, top), (self.flat_width / 2, top)),
            arc := JernArc(start=(0, -r2), tangent=(1, 0), radius=r2, 
                    arc_size=180. - circle_pivot_tangent_angle(r2, top, self.flat_width / 2)),
            Line(line@1, arc@1)
        ]
        c = c + mirror(c, about=Plane.YZ)
        w = Wire(c).fillet_2d(radius=self.flat_bevel, vertices=c.vertices().group_by(Axis.Y)[-1])
        return make_face(w)

    def hole(self):
        return Circle(self.inner_diameter / 2)

    # Create terminal outer contour in XY plane with the flat side pointing up, drill the hole.
    def profile(self):
        return self.outer_profile() - self.hole()

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
