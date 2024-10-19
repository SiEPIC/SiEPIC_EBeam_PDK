print("SiEPIC-EBeam-PDK Python module: siepic_ebeam_pdk, KLayout technology: EBeam")

# Check KLayout version
import SiEPIC
from SiEPIC._globals import KLAYOUT_VERSION
if KLAYOUT_VERSION < 28:
    question = pya.QMessageBox()
    question.setStandardButtons(pya.QMessageBox.Ok)
    question.setText(
        "SiEPIC-EBeam is not compatible with older versions (<0.28) of KLayout."
    )
    KLayout_link0 = "https://www.klayout.de/build.html"
    question.setInformativeText(
        "\nSiEPIC-EBeam is not compatible with older versions (<0.28) of KLayout.\nPlease download an install the latest version, from %s"
        % (KLayout_link0)
    )
    pya.QMessageBox_StandardButton(question.exec_())

from packaging.version import Version
if Version(SiEPIC.__version__) < Version('0.5.14'):
    raise Exception ('This PDK requires SiEPIC-Tools v0.5.14 or greater.')

# Load the KLayout technology, when running in Script mode
import pya
import os

if not pya.Technology().has_technology("EBeam"):
    tech = pya.Technology().create_technology("EBeam")
    tech.load(os.path.join(os.path.dirname(os.path.realpath(__file__)), "EBeam.lyt"))

# then import all the technology modules
from . import pymacros

# List the libraries loaded       
from SiEPIC.scripts import technology_libraries
technology_libraries(tech)

