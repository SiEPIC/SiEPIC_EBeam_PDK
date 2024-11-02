import pya
import math
from pya import *


class ebeam_dream_PWB_edge_couplers_BB(pya.PCellDeclarationHelper):
    """
    The PCell declaration for the ebeam_dream_PWB_edge_couplers_BB

    Authors: Dream Photonics
    """

    def __init__(self):
        # Important: initialize the super class
        super(ebeam_dream_PWB_edge_couplers_BB, self).__init__()
        from SiEPIC.utils import get_technology_by_name

        self.technology_name = "EBeam"
        TECHNOLOGY = get_technology_by_name(self.technology_name)

        # declare the parameters
        self.param(
            "num_channels", self.TypeInt, "Number of Channels (1 - 16)", default=1
        )
        p = self.param(
            "center_wavelength",
            self.TypeList,
            "Center Wavelength of Operation [nm]",
            default="1550",
        )
        p.add_choice("1550 nm", "1550")
        p.add_choice("1310 nm", "1310")

        # declare the layers
        self.param("silayer", self.TypeLayer, "Si Layer", default=TECHNOLOGY["Si"])
        self.param(
            "waveguidelayer",
            self.TypeLayer,
            "Waveguide Layer",
            default=TECHNOLOGY["Waveguide"],
        )
        self.param(
            "pinrec", self.TypeLayer, "PinRec Layer", default=TECHNOLOGY["PinRec"]
        )
        self.param(
            "devrec", self.TypeLayer, "DevRec Layer", default=TECHNOLOGY["DevRec"]
        )
        self.param(
            "fibertarget",
            self.TypeLayer,
            "Fiber Target Layer",
            default=TECHNOLOGY["FbrTgt"],
        )
        self.param("textl", self.TypeLayer, "Text Layer", default=TECHNOLOGY["Text"])
        self.param("bb", self.TypeLayer, "BB Layer", default=TECHNOLOGY["BlackBox"])

    def can_create_from_shape_impl(self):
        return False

    def produce(self, layout, layers, parameters, cell):
        # This is the main part of the implementation: create the layout

        self.cell = cell
        self._param_values = parameters
        self.layout = layout

        # import neccessary libraries
        from SiEPIC._globals import PIN_LENGTH as pin_length
        from SiEPIC.extend import to_itype

        # fetch the parameters
        dbu = self.layout.dbu
        ly = self.layout
        shapes = self.cell.shapes

        LayerSiN = ly.layer(self.silayer)
        LayerPinRecN = ly.layer(self.pinrec)
        LayerDevRecN = ly.layer(self.devrec)
        LayerFbrTgtN = ly.layer(self.fibertarget)
        LayerWN = ly.layer(self.waveguidelayer)
        LayerTEXTN = ly.layer(self.textl)
        LayerBBN = ly.layer(self.bb)

        w_tip = to_itype(0.100, dbu)
        l_taper = to_itype(65, dbu)
        num_channels = self.num_channels
        offset = to_itype(0, dbu)
        pitch = to_itype(127, dbu)
        Lw2 = to_itype(15, dbu)
        Lw3 = Lw2 + to_itype(20, dbu)
        wavelength = int(self.center_wavelength)
        waveguide_type = "Strip TE 1550 nm, w=500 nm"

        if num_channels < 1:
            num_channels = 1
        if num_channels > 16:
            num_channels = 16

        if wavelength == 1310:
            waveguide_type = "Strip TE 1310 nm, w=350 nm"
            w_waveguide = to_itype(0.350, dbu)
        elif wavelength == 1550:
            waveguide_type = "Strip TE 1550 nm, w=500 nm"
            w_waveguide = to_itype(0.500, dbu)

        def circle(x, y, r):
            npts = 180
            theta = 2 * math.pi / npts
            pts = []
            for i in range(0, npts):
                pts.append(
                    Point.from_dpoint(
                        pya.DPoint(
                            (x + r * math.cos(i * theta)) / 1,
                            (y + r * math.sin(i * theta)) / 1,
                        )
                    )
                )
            return pts

        # draw one loopback device
        for ref_loop in range(2):
            # draw fibre target circle
            align_circle = circle(offset, -pitch * (ref_loop + 1), 2 / dbu)

            # place fibre target circle
            shapes(LayerFbrTgtN).insert(Polygon(align_circle))

        # create waveguide to for loopback
        loopback_path = DPath(
            [
                DPoint(0, -127),
                DPoint((offset + l_taper + Lw2) * dbu + 15, -127),
                DPoint((offset + l_taper + Lw2) * dbu + 15, -254),
                DPoint(0, -254),
            ],
            0.5,
        )
        self.layout.technology_name = (
            self.technology_name
        )  # required otherwise "create_cell" doesn't load
        pcell = self.layout.create_cell(
            "Waveguide",
            self.technology_name,
            {"path": loopback_path, "waveguide_type": waveguide_type},
        )
        t = Trans(Trans.R0, 0, 0)
        self.cell.copy(pcell, LayerSiN, LayerBBN)
        wg = self.cell.insert(CellInstArray(pcell.cell_index(), t))
        wg.flatten()
        self.cell.clear(LayerDevRecN)
        self.cell.clear(LayerPinRecN)
        self.cell.clear(LayerSiN)
        self.cell.clear(LayerWN)

        ##########################################################################################################################################################################
        # draw N tapers
        for n_ch in range(int(num_channels)):
            # draw the taper
            taper_pts = [
                Point(0, -w_waveguide / 2 + pitch * n_ch),
                Point(0, w_waveguide / 2 + pitch * n_ch),
                Point(offset + l_taper + Lw3, w_waveguide / 2 + pitch * n_ch),
                Point(offset + l_taper + Lw3, -w_waveguide / 2 + pitch * n_ch),
            ]

            # place the taper
            shapes(LayerBBN).insert(Polygon(taper_pts))

            # draw and place pin on the waveguide:
            x = offset + l_taper + Lw3
            t = Trans(Trans.R0, x, pitch * n_ch)
            pin = Path(
                [Point(-pin_length / 2, 0), Point(pin_length / 2, 0)], w_waveguide
            )
            pin_t = pin.transformed(t)
            shapes(LayerPinRecN).insert(pin_t)
            text = Text(f"opt_{n_ch+1}", t)
            shape = shapes(LayerPinRecN).insert(text)
            shape.text_size = 4 / dbu

            # draw fibre target circle
            align_circle = circle(offset, pitch * n_ch, 2 / dbu)

            # place fibre target circle
            shapes(LayerFbrTgtN).insert(Polygon(align_circle))

        # draw devrec box
        devrec_pts = [
            Point(0, pitch * n_ch + 20 / dbu),
            Point(x, pitch * n_ch + 20 / dbu),
            Point(x, -pitch * 2 - 5 / dbu),
            Point(0, -pitch * 2 - 5 / dbu),
        ]

        # place devrec box
        shapes(LayerDevRecN).insert(Polygon(devrec_pts))

        # edge of chip text
        t = Trans(Trans.R0, 0, -110 / dbu)
        text = Text("<- Edge of chip", t)
        shape = shapes(LayerTEXTN).insert(text)
        shape.text_size = 6 / dbu

        # BB description
        t = Trans(Trans.R0, 0, -95 / dbu)
        text = Text(
            "  Number of Channel(s): "
            + str(num_channels)
            + "\n  Center Wavelength: "
            + str(wavelength)
            + " nm",
            t,
        )
        shape = shapes(LayerTEXTN).insert(text)
        shape.text_size = 4 / dbu

        # BB description
        t = Trans(Trans.R0, 20 / dbu, -200 / dbu)
        text = Text("    PWB reference  ->\nloopback structure", t)
        shape = shapes(LayerTEXTN).insert(text)
        shape.text_size = 4 / dbu

        # draw DP BB logo
        import os

        dir_path = os.path.realpath(__file__)
        filename = os.path.join(dir_path, "DP_Edge_coupler_for_PWB_BB_logo.gds")
        tech_name = "EBeam"
        ly2 = pya.Layout()
        ly2.read(filename)
        top_cell = ly2.top_cell()
        top_cell.flatten(True)
        # top_cell.Trans(Trans.R0,0,-192)
        # self.cell.copy_shapes(top_cell)
        self.cell.copy_shapes(top_cell)

    def display_text_impl(self):
        # Provide a descriptive text for the cell
        return "ebeam_dream_PWB_edge_couplers_BB"
