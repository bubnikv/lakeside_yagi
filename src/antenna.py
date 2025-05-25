from build123d import *
from ocp_vscode import *

import os
from math import atan, degrees
from enum import Enum
from dataclasses import dataclass
from typing import List

import housing
from terminal import ChocoTerminal

# Where to store the results
output_path = os.path.dirname(os.path.realpath(__file__)) + '/../output/'
output_variant = '1'

# 3D printing technology constraints
print_gap = 0.15
# to keep the aluminium welding rod tight
print_gap_element = 0.1
# tighter gap to heat press the choco terminal into the housing
print_gap_terminal = 0.1
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

screw_terminal = ChocoTerminal.make_terminal_10mm2()
# Gap between the left / right terminals. To be filled with a FR4 separator.
terminal_spacing = 1.6
terminal_extra_width = 2 * print_line_width

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

elevation_rod_element_70cm=print_gap+2*print_line_width+dmr_element/2
elevation_rod_element_2m=print_gap+2*print_line_width+screw_terminal.outer_diameter/2

class ElementType(Enum):
    WIRE = 0
    CHOCO = 1

class Polarization(Enum):
    HORIZONTAL = 0
    VERTICAL = 1

@dataclass
class Element:
    position: float
    length:   float
    reversed: bool
    label:    str

@dataclass
class Elements:
    elements: List[Element]
    type: ElementType
    polarization: Polarization
    elevation: float

elements_2m_data = Elements(
    elements = [
        Element(pos_2m_reflector, l_2m_reflector, False, "2R"),
        Element(pos_2m_driven_element, l_2m_director1, False, "2D"),
        Element(pos_2m_director1, l_2m_director1, True, "21"),
    ],
    type = ElementType.CHOCO,
    polarization = Polarization.HORIZONTAL,
    elevation = elevation_rod_element_2m
)

elements_70cm_data = Elements(
    elements = [
        Element(pos_70cm_reflector, l_70cm_reflector, True, "7R"),
        Element(pos_70cm_driven_element, l_70cm_director1, False, "7D"),
        Element(pos_70cm_director1, l_70cm_director1, False, "71"),
        Element(pos_70cm_director2, l_70cm_director2, False, "72"),
        Element(pos_70cm_director3, l_70cm_director3, False, "73"),
        Element(pos_70cm_director4, l_70cm_director4, False, "74"),
        Element(pos_70cm_director5, l_70cm_director5, False, "75"),
        Element(pos_70cm_director6, l_70cm_director6, True, "76"),
    ],
    type = ElementType.WIRE,
    polarization = Polarization.VERTICAL,
    elevation = elevation_rod_element_70cm
)

rod = loft([Circle(d_rod_base/2), Pos(0, 0, l_rod) * Circle(d_rod_tip/2)])

def rod_radius(pos):
    return 0.5 * (d_rod_base - pos * (d_rod_base - d_rod_tip) / l_rod)

def element(polarization: Polarization, position, length, elevation, dmr = dmr_element):
    return (
        Rotation(0, 0, 0 if polarization is Polarization.HORIZONTAL else 90) *
        Location([0, rod_radius(position) + elevation, position]) *
        # Centered cylinder aligned with X axis
        Cylinder(radius=dmr/2, height=length, rotation=(0, 90, 0)))

def elements(element_data):
    elements = None
    elements = [element(element_data.polarization, 
                        el.position, el.length, element_data.elevation, dmr_element)
        for el in element_data.elements]
    return Part() + elements

def screw_terminals(element_data):
    elements = []
    for el in element_data.elements:
        gap = 2
        t = Rotation(0, 90, 0) * Rotation(0, 0, (-1 if el.reversed else 1) * screw_terminal.tangent_angle()) * screw_terminal.body()
        elements.append(Pos(screw_terminal.length/2 + gap/2, rod_radius(el.position) + element_data.elevation, el.position) * t)
        elements.append(Pos(- screw_terminal.length/2 - gap/2, rod_radius(el.position) + element_data.elevation, el.position) * t)
    return Part() + elements

#print("Close encounters of 2m and 70cm elements: ", elements_70cm_data.elements[0][0] - elements_2m_data.elements[0][0], elements_70cm_data.elements[4].position - elements_2m_data[2].position, elements_70cm_data[7].position - elements_2m_data[3].position)
print("Distance of the tip 2m rod from the laminate rod tip:", 
      l_rod - elements_2m_data.elements[2].position)
print("Distance of the 2m reflector from the laminate rod base:", 
      elements_2m_data.elements[0].position)

def element_housing(type: ElementType, polarization: Polarization, pos, reversed, elevation, label):
    assert d_rod_base > d_rod_tip
    boom_taper_angle = degrees(atan((d_rod_tip - d_rod_base) / l_rod))
    assert boom_taper_angle < 0
    if type == ElementType.WIRE:
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
    elif type == ElementType.CHOCO:
        body = housing.element_holder_for_choco_terminal(
            sleeve_base_radius = rod_radius(pos) + print_gap,
            sleeve_thickness = sleeve_thickness,
            sleeve_length = element_housing_length,
            sleeve_angle = 270,
            boom_taper_angle = -boom_taper_angle if reversed else boom_taper_angle,
            terminal = screw_terminal,
            terminal_spacing = terminal_spacing,
            extra_width = terminal_extra_width,
            element_above_boom_axis = rod_radius(pos) + elevation,
            element_wall = print_gap_element + element_housing_wall_thickness,
            element_wall_top_extra = element_housing_wall_thickness_extra,
            print_gap = print_gap_terminal,
            label = housing.Label(labels=[label[0], label[1]], font='Arial Black', size=6, depth=.28))
    else:
        raise ValueError(f"Unknown element type: {type}")

#    show_object(body, name="skoronakonci")
    return Pos(0, 0, pos) * \
           Rotation(0, 0, 0. if polarization is Polarization.HORIZONTAL else 90.) * \
           Rotation(0, -180 if reversed else 0, 0) * body

def element_housings(element_data):
    housings = []
    models = []
    for this_element_data in element_data.elements:
        el = element_housing(element_data.type, element_data.polarization, this_element_data.position, 
                             this_element_data.reversed, element_data.elevation, this_element_data.label)
        housings.append((this_element_data, el))
        models.append(el)
    return (housings, Part() + models)

def export_elements_stl(elements, polarization: Polarization):
    os.makedirs(output_path, exist_ok=True)

    for (this_element_data, model) in elements:
        (pos, len, reversed, label) = (this_element_data.position, this_element_data.length,
                                       this_element_data.reversed, this_element_data.label)
        if polarization == Polarization.VERTICAL:
            model = Rotation(0, 0, -90) * model
        if reversed:
            model = Rotation(0, 180, 0) * model
        label = label+'-'+output_variant
        if False:
    #        model.color = Color("blue")
            model.label = label
            exporter = Mesher()
            exporter.add_shape(model, part_number=label)
    #        exporter.add_meta_data(
    #            name_space="custom",
    #            name="test_meta_data",
    #            value="hello world",
    #            metadata_type="str",
    #            must_preserve=False,
    #        )
            exporter.add_code_to_metadata()
            exporter.write(output_path+label+".stl") # or 3mf
        else:
            export_stl(model, output_path+label+".stl")

elements_2m = elements(elements_2m_data)
housings_2m, housings_2m_model = element_housings(elements_2m_data)
screw_terminals_2m = screw_terminals(elements_2m_data)

polarization_70cm = Polarization.VERTICAL
elements_70cm = elements(elements_70cm_data)
housings_70cm, housings_70cm_model = element_housings(elements_70cm_data)

color_rod = Color(.35, .35, .35)
color_elements = Color("yellow")
color_housing = Color(1, .5, .5)

show_object(rod, name="rod", options={"color": color_rod.to_tuple()})
show_object(elements_2m, name="2m elements", options={"color": color_elements.to_tuple()})
show_object(elements_70cm, name="70cm elements", options={"color": color_elements.to_tuple()})
show_object(housings_2m_model, name="2m housing", options={"color": color_housing.to_tuple()})
show_object(housings_70cm_model, name="70cm housing", options={"color": color_housing.to_tuple()})
show_object(screw_terminals_2m, name="2m screw terminals", options={"color": color_elements.to_tuple()})

export_elements_stl(housings_2m, elements_2m_data.polarization)
export_elements_stl(housings_70cm, elements_70cm_data.polarization)
