import pya
from pya import *
import os
import pathlib
import sys

#import pcells_EBeam ### folder name ###
import importlib


"""
Python script to test that all EBeam Pcells are properly registered in the EBeam library and will display polygons when placed on a new layout.

To run this script from the command line: '{path to klayout} -e -r {path to this script/EBeam_Lib_PCellTests.py}'.
This script can also be run within KLayout.

This is a preliminary test script and will be implemented using GitHub Actions to be run every time a new EBeam Pcell is added to the code base.

by Jasmina Brar
2023/08

"""

# get all .py files in pcells_EBeam folder
files = [f for f in os.listdir(os.path.join(os.path.dirname(
    os.path.realpath(__file__)),'pcells_EBeam')) if '.py' in pathlib.Path(f).suffixes  and '__init__' not in f]


importlib.invalidate_caches()

# get EBeam library layout object 
tech_name = 'EBeam'
library_name = 'EBeam'
library = pya.Library().library_by_name(library_name,tech_name)
ebeam_layout = library.layout()

# check that EBeam library is not nil
if ebeam_layout == None:
      print("EBeam Library Error. Library is not registered.")
      exit()

error_occured = False

for f in files:
        mm = f.replace('.py','')
        
        # check pcell has been registered in layout
        if mm not in ebeam_layout.pcell_names():
             print("PCell Registration Error. PCell {} could not be registered".format(mm))
             error_occured = True
             continue
              
        # instantiate pcell in new layer and check that it contains polygons
        new_layout = pya.Layout()
        pcell_decl = ebeam_layout.pcell_declaration(mm)
        new_layout.register_pcell(mm, pcell_decl)
            
        parameter_decl = pcell_decl.get_parameters()

        all_params = {}
        for p in parameter_decl:
            all_params[p.name] = p.default
            
        pcell = new_layout.create_cell(mm, all_params)
            
        if pcell.is_empty():
             print("PCell Insantiation Error. PCell {} is empty when instantiated in a new layout".format(mm))
             error_occured = True

                
completion_messages = ["All pcells from pcells_EBeam folder were successfully registered in EBeam library.", 
                       "Some pcells from pcells_EBeam folder were unsuccessfully registered in EBeam library."]

print("Complete. " + completion_messages[error_occured])

        












