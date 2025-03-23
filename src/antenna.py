from build123d import *
from ocp_vscode import *

from math import atan, degrees
from enum import Enum

import housing
from terminal import ChocoTerminal

# Where to store the results
output_path = '../output/'
output_variant = '1'

# 3D printing technology constraints
print_gap = 0.15
# to keep the aluminium welding rod tight
print_gap_element = 0.1
# Width of an extrusion line
print_line_width=0.4

# sleeve around the rod holding the element
sleeve_thickness = 4 * print_line_width
# Lenght of the laminate fishing rod
l_rod=1130
# Diameter of the laminate fishing rod, base
d_rod_base=19.5
# Diameter of the laminate fishing rod, tip
d_rod_tip=16

# Diameter of the aluminium element 1/8 of an inch
dmr_element=3.175

# Elevation of the antenna element axis above the fishing rod surface.
elevation_rod_element_2m=print_gap+2*print_line_width+dmr_element/2
elevation_rod_element_70cm=elevation_rod_element_2m+dmr_element/2

# Width of the element housing along the element
element_housing_width = 21 + 2 * print_gap + 2 * sleeve_thickness
element_housing_length = 18
element_housing_wall_thickness = 2*print_line_width
# Make the housing a bit thicker at the far end to increase layer bonding
# of the tube around the element.
element_housing_wall_thickness_extra = 1 * print_line_width

# Positions of 2m elements with regard to the base of the rod
# Distance between the center of the reflector and the center of the last director.
l_2m=1016
pos_base=l_rod - l_2m - (dmr_element/2 + print_gap_element + element_housing_wall_thickness)
pos_2m_reflector=pos_base - 30
pos_2m_driven_element=pos_2m_reflector + 50 + 560
pos_2m_director1=pos_2m_reflector + 50 + 860
# Length of 2m elements
l_2m_reflector=1028.7
l_2m_director1=927.1
l_2m_director2=825.5
 
# Positions of 70cm elements with regard to the base of the rod
# Distance between the center of the reflector and the center of the last director.
l_70cm=958.9
#pos_70cm_reflector=pos_2m_reflector + ( l_2m - l_70cm ) / 2
pos_70cm_reflector=pos_base + 19
pos_70cm_driven_element=pos_70cm_reflector + 63.5
pos_70cm_director1=pos_70cm_reflector + 139.7
pos_70cm_director2=pos_70cm_reflector + 285.8
pos_70cm_director3=pos_70cm_reflector + 444.5
pos_70cm_director4=pos_70cm_reflector + 609.6
pos_70cm_director5=pos_70cm_reflector + 774.7
pos_70cm_director6=pos_70cm_reflector + l_70cm
# Length of 70cm elements
l_70cm_reflector=340.4
l_70cm_director1=315
l_70cm_director2=304.8
l_70cm_director3=304.8
l_70cm_director4=304.8
l_70cm_director5=304.8
l_70cm_director6=281.9

elements_2m_data = [
    (pos_2m_reflector, l_2m_reflector, False, "2R"),
    (pos_2m_driven_element, l_2m_director1, False, "2D"),
    (pos_2m_director1, l_2m_director1, True, "21"),
]

elements_70cm_data = [
    (pos_70cm_reflector, l_70cm_reflector, True, "7R"),
    (pos_70cm_driven_element, l_70cm_director1, False, "7D"),
    (pos_70cm_director1, l_70cm_director1, False, "71"),
    (pos_70cm_director2, l_70cm_director2, False, "72"),
    (pos_70cm_director3, l_70cm_director3, False, "73"),
    (pos_70cm_director4, l_70cm_director4, False, "74"),
    (pos_70cm_director5, l_70cm_director5, False, "75"),
    (pos_70cm_director6, l_70cm_director6, True, "76"),
]

class Polarization(Enum):
    HORIZONTAL = 0
    VERTICAL = 1

rod = loft([Circle(d_rod_base/2), Pos(0, 0, l_rod) * Circle(d_rod_tip/2)])

def rod_radius(pos):
    return 0.5 * (d_rod_base - pos * (d_rod_base - d_rod_tip) / l_rod)

def element(polarization: Polarization, position, length, elevation, dmr = dmr_element):
    return (
        Rotation(0, 0, 0 if polarization is Polarization.HORIZONTAL else 90) *
        Location([0, rod_radius(position) + elevation, position]) *
        # Centered cylinder aligned with X axis
        Cylinder(radius=dmr/2, height=length, rotation=(0, 90, 0)))

def elements(polarization: Polarization, element_data, elevation):
    elements = None
    elements = [element(polarization, pos, element_length, elevation, dmr_element)
        for (pos, element_length, reverse, label) in element_data]
    return Part() + elements

#print("Close encounters of 2m and 70cm elements: ", elements_70cm_data[0][0] - elements_2m_data[0][0], elements_70cm_data[4][0] - elements_2m_data[2][0], elements_70cm_data[7][0] - elements_2m_data[3][0])
print("Distance of the tip 2m rod from the laminate rod tip:", l_rod - elements_2m_data[2][0])
print("Distance of the 2m reflector from the laminate rod base:", elements_2m_data[0][0])

def element_housing(polarization: Polarization, pos, reversed, elevation, label):
    assert d_rod_base > d_rod_tip
    boom_taper_angle = degrees(atan((d_rod_tip - d_rod_base) / l_rod))
    assert boom_taper_angle < 0
    body = housing.element_holder_for_wire(
        sleeve_base_radius = rod_radius(pos) + print_gap,
        sleeve_thickness = sleeve_thickness,
        sleeve_length = element_housing_length,
        sleeve_angle = 270,
        boom_taper_angle = -boom_taper_angle if reversed else boom_taper_angle,
        housing_width = element_housing_width,
        element_dmr = dmr_element,
        element_above_boom_axis = rod_radius(pos) + elevation,
        element_wall = print_gap_element + element_housing_wall_thickness,
        element_wall_top_extra = element_housing_wall_thickness_extra,
        label = housing.Label(labels=[label[0], label[1]], font='Arial Black', size=6, depth=.28))
#    show_object(body, name="skoronakonci")
    return Pos(0, 0, pos) * \
           Rotation(0, 0, 0. if polarization is Polarization.HORIZONTAL else 90.) * \
           Rotation(0, -180 if reversed else 0, 0) * body

def element_housings(polarization: Polarization, element_data, elevation):
    housings = []
    models = []
    for this_element_data in element_data:
        (pos, len, reversed, label) = this_element_data
        el = element_housing(polarization, pos, reversed, elevation, label)
        housings.append((this_element_data, el))
        models.append(el)
    return (housings, Part() + models)

#def export_elements_stl(elements):
#    for (this_element_data, workplane) in elements:
#        (pos, len, reversed, label) = this_element_data
#        model = workplane.val()
#        model = model.located(Location((pos, 0, 0)))
#        model = model.rotate((0, 0, 0), (0, 1, 0), - 90 if reversed else 90)
#        cq.exporters.export(model, output_path+label+'-'+output_variant+".stl")

polatization_2m = Polarization.HORIZONTAL
elements_2m = elements(polatization_2m, elements_2m_data, elevation_rod_element_2m)
housings_2m, housings_2m_model = element_housings(polatization_2m, elements_2m_data, elevation_rod_element_2m)

polarization_70cm = Polarization.VERTICAL
elements_70cm = elements(polarization_70cm, elements_70cm_data, elevation_rod_element_70cm)
housings_70cm, housings_70cm_model = element_housings(Polarization.VERTICAL, elements_70cm_data, elevation_rod_element_70cm)

color_rod = Color(.35, .35, .35)
color_elements = Color("yellow")
color_housing = Color(1, .5, .5)

show_object(rod, name="rod", options={"color": color_rod.to_tuple()})
show_object(elements_2m, name="2m elements", options={"color": color_elements.to_tuple()})
show_object(elements_70cm, name="70cm elements", options={"color": color_elements.to_tuple()})
show_object(housings_2m_model, name="2m housing", options={"color": color_housing.to_tuple()})
show_object(housings_70cm_model, name="70cm housing", options={"color": color_housing.to_tuple()})
