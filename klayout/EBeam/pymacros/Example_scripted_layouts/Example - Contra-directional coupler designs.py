# $description: Contra-directional coupler designs (EBeam)
# $show-in-menu
# $group-name: Examples_EBeam
# $menu-path: siepic_menu.exlayout.begin


"""

Create a complete layout for several contra-directional coupler circuits

using KLayout & SiEPIC-Tools scripted layout

usage:
 - the SiEPIC EBeam Library
 - Uncomment path_to_waveguide to convert everything to waveguides, or just do it on your own from SiEPIC Tools menu.
 - Run circuit simulations either using OPICS or INTERCONNECT

Script will generate an series of devices with the selected parameters, and generate GCs for testing with automated measurement labels

Author: Lukas Chrostowski, Mustafa Hammood

March 2024
"""

print("SiEPIC_EBeam_PDK: Example - Example - Contra-directional coupler designs.py")

# Import KLayout-Python API
import pya
from pya import *

import SiEPIC
from SiEPIC._globals import Python_Env
from SiEPIC.scripts import zoom_out, export_layout
import os

if Python_Env == "Script":
    try:
        # For external Python mode, when installed using pip install siepic_ebeam_pdk
        import siepic_ebeam_pdk
    except:
        # Load the PDK from a folder, e.g, GitHub, when running externally from the KLayout Application
        import os, sys

        path_GitHub = os.path.expanduser("~/Documents/GitHub/")
        sys.path.append(os.path.join(path_GitHub, "SiEPIC_EBeam_PDK/klayout"))
        import siepic_ebeam_pdk

tech_name = "EBeam"

# Import from SiEPIC-Tools
from SiEPIC.extend import to_itype
from SiEPIC.scripts import connect_pins_with_waveguide, connect_cell

from packaging import version

if version.parse(SiEPIC.__version__) < version.parse("0.5.1"):
    pya.MessageBox.warning(
        "Errors",
        "This example requires SiEPIC-Tools version 0.5.1 or greater.",
        pya.MessageBox.Ok,
    )


# define layout parameters in the class below
# ALL distance parameters are in microns unless specified otherwise
class parameters:
    """Define the circuit layout parameters"""

    # Default contraDC PCell parameters
    component_contraDC = "contra_directional_coupler"
    libname = "EBeam"
    N = 1000
    period = 0.316
    g = 100
    w1 = 560
    w2 = 440
    dW1 = 0.05
    dW2 = 0.025
    sine = 0
    a = 2.7

    # routing and device placement parameters
    x_offset = 170  # spacing between grating couplers columns
    wg_bend_radius = 35  # waveguide routes bend radius
    device_spacing = 7.3  # spacing between devices
    wg_pitch = (
        5  # spacing between waveguides ( keep > 2 microns to minimize cross coupling)
    )
    pol = "TE"
    waveguide_type = "Strip TE 1550 nm, w=500 nm"
    gc_pitch = 127  # spacing between grating couplers array (for a single device)
    cdc_offset = 20
    name = "contraDC"


params = parameters()


def import_fixed_cells(ly):
    """Import the fixed cells from the library, and add them to the layout"""
    params.cell_gc = ly.create_cell(
        "ebeam_gc_%s1550" % params.pol.lower(), "EBeam"
    )  # .cell_index()
    # params.cell_y = ly.create_cell("ebeam_y_1550", "EBeam") # .cell_index()

    params.gc_length = 41  # Length of a grating coupler cell
    params.gc_height = 30  # Height of a grating coupler cell


def ebeam_c_te_mux_1ch_standard_1543nm(
    topcell,
    x_pos=0,
    y_pos=0,
    N=params.N,
    period=params.period,
    g=0.1,
    w1=0.56,
    w2=0.44,
    dW1=0.048,
    dW2=0.024,
    sine=0,
    a=2.7,
    wg_width=0.5,
    pol=params.pol,
):
    """Create a layout of a contradirectional coupler, with grating couplers
    This is a known-good design by Mustafa Hammood,
    having been fabricated by Applied Nanotools, and tested at UBC
    It is in the C-band and is used for the Process Control Monitor (PCM) structure (C-PCM).
    Works well when cascaded.
    Strip waveguides
    Bandwidth ~6 nm;	Wavelength 1543 nm
    Data: single stage, cascaded, exists on every PCM
    function by Lukas Chrostowski
    """

    # Create a sub-cell for our contraDC layout
    cell = topcell.layout().create_cell("contraDC_GCarray")

    # place the cell in the top cell
    t = Trans(Trans.R0, x_pos, y_pos)
    topcell.insert(CellInstArray(cell.cell_index(), t))
    ly = topcell.layout()

    # Grating couplers, Ports 1, 2, 3, 4 (top-down)
    instGCs = []
    for i in range(4):
        t = Trans(
            Trans.R0,
            to_itype(params.gc_length, ly.dbu),
            to_itype(params.gc_height / 2 + i * params.gc_pitch, ly.dbu),
        )
        instGCs.append(cell.insert(CellInstArray(params.cell_gc.cell_index(), t)))
    t = Trans(
        Trans.R0,
        to_itype(params.gc_length, ly.dbu),
        to_itype(params.gc_height / 2 + params.gc_pitch * 2, ly.dbu),
    )
    text = Text(
        "opt_in_%s_1550_device_%s%dN%dperiod%dg%dwa%dwb%ddwa%ddwb%dsine%sa"
        % (
            pol,
            params.name,
            N,
            1000 * period,
            1000 * g,
            1000 * w1,
            1000 * w2,
            1000 * dW1,
            1000 * dW2,
            sine,
            a,
        ),
        t,
    )
    # text = Text ("opt_in_TE_1550_device_contraDC1"
    shape = cell.shapes(ly.layer(ly.TECHNOLOGY["Text"])).insert(text)
    shape.text_size = 1.5 / ly.dbu

    # contraDC PCell
    pcell = ly.create_cell(
        params.component_contraDC,
        params.libname,
        {
            "sbend": 1,
            "number_of_periods": N,
            "grating_period": period,
            "gap": g,
            "wg1_width": w1,
            "wg2_width": w2,
            "corrugation_width1": dW1,
            "corrugation_width2": dW2,
            "sinusoidal": sine,
            "index": a,
        },
    )
    if not pcell:
        raise Exception(
            "Cannot find cell %s in library %s."
            % (params.component_contraDC, params.libname)
        )
    t = Trans(
        Trans.R90,
        to_itype(params.gc_length + params.cdc_offset, ly.dbu),
        to_itype(params.gc_height / 2 + params.gc_pitch * 0.2, ly.dbu),
    )
    instCDC = cell.insert(CellInstArray(pcell.cell_index(), t))

    # Waveguides:
    connect_pins_with_waveguide(
        instGCs[3], "opt1", instCDC, "opt3", waveguide_type=params.waveguide_type
    )
    connect_pins_with_waveguide(
        instGCs[2],
        "opt1",
        instCDC,
        "opt4",
        waveguide_type=params.waveguide_type,
        turtle_A=[5, 90, 30, -90],
        turtle_B=[5, 90],
    )
    connect_pins_with_waveguide(
        instGCs[1],
        "opt1",
        instCDC,
        "opt2",
        waveguide_type=params.waveguide_type,
        turtle_A=[5, -90, 30, 90],
        turtle_B=[5, -90],
    )
    connect_pins_with_waveguide(
        instGCs[0], "opt1", instCDC, "opt1", waveguide_type=params.waveguide_type
    )

    return cell


def layout_contraDC_circuits(newlayout=True):
    """
    Generates contraDC circuits.
    Either create a new layout using the EBeam technology,
        newlayout = True
    or delete everything in the present layout
        newlayout = False
    """

    from SiEPIC.utils.layout import new_layout, floorplan
    from SiEPIC.utils import select_paths, get_layout_variables

    """
    Create a new layout using the EBeam technology, with a top cell
    """
    topcell, ly = new_layout(
        tech_name, "SiEPIC_EBeam_contraDC_circuits", GUI=True, overwrite=not newlayout
    )

    # Import the grating couplers, and other fixed cells
    import_fixed_cells(ly)

    # create a floor plan
    # 605 x 410 microns is the space allocation for the edX course and openEBL
    # https://siepic.ca/openebl/
    floorplan(topcell, 605e3, 410e3)

    # Create the contraDC circuits
    ebeam_c_te_mux_1ch_standard_1543nm(topcell)

    # Zoom out
    zoom_out(topcell)

    # Save
    path = os.path.dirname(os.path.realpath(__file__))
    filename = "openEBL_Contra-directional-coupler-design"
    file_out = export_layout(
        topcell, path, filename, relative_path="..", format="oas", screenshot=False
    )

    from SiEPIC.verification import layout_check

    print("SiEPIC_EBeam_PDK: - verification")

    file_lyrdb = os.path.join(path, filename + ".lyrdb")
    num_errors = layout_check(
        cell=topcell, verbose=False, GUI=True, file_rdb=file_lyrdb
    )

    if Python_Env == "Script":
        from SiEPIC.utils import klive

        klive.show(file_out, lyrdb_filename=file_lyrdb, technology=tech_name)

    if num_errors == 0:
        print("Functional verification: Passed with 0 errors")
    else:
        print("Functional verification: Failed with %s errors" % num_errors)


layout_contraDC_circuits(newlayout=False)


# All done!
