import pya
from pya import *
from SiEPIC.utils import get_technology_by_name


class Bezier_Bend(pya.PCellDeclarationHelper):
    """
    Input: bezier number, effective radius, waveguide width, layers
    draws a 90 degree bezier bend with a given bezier factor
    Usage: instantiate, and use transformations (rotation)

    This implementation is Python translation of the 90 degree Bezier bend ample script for Mentor Graphics Pyxis
      by Jonas Flueckiger and Lukas Chrostowski's
      influenced by www.tinaja.com/glib/cubemath.pdf implementation

    Author: Mustafa Hammood     mustafa@ece.ubc.ca
    """

    def __init__(self):
        # Important: initialize the super class
        super(Bezier_Bend, self).__init__()
        TECHNOLOGY = get_technology_by_name("EBeam")

        # declare the parameters
        self.param("bezier_num", self.TypeDouble, "Bezier factor", default=25)
        self.param(
            "eff_r", self.TypeDouble, "Effective bend radius (microns)", default=5
        )
        self.param(
            "wg_width", self.TypeDouble, "Waveguide width (microns)", default=0.500
        )
        self.param("layer", self.TypeLayer, "Layer", default=TECHNOLOGY["Si"])
        self.param(
            "pinrec", self.TypeLayer, "PinRec Layer", default=TECHNOLOGY["PinRec"]
        )
        self.param(
            "devrec", self.TypeLayer, "DevRec Layer", default=TECHNOLOGY["DevRec"]
        )

    #    self.param("textl", self.TypeLayer, "Text Layer", default = LayerInfo(10, 0))

    def display_text_impl(self):
        # Provide a descriptive text for the cell
        return "Bezier_Number_%.3f-%.3f" % (
            self.bezier_num / 1000,
            self.wg_width / 1000,
        )

    def coerce_parameters_impl(self):
        pass

    def can_create_from_shape(self, layout, shape, layer):
        return False

    def produce_impl(self):
        # fetch the parameters
        dbu = self.layout.dbu
        ly = self.layout

        LayerSi = self.layer
        LayerSiN = ly.layer(LayerSi)
        LayerPinRecN = ly.layer(self.pinrec)
        LayerDevRecN = ly.layer(self.devrec)

        from SiEPIC.utils import arc_bezier
        from SiEPIC._globals import PIN_LENGTH as pin_length

        wg_width = self.wg_width
        w = self.wg_width / dbu

        r = self.eff_r / dbu
        bezier = self.bezier_num / 100

        x = -r
        y = r

        points = arc_bezier(r, 0, 360, bezier)
        a = pya.Path(points, w).simple_polygon()
        d = [each for each in a.each_point()]
        pt_idx = int(len(d) / 2)
        ptA = d[pt_idx]
        ptB = d[pt_idx + 1]
        # print(pt_idx)
        # print(d)
        if abs(ptA.x - ptB.x) * dbu == wg_width:
            new_y = (ptA.y + ptB.y) / 2
            d[pt_idx].y = new_y
            d[pt_idx + 1].y = new_y
        elif abs(ptA.y - ptB.y) * dbu == wg_width:
            new_x = (ptA.x + ptB.x) / 2
            d[pt_idx].x = new_x
            d[pt_idx + 1].x = new_x
        # print(d)

        self.cell.shapes(LayerSiN).insert(Polygon(d))

        # Create the pins, as short paths:
        w = int(round(self.wg_width / dbu))
        r = int(round(self.eff_r / dbu))
        x = r
        y = r

        # Pin on the top side:
        p2 = [Point(0, y - pin_length / 2), Point(0, y + pin_length / 2)]
        p2c = Point(x, y)
        self.set_p2 = p2c
        self.p2 = p2c
        pin = Path(p2, w)
        self.cell.shapes(LayerPinRecN).insert(pin)
        t = Trans(Trans.R0, 0, y)
        text = Text("pin2", t)
        shape = self.cell.shapes(LayerPinRecN).insert(text)
        shape.text_size = 0.4 / dbu

        x = 0
        y = 0
        # Pin on the left side:
        p1 = [Point(pin_length / 2 - r, 0), Point(-pin_length / 2 - r, 0)]
        p1c = Point(x, 0)
        self.set_p1 = p1c
        self.p1 = p1c
        pin = Path(p1, w)
        self.cell.shapes(LayerPinRecN).insert(pin)
        t = Trans(Trans.R0, -r, 0)
        text = Text("pin1", t)
        shape = self.cell.shapes(LayerPinRecN).insert(text)
        shape.text_size = 0.4 / dbu

        # Create the device recognition layer -- make it 1 * wg_width away from the waveguides.
        points = arc_bezier(r, 270, 360, bezier)
        self.cell.shapes(LayerDevRecN).insert(pya.Path(points, w * 3))
