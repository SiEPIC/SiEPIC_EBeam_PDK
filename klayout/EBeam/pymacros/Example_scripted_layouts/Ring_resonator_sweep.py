# $description: Double-bus ring resonator sweep (EBeam)
# $show-in-menu
# $group-name: Examples_EBeam
# $menu-path: siepic_menu.exlayout.begin

"""
Scripted layout for ring resonators using SiEPIC-Tools
in the SiEPIC-EBeam-PDK "EBeam" technology

by Lukas Chrostowski, 2020-2023
"""

def Ring_resonator_sweep():
    print("SiEPIC_EBeam_PDK: Example - Ring_resonator_sweep.py")
    import pya
    from pya import Trans, CellInstArray, Text

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


    # Example layout function
    def dbl_bus_ring_res():
        # Import functions from SiEPIC-Tools
        from SiEPIC.extend import to_itype
        from SiEPIC.scripts import connect_cell, connect_pins_with_waveguide
        from SiEPIC.utils.layout import new_layout, floorplan

        # Create a layout for testing a double-bus ring resonator.
        # uses:
        #  - the SiEPIC EBeam Library
        # creates the layout in the presently selected cell
        # deletes everything first

        # Configure parameter sweep
        pol = "TE"
        if pol == "TE":
            sweep_radius = [3, 5, 5, 5, 10, 10, 10, 10, 10]
            sweep_gap = [0.07, 0.07, 0.08, 0.09, 0.07, 0.08, 0.09, 0.10, 0.11]
            x_offset = 67
            wg_bend_radius = 5
        else:
            sweep_radius = [30, 30, 30, 30, 30, 30, 30, 30]
            sweep_gap = [0.25, 0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.60]
            x_offset = 67
            wg_bend_radius = 15

        wg_width = 0.5

        """
        Create a new layout using the EBeam technology,
        with a top cell
        and Draw the floor plan
        """
        cell, ly = new_layout(tech_name, "top", GUI=True, overwrite=True)
        floorplan(cell, 605e3, 410e3)

        from packaging import version

        if version.parse(SiEPIC.__version__) < version.parse("0.5.1"):
            pya.MessageBox.warning(
                "Errors",
                "This example requires SiEPIC-Tools version 0.5.1 or greater.",
                pya.MessageBox.Ok,
            )

        # Layer mapping:
        LayerSiN = ly.layer(ly.TECHNOLOGY["Si"])
        fpLayerN = cell.layout().layer(ly.TECHNOLOGY["FloorPlan"])
        TextLayerN = cell.layout().layer(ly.TECHNOLOGY["Text"])

        # Create a sub-cell for our Ring resonator layout
        top_cell = cell
        dbu = ly.dbu
        cell = cell.layout().create_cell("RingResonator")
        if pol == "TE":
            t = Trans(Trans.R0, 40 / dbu, 12 / dbu)
        else:
            # rotate the layout since EBeam TM grating couplers have an angle that is negative
            t = Trans(Trans.R180, 560 / dbu, 393 / dbu)

        # place the cell in the top cell
        top_cell.insert(CellInstArray(cell.cell_index(), t))

        # Import cell from the SiEPIC EBeam Library
        cell_ebeam_gc = ly.create_cell("GC_%s_1550_8degOxide_BB" % pol, "EBeam")
        # get the length of the grating coupler from the cell
        gc_length = cell_ebeam_gc.bbox().width() * dbu
        # spacing of the fibre array to be used for testing
        GC_pitch = 127

        # Loop through the parameter sweep
        for i in range(len(sweep_gap)):
            # place layout at location:
            if i == 0:
                x = 0
            else:
                # next device is placed at the right-most element + length of the grating coupler
                x = inst_dc2.bbox().right * dbu + gc_length + 1

            # get the parameters
            r = sweep_radius[i]
            g = sweep_gap[i]

            # Grating couplers, Ports 0, 1, 2, 3 (from the bottom up)
            instGCs = []
            for i in range(0, 4):
                t = Trans(Trans.R0, to_itype(x, dbu), i * 127 / dbu)
                instGCs.append(cell.insert(CellInstArray(cell_ebeam_gc.cell_index(), t)))

            # Label for automated measurements, laser on Port 2, detectors on Ports 1, 3, 4
            t = Trans(Trans.R90, to_itype(x, dbu), to_itype(GC_pitch * 2, dbu))
            text = Text(
                "opt_in_%s_1550_device_RingDouble%sr%sg%s"
                % (pol.upper(), pol.upper(), r, int(round(g * 1000))),
                t,
            )
            text.halign = 1
            cell.shapes(TextLayerN).insert(text).text_size = 5 / dbu

            """
            # Label for automated measurements, laser on Port 1, detectors on Ports 2, 3
            # this will cause an error in the verification since the 4th detector is not connected
            t = Trans(Trans.R0, to_itype(x,dbu), to_itype(GC_pitch*3,dbu))
            text = Text ("opt_in_%s_1550_device_RingDouble%sr%sg%sB" % (pol.upper(), pol.upper(),r,int(round(g*1000))), t)
            text.halign = 1
            cell.shapes(TextLayerN).insert(text).text_size = 5/dbu
            """

            # Ring resonator from directional coupler PCells
            cell_dc = ly.create_cell(
                "ebeam_dc_halfring_straight",
                "EBeam",
                {"r": r, "w": wg_width, "g": g, "bustype": 0},
            )
            y_ring = GC_pitch * 3 / 2
            # first directional coupler
            t1 = Trans(Trans.R270, to_itype(x + wg_bend_radius, dbu), to_itype(y_ring, dbu))
            inst_dc1 = cell.insert(CellInstArray(cell_dc.cell_index(), t1))
            # add 2nd directional coupler, snapped to the first one
            inst_dc2 = connect_cell(inst_dc1, "pin2", cell_dc, "pin4")

            # Create paths for waveguides, with the type defined in WAVEGUIDES.xml in the PDK
            waveguide_type = "Strip TE 1550 nm, w=500 nm"

            # GC1 to bottom-left of ring pin3
            connect_pins_with_waveguide(
                instGCs[1], "opt1", inst_dc1, "pin3", waveguide_type=waveguide_type
            )

            # GC2 to top-left of ring pin1
            connect_pins_with_waveguide(
                instGCs[2], "opt1", inst_dc1, "pin1", waveguide_type=waveguide_type
            )

            # GC0 to top-right of ring
            connect_pins_with_waveguide(
                instGCs[0], "opt1", inst_dc2, "pin1", waveguide_type=waveguide_type
            )

            # GC3 to bottom-right of ring
            connect_pins_with_waveguide(
                instGCs[3], "opt1", inst_dc2, "pin3", waveguide_type=waveguide_type
            )

        # Introduce an error, to demonstrate the Functional Verification
        inst_dc2.transform(Trans(1000, -1000))

        return ly, cell


    ly, cell = dbl_bus_ring_res()

    # Zoom out
    zoom_out(cell)

    # Save
    path = os.path.dirname(os.path.realpath(__file__))
    filename = "Test_structures_ring_resonators"
    file_out = export_layout(
        cell, path, filename, relative_path="", format="oas", screenshot=True
    )

    from SiEPIC.verification import layout_check

    print("SiEPIC_EBeam_PDK: example_Ring_resonator_sweep.py - verification")

    file_lyrdb = os.path.join(path, filename + ".lyrdb")
    num_errors = layout_check(cell=cell, verbose=False, GUI=True, file_rdb=file_lyrdb)

    if Python_Env == "Script":
        from SiEPIC.utils import klive

        klive.show(file_out, lyrdb_filename=file_lyrdb, technology=tech_name)

    print("SiEPIC_EBeam_PDK: example_Ring_resonator_sweep.py - done")

if __name__ == "__main__":
    Ring_resonator_sweep()
    