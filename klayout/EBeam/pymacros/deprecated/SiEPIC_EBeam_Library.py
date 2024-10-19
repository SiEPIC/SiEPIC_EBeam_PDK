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

version = "0.4.22"
print("SiEPIC_EBeam PDK, version %s" % version)

verbose = False

import pya
from pya import *
import os
import pathlib
import sys

from SiEPIC.scripts import load_klayout_library

# load_klayout_library('EBeam', 'pymacros', 'pcells_EBeam')

dir_path = os.path.dirname(os.path.realpath(__file__))
if dir_path not in sys.path:
    sys.path.append(dir_path)

files = [
    f
    for f in os.listdir(
        os.path.join(os.path.dirname(os.path.realpath(__file__)), "pcells_EBeam")
    )
    if ".py" in pathlib.Path(f).suffixes and "__init__" not in f
]
import pcells_EBeam  ### folder name ###
import importlib

importlib.invalidate_caches()
pcells_ = []
for f in files:
    module = "pcells_EBeam.%s" % f.replace(".py", "")  ### folder name ###
    if verbose:
        print(" - found module: %s" % module)
    m = importlib.import_module(module)
    if verbose:
        print(m)
    pcells_.append(importlib.reload(m))


class SiEPIC_EBeam_Library(Library):
    """
    The library where we will put the PCells and GDS into
    """

    def __init__(self):
        tech_name = "EBeam"
        library = tech_name
        self.technology = tech_name

        if verbose:
            print("Initializing '%s' Library." % library)

        # Set the description
        self.description = "v%s, Components with models" % version

        # Save the path, used for loading WAVEGUIDES.XML
        import os

        self.path = os.path.dirname(os.path.realpath(__file__))

        # Import all the GDS files from the tech folder
        import os
        import fnmatch

        dir_path = os.path.normpath(
            os.path.join(os.path.dirname(os.path.realpath(__file__)), "../gds/EBeam")
        )
        if verbose:
            print("  library path: %s" % dir_path)
        search_str = "*.[Oo][Aa][Ss]"  # OAS
        for root, dirnames, filenames in os.walk(dir_path, followlinks=True):
            for filename in fnmatch.filter(filenames, search_str):
                file1 = os.path.join(root, filename)
                if verbose:
                    print(" - reading %s" % file1)
                self.layout().read(file1)
        search_str = "*.[Gg][Dd][Ss]"  # GDS
        for root, dirnames, filenames in os.walk(dir_path, followlinks=True):
            for filename in fnmatch.filter(filenames, search_str):
                file1 = os.path.join(root, filename)
                if verbose:
                    print(" - reading %s" % file1)
                self.layout().read(file1)

        # Create the PCell declarations
        for m in pcells_:
            mm = m.__name__.replace("pcells_EBeam.", "")
            mm2 = m.__name__ + "." + mm + "()"
            if verbose:
                print(" - register_pcell %s, %s" % (mm, mm2))
            self.layout().register_pcell(mm, eval(mm2))

        if verbose:
            print(" done with pcells")

        # Register us the library with the technology name
        # If a library with that name already existed, it will be replaced then.
        self.register(library)


# Instantiate and register the library
SiEPIC_EBeam_Library()
