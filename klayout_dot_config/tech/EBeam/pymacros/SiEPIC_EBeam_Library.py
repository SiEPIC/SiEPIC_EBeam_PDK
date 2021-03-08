"""
This file is part of the SiEPIC_EBeam_PDK
by Lukas Chrostowski (c) 2015-2017

This Python file implements a library called "SiEPIC_EBeam", consisting of mature components that have Layouts and Compact Models for circuit simulations:
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
 https://www.klayout.de/forum/comments.php?DiscussionID=734&page=1#Item_13
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
 self.cell.shapes(Layerm1N).insert(Polygon(arc(w_m1_in, angle_min_doping, angle_max_doping) + [Point(0, 0)]).transformed(t))


Lukas Chrostowski 2020/06/21
 - Waveguide update, cellName

Mustafa Hammood 2020/06/26
 - major refactoring and splitting of individual classes into sub files

"""
import math
from SiEPIC.utils import get_technology, get_technology_by_name

# Import KLayout Python API methods:
# Box, Point, Polygon, Text, Trans, LayerInfo, etc
import pya
from pya import *
import pcells_EBeam


import sys
if int(sys.version[0]) > 2:
  from importlib import reload
# pcells_EBeam = reload(pcells_EBeam)

class SiEPIC_EBeam(Library):
  """
  The library where we will put the PCells and GDS into 
  """

  def __init__(self):
  
    tech_name = 'EBeam'
    library = tech_name

    print("Initializing '%s' Library." % library)

    # Set the description
# windows only allows for a fixed width, short description 
    self.description = ""
# OSX does a resizing:
    self.description = "v0.3.30, Components with models"

  
    # Import all the GDS files from the tech folder "gds"
    import os, fnmatch
    dir_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../gds/mature")
    search_str = '*' + '.gds'
    for root, dirnames, filenames in os.walk(dir_path, followlinks=True):
        for filename in fnmatch.filter([f.lower() for f in filenames], search_str):
            file1=os.path.join(root, filename)
            print(" - reading %s" % file1 )
            self.layout().read(file1)
    
       
    # Create the PCell declarations
    for attr, value in pcells_EBeam.__dict__.items():
        if '__module__' in dir(value):
            try:
                if value.__module__.split('.')[0] == 'pcells_EBeam' and attr != 'cls':
                    print('Registered pcell: '+attr)
                    self.layout().register_pcell(attr, value())
            except:
                pass
    print(' done with pcells')
    # Register us the library with the technology name
    # If a library with that name already existed, it will be replaced then.
    self.register(library)

    if int(Application.instance().version().split('.')[1]) > 24:
      # KLayout v0.25 introduced technology variable:
      self.technology=tech_name

    self.layout().add_meta_info(LayoutMetaInfo("path",os.path.realpath(__file__)))
    self.layout().add_meta_info(LayoutMetaInfo("technology",tech_name))
 
# Instantiate and register the library
# SiEPIC_EBeam()