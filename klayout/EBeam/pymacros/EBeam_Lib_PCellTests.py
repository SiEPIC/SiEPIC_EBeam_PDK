import pya
from pya import *
import os
import pathlib
#import sys

#import pcells_EBeam ### folder name ###
import importlib

# get all .py files in pcells_EBeam folder
files = [f for f in os.listdir(os.path.join(os.path.dirname(
    os.path.realpath(__file__)),'pcells_EBeam')) if '.py' in pathlib.Path(f).suffixes  and '__init__' not in f]


importlib.invalidate_caches()

# get EBeam library layout object 
ebeam_id = pya.Library().library_ids()[1]
ebeam_layout = pya.Library().library_by_id(ebeam_id).layout()

error_occured = False

for f in files:
        mm = f.replace('.py','')# Example: mm = Waveguide
        
        # check pcell has been registered in layout
        if mm not in ebeam_layout.pcell_names():
             #pya.MessageBox.critical("PCell Registration Error", "PCell {} could not be registered".format(mm), pya.MessageBox.Ok)
             print("PCell Registration Error. PCell {} could not be registered".format(mm))
             error_occured = True
              
        # instantiate pCell in new layer and check that it contains polygons
        new_layout = pya.Layout()
        pcell_decl = ebeam_layout.pcell_declaration(mm)
        new_layout.register_pcell(mm, pcell_decl)
            
        parameter_decl = pcell_decl.get_parameters()

        all_params = {}
        for p in parameter_decl:
            all_params[p.name] = p.default
            
        pcell = new_layout.create_cell(mm, all_params)
            
        if pcell.is_empty():
             #pya.MessageBox.critical("PCell Insantiation Error", "PCell {} is empty when instantiated in a new layout".format(mm), pya.MessageBox.Ok)
             print("PCell Insantiation Error. PCell {} is empty when instantiated in a new layout".format(mm))
             error_occured = True

                
completion_messages = ["All pcells from pcells_EBeam folder were successfully registered in EBeam library.", 
                       "Some pcells from pcells_EBeam folder were unsuccessfully registered in EBeam library."]

print("Complete. " + completion_messages[error_occured])

#with open(os.path.join(os.path.dirname(__file__), 'hello_world.txt'), 'w') as f:
    #f.write('hello world')

        












