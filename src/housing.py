from dataclasses import dataclass
from typing import List
from build123d import *
from ocp_vscode import *

from math import sin, cos, tan, asin, acos, atan, atan2, pi, floor, sqrt, degrees, radians

from util import circle_pivot_tangent_angle

import terminal

def make_c_sleeve(
    r1:         float,  # Radius at Z=0
    r2:         float,  # Radius at Z=length 
    length:     float,  # Length in Z from 0 up 
    thickness:  float,  # Thickness of the sleeve 
    angle:      float): # Full angle of the sleeve in degrees, angle > 180 to hold to the boom
    """Make a C-shaped sleeve in XY plane with r1 at Z=0 and r2 at Z=length."""
    def make_c_slot(r1: float, r2: float, angle: float) -> Face:
        arc = [CenterArc(center=(0,0,0), radius=r, start_angle=90, arc_size=angle/2) for r in (r1, r2)]
        c = Curve() + arc + Line(arc[0] @ 1, arc[1] @ 1)
        c = c + mirror(c, about=Plane.YZ)
        return Face(outer_wire=Wire(c).fillet_2d(radius=0.499*abs(r2-r1), vertices=c.vertices()))
    assert angle > 180
    s1 = make_c_slot(r1, r1+thickness, angle)
    s2 = make_c_slot(r2, r2+thickness, angle)
    return loft([s1, Location([0, 0, length]) * s2])

def make_c_sleeve_slice(
    base_radius:        float,  # Base radius of the C-sleeve at the center of an antenna element
    thickness:          float,  # Thickness of the C-sleeve
    length_pos:         float,  # Length of C-sleeve above the XY plane
    length_neg:         float,  # Length of C-sleeve below the XY plane
    sleeve_angle:       float,  # Angle of the C-sleeve in degrees, larger than 180 to hold to the boom
    boom_taper_angle:   float): # Angle of the boom taper in degrees
    """Make a tapered C-shaped sleeve from -length_neg to length_pos"""
    assert base_radius > 0
    assert thickness > 0
    assert length_pos > 0
    assert length_neg > 0
    assert sleeve_angle > 180
    taper = tan(radians(boom_taper_angle))
    return Location((0, 0, -length_neg)) * make_c_sleeve(
        r1 = base_radius - length_neg * taper,
        r2 = base_radius + length_pos * taper,
        length = length_pos + length_neg,
        thickness = thickness,
        angle = sleeve_angle)

# Profile of a rectangular element holder perpendicular to the axis of the boom 
# merging into a C-clamp profile tangentially.
# Two of such profiles will be generated for each element holder, 
# one at the front, the other at the rear plane of an element holder.
# The rectangular profile is centered at (0, housing_center)
# with width (housing_width, 2 * housing_r),
# then tangentially extended to a circle centered at (0, 0)
# with radius base_r.
def element_housing_profile_xy(
        housing_width,  # Width of the housing along the element axis
        housing_top,    # Top of the housing profile rectangle
        housing_bottom, # Top of the housing profile rectangle
        v_dent_depth,   # Half height of the element housing rectangle
        base_r):        # Radius touching the outer surface of a C-clamp
    w = housing_width / 2
    alpha = 90 - circle_pivot_tangent_angle(r=base_r, x=w, y=housing_bottom)
    # Thickness of the housing profile just to sink a bit into the outer surface of a C-clamp.
    eps_thickness = 0.1
#    assert housing_top - v_dent_depth > base_r
    c = Curve() + [
        arc := CenterArc(center=(0,0,0), radius=base_r - eps_thickness, start_angle=90, arc_size=-90-alpha),
        Polyline([
            arc@1,
            (base_r * cos(radians(alpha)), - base_r * sin(radians(alpha))),
            (w, housing_bottom),
            (w, housing_top),
            (v_dent_depth, housing_top),
            (0, housing_top - v_dent_depth)
        ]),
    ]
    f = make_face(c + mirror(c, about=Plane.YZ))
#    show_object(f, 'housing_profile')
#    exit(0)
    return f

#    dent_depth = min(
#        housing_top - base_r, # Should not dent into the top surface of the C-clamp
#        1.5 * housing_r) # Open the holder more than half of an elemen diameter

# Profile perpendicular to the element, trimming the rectangular housing body
# with a circular / drop shape for printability (45 taper at print bed, rounding on the other side)
def element_housing_profile_yz(
        housing_depth:  float,  # Housing depth (along the boom axis)
        housing_top:    float,  # Height of the housing above the boom axis
        base_r:         float,  # Outer radius of the C-clamp
        bevel_r:        float,  # Bevel of the housing profile in the YZ plane, teardrop bevel at the print bed side
        housing_profile=None):  # Extra profile, used for choco terminal
    w = housing_depth / 2
    cntr = housing_top - w
    c = Curve() + [
        arc := ThreePointArc((w, cntr), 
                (0, cntr + w),
                (-w / sqrt(2), cntr + w / sqrt(2))),
        Polyline([
            arc@1,
            (-w, cntr + w * sin(45 * pi / 360)),
            (-w, -base_r),
            (w, -base_r),
            (w, cntr)])
    ]
    f = make_face(c)
#    show_object(f, 'housing_profile0')
    if housing_profile:
        f = f + housing_profile
#    show_object(f, 'housing_profile')
#    exit(0)
    return Plane.ZY * f

# Housing for an antenna element in XY plane, centered at the center of the boom and along Z thickness,
# tapering into an outer surface of a C-clamp, slightly intersecting it for booleanability.
def element_housing(
        housing_width,  # Width of the housing along the element axis
        housing_depth,
        housing_top,    # Top of the housing profile rectangle
        housing_bottom, # Top of the housing profile rectangle
        v_dent_depth,   # Half height of the element housing rectangle
        base_r_start,
        base_r_end,      # Radius touching the outer surface of a C-clamp
        housing_profile=None):  # Extra profile, used for choco terminal
    ext = housing_top
    if housing_profile:
        ext = max(ext, housing_profile.bounding_box().max.Y)
    l = loft([
        Pos(0, 0, zdir * housing_depth/2) * element_housing_profile_xy(
            housing_width=housing_width, housing_top=ext, housing_bottom=housing_bottom, 
            v_dent_depth=v_dent_depth, base_r=base_r)
        for zdir, base_r in [(-1, base_r_start), (1, base_r_end)]
    ])
#    show_object(l, 'loft')
    # Round the housing around the length of the element.
    l2 = extrude(to_extrude = 
            Pos(-housing_width/2, 0) * 
                element_housing_profile_yz(
                    housing_depth=housing_depth,
                    housing_top=housing_top,
                    base_r=(base_r_start + base_r_end)/2,
                    bevel_r=housing_depth/2,
                    housing_profile=housing_profile),
            amount = -housing_width)
#    show_object(l2, 'extrude')
    return l & l2

@dataclass
class Label:
    labels: List[str]
    font:  str   = "Arial Black"
    size:  float = 6
    depth: float = .28

def gen_labels(label: Label, housing_width: float, housing_top: float):
    bodies = [
        Pos((-1 if i == 0 else 1) * housing_width * 0.3,
#            label.size/2 + 4,
            housing_top * 0.65,
            -label.depth) * extrude(
            Text(label.labels[i], font_size=label.size, 
                 align=(Align.CENTER, Align.CENTER)),
            amount=label.depth)
        for i, l in enumerate(label.labels)]
    return bodies

def element_holder_body(
    sleeve_base_radius:         float, # Radius of the C-sleeve at the center of an antenna element
    sleeve_thickness:           float, # Thickness of the C-sleeve
    sleeve_length:              float,
    sleeve_angle:               float,
    boom_taper_angle:           float,
    housing_width:      float,  # Width of the housing along the element axis
    housing_depth:      float,
    housing_top:        float,  # Top of the housing profile rectangle
    housing_bottom:     float,  # Top of the housing profile rectangle
    housing_profile:    Face,   # Extra profile, used for choco terminal
    v_dent_depth:       float,
    label:              Label): # Half height of the element housing rectangle

    sleeve = make_c_sleeve_slice(
        base_radius=sleeve_base_radius,
        thickness=sleeve_thickness,
        length_pos=sleeve_length - housing_depth/2,
        length_neg=housing_depth/2,
        sleeve_angle=sleeve_angle,
        boom_taper_angle=boom_taper_angle)
    
    taper = (housing_depth/2) * tan(radians(boom_taper_angle))
    housing = element_housing(
        housing_width=housing_width,
        housing_depth=housing_depth,
        housing_top=housing_top,
        housing_bottom=housing_bottom,
        v_dent_depth=v_dent_depth,
        base_r_start=sleeve_base_radius + sleeve_thickness - taper,
        base_r_end=sleeve_base_radius + sleeve_thickness + taper,
        housing_profile=housing_profile)
#    show_object(housing, 'housing')
    
    body = sleeve + housing

    if label:
        for l in gen_labels(label, housing_width, housing_top):
            body -= Pos(0, 0, - housing_depth/2) * Rotation(0., 180., 0.) * l
    return body

def element_holder_for_wire(
    sleeve_base_radius:     float,
    sleeve_thickness:       float,
    sleeve_length:          float,
    sleeve_angle:           float,
    boom_taper_angle:       float,
    housing_width:          float,
    element_dmr:            float,
    element_above_boom_axis: float,
    element_wall:           float,
    element_wall_top_extra: float,
    label:                  Label):

    h = element_dmr + 2*element_wall
#    assert element_above_boom_axis - h/2 > sleeve_base_radius
    body = element_holder_body(
        sleeve_base_radius=sleeve_base_radius,
        sleeve_thickness=sleeve_thickness,
        sleeve_length=sleeve_length,
        sleeve_angle=sleeve_angle,
        boom_taper_angle=boom_taper_angle,
        housing_width=housing_width,
        housing_depth=h,
        housing_top=element_above_boom_axis + h / 2 + element_wall_top_extra,
        housing_bottom=sleeve_base_radius,
        housing_profile=None, # extra profile, not used here
        v_dent_depth=3 * h / 4, # + element_wall_top_extra, #3 * h / 8 + element_wall_top_extra,
        label=label)
#    show_object(body, 'body')
    wire = Pos(0, element_above_boom_axis) * Cylinder(element_dmr/2, housing_width, rotation=(0., -90., 0.))
    return body - wire

def element_holder_for_choco_terminal(
    sleeve_base_radius:     float,
    sleeve_thickness:       float,
    sleeve_length:          float,
    sleeve_angle:           float,
    boom_taper_angle:       float,
    terminal:               terminal.ChocoTerminal,
    terminal_spacing:       float, # Spacing between left / right terminals
    extra_width:            float, # Extra width of the housing for the terminal, applied to both sides
    element_above_boom_axis: float,
    element_wall:           float,
    element_wall_top_extra: float,
    print_gap:              float, # 3D printing technology constraint: Gap between the terminal and the element
    label:                  Label):

    terminal_top = terminal.height - terminal.outer_diameter / 2
    housing_width = terminal_spacing + 2 * (terminal.length + extra_width)
    body = element_holder_body(
        sleeve_base_radius=sleeve_base_radius,
        sleeve_thickness=sleeve_thickness,
        sleeve_length=sleeve_length,
        sleeve_angle=sleeve_angle,
        boom_taper_angle=boom_taper_angle,
        housing_width=housing_width,
        housing_depth=terminal.outer_diameter + 2 * print_gap + 2 * element_wall,
        housing_top=element_above_boom_axis + terminal_top + element_wall + element_wall_top_extra,
        housing_bottom=sleeve_base_radius,
        housing_profile=Pos(0, element_above_boom_axis + element_wall_top_extra) * \
            terminal.teardrop_profile(print_gap + element_wall),
        v_dent_depth=terminal_top, # + element_wall_top_extra, #3 * h / 8 + element_wall_top_extra,
        label=label)
#    show_object(body, 'body')
#    wire = Pos(0, element_above_boom_axis) * Cylinder(element_dmr/2, housing_width, rotation=(0., -90., 0.))
#    return body - wire
    through = extrude(to_extrude = Plane.ZY * terminal.teardrop_profile_inner(print_gap), 
                      amount = housing_width)
    screw = Rotation(0, 90, 0) * Rotation(0, 0, terminal.tangent_angle()) * \
            Cylinder(terminal.screw_diameter/2, terminal.height * 2, rotation=(-90., 0., 0.), 
                     align = (Align.CENTER, Align.CENTER, Align.MIN))
    screw_offset_inner = (terminal_spacing + terminal.length) / 2 - terminal.screw_offset_from_center
    screw_offset_outer = (terminal_spacing + terminal.length) / 2 + terminal.screw_offset_from_center
    throughs = [Pos(housing_width/2) * through, 
                Pos(screw_offset_inner) * screw, 
                Pos(- screw_offset_inner) * screw,
                Pos(screw_offset_outer) * screw, 
                Pos(- screw_offset_outer) * screw]
    
    throughs = Pos(0., element_above_boom_axis, 0) * (Part() + throughs)
 #   show_object([body, throughs])
 #   exit(0)
    return body - throughs
