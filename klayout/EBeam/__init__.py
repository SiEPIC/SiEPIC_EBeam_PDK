print("SiEPIC-EBeam-PDK Python module: siepic_ebeam_pdk v0.4.17, KLayout technology: EBeam")

# Load the KLayout technology, when running in Script mode
import pya
import os

if not pya.Technology().has_technology("EBeam"):
    tech = pya.Technology().create_technology("EBeam")
    tech.load(os.path.join(os.path.dirname(os.path.realpath(__file__)), "EBeam.lyt"))

# then import all the technology modules
from . import pymacros
print(pymacros.__file__)
'''
from .pymacros import (
    SiEPIC_EBeam_Library,
    SiEPIC_EBeam_Library_SiN,
    SiEPIC_EBeam_Library_Dream,
    SiEPIC_EBeam_Library_Beta,
    SiEPIC_EBeam_Library_ANT,
)
'''

# display the registered libraries
print("Loaded technology libraries: %s" % pya.Library.library_names())
