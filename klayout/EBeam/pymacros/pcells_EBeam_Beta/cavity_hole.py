import pya
from pya import *
from SiEPIC.utils import get_technology_by_name
from . import *


class cavity_hole(pya.PCellDeclarationHelper):
    """
    The PCell declaration for the cavity hole.
    This is an example of how to perform inversion operations
    by Jaspreet, Jingda, and Lukas
    """

    def __init__(self):
        # Important: initialize the super class
        super(cavity_hole, self).__init__()
        TECHNOLOGY = get_technology_by_name("EBeam")

        # declare the parameters
        self.param("x", self.TypeDouble, "x coordinate", default=0)
        self.param("y", self.TypeDouble, "y coordinate", default=0)
        self.param("radius", self.TypeDouble, "hole radius", default=10)
        self.param(
            "gap",
            self.TypeDouble,
            "half of the gap between surrounding holes (microns)",
            default=2,
        )
        self.param("LayerSi", self.TypeLayer, "Si Layer", default=TECHNOLOGY["Si"])
        self.param(
            "pinrec", self.TypeLayer, "PinRec Layer", default=TECHNOLOGY["PinRec"]
        )
        self.param(
            "devrec", self.TypeLayer, "DevRec Layer", default=TECHNOLOGY["DevRec"]
        )

    def display_text_impl(self):
        # Provide a descriptive text for the cell
        return "cavity_hole(R=" + ("%.3f-%.3f" % (self.radius, self.gap)) + ")"

    def can_create_from_shape(self, layout, shape, layer):
        return False

    def produce_impl(self):
        dbu = self.layout.dbu
        ly = self.layout
        shapes = self.cell.shapes

        # Layers definitions
        LayerSi = self.layer
        LayerSiN = ly.layer(self.LayerSi)
        LayerPinRecN = ly.layer(self.pinrec)
        LayerDevRecN = ly.layer(self.devrec)
        TECHNOLOGY = get_technology_by_name("EBeam")
        LayerTextN = TECHNOLOGY["Text"]
        # cell: layout cell to place the layout
        # LayerSiN: which layer to use
        # x, y: location of the origin
        # r: radius
        # w: waveguide width
        # length units in dbu

        x = self.x / dbu
        y = self.y / dbu
        r = self.radius / dbu
        r = r / 2
        w = 2 * r

        gap = self.gap / dbu  # gap between one hole to another

        # function to generate points to create a circle
        def circle(x, y, r):
            npts = 32
            theta = 2 * math.pi / npts  # increment, in radians
            pts = []
            for i in range(0, npts):
                pts.append(
                    Point.from_dpoint(
                        DPoint(
                            (x + r * math.cos(i * theta)) / 1,
                            (y + r * math.sin(i * theta)) / 1,
                        )
                    )
                )
            return pts

        # rectangular shapes
        side_gap = gap  # half of gap between surrounding holes
        dx = side_gap + (2 * r)
        dy = side_gap + (2 * r)

        Si_slab = Region()
        Si_slab.insert(Box(-dx / 2, -dy / 2, dx / 2, dy / 2))

        # Circle
        hole = Region()
        hole_cell = circle(0, 0, r)
        hole_poly = Polygon(hole_cell)
        hole_t = hole_poly.transformed(Trans(Trans.R0, x, y))
        hole.insert(hole_t)

        # perform inversion:
        phc = Si_slab - hole
        self.cell.shapes(LayerSiN).insert(phc)
        # inversion can also be done by performing the XOR function
        # upper_poly = xor(Region(Polygon(circleu_pts)),Region(Polygon(rectu_pts)))

        return "cavity_hole(R=" + ("%.3f-%.3f" % (r, gap)) + ")"
