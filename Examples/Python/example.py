
path_GitHub = '/Users/lukasc/Documents/GitHub/'

import klayout
import pya
from pya import *
import os, sys

path_siepic = os.path.join(path_GitHub, 'SiEPIC-Tools/klayout_dot_config/python')
if not path_siepic in sys.path:
    sys.path.append(path_siepic)
import SiEPIC
import SiEPIC.extend

from SiEPIC._globals import Python_Env
print('KLayout running in mode: %s' % Python_Env)

path_ebeam = os.path.join(path_GitHub, 'SiEPIC_EBeam_PDK/klayout')
if not path_ebeam in sys.path:
    sys.path.append(path_ebeam)
tech = pya.Technology().create_technology('EBeam')
tech = tech.load(os.path.join(path_GitHub, 'SiEPIC_EBeam_PDK/klayout/EBeam/EBeam.lyt'))
import EBeam  # technology needs to be defined first.


from SiEPIC.utils.layout import new_layout, floorplan
from SiEPIC.scripts import zoom_out, export_layout

topcell, ly = new_layout(tech.name, "top", overwrite = True)

#topcell = ly.create_cell('top')

'''pcell = ly.create_cell('ebeam_dc_halfring_straight','EBeam', {})
t = Trans(Trans.R0, 0, 0)
topcell.insert(CellInstArray(pcell.cell_index(), t))
pcell = ly.create_cell('contra_directional_coupler','EBeam', {})
t = Trans(Trans.R0, 0, 0)
topcell.insert(CellInstArray(pcell.cell_index(), t))
'''

# all the libraries
x,y,xmax=0,0,0
for lib in pya.Library().library_ids():
    li = pya.Library().library_by_id(lib)
    if li.name() == 'Basic':
        continue
    print(li.layout().pcell_names())

    # all the pcells
    for n in li.layout().pcell_names():
        print(li.name(), n)
        pcell = ly.create_cell(n,li.name(), {})
        if pcell:
            t = Trans(Trans.R0, x-pcell.bbox().left, y-pcell.bbox().bottom)
            topcell.insert(CellInstArray(pcell.cell_index(), t))
            y += pcell.bbox().height()+2000
            xmax = max(xmax, pcell.bbox().width()+2000)
        else:
            print('Error in: %s' % n)
    x, y = xmax, 0
    # all the fixed cells
    for c in li.layout().each_top_cell():
        # instantiate
        if not li.layout().cell(c).is_pcell_variant():
            print(li.name(), li.layout().cell(c).name)
            pcell = ly.create_cell(li.layout().cell(c).name,li.name(), {})
            if not pcell:
                pcell = ly.create_cell(li.layout().cell(c).name,li.name())
            if pcell:
                t = Trans(Trans.R0, x-pcell.bbox().left, y-pcell.bbox().bottom)
                topcell.insert(CellInstArray(pcell.cell_index(), t))
                y += pcell.bbox().height()+2000
                xmax = max(xmax, pcell.bbox().width()+2000)
            else:
                print('Error in: %s' % li.layout().cell(c).name)
    x, y = xmax, 0

path_out = os.path.dirname(os.path.realpath(__file__))
ly.write(os.path.join(path_out,'a.oas'))
export_layout(topcell, path_out,'a_static',format='oas')
print('done')

