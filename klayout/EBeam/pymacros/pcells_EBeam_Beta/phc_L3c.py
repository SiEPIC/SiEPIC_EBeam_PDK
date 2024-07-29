import pya
from pya import *
from SiEPIC.utils import get_technology_by_name
import math


class phc_L3c(pya.PCellDeclarationHelper):
    """
    Input: length, width
    """

    import numpy

    def __init__(self):
        # Important: initialize the super class
        super(phc_L3c, self).__init__()

        self.param("a", self.TypeDouble, "lattice constant (microns)", default=0.720)
        self.param(
            "n", self.TypeInt, "Number of holes in x and y direction", default=30
        )
        self.param("r", self.TypeDouble, "hole radius (microns)", default=0.181)
        self.param(
            "wg_dis", self.TypeInt, "Waveguide distance (number of holes)", default=3
        )
        self.param("n_bus", self.TypeInt, "Bus number, 1 or 2 ", default=2)
        self.param("n_vertices", self.TypeInt, "Vertices of a hole", default=32)
        self.param("S1x", self.TypeDouble, "S1x shift", default=0.337)
        self.param("S2x", self.TypeDouble, "S2x shift", default=0.27)
        self.param("S3x", self.TypeDouble, "S3x shift", default=0.088)
        self.param("S4x", self.TypeDouble, "S4x shift", default=0.323)
        self.param("S5x", self.TypeDouble, "S5x shift", default=0.173)
        TECHNOLOGY = get_technology_by_name("EBeam")
        self.param("layer", self.TypeLayer, "Layer", default=TECHNOLOGY["Si"])
        self.param(
            "pinrec", self.TypeLayer, "PinRec Layer", default=TECHNOLOGY["PinRec"]
        )
        self.param(
            "devrec", self.TypeLayer, "DevRec Layer", default=TECHNOLOGY["DevRec"]
        )
        self.param("textl", self.TypeLayer, "Text Layer", default=TECHNOLOGY["Text"])
        self.param(
            "etch", self.TypeLayer, "oxide etch layer", default=pya.LayerInfo(12, 0)
        )

    def display_text_impl(self):
        # Provide a descriptive text for the cell
        return "phc_L3c_a%s-r%.3f-wg_dis%.3f-n%.3f" % (
            self.a,
            self.r,
            self.wg_dis,
            self.n,
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
        LayerSiN = ly.layer(self.layer)
        LayerPinRecN = ly.layer(self.pinrec)
        LayerDevRecN = ly.layer(self.devrec)
        LayerTextN = ly.layer(self.textl)
        LayerEtch = ly.layer(self.etch)

        # Fetch all the parameters:
        a = self.a / dbu
        r = self.r / dbu
        wg_dis = self.wg_dis + 1
        n_vertices = self.n_vertices
        n_bus = self.n_bus
        n = int(math.ceil(self.n / 2))
        Sx = [self.S1x, self.S2x, self.S3x, self.S4x, self.S5x]
        if n_bus == 1:
            Sx = [0, 0, 0, 0, 0]
            Sy = [0, 0, 0]

        if wg_dis % 2 == 0:
            length_slab_x = 2 * n * a
        else:
            length_slab_x = (2 * n - 1) * a

        length_slab_y = 2 * (wg_dis + 10) * a * math.sqrt(3) / 2

        length_anchor_y = length_slab_y + 20 * a
        length_anchor_x = length_slab_x + 20 * a

        n_x = n
        n_y = wg_dis + 10

        # Define Si slab and hole region for future subtraction
        Si_slab = pya.Region()
        Si_slab.insert(
            pya.Box(
                -length_anchor_x / 2,
                -length_anchor_y / 2,
                length_anchor_x / 2,
                length_anchor_y / 2,
            )
        )
        hole = pya.Region()
        hole_r = r
        trench = pya.Region()

        # add the trenches for waveguide connection
        trench_width = 20 / dbu
        trench_height = 9 * a * math.sqrt(3) / 2
        wg_pos = a * math.sqrt(3) / 2 * wg_dis

        trench.insert(
            pya.Box(
                -trench_width - length_slab_x / 2,
                wg_pos - trench_height / 2,
                -length_slab_x / 2,
                wg_pos + trench_height / 2,
            )
        )
        trench.insert(
            pya.Box(
                length_slab_x / 2,
                wg_pos - trench_height / 2,
                trench_width + length_slab_x / 2,
                wg_pos + trench_height / 2,
            )
        )

        if n_bus == 2:
            wg_pos_2 = -a * math.sqrt(3) / 2 * wg_dis
            trench.insert(
                pya.Box(
                    length_slab_x / 2,
                    wg_pos_2 - trench_height / 2,
                    trench_width + length_slab_x / 2,
                    wg_pos_2 + trench_height / 2,
                )
            )

        # function to generate points to create a circle
        def circle(x, y, r):
            npts = n_vertices
            theta = 2 * math.pi / npts  # increment, in radians
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

        # raster through all holes with shifts and waveguide

        hole_cell = circle(0, 0, hole_r)
        hole_poly = pya.Polygon(hole_cell)

        for j in range(-n_y, n_y + 1):
            if j % 2 == 0 and j != wg_dis:
                for i in range(-n_x, n_x + 1):
                    if j == -wg_dis and i > 3 and n_bus == 2:
                        None
                    elif j == 0 and i in (-1, 0, 1):
                        None
                    elif j == 0 and i in (2, -2, 3, -3, 4, -4, 5, -5, 6, -6):
                        hole_x = (i + (abs(i) / i) * Sx[abs(i) - 2]) * a
                        hole_y = 0
                        hole_trans = pya.Trans(Trans.R0, hole_x, hole_y)
                        hole_t = hole_poly.transformed(hole_trans)
                        hole.insert(hole_t)
                    else:
                        hole_x = i * a
                        hole_y = j * a * math.sqrt(3) / 2
                        hole_trans = pya.Trans(Trans.R0, hole_x, hole_y)
                        hole_t = hole_poly.transformed(hole_trans)
                        hole.insert(hole_t)
            elif j % 2 == 1 and j != wg_dis:
                for i in range(-n_x, n_x + 1):
                    if j == -wg_dis and i > 3 and n_bus == 2:
                        None
                    elif i != 0:
                        hole_x = abs(i) / i * (abs(i) - 0.5) * a
                        hole_y = j * a * math.sqrt(3) / 2
                        hole_trans = pya.Trans(Trans.R0, hole_x, hole_y)
                        hole_t = hole_poly.transformed(hole_trans)
                        hole.insert(hole_t)

        phc = Si_slab - hole - trench
        self.cell.shapes(LayerSiN).insert(phc)
        box_etch = pya.Box(
            -(length_slab_x / 2 - 3000),
            -(length_slab_y / 2 - 3000),
            length_slab_x / 2 - 3000,
            length_slab_y / 2 - 3000,
        )
        self.cell.shapes(LayerEtch).insert(box_etch)

        # Pins on the waveguide:
        pin_length = 200
        pin_w = a

        t = pya.Trans(Trans.R0, -length_slab_x / 2, wg_pos)
        pin = pya.Path(
            [pya.Point(pin_length / 2, 0), pya.Point(-pin_length / 2, 0)], pin_w
        )
        pin_t = pin.transformed(t)
        self.cell.shapes(LayerPinRecN).insert(pin_t)
        text = pya.Text("pin1", t)
        shape = self.cell.shapes(LayerPinRecN).insert(text)
        shape.text_size = 0.4 / dbu

        t = pya.Trans(Trans.R0, length_slab_x / 2, wg_pos)
        pin = pya.Path(
            [pya.Point(-pin_length / 2, 0), pya.Point(pin_length / 2, 0)], pin_w
        )
        pin_t = pin.transformed(t)
        self.cell.shapes(LayerPinRecN).insert(pin_t)
        text = pya.Text("pin2", t)
        shape = self.cell.shapes(LayerPinRecN).insert(text)
        shape.text_size = 0.4 / dbu

        # pin for drop waveguide
        if n_bus == 2:
            t = pya.Trans(Trans.R0, length_slab_x / 2, -wg_pos)
            pin_t = pin.transformed(t)
            self.cell.shapes(LayerPinRecN).insert(pin_t)
            text = pya.Text("pin3", t)
            shape = self.cell.shapes(LayerPinRecN).insert(text)
            shape.text_size = 0.4 / dbu

        # Create the device recognition layer -- make it 1 * wg_width away from the waveguides.
        points = [[-length_slab_x / 2, 0], [length_slab_x / 2, 0]]
        points = [Point(each[0], each[1]) for each in points]
        path = Path(points, length_slab_y)
        self.cell.shapes(LayerDevRecN).insert(path.simple_polygon())
