# $description: Unit testing: all EBeam libraries' cells
# $show-in-menu
# $group-name: Examples_EBeam
# $menu-path: siepic_menu.exlayout.end
# Unit testing for all library layout fixed cells and PCells

tech_name = "EBeam"

import os
from SiEPIC._globals import Python_Env

print("KLayout running in mode: %s" % Python_Env)
from SiEPIC.utils.layout import new_layout
from SiEPIC.scripts import instantiate_all_library_cells


def test_all_library_cells():
    if Python_Env == "Script":
        # Load the PDK from a folder, e.g, GitHub, when running externally from the KLayout Application
        import sys

        path = os.path.dirname(os.path.realpath(__file__))
        sys.path.insert(0, os.path.abspath(os.path.join(path, "../../..")))
        import siepic_ebeam_pdk

    # Create a new layout
    topcell, ly = new_layout(tech_name, "UnitTesting", GUI=True, overwrite=True)

    # Instantiate all cells
    instantiate_all_library_cells(topcell)

    """
    # Save the layout
    path_out = os.path.dirname(os.path.realpath(__file__))
    ly.write(os.path.join(path_out,'a.gds'))
    export_layout(topcell, path_out,'a_static',format='oas')
    print('done')
    """

    # Check if there are any errors
    for cell_id in topcell.each_child_cell():
        c = ly.cell(cell_id)
        error_shapes = c.shapes(ly.error_layer())
        for error in error_shapes.each():
            raise Exception("Error in cell: %s, %s" % (c.name, error.text))
        if c.is_empty() or c.bbox().area() == 0:
            raise Exception("Empty cell: %s" % c.name)


if __name__ == "__main__":
    test_all_library_cells()
