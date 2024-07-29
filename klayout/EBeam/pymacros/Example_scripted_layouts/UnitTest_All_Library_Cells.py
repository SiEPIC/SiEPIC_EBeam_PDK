# $description: Unit testing: all EBeam libraries' cells
# $show-in-menu
# $group-name: Examples_EBeam
# $menu-path: siepic_menu.exlayout.end
# Unit testing for all library layout fixed cells and PCells

import os
import sys

path_GitHub = os.path.expanduser("~/Documents/GitHub/")
if 0:
    if "SiEPIC" not in sys.modules:
        path_siepic = os.path.join(
            path_GitHub, "SiEPIC-Tools/klayout_dot_config/python"
        )
        if path_siepic not in sys.path:
            sys.path.insert(0, path_siepic)
from SiEPIC._globals import Python_Env

print("KLayout running in mode: %s" % Python_Env)
from SiEPIC.utils.layout import new_layout
from SiEPIC.utils import load_klayout_technology
from SiEPIC.scripts import instantiate_all_library_cells, export_layout

path_module = os.path.join(path_GitHub, "SiEPIC_EBeam_PDK/klayout")
path_lyt_file = os.path.join(path_GitHub, "SiEPIC_EBeam_PDK/klayout/EBeam/EBeam.lyt")
tech = load_klayout_technology("EBeam", path_module, path_lyt_file)


# Create a new layout
topcell, ly = new_layout(tech.name, "UnitTesting", GUI=True, overwrite=True)
# Instantiate all cells
instantiate_all_library_cells(topcell)
# Save the layout
path_out = os.path.dirname(os.path.realpath(__file__))
ly.write(os.path.join(path_out, "a.gds"))
export_layout(topcell, path_out, "a_static", format="oas")
print("done")
