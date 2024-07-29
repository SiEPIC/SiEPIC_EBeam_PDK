import pya
from pya import *
from SiEPIC.utils import get_technology_by_name


class Tapered_Ring(pya.PCellDeclarationHelper):
    """
    The PCell declaration for the tapered ring.
    Author: Mustafa Hammood     mustafa@ece.ubc.ca
    """

    def __init__(self):
        # Important: initialize the super class
        super(Tapered_Ring, self).__init__()
        TECHNOLOGY = get_technology_by_name("EBeam")

        # declare the parameters
        self.param("w_top", self.TypeDouble, "Top width", default=0.5)
        self.param("w_bot", self.TypeDouble, "Bottom width (>Top Width)", default=2)
        self.param("radius", self.TypeDouble, "Radius", default=10)
        self.param("LayerSi", self.TypeLayer, "Si Layer", default=TECHNOLOGY["Si"])
        self.param(
            "pinrec", self.TypeLayer, "PinRec Layer", default=TECHNOLOGY["PinRec"]
        )
        self.param(
            "devrec", self.TypeLayer, "DevRec Layer", default=TECHNOLOGY["DevRec"]
        )

    def display_text_impl(self):
        # Provide a descriptive text for the cell
        return "Tapered_Ring(R=" + ("%.3f-%.3f" % (self.radius, self.w_bot)) + ")"

    def can_create_from_shape(self, layout, shape, layer):
        return False

    def produce_impl(self):
        from pya import Region, Polygon
        import math

        # fetch parameters
        dbu = self.layout.dbu
        ly = self.layout
        shapes = self.cell.shapes

        # Layers definitions
        LayerSi = self.layer
        LayerSiN = ly.layer(self.LayerSi)
        LayerPinRecN = ly.layer(self.pinrec)
        LayerDevRecN = ly.layer(self.devrec)
        # LayerTextN = ly.layer(LayerText)

        # cell: layout cell to place the layout
        # LayerSiN: which layer to use
        # x, y: location of the origin
        # r: radius
        # w: waveguide width
        # length units in dbu

        x = 0
        w_top = self.w_top / dbu
        r = self.radius / dbu

        w_bot = self.w_bot / dbu

        deltaW = w_bot - w_top

        nptsFactor = 12

        # function to generate points to create circle
        def circle(x, w_top, r):
            npts = 32 * nptsFactor
            theta = 2 * math.pi / npts  # increment, in radians
            pts = []
            for i in range(0, npts):
                pts.append(
                    Point.from_dpoint(
                        DPoint(
                            (x + r * math.cos(i * theta)) / 1,
                            (w_top + r * math.sin(i * theta)) / 1,
                        )
                    )
                )
            return pts

        # function to generate points to create innercircle
        def inner_circle(x, w_top, r):
            npts = 32 * nptsFactor
            theta = 2 * math.pi / npts  # increment, in radians
            pts = []
            for i in range(0, npts):
                pts.append(
                    Point.from_dpoint(
                        DPoint(
                            (x + r * math.cos(i * theta)) / 1,
                            (w_top + r * math.sin(i * theta)) / 1,
                        )
                    )
                )
            return pts

        # Outer circle
        x = 0
        y = 0
        r_out = r + w_top / 2
        ring = Region()
        ring_cell = circle(0, 0, r_out)
        ring_poly = Polygon(ring_cell)
        # ring_t = ring_poly.transformed(Trans(x,y))
        ring.insert(ring_poly)

        # Inner erasing circle
        r_in = r - (w_top) / 2 - deltaW / 2
        x = 0
        y = -deltaW / 2
        # Inner Circle
        hole = Region()
        hole_cell = inner_circle(x, y, r_in)
        hole_poly = Polygon(hole_cell)
        # hole_t = hole_poly.transformed(Trans(x,y))
        hole.insert(hole_poly)

        # perform inversion:
        phc = ring - hole
        self.cell.shapes(LayerSiN).insert(phc)
        # inversion can also be done by performing the XOR function
        # upper_poly = xor(Region(Polygon(circleu_pts)),Region(Polygon(rectu_pts)))

        return "Tapered_Ring(R=" + ("%.3f-%.3f" % (r, w_bot)) + ")"
