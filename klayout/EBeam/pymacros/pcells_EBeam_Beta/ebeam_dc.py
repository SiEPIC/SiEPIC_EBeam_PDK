import pya
from pya import *
from SiEPIC.utils import get_technology_by_name


class ebeam_dc(pya.PCellDeclarationHelper):
    """
    The PCell declaration for the Directional Coupler
    by Lukas Chrostowski, 2018/09
    compact model in INTERCONNECT based on:
     - https://kx.lumerical.com/t/lcml-directional-coupler-based-on-lookup-table-lcml-dc-strip-1550-lookuptable/2094
     - only parameterized for Lc, for the 500 x 220 nm waveguide with 200 nm gap, and 5 micron radius
     could be improved:
     - https://kx.lumerical.com/t/lcml-directional-coupler-based-on-analytical-functions-lcml-dc-strip-1550-analytical/2091

    """

    def __init__(self):
        # Important: initialize the super class
        super(ebeam_dc, self).__init__()
        TECHNOLOGY = get_technology_by_name("EBeam")

        # declare the parameters
        self.param("Lc", self.TypeDouble, "Coupler Length", default=10.0)
        self.param("r", self.TypeDouble, "Radius", default=10)
        self.param("w", self.TypeDouble, "Waveguide Width", default=0.5)
        self.param("g", self.TypeDouble, "Gap", default=0.2)
        self.param("silayer", self.TypeLayer, "Si Layer", default=TECHNOLOGY["Si"])
        self.param(
            "pinrec", self.TypeLayer, "PinRec Layer", default=TECHNOLOGY["PinRec"]
        )
        self.param(
            "devrec", self.TypeLayer, "DevRec Layer", default=TECHNOLOGY["DevRec"]
        )
        self.param("textl", self.TypeLayer, "Text Layer", default=LayerInfo(10, 0))

    def display_text_impl(self):
        # Provide a descriptive text for the cell
        return "ebeam_dc(Lc=" + ("%.3f" % self.Lc) + ")"

    def can_create_from_shape_impl(self):
        return False

    def produce_impl(self):
        # This is the main part of the implementation: create the layout

        # Fixed PCell parameters
        port_spacing = 2000  # spacing of the two ports, determines the angle required by the s-bend.

        from math import pi, cos, sin, acos
        from SiEPIC.utils import arc_wg, arc_wg_xy
        from SiEPIC._globals import PIN_LENGTH

        # fetch the parameters
        dbu = self.layout.dbu
        ly = self.layout
        shapes = self.cell.shapes
        LayerSiN = ly.layer(self.silayer)
        LayerPinRecN = ly.layer(self.pinrec)
        LayerDevRecN = ly.layer(self.devrec)
        TextLayerN = ly.layer(self.textl)

        Lc = int(round(self.Lc / dbu))
        w = int(round(self.w / dbu))
        r = int(round(self.r / dbu))
        g = int(round(self.g / dbu))

        # Create the parallel waveguides
        if Lc > 0:
            wg1 = Box(-Lc / 2, -w / 2 + (w + g) / 2, Lc / 2, w / 2 + (w + g) / 2)
            shapes(LayerSiN).insert(wg1)
            wg1 = Box(-Lc / 2, -w / 2 - (w + g) / 2, Lc / 2, w / 2 - (w + g) / 2)
            shapes(LayerSiN).insert(wg1)

        dc_angle = acos((r - abs(port_spacing / 2)) / r) * 180 / pi

        # bottom S-bends
        self.cell.shapes(LayerSiN).insert(
            arc_wg_xy(Lc / 2, -r - (w + g) / 2, r, w, 90 - dc_angle, 90)
        )
        self.cell.shapes(LayerSiN).insert(
            arc_wg_xy(-Lc / 2, -r - (w + g) / 2, r, w, 90, 90 + dc_angle)
        )
        y_bottom = round(-2 * (1 - cos(dc_angle / 180.0 * pi)) * r) - (w + g) / 2
        x_bottom = round(2 * sin(dc_angle / 180.0 * pi) * r)
        t = Trans(Trans.R0, -x_bottom - Lc / 2, y_bottom + r)
        self.cell.shapes(LayerSiN).insert(
            arc_wg(r, w, -90, -90 + dc_angle).transformed(t)
        )
        t = Trans(Trans.R0, x_bottom + Lc / 2, y_bottom + r)
        self.cell.shapes(LayerSiN).insert(
            arc_wg(r, w, -90 - dc_angle, -90).transformed(t)
        )

        # top S-bends
        self.cell.shapes(LayerSiN).insert(
            arc_wg_xy(Lc / 2, r + (w + g) / 2, r, w, 270, 270 + dc_angle)
        )
        self.cell.shapes(LayerSiN).insert(
            arc_wg_xy(-Lc / 2, r + (w + g) / 2, r, w, 270 - dc_angle, 270)
        )
        y_top = round(2 * (1 - cos(dc_angle / 180.0 * pi)) * r) + (w + g) / 2
        x_top = round(2 * sin(dc_angle / 180.0 * pi) * r)
        t = Trans(Trans.R0, -x_top - Lc / 2, y_top - r)
        self.cell.shapes(LayerSiN).insert(
            arc_wg(r, w, 90 - dc_angle, 90).transformed(t)
        )
        t = Trans(Trans.R0, x_top + Lc / 2, y_top - r)
        self.cell.shapes(LayerSiN).insert(
            arc_wg(r, w, 90, 90 + dc_angle).transformed(t)
        )

        # Pins on the bottom waveguide side:
        pin = Path(
            [
                Point(-x_bottom + PIN_LENGTH / 2 - Lc / 2, y_bottom),
                Point(-x_bottom - PIN_LENGTH / 2 - Lc / 2, y_bottom),
            ],
            w,
        )
        shapes(LayerPinRecN).insert(pin)
        text = Text("pin1", Trans(Trans.R0, -x_bottom - Lc / 2, y_bottom))
        shape = shapes(LayerPinRecN).insert(text)
        shape.text_size = 0.4 / dbu

        pin = Path(
            [
                Point(x_bottom - PIN_LENGTH / 2 + Lc / 2, y_bottom),
                Point(x_bottom + PIN_LENGTH / 2 + Lc / 2, y_bottom),
            ],
            w,
        )
        shapes(LayerPinRecN).insert(pin)
        text = Text("pin3", Trans(Trans.R0, x_bottom + Lc / 2, y_bottom))
        shape = shapes(LayerPinRecN).insert(text)
        shape.text_size = 0.4 / dbu

        # Pins on the top waveguide side:
        pin = Path(
            [
                Point(-x_bottom + PIN_LENGTH / 2 - Lc / 2, y_top),
                Point(-x_bottom - PIN_LENGTH / 2 - Lc / 2, y_top),
            ],
            w,
        )
        shapes(LayerPinRecN).insert(pin)
        text = Text("pin2", Trans(Trans.R0, -x_bottom - Lc / 2, y_top))
        shape = shapes(LayerPinRecN).insert(text)
        shape.text_size = 0.4 / dbu

        pin = Path(
            [
                Point(x_bottom - PIN_LENGTH / 2 + Lc / 2, y_top),
                Point(x_bottom + PIN_LENGTH / 2 + Lc / 2, y_top),
            ],
            w,
        )
        shapes(LayerPinRecN).insert(pin)
        text = Text("pin4", Trans(Trans.R0, x_bottom + Lc / 2, y_top))
        shape = shapes(LayerPinRecN).insert(text)
        shape.text_size = 0.4 / dbu

        # Merge all the waveguide shapes, to avoid any small gaps
        layer_temp = self.layout.layer(LayerInfo(913, 0))
        shapes_temp = self.cell.shapes(layer_temp)
        ShapeProcessor().merge(
            self.layout, self.cell, LayerSiN, shapes_temp, True, 0, True, True
        )
        self.cell.shapes(LayerSiN).clear()
        shapes_SiN = self.cell.shapes(LayerSiN)
        ShapeProcessor().merge(
            self.layout, self.cell, layer_temp, shapes_SiN, True, 0, True, True
        )
        self.cell.shapes(layer_temp).clear()

        # Create the device recognition layer -- make it 1 * wg_width away from the waveguides.
        dev = Box(
            -x_bottom - Lc / 2,
            y_bottom - w / 2 - w,
            x_bottom + Lc / 2,
            y_top + w / 2 + w,
        )
        shapes(LayerDevRecN).insert(dev)

        # Compact model information
        t = Trans(Trans.R0, 0, -w)
        text = Text("Lumerical_INTERCONNECT_library=Design kits/ebeam_v1.2", t)
        shape = shapes(LayerDevRecN).insert(text)
        shape.text_size = r * 0.017
        t = Trans(Trans.R0, 0, 0)
        text = Text("Component=NO_MODEL", t)
        shape = shapes(LayerDevRecN).insert(text)
        shape.text_size = r * 0.017
        t = Trans(Trans.R0, 0, w)
        text = Text(
            "Spice_param:wg_width=%.3fu gap=%.3fu radius=%.3fu Lc=%.3fu"
            % (w * dbu, g * dbu, r * dbu, self.Lc),
            t,
        )
        shape = shapes(LayerDevRecN).insert(text)
        shape.text_size = r * 0.017

        # print("Done drawing the layout for - ebeam_dc: %.3f" % ( self.Lc) )
