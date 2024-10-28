# %%
"""
This file is part of the SiEPIC_EBeam_PDK
Mustafa Hammood, 2024
"""

import numpy as np
import pya
import os
from SiEPIC.extend import to_itype
from SiEPIC.scripts import connect_pins_with_waveguide, connect_cell, export_layout
from SiEPIC.utils.layout import new_layout
from SiEPIC._globals import Python_Env
import siepic_ebeam_pdk as ebeam
from SiEPIC.verification import layout_check

export_type = "static"


class layout_bragg:
    def __init__(
        self,
        ly,
        cell,
        tech,
        cell_name,
        io,
        io_lib,
        taper,
        taper_lib,
        bragg,
        bragg_lib,
        ybranch,
        ybranch_lib,
        num_sweep,
        wavl,
        pol,
        label,
        layer_floorplan,
        layer_text,
        layer,
        number_of_periods,
        grating_period,
        wg_width,
        corrugation_width,
        sinusoidal,
        a,
        wg_type,
        wg_radius,
        io_pitch,
        wg_spacing,
        wg_turnleft,
        wg_turnright,
    ):
        # layout parameters
        self.ly = ly
        self.tech = tech
        self.cell = cell
        self.cell_name = cell_name
        self.io = io
        self.io_lib = io_lib
        self.taper = taper
        self.taper_lib = taper_lib
        self.bragg = bragg
        self.bragg_lib = bragg_lib
        self.ybranch = ybranch
        self.ybranch_lib = ybranch_lib
        self.num_sweep = num_sweep
        self.wavl = wavl
        self.pol = pol
        self.label = label
        self.layer_floorplan = layer_floorplan
        self.layer_text = layer_text
        self.layer = layer

        # pcell parameters
        self.number_of_periods = number_of_periods
        self.grating_period = grating_period  # µm
        self.wg_width = wg_width  # µm
        self.corrugation_width = corrugation_width  # µm
        self.sinusoidal = sinusoidal
        self.a = a

        # waveguide routing and placement parameters
        self.wg_type = wg_type
        self.wg_radius = wg_radius  # µm
        self.io_pitch = io_pitch  # µm
        self.wg_spacing = wg_spacing  # µm
        self.wg_turnleft = wg_turnleft  # additional left turn bias µm
        self.wg_turnright = wg_turnright  # additional right turn bias µm

    def make_dependent_params(self):
        """Define "dependent" waveguide routing variables."""
        self.route_up = 10  # µm
        self.device_io_space = self.wg_radius * 2.5 + 34  # µm
        self.io_column_space = 140  # µm
        self.device_column_space = 6.75 / 2  # µm

    def make_bragg(
        self,
        number_of_periods,
        grating_period,
        wg_width,
        corrugation_width,
        sinusoidal,
        a,
        layer,
    ):
        """Create the device PCell."""
        pcell_params = {
            "number_of_periods": number_of_periods,
            "grating_period": grating_period,
            "layer": self.tech["SiN"],
            "wg_width": wg_width,
            "corrugation_width": corrugation_width,
            "sinusoidal": sinusoidal,
        }
        return self.ly.create_cell(
            self.bragg, self.bragg_lib, pcell_params
        ).cell_index()

    def make_params(self):
        """Convert the pcell params to list of size self.num_sweep."""
        if type(self.number_of_periods) not in [list, np.ndarray]:
            self.number_of_periods = [self.number_of_periods] * self.num_sweep
        if type(self.grating_period) not in [list, np.ndarray]:
            self.grating_period = [self.grating_period] * self.num_sweep
        if type(self.wg_width) not in [list, np.ndarray]:
            self.wg_width = [self.wg_width] * self.num_sweep
        if type(self.corrugation_width) not in [list, np.ndarray]:
            self.corrugation_width = [self.corrugation_width] * self.num_sweep
        if type(self.sinusoidal) not in [list, np.ndarray]:
            self.sinusoidal = [self.sinusoidal] * self.num_sweep
        if type(self.a) not in [list, np.ndarray]:
            self.a = [self.a] * self.num_sweep

    def make(self):
        """Make the layout cell."""
        dbu = self.ly.dbu
        cell = self.cell.layout().create_cell(self.cell_name)
        cell_io = self.ly.create_cell(self.io, self.io_lib).cell_index()
        io_width = (
            self.ly.create_cell(self.io, self.io_lib).find_pins()[0][0].path.width
        )
        cell_ybranch = self.ly.create_cell(self.ybranch, self.ybranch_lib)
        cell_taper = self.ly.create_cell(
            self.taper,
            self.taper_lib,
            {
                "wg_width1": io_width * self.ly.dbu,
                "wg_width2": self.wg_width,
                "wg_length": 1.0,
                "silayer": self.tech["SiN"],
            },
        )
        width_ybranch = to_itype(cell_ybranch.bbox().width(), 1 / dbu)
        self.make_dependent_params()
        self.make_params()  # convert parameters to lists in case they weren't already

        insts_bragg = []
        insts_ybranch = []

        for i in range(self.num_sweep):
            if i % 2 == 0:
                # direct routing devices
                insts_io = []
                insts_taper = []
                cell_bragg = self.make_bragg(
                    self.number_of_periods[i],
                    self.grating_period[i],
                    self.wg_width[i],
                    self.corrugation_width[i],
                    self.sinusoidal[i],
                    self.a[i],
                    self.layer,
                )
                device_length = self.number_of_periods[i] * self.grating_period[i]
                x = (
                    -self.io_pitch - self.io_pitch / 4 + width_ybranch
                )  # starting coordinate for Ybranch + bragg
                y = i * self.device_column_space + self.device_io_space
                t = pya.Trans(pya.Trans.R0, to_itype(x, dbu), to_itype(y, dbu))
                insts_bragg.append(cell.insert(pya.CellInstArray(cell_bragg, t)))
                insts_ybranch.append(
                    connect_cell(insts_bragg[-1], "pin1", cell_ybranch, "opt1")
                )

                # measurement labels
                device_label = f"opt_in_{self.pol}_{self.wavl}_{self.label}"
                device_attributes = f"_{self.number_of_periods[i]}N{int(self.grating_period[i]*1e3)}nmPeriod{int(self.wg_width[i]*1e3)}nmW{int(self.corrugation_width[i]*1e3)}nmdW{self.a[i]}Apo{int(self.sinusoidal[i])}"
                text = device_label + device_attributes
                text_size = 1.5 / dbu
                # instantiate IOs
                x = -self.io_pitch - self.io_pitch / 4
                y = -i * self.io_column_space / 2
                t = pya.Trans(pya.Trans.R90, to_itype(x, dbu), to_itype(y, dbu))
                insts_io.append(cell.insert(pya.CellInstArray(cell_io, t)))
                insts_taper.append(
                    connect_cell(insts_io[-1], "opt1", cell_taper, "pin1")
                )
                t = pya.Trans(
                    pya.Trans.R90, to_itype(x + self.io_pitch, dbu), to_itype(y, dbu)
                )
                insts_io.append(cell.insert(pya.CellInstArray(cell_io, t)))
                insts_taper.append(
                    connect_cell(insts_io[-1], "opt1", cell_taper, "pin1")
                )
                t = pya.Trans(
                    pya.Trans.R90,
                    to_itype(x + 2 * self.io_pitch, dbu),
                    to_itype(y, dbu),
                )
                insts_io.append(cell.insert(pya.CellInstArray(cell_io, t)))
                insts_taper.append(
                    connect_cell(insts_io[-1], "opt1", cell_taper, "pin1")
                )

                # measurement text label on IO
                t = pya.Trans(
                    pya.Trans.R0, to_itype(-self.io_pitch / 4, dbu), to_itype(y, dbu)
                )
                io_text = pya.Text(text.replace(".", "p"), t)
                TextLayerN = cell.layout().layer(self.tech[self.layer_text])
                shape = cell.shapes(TextLayerN).insert(io_text)
                shape.text_size = text_size

                # connect IOs to devices
                # middle IO
                pt2_1 = self.wg_radius + self.wg_spacing
                pt2_2 = (
                    self.io_pitch
                    + self.wg_radius
                    + self.wg_turnleft
                    + i * self.wg_spacing * 2
                )
                turtle1 = [pt2_1, 90, pt2_2, 90]  # inflection points
                wg_io_device2 = connect_pins_with_waveguide(
                    insts_taper[1],
                    "pin2",
                    insts_ybranch[-1],
                    "opt2",
                    waveguide_type=self.wg_type,
                    turtle_A=turtle1,
                )  # center io
                # leftmost IO
                pt1_1 = pt2_1 - self.wg_spacing
                pt1_2 = pt2_2 - self.io_pitch + self.wg_spacing
                turtle1 = [pt1_1, 90, pt1_2, 90]  # inflection points
                wg_io_device1 = connect_pins_with_waveguide(
                    insts_taper[0],
                    "pin2",
                    insts_ybranch[-1],
                    "opt3",
                    waveguide_type=self.wg_type,
                    turtle_A=turtle1,
                )  # top io

                # rightmost IO
                pt3_1 = self.wg_radius + self.wg_spacing
                pt3_2 = (
                    self.io_pitch / 2
                    + self.wg_radius
                    + self.wg_turnright
                    + i * self.wg_spacing
                )
                if device_length - np.abs(x) > pt3_2:
                    pt3_2 = (
                        device_length
                        - np.abs(x)
                        + self.wg_radius
                        + self.wg_turnright
                        + i * self.wg_spacing
                    )
                    print("long device exception handled")
                turtle1 = [pt3_1, -90, pt3_2, -90]  # inflection points
                wg_io_device3 = connect_pins_with_waveguide(
                    insts_taper[2],
                    "pin2",
                    insts_bragg[-1],
                    "opt2",
                    waveguide_type=self.wg_type,
                    turtle_A=turtle1,
                )  # bottom io

            # backwards routing devices (interdigitated io layout, not used in SiN, too tight)
            """
            else:
                # instantiate IOs
                x = -self.io_pitch + self.io_pitch/2 -self.io_pitch/4
                y = -(i-1)*self.io_column_space/2
                t = pya.Trans(pya.Trans.R90, to_itype(x, dbu), to_itype(y, dbu))
                insts_io.append(cell.insert(pya.CellInstArray(cell_io, t)))
                t = pya.Trans(pya.Trans.R90, to_itype(
                    x + self.io_pitch, dbu), to_itype(y, dbu))
                insts_io.append(cell.insert(pya.CellInstArray(cell_io, t)))
                t = pya.Trans(pya.Trans.R90, to_itype(
                    x + 2*self.io_pitch, dbu), to_itype(y, dbu))
                insts_io.append(cell.insert(pya.CellInstArray(cell_io, t)))

                # measurement text label on IO
                t = pya.Trans(pya.Trans.R0, to_itype(self.io_pitch/4, dbu), to_itype(y, dbu))
                io_text = pya.Text(text.replace('.', 'p'), t)
                TextLayerN = cell.layout().layer(self.tech[self.layer_text])
                shape = cell.shapes(TextLayerN).insert(io_text)
                shape.text_size = text_size

                # connect IOs to devices
                # middle IO
                pt2_1x = pt2_1
                pt2_2x = self.io_pitch/4
                pt2_3x = self.io_column_space*3/4 + self.wg_spacing
                pt2_4x = pt2_2 + self.io_pitch/4 + 3*self.wg_spacing
                turtle1 = [pt2_1x, 90, pt2_2x, 90, pt2_3x, -90, pt2_4x, -90]  # inflection points
                wg_io_device2 = connect_pins_with_waveguide(
                    insts_io[1], 'opt1', insts_ybranch[-1], 'opt3', waveguide_type=self.wg_type, turtle_A=turtle1)  # top io

                # leftmost IO
                pt1_1x = self.wg_radius
                pt1_2x = pt2_2x
                pt1_3x = pt2_3x - 2*self.wg_spacing
                pt1_4x = pt1_2 + self.io_pitch/4 + self.wg_spacing
                turtle1 = [pt1_1x, 90, pt1_2x, 90, pt1_3x, -90, pt1_4x, -90]  # inflection points
                wg_io_device1 = connect_pins_with_waveguide(
                    insts_io[0], 'opt1', insts_ybranch[-1], 'opt2', waveguide_type=self.wg_type, turtle_A=turtle1)  # top io


                pt3_1x = pt3_1 - self.wg_spacing
                pt3_2x = pt3_2 - self.io_pitch/2 + self.wg_spacing
                turtle1 = [pt3_1x, -90, pt3_2x, -90]  # inflection points
                wg_io_device3 = connect_pins_with_waveguide(
                    insts_io[2], 'opt1', insts_bragg[-1], 'opt2', waveguide_type=self.wg_type, turtle_A=turtle1)  # bottom io
            """

        self.bragg_cell = cell

    def add_to_layout(self, cell):
        t = pya.Trans(pya.Trans.R270, 0, 0)
        x = -pya.CellInstArray(self.bragg_cell.cell_index(), t).bbox(self.ly).p1.x
        y = -pya.CellInstArray(self.bragg_cell.cell_index(), t).bbox(self.ly).p1.y
        t = pya.Trans(pya.Trans.R270, x, y)
        cell.insert(pya.CellInstArray(self.bragg_cell.cell_index(), t))
        FloorplanLayer = self.bragg_cell.layout().layer(self.tech[self.layer_floorplan])
        cell.shapes(FloorplanLayer).insert(
            pya.Box(
                0, 0, self.bragg_cell.bbox().height(), self.bragg_cell.bbox().width()
            )
        )


if __name__ == "__main__":
    cell, ly = new_layout(
        "EBeam", "doe_bragg_grating_sin_te1550", GUI=True, overwrite=True
    )

    layout = layout_bragg(
        ly=ly,
        tech=ly.TECHNOLOGY,
        cell=cell,
        cell_name="doe_bragg_grating_sin_te1550",
        number_of_periods=300,
        grating_period=np.linspace(0.47, 0.505, 30),
        wg_width=0.8,
        corrugation_width=0.12,
        sinusoidal=False,
        a=0,
        wg_type="SiN Strip TE 1550 nm, w=800 nm",
        wg_radius=75,
        io_pitch=127,
        wg_spacing=3,
        wg_turnleft=10 + 36,
        wg_turnright=-50 + 37,
        layer_floorplan="FloorPlan",
        layer_text="Text",
        layer="SiN",
        io="GC_SiN_TE_1550_8degOxide_BB",
        io_lib="EBeam-SiN",
        taper="ebeam_taper_te1550",
        taper_lib="EBeam",
        bragg="ebeam_bragg_te1550",
        bragg_lib="EBeam",
        ybranch="ebeam_sin_dream_splitter1x2_te1550",
        ybranch_lib="EBeam-Dream",
        num_sweep=30,
        wavl=1550,
        pol="TE",
        label="device_bragg",
    )

    layout.make()
    layout.add_to_layout(cell)

    # Verify
    path = os.path.dirname(os.path.realpath(__file__))
    filename, extension = os.path.splitext(os.path.basename(__file__))
    file_lyrdb = os.path.join(path, filename + ".lyrdb")
    num_errors = layout_check(cell=cell, verbose=False, GUI=True, file_rdb=file_lyrdb)
    print("Number of errors: %s" % num_errors)

    if export_type == "static":
        file_out = export_layout(
            cell, path, filename, relative_path="..", format="oas", screenshot=True
        )
    else:
        file_out = os.path.join(path, "..", filename + ".oas")
        ly.write(file_out)
    # Display the layout in KLayout, using KLayout Package "klive", which needs to be installed in the KLayout Application
    if Python_Env == "Script":
        from SiEPIC.utils import klive

        klive.show(
            file_out,
            lyrdb_filename=file_lyrdb,
            technology=ly.TECHNOLOGY["technology_name"],
        )

# %%
