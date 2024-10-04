import pya
from pya import *
from SiEPIC.utils import get_technology_by_name


class ebeam_dc_halfring_arc(pya.PCellDeclarationHelper):
    """
    The PCell declaration for the Directional Coupler Half Ring with Arc for the bus waveguide.
    Consists of a half-ring with 1 waveguide.
    """

    def __init__(self):
        # Important: initialize the super class
        super(ebeam_dc_halfring_arc, self).__init__()
        TECHNOLOGY = get_technology_by_name("EBeam")

        # declare the parameters
        self.param("silayer", self.TypeLayer, "Si Layer", default=TECHNOLOGY["Si"])
        self.param("r", self.TypeDouble, "Radius", default=10)
        self.param("w", self.TypeDouble, "Waveguide Width", default=0.5)
        self.param("g", self.TypeDouble, "Gap", default=0.2)
        self.param("Lc", self.TypeDouble, "Coupler Length", default=0.0)
        self.param(
            "pinrec", self.TypeLayer, "PinRec Layer", default=TECHNOLOGY["PinRec"]
        )
        self.param(
            "devrec", self.TypeLayer, "DevRec Layer", default=TECHNOLOGY["DevRec"]
        )
        self.param("textl", self.TypeLayer, "Text Layer", default=LayerInfo(10, 0))

    def display_text_impl(self):
        # Provide a descriptive text for the cell
        return (
            "ebeam_dc_halfring_arc(R="
            + ("%.3f" % self.r)
            + ",g="
            + ("%g" % (1000 * self.g))
            + ")"
        )

    def can_create_from_shape_impl(self):
        return False

    def produce_impl(self):
        # This is the main part of the implementation: create the layout

        from math import pi, cos, sin
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

        w = int(round(self.w / dbu))
        r = int(round(self.r / dbu))
        g = int(round(self.g / dbu))
        Lc = int(round(self.Lc / dbu))

        # draw the half-circle
        x = 0
        y = r + w + g

        self.cell.shapes(LayerSiN).insert(arc_wg_xy(x - Lc / 2, y, r, w, 180, 270))
        self.cell.shapes(LayerSiN).insert(arc_wg_xy(x + Lc / 2, y, r, w, 270, 360))

        # Pins on the top side:
        pin = Path(
            [
                Point(-r - Lc / 2, y - PIN_LENGTH / 2),
                Point(-r - Lc / 2, y + PIN_LENGTH / 2),
            ],
            w,
        )
        shapes(LayerPinRecN).insert(pin)
        t = Trans(Trans.R0, -r - Lc / 2, y)
        text = Text("pin2", t)
        shape = shapes(LayerPinRecN).insert(text)
        shape.text_size = 0.4 / dbu

        pin = Path(
            [
                Point(r + Lc / 2, y - PIN_LENGTH / 2),
                Point(r + Lc / 2, y + PIN_LENGTH / 2),
            ],
            w,
        )
        shapes(LayerPinRecN).insert(pin)
        t = Trans(Trans.R0, r + Lc / 2, y)
        text = Text("pin4", t)
        shape = shapes(LayerPinRecN).insert(text)
        shape.text_size = 0.4 / dbu

        if Lc > 0:
            wg1 = Box(-Lc / 2, -w / 2 + w + g, Lc / 2, w / 2 + w + g)
            shapes(LayerSiN).insert(wg1)

        # Create the waveguide
        if Lc > 0:
            wg1 = Box(-Lc / 2, -w / 2, Lc / 2, w / 2)
            shapes(LayerSiN).insert(wg1)

        dc_angle = 30.0
        self.cell.shapes(LayerSiN).insert(
            arc_wg_xy(Lc / 2, -r, r, w, 90 - dc_angle, 90)
        )
        self.cell.shapes(LayerSiN).insert(
            arc_wg_xy(-Lc / 2, -r, r, w, 90, 90 + dc_angle)
        )
        y_bottom = round(-2 * (1 - cos(dc_angle / 180.0 * pi)) * r)
        x_bottom = round(2 * sin(dc_angle / 180.0 * pi) * r)
        t = Trans(Trans.R0, -x_bottom - Lc / 2, y_bottom + r)
        self.cell.shapes(LayerSiN).insert(
            arc_wg(r, w, -90, -90 + dc_angle).transformed(t)
        )
        t = Trans(Trans.R0, x_bottom + Lc / 2, y_bottom + r)
        self.cell.shapes(LayerSiN).insert(
            arc_wg(r, w, -90 - dc_angle, -90).transformed(t)
        )

        wg1 = Box(
            -r - w / 2 - w - Lc / 2,
            y_bottom - w / 2,
            -x_bottom - Lc / 2,
            y_bottom + w / 2,
        )
        shapes(LayerSiN).insert(wg1)
        wg1 = Box(
            x_bottom + Lc / 2,
            y_bottom - w / 2,
            r + w / 2 + w + Lc / 2,
            y_bottom + w / 2,
        )
        shapes(LayerSiN).insert(wg1)

        # Pins on the bus waveguide side:
        pin = Path(
            [
                Point(-r - w / 2 - w + PIN_LENGTH / 2 - Lc / 2, y_bottom),
                Point(-r - w / 2 - w - PIN_LENGTH / 2 - Lc / 2, y_bottom),
            ],
            w,
        )
        shapes(LayerPinRecN).insert(pin)
        text = Text("pin1", Trans(Trans.R0, -r - w / 2 - w - Lc / 2, y_bottom))
        shape = shapes(LayerPinRecN).insert(text)
        shape.text_size = 0.4 / dbu

        pin = Path(
            [
                Point(r + w / 2 + w - PIN_LENGTH / 2 + Lc / 2, y_bottom),
                Point(r + w / 2 + w + PIN_LENGTH / 2 + Lc / 2, y_bottom),
            ],
            w,
        )
        shapes(LayerPinRecN).insert(pin)
        text = Text("pin3", Trans(Trans.R0, r + w / 2 + w + Lc / 2, y_bottom))
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
            -r - w / 2 - w - Lc / 2, y_bottom - w / 2 - w, r + w / 2 + w + Lc / 2, y
        )
        shapes(LayerDevRecN).insert(dev)

        # Compact model information
        t = Trans(Trans.R0, r / 4, 0)
        text = Text("Lumerical_INTERCONNECT_library=Design kits/ebeam_v1.2", t)
        shape = shapes(LayerDevRecN).insert(text)
        shape.text_size = self.r * 0.017 / dbu
        t = Trans(Trans.R0, r / 4, r / 4)
        text = Text("Component=ebeam_dc_halfring_arc_te1550", t)
        shape = shapes(LayerDevRecN).insert(text)
        shape.text_size = self.r * 0.017 / dbu
        t = Trans(Trans.R0, r / 4, r / 2)
        text = Text(
            "Spice_param:wg_width=%.3fu gap=%.3fu radius=%.3fu Lc=%.3fu"
            % (self.w, self.g, self.r, self.Lc),
            t,
        )
        shape = shapes(LayerDevRecN).insert(text)
        shape.text_size = self.r * 0.017 / dbu

        # print("Done drawing the layout for - ebeam_dc_halfring_arc: %.3f-%g" % ( self.r, self.g) )
