import pya
from pya import *
from SiEPIC.utils import get_technology_by_name
import math


class phc_wg_w1(pya.PCellDeclarationHelper):
    """
    Input: length, width
    """

    import numpy

    def __init__(self):
        # Important: initialize the super class
        super(phc_wg_w1, self).__init__()

        self.param("a", self.TypeDouble, "lattice constant (microns)", default=0.744)
        self.param(
            "n", self.TypeInt, "Number of holes in x and y direction", default=30
        )
        self.param("r", self.TypeDouble, "hole radius (microns)", default=0.179)
        self.param(
            "wg_dis", self.TypeInt, "Waveguide distance (number of holes)", default=2
        )
        self.param("n_vertices", self.TypeInt, "Vertices of a hole", default=32)
        self.param("etch_condition", self.TypeInt, "Etch = 1, No Etch = 2", default=1)

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
        n = int(math.ceil(self.n / 2))
        n_bus = 1
        etch_condition = self.etch_condition

        if n_bus == 1:
            Sx = [0, 0, 0, 0, 0]
            Sy = [0, 0, 0]

        if wg_dis % 2 == 0:
            length_slab_x = (2 * n - 1) * a
        else:
            length_slab_x = 2 * n * a

        length_slab_y = 2 * (wg_dis + 15) * a * math.sqrt(3) / 2

        n_x = n
        n_y = wg_dis + 10

        # Define Si slab and hole region for future subtraction
        Si_slab = pya.Region()
        Si_slab.insert(
            pya.Box(
                -length_slab_x / 2,
                -length_slab_y / 2,
                length_slab_x / 2,
                length_slab_y / 2,
            )
        )
        hole = pya.Region()
        hole_r = r

        # add suspension beams
        beam_width = 3 / dbu
        beam_length = 20 / dbu
        beam_x_0 = 8 * a
        beam_y_0 = beam_length / 2 + length_slab_y / 2 - 5000

        for i in (-1, 1):
            for j in (-1, 1):
                beam_x = i * beam_x_0
                beam_y = j * beam_y_0
                Si_slab.insert(
                    pya.Box(
                        -beam_width / 2 + beam_x,
                        -length_slab_y / 2 + beam_y,
                        beam_width / 2 + beam_x,
                        length_slab_y / 2 + beam_y,
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
                    elif j == 0 and i in (1, -1, 2, -2, 3, -3, 4, -4, 5, -5):
                        hole_x = abs(i) / i * (abs(i) - 0.5 + Sx[abs(i) - 1]) * a
                        hole_y = 0
                        hole_trans = pya.Trans(Trans.R0, hole_x, hole_y)
                        hole_t = hole_poly.transformed(hole_trans)
                        hole.insert(hole_t)
                    elif i != 0:
                        hole_x = abs(i) / i * (abs(i) - 0.5) * a
                        hole_y = j * a * math.sqrt(3) / 2
                        hole_trans = pya.Trans(Trans.R0, hole_x, hole_y)
                        hole_t = hole_poly.transformed(hole_trans)
                        hole.insert(hole_t)
            elif j % 2 == 1 and j != wg_dis:
                for i in range(-n_x, n_x + 1):
                    if j == -wg_dis and i > 3 and n_bus == 2:
                        None
                    elif i == 0 and j in (1, -1, 3, -3):
                        hole_x = 0
                        hole_y = (
                            j * a * (math.sqrt(3) / 2) + abs(j) / j * a * Sy[abs(j) - 1]
                        )
                        hole_trans = pya.Trans(Trans.R0, hole_x, hole_y)
                        hole_t = hole_poly.transformed(hole_trans)
                        hole.insert(hole_t)
                    else:
                        hole_x = i * a
                        hole_y = j * a * math.sqrt(3) / 2
                        hole_trans = pya.Trans(Trans.R0, hole_x, hole_y)
                        hole_t = hole_poly.transformed(hole_trans)
                        hole.insert(hole_t)

        phc = Si_slab - hole  # Perform the boolean operation
        self.cell.shapes(LayerSiN).insert(phc)
        if etch_condition == 1:
            box_etch = pya.Box(
                -(length_slab_x / 2 - 3000),
                -(length_slab_y / 2 - 6000),
                length_slab_x / 2 - 3000,
                length_slab_y / 2 - 6000,
            )
            self.cell.shapes(LayerEtch).insert(box_etch)

        # Pins on the waveguide:
        pin_length = 200
        pin_w = a
        wg_pos = a * math.sqrt(3) / 2 * wg_dis

        t = pya.Trans(Trans.R0, -length_slab_x / 2, wg_pos)
        pin = pya.Path(
            [pya.Point(-pin_length / 2, 0), pya.Point(pin_length / 2, 0)], pin_w
        )
        pin_t = pin.transformed(t)
        self.cell.shapes(LayerPinRecN).insert(pin_t)
        text = pya.Text("pin1", t)
        shape = self.cell.shapes(LayerPinRecN).insert(text)
        shape.text_size = 0.4 / dbu

        t = pya.Trans(Trans.R0, length_slab_x / 2, wg_pos)
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
