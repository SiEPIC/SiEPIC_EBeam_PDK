import pya
from pya import *
from SiEPIC.utils import get_technology_by_name


class DirectionalCoupler_SeriesRings(pya.PCellDeclarationHelper):
    """
    The PCell declaration for the DirectionalCoupler_SeriesRings.

    """

    def __init__(self):
        # Important: initialize the super class
        super(DirectionalCoupler_SeriesRings, self).__init__()
        TECHNOLOGY = get_technology_by_name("EBeam")

        # declare the parameters
        self.param("silayer", self.TypeLayer, "Si Layer", default=TECHNOLOGY["Si"])
        self.param("r2", self.TypeDouble, "Radius of Upper Ring", default=3)
        self.param("r1", self.TypeDouble, "Radius of Lower Ring", default=3)
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
            "DirectionalCoupler_SeriesRings(R1="
            + ("%.3f" % self.r1)
            + ",R2="
            + ("%.3f" % self.r2)
            + ",g="
            + ("%g" % (1000 * self.g))
            + ")"
        )

    def can_create_from_shape_impl(self):
        return False

    def produce_impl(self):
        # This is the main part of the implementation: create the layout

        from SiEPIC._globals import PIN_LENGTH as pin_length
        from SiEPIC.utils import arc_wg_xy

        # fetch the parameters
        dbu = self.layout.dbu
        ly = self.layout
        shapes = self.cell.shapes

        LayerSi = self.silayer
        LayerSiN = ly.layer(LayerSi)
        LayerPinRecN = ly.layer(self.pinrec)
        LayerDevRecN = ly.layer(self.devrec)
        TextLayerN = ly.layer(self.textl)

        w = int(round(self.w / dbu))
        r1 = int(round(self.r1 / dbu))
        r2 = int(round(self.r2 / dbu))
        g = int(round(self.g / dbu))
        Lc = int(round(self.Lc / dbu))

        # draw the half-circle
        x = 0
        y = r1 + r2 + g + w
        self.cell.shapes(LayerSiN).insert(arc_wg_xy(x - Lc / 2, y, r2, w, 180, 270))
        self.cell.shapes(LayerSiN).insert(arc_wg_xy(x + Lc / 2, y, r2, w, 270, 360))

        # Create the pins, as short paths:

        # Pins on the top side:
        pin = Path(
            [
                Point(-r2 - Lc / 2, y - pin_length / 2),
                Point(-r2 - Lc / 2, y + pin_length / 2),
            ],
            w,
        )
        shapes(LayerPinRecN).insert(pin)
        t = Trans(Trans.R0, -r2 - Lc / 2, y)
        text = Text("pin2", t)
        shape = shapes(LayerPinRecN).insert(text)
        shape.text_size = 0.4 / dbu

        pin = Path(
            [
                Point(r2 + Lc / 2, y - pin_length / 2),
                Point(r2 + Lc / 2, y + pin_length / 2),
            ],
            w,
        )
        shapes(LayerPinRecN).insert(pin)
        t = Trans(Trans.R0, r2 + Lc / 2, y)
        text = Text("pin4", t)
        shape = shapes(LayerPinRecN).insert(text)
        shape.text_size = 0.4 / dbu

        if Lc > 0:
            wg1 = Box(-Lc / 2, w + w / 2 + g + r1, Lc / 2, w / 2 + g + r1)
            shapes(LayerSiN).insert(wg1)

        y = 0
        self.cell.shapes(LayerSiN).insert(arc_wg_xy(x - Lc / 2, y, r1, w, 90, 180))
        self.cell.shapes(LayerSiN).insert(arc_wg_xy(x + Lc / 2, y, r1, w, 0, 90))

        # Pins on the lower side:
        pin = Path(
            [
                Point(-r1 - Lc / 2, y + pin_length / 2),
                Point(-r1 - Lc / 2, y - pin_length / 2),
            ],
            w,
        )
        shapes(LayerPinRecN).insert(pin)
        t = Trans(Trans.R0, -r1 - Lc / 2, y)
        text = Text("pin1", t)
        shape = shapes(LayerPinRecN).insert(text)
        shape.text_size = 0.4 / dbu

        pin = Path(
            [
                Point(r1 + Lc / 2, y + pin_length / 2),
                Point(r1 + Lc / 2, y - pin_length / 2),
            ],
            w,
        )
        shapes(LayerPinRecN).insert(pin)
        t = Trans(Trans.R0, r1 + Lc / 2, y)
        text = Text("pin3", t)
        shape = shapes(LayerPinRecN).insert(text)
        shape.text_size = 0.4 / dbu

        if Lc > 0:
            wg1 = Box(-Lc / 2, r1 - w / 2, Lc / 2, w / 2 + r1)
            shapes(LayerSiN).insert(wg1)

        if r1 > r2:
            r = r1
        else:
            r = r2

        # Create the device recognition layer -- make it 1 * wg_width away from the waveguides.
        dev = Box(-r - w / 2 - w - Lc / 2, r1 + r2 + g + w, r + w / 2 + w + Lc / 2, y)
        shapes(LayerDevRecN).insert(dev)

        # Compact model information
        t = Trans(Trans.R0, ((r1 + r2) / 2) / 4, 0)
        text = Text("Lumerical_INTERCONNECT_library=Design kits/ebeam_v1.2", t)
        shape = shapes(LayerDevRecN).insert(text)
        shape.text_size = r * 0.017
        t = Trans(Trans.R0, ((r1 + r2) / 2) / 4, ((r1 + r2) / 2) / 4)
        text = Text("Component=ebeam_dc_seriesrings", t)
        shape = shapes(LayerDevRecN).insert(text)
        shape.text_size = r * 0.017
        t = Trans(Trans.R0, ((r1 + r2) / 2) / 4, ((r1 + r2) / 2) / 2)
        #  text = Text ('Spice_param:wg_width=%.3fu gap="%s" radius="%s"'% ( w, g,int( r)), t)
        text = Text(
            "Spice_param:wg_width=%.3fu gap=%.3fu radius1=%.3fu radius2=%.3fu"
            % (self.w, self.g, int(self.r1), int(self.r2)),
            t,
        )
        shape = shapes(LayerDevRecN).insert(text)
        shape.text_size = r * 0.017

        # print("Done drawing the layout for - DirectionalCoupler_SeriesRings: %.3f-%.3f-%g" % ( self.r1, self.r2, self.g) )
