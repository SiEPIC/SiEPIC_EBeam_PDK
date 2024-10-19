"""
This file is part of the SiEPIC_EBeam_PDK
by Lukas Chrostowski, et al., (c) 2015-2023

This Python file implements a library called "SiEPIC-EBeam-Beta"
# - Development components, e.g., Layout only with no Compact Model.
 - Fixed GDS cell components: imported from SiEPIC-EBeam-dev.gds
 - PCells:
    DirectionalCoupler_SeriesRings, DirectionalCoupler_SeriesRings())
    ebeam_dc_halfring_arc, ebeam_dc_halfring_arc())
    DoubleBus_Ring, DoubleBus_Ring())
    TestStruct_DoubleBus_Ring, TestStruct_DoubleBus_Ring())
    TestStruct_DoubleBus_Ring2, TestStruct_DoubleBus_Ring2())
    Waveguide_Route, Waveguide_Route())
    Waveguide_Route_simple, Waveguide_Route_simple())
    Waveguide_Arc, Waveguide_Arc())
    Bent_Coupled_Half_Ring, Bent_Coupled_Half_Ring())
    Bent_CDC_Half_Ring, Bent_CDC_Half_Ring())
    Bezier_Bend, Bezier_Bend())
    Cavity Hole, cavity_hole())
    Tapered Ring, Tapered_Ring())
    Focusing Sub-wavelength grating coupler (fswgc), fswgc() )
    SWG_waveguide, SWG_waveguide())
    SWG_to_strip_waveguide, SWG_to_strip_waveguide())
    strip_to_slot, strip_to_slot() )
    spiral, spiral())
    Waveguide_SBend, Waveguide_SBend())
    ebeam_irph_mrr: in-resonator photoconductive heater, in a ring resonator
    ebeam_irph_wg: in-resonator photoconductive heater, in a straight waveguide


NOTE: after changing the code, the macro needs to be rerun to install the new
implementation. The macro is also set to "auto run" to install the PCell
when KLayout is run.

Crash warning:
 https://www.klayout.de/forum/discussion/734
 This library has nested PCells. Running this macro with a layout open may
 cause it to crash. Close the layout first before running.

*******
GDS:
*******
imported from SiEPIC-EBeam.gds

*******
PCells:
*******

1) Double-bus ring resonator
class TestStruct_DoubleBus_Ring
class DoubleBus_Ring
def layout_Ring(cell, layer, x, y, r, w, npoints):

2) Waveguide Taper
class ebeam_taper_te1550

3) Bragg grating waveguide
class Bragg_waveguide

Also includes additional functions:

1) code for waveguide bends:
def layout_waveguide_abs(cell, layer, points, w, radius):
def layout_waveguide_rel(cell, layer, start_point, points, w, radius):

2) function for making polygon text
def layout_pgtext(cell, layer, x, y, text, mag):

3) functions for inspecting PCell parameters
def PCell_get_parameter_list ( cell_name, library_name ):
def PCell_get_parameters ( pcell ):


Version history:

Lukas Chrostowski           2015/11/05 - 2015/11/10
 - Double-bus ring resonator
 - waveguide bends
 - PCell parameter functions
 - polygon text
 - PCell calling another PCell - TestStruct_DoubleBus_Ring

Lukas Chrostowski           2015/11/14
 - fix for rounding error in "DoubleBus_Ring"

Lukas Chrostowski           2015/11/15
 - fix for Python 3.4: print("xxx")

Lukas Chrostowski           2015/11/17
 - update "layout_waveguide_rel" to use the calculated points_per_circle(radius)

Lukas Chrostowski           2016/05/27
 - SWG_waveguide
 - SWG_to_strip_waveguide

Lukas Chrostowski           2016/06/11
 - spiral

S. Preble                   2016/08/26
 - Double Bus Ring Pin's shifted - text now is in the middle of the pin path

Timothy Richards, Adam DeAbreu, Lukas Chrostowski  2017/07/11
 -  Focusing Sub-wavelength grating coupler PCell.

Lukas Chrostowski 2017/12/16
 - compatibility with KLayout 0.25 and SiEPIC-Tools

Mustafa Hammood 2018/02/06
 - EBeam-Dev updates and fixes for compatibility with KLayout 0.25 and SiEPIC-Tools

Lukas Chrostowski 2020/04/03
 - SWG_assisted_Strip_WG based on SWG waveguide: adds a strip waveguide

Lukas 2023/11
 - compatibility with PyPI usage of KLayout

todo:
replace:
 layout_arc_wg_dbu(self.cell, Layerm1N, x0,y0, r_m1_in, w_m1_in, angle_min_doping, angle_max_doping)
with:
 self.cell.shapes(Layerm1N).insert(Polygon(arc(w_m1_in, angle_min_doping, angle_max_doping) + [Point(0, 0)]).transformed(t))


"""


import os
import sys
import SiEPIC
from SiEPIC.utils import get_technology, get_technology_by_name
from pya import *
import math

path = os.path.dirname(os.path.abspath(__file__))


def linspace_without_numpy(low, high, length):
    step = (high - low) * 1.0 / length
    return [low + i * step for i in range(length)]


def pin(w, pin_text, trans, LayerPinRecN, dbu, cell):
    """
    w: Waveguide Width, e.g., 500 (in dbu)
    pin_text: Pin Text, e.g., "pin1"
    trans: e.g., trans =  Trans(0, False, 0, 0)  - first number is 0, 1, 2, or 3.
    pinrec: PinRec Layer, e.g., layout.layer(TECHNOLOGY['PinRec']))
    devrec: DevRec Layer, e.g., layout.layer(TECHNOLOGY['DevRec']))
    """

    # Create the pin, as short paths:
    from SiEPIC._globals import PIN_LENGTH

    pin = trans * Path([Point(-PIN_LENGTH / 2, 0), Point(PIN_LENGTH / 2, 0)], w)
    cell.shapes(LayerPinRecN).insert(pin)
    text = Text(pin_text, trans)
    shape = cell.shapes(LayerPinRecN).insert(text)
    shape.text_size = w * 0.8

    # print("Done drawing the layout for - pin" )
