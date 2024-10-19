
"""
This file is part of the SiEPIC_EBeam_PDK
by Lukas Chrostowski (c) 2015-2023

This Python file implements a library called "SiEPIC_EBeam", consisting of mature components that
have Layouts and Compact Models for circuit simulations:
 - Fixed GDS cell components: imported from SiEPIC-EBeam.gds
 - PCells:
    - ebeam_dc_halfring_straight
    - ebeam_bragg_te1550: waveguide Bragg grating
                - ebeam_taper_te1550: Waveguide Taper
                - Waveguide_bump
                -
                - Waveguide_Bend

NOTE: after changing the code, the macro needs to be rerun to install the new
implementation. The macro is also set to "auto run" to install the PCell
when KLayout is run.

Crash warning:
 https://www.klayout.de/forum/discussion/734
 This library has nested PCells. Running this macro with a layout open may
 cause it to crash. Close the layout first before running.

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

Lukas Chrostowski           2015/11/xx
 - Waveguide based on bends, straight waveguide.

Lukas Chrostowski           2015/12/3
 - Bragg grating

Lukas Chrostowski           2016/01/17
 - Taper, matching EBeam CML component

Lukas Chrostowski           2016/01/20
 - (sinusoidal) Bragg grating

Lukas Chrostowski           2016/05/27
 - SWG_waveguide
 - SWG_to_strip_waveguide

S. Preble                   2016/08/26
 - Double Bus Ring Pin's shifted - text now is in the middle of the pin path

Lukas Chrostowski           2016/11/06
 - waveguide bump, to provide a tiny path length increase

Lukas Chrostowski           2017/02/14
 - renaming "SiEPIC" PCells library to "SiEPIC-EBeam PCells", update for Waveguide_Route
 - code simplifications: Box -> Box

Lukas Chrostowski           2017/03/08
 - S-Bend -

Lukas Chrostowski           2017/03/18
 - ebeam_dc_halfring_straight, with TE/TM support.  Zeqin Lu adding CML for this component.

Lukas Chrostowski 2017/12/16
 - compatibility with KLayout 0.25 and SiEPIC-Tools

Lukas Chrostowski 2020/02/22
 - contra directional coupler; moved from Dev library; now has a compact model generator

todo:
replace:
 layout_arc_wg_dbu(self.cell, Layerm1N, x0,y0, r_m1_in, w_m1_in, angle_min_doping, angle_max_doping)
with:
 self.cell.shapes(Layerm1N).insert(Polygon(arc(w_m1_in, angle_min_doping, angle_max_doping) +
 [Point(0, 0)]).transformed(t))


Lukas Chrostowski 2020/06/21
 - Waveguide update, cellName

Mustafa Hammood 2020/06/26
 - major refactoring and splitting of individual classes into sub files

Lukas 2021/04/01
 - fixing loading library (previous collisions with other PDKs)

Lukas 2023/11
 - compatibility with PyPI usage of KLayout
 
Lukas 2024/10
 - moving most of the code into SiEPIC.scripts.load_klayout_library

"""



import os
import sys
import SiEPIC

from SiEPIC.utils import get_technology_by_name
