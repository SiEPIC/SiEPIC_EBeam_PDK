"""
Debug sliver issue foundy by Susan at CMC

by Lukas Chrostowski 2024

Caused when a bezier curve ending is the end of the waveguide.
Caused by translate_from_normal(wg_pts, width/2 + (offset if turn > 0 else - offset))
Caused by Bezier curve, which returns:
  433, 12745
  220, 12748
  1,   12750
  0,   12750
 (length 111)
"""

designer_name = "Example"
top_cell_name = "EBeam_%s_MZI" % designer_name

import pya
from pya import *

import siepic_ebeam_pdk
from SiEPIC.scripts import connect_pins_with_waveguide, export_layout
from SiEPIC.utils.layout import new_layout

import os


def test_sliver():
    tech_name = "EBeam"
    from SiEPIC.utils import get_technology_by_name

    TECHNOLOGY = get_technology_by_name(tech_name)

    cell, ly = new_layout(tech_name, top_cell_name, GUI=True, overwrite=True)

    waveguide_type = "Strip TE 1550 nm, w=500 nm"

    cell_ebeam_y = ly.create_cell("ebeam_y_1550", tech_name)
    t = pya.Trans.from_s("r0 %s, %s" % (-7400, 0))
    instY1 = cell.insert(pya.CellInstArray(cell_ebeam_y.cell_index(), t))
    t = pya.Trans.from_s("r0 %s, %s" % (-7400, 10e3))
    instY2 = cell.insert(pya.CellInstArray(cell_ebeam_y.cell_index(), t))
    wg1 = connect_pins_with_waveguide(
        instY1, "opt2", instY2, "opt2", waveguide_type=waveguide_type
    )

    instY1.delete()
    instY2.delete()

    # check for sliver:
    wg1.cell.shapes(ly.layer(ly.TECHNOLOGY["Si"])).each
    polygon = [p for p in wg1.cell.shapes(ly.layer(ly.TECHNOLOGY["Si"])).each()][
        0
    ].polygon
    for p in [r for r in polygon.to_simple_polygon().each_point()]:
        if p.x < 0:
            raise Exception(" Polygon error: %s" % p)

    # Save
    path = os.path.dirname(os.path.realpath(__file__))
    filename = "test_waveguide_sliver"
    file_out = export_layout(cell, path, filename, relative_path="", format="oas")

    from SiEPIC.utils import klive

    klive.show(file_out, technology=tech_name, keep_position=True)


if __name__ == "__main__":
    test_sliver()
