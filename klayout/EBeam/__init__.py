print("SiEPIC-EBeam-PDK Python module: siepic_ebeam_pdk, KLayout technology: EBeam")

# Load the KLayout technology, when running in Script mode
import pya
import os

if not pya.Technology().has_technology("EBeam"):
    tech = pya.Technology().create_technology("EBeam")
    tech.load(os.path.join(os.path.dirname(os.path.realpath(__file__)), "EBeam.lyt"))

# then import all the technology modules
from . import pymacros

# display the registered libraries
print("Loaded technology libraries: %s" % pya.Library.library_names())
