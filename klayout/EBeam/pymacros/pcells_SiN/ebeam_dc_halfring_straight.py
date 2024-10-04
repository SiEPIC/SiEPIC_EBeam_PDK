import pya
from pya import *


class ebeam_dc_halfring_straight(pya.PCellDeclarationHelper):
    """
    The PCell declaration for the ebeam_dc_halfring_straight.
    Consists of a half-ring with 1 waveguides.
    """

    def __init__(self):
        # Important: initialize the super class
        super(ebeam_dc_halfring_straight, self).__init__()
        from SiEPIC.utils import get_technology_by_name

        TECHNOLOGY = get_technology_by_name("EBeam")

        # declare the parameters
        self.param("silayer", self.TypeLayer, "SiN Layer", default=TECHNOLOGY["SiN"])
        self.param("r", self.TypeDouble, "Radius", default=250)
        self.param("w", self.TypeDouble, "Waveguide Width", default=0.75)
        self.param("g", self.TypeDouble, "Gap", default=1.15)
        self.param("Lc", self.TypeDouble, "Coupler Length", default=0.0)
        self.param(
            "pinrec", self.TypeLayer, "PinRec Layer", default=TECHNOLOGY["PinRec"]
        )
        self.param(
            "devrec", self.TypeLayer, "DevRec Layer", default=TECHNOLOGY["DevRec"]
        )
        self.param("textl", self.TypeLayer, "Text Layer", default=TECHNOLOGY["Text"])

    def display_text_impl(self):
        # Provide a descriptive text for the cell
        return (
            "ebeam_dc_halfring_straight(R="
            + ("%.3f" % self.r)
            + ",g="
            + ("%g" % (1000 * self.g))
            + ",Lc="
            + ("%g" % (1000 * self.Lc))
            + ")"
        )

    def can_create_from_shape_impl(self):
        return False

    def produce_impl(self):
        # This is the main part of the implementation: create the layout

        from SiEPIC.utils import arc_wg_xy
        from SiEPIC.utils.layout import make_pin
        from SiEPIC.extend import to_itype

        # fetch the parameters
        dbu = self.layout.dbu
        ly = self.layout
        shapes = self.cell.shapes

        LayerSiN = ly.layer(self.silayer)
        LayerPinRecN = ly.layer(self.pinrec)
        LayerDevRecN = ly.layer(self.devrec)
        TextLayerN = ly.layer(self.textl)

        w = to_itype(self.w, dbu)
        w2 = to_itype(self.w / 2, dbu)
        r = to_itype(self.r, dbu)
        g = to_itype(self.g, dbu)
        Lc = to_itype(self.Lc, dbu)
        Lc2 = to_itype(self.Lc / 2, dbu)

        # draw the half-circle
        x = 0
        y = r + w + g
        from SiEPIC import __version__

        if __version__ > "0.5.0":
            self.cell.shapes(LayerSiN).insert(
                arc_wg_xy(x - Lc2, y, r, w, 180, 270, dbu=dbu)
            )
            self.cell.shapes(LayerSiN).insert(
                arc_wg_xy(x + Lc2, y, r, w, 270, 360, dbu=dbu)
            )
        else:
            self.cell.shapes(LayerSiN).insert(arc_wg_xy(x - Lc2, y, r, w, 180, 270))
            self.cell.shapes(LayerSiN).insert(arc_wg_xy(x + Lc2, y, r, w, 270, 360))

        # Pins on the top side:
        make_pin(self.cell, "pin2", [-r - Lc2, y], w, LayerPinRecN, 90)
        make_pin(self.cell, "pin4", [r + Lc2, y], w, LayerPinRecN, 90)

        if Lc > 0:
            wg1 = Box(-Lc2, -w2 + w + g, Lc2, w2 + w + g)
            shapes(LayerSiN).insert(wg1)

        # Create the waveguide
        wg1 = Box(-r - w2 - w - Lc2, -w2, r + w2 + w + Lc2, w2)
        shapes(LayerSiN).insert(wg1)

        # Pins on the bus waveguide side:
        make_pin(self.cell, "pin1", [-r - w2 - w - Lc2, 0], w, LayerPinRecN, 180)
        make_pin(self.cell, "pin3", [r + w2 + w + Lc2, 0], w, LayerPinRecN, 0)

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
        dev = Box(-r - w2 - w - Lc2, -w2 - w, r + w2 + w + Lc2, y)
        shapes(LayerDevRecN).insert(dev)

        """
    # Compact model information
    t = Trans(Trans.R0, -r, 0)
    text = Text ("Lumerical_INTERCONNECT_library=Design kits/ebeam", t)
    shape = shapes(LayerDevRecN).insert(text)
    shape.text_size = self.r*0.03/dbu

    t = Trans(Trans.R0, -r, r/4)
    text = Text ('Component=ebeam_dc_halfring_straight', t)
    shape = shapes(LayerDevRecN).insert(text)
    shape.text_size = self.r*0.03/dbu

    t = Trans(Trans.R0, -r, r/2)
    text = Text ('Spice_param:wg_width=%.3g gap=%.3g radius=%.3g Lc=%.3g orthogonal_identifier=%s'% (self.w*1e-6,self.g*1e-6,self.r*1e-6,self.Lc*1e-6, self.orthogonal_identifier), t)
    shape = shapes(LayerDevRecN).insert(text)
    shape.text_size = self.r*0.03/dbu
    """

        # print("Done drawing the layout for - ebeam_dc_halfring_straight: %.3f-%g" % ( self.r, self.g) )
