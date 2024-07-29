import pya
from pya import *
from SiEPIC.utils import get_technology_by_name
import math


class phc_H0c_new(pya.PCellDeclarationHelper):
    """
    Input: length, width
    """

    import numpy

    def __init__(self):
        # Important: initialize the super class
        super(phc_H0c_new, self).__init__()

        self.param("a", self.TypeDouble, "lattice constant (microns)", default=0.744)
        self.param(
            "n", self.TypeInt, "Number of holes in x and y direction", default=30
        )
        self.param("r", self.TypeDouble, "hole radius (microns)", default=0.179)
        self.param(
            "wg_dis", self.TypeInt, "Waveguide distance (number of holes)", default=3
        )
        self.param("S1x", self.TypeDouble, "S1x shift", default=0.28)
        self.param("S2x", self.TypeDouble, "S2x shift", default=0.193)
        self.param("S3x", self.TypeDouble, "S3x shift", default=0.194)
        self.param("S4x", self.TypeDouble, "S4x shift", default=0.162)
        self.param("S5x", self.TypeDouble, "S5x shift", default=0.113)
        self.param("S1y", self.TypeDouble, "S1y shift", default=-0.016)
        self.param("S2y", self.TypeDouble, "S2y shift", default=0.134)
        self.param(
            "bus_number", self.TypeInt, "2 for double, 1 for single, max 2", default=2
        )
        TECHNOLOGY = get_technology_by_name("EBeam")
        self.param("layer", self.TypeLayer, "Layer", default=TECHNOLOGY["Si"])
        self.param(
            "pinrec", self.TypeLayer, "PinRec Layer", default=TECHNOLOGY["PinRec"]
        )
        self.param(
            "devrec", self.TypeLayer, "DevRec Layer", default=TECHNOLOGY["DevRec"]
        )
        self.param("textl", self.TypeLayer, "Text Layer", default=TECHNOLOGY["Text"])

    def display_text_impl(self):
        # Provide a descriptive text for the cell
        return "H0 Cavity_a%s-r%.3f-wg_dis%.3f-n%.3f" % (
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
        bus_n = self.bus_number

        LayerSi = self.layer
        LayerSiN = ly.layer(self.layer)
        LayerPinRecN = ly.layer(self.pinrec)
        LayerDevRecN = ly.layer(self.devrec)
        LayerTextN = ly.layer(self.textl)

        a = self.a / dbu
        r = self.r / dbu
        wg_dis = self.wg_dis + 1
        n = int(math.ceil(self.n / 2))
        Sx = [self.S1x, self.S2x, self.S3x, self.S4x, self.S5x]
        Sy = [self.S1y, 0, self.S2y]
        if wg_dis % 2 == 0:
            length_slab_x = 2 * n * a
        else:
            length_slab_x = (2 * n + 1) * a

        length_slab_y = 2 * (n - 2) * a

        if bus_n == 2:
            k = -1
        else:
            k = 1

        # function to creat polygon pts for right half of a hole in a hexagon unit cell
        def hexagon_hole_half(a, r):
            npts = 10
            theta_div = math.pi / 3
            theta_div_hole = math.pi / npts
            triangle_length = a / math.sqrt(3)
            pts = []
            for i in range(0, 4):
                pts.append(
                    Point.from_dpoint(
                        pya.DPoint(
                            triangle_length * math.cos(i * theta_div - math.pi / 2),
                            triangle_length * math.sin(i * theta_div - math.pi / 2),
                        )
                    )
                )
            for i in range(0, npts + 1):
                pts.append(
                    Point.from_dpoint(
                        pya.DPoint(
                            r * math.cos(math.pi / 2 - i * theta_div_hole),
                            r * math.sin(math.pi / 2 - i * theta_div_hole),
                        )
                    )
                )
            return pts

        def hexagon_shifthole_half(a, r):
            npts = 10
            theta_div = math.pi / 3
            theta_div_hole = math.pi / npts
            triangle_length = a * 1.235 / math.sqrt(3)
            pts = []
            for i in range(0, 4):
                pts.append(
                    Point.from_dpoint(
                        pya.DPoint(
                            triangle_length * math.cos(i * theta_div - math.pi / 2),
                            triangle_length * math.sin(i * theta_div - math.pi / 2),
                        )
                    )
                )
            for i in range(0, npts + 1):
                pts.append(
                    Point.from_dpoint(
                        pya.DPoint(
                            r * math.cos(math.pi / 2 - i * theta_div_hole),
                            r * math.sin(math.pi / 2 - i * theta_div_hole),
                        )
                    )
                )
            return pts

        # function to creat polygon pts for right half of a hexagon unit cell
        def hexagon_half(a):
            theta_div = math.pi / 3
            triangle_length = a / math.sqrt(3)
            pts = []
            for i in range(0, 4):
                pts.append(
                    Point.from_dpoint(
                        pya.DPoint(
                            triangle_length * math.cos(i * theta_div - math.pi / 2),
                            triangle_length * math.sin(i * theta_div - math.pi / 2),
                        )
                    )
                )
            return pts

        # create the right and left half of the hole and hexagon cells
        # hole_cell = pya.Region()
        # hexagon_cell = pya.Region()
        hole = pya.Region()

        hole_cell_pts = hexagon_hole_half(a, r)
        hexagon_pts = hexagon_half(a)
        hole_shiftcell_pts = hexagon_shifthole_half(a, r)
        hole_cell_poly_0 = pya.Polygon(hole_cell_pts)
        hexagon_cell_poly_0 = pya.Polygon(hexagon_pts)
        hole_shiftcell_poly_0 = pya.Polygon(hole_shiftcell_pts)

        hole_trans = pya.Trans(pya.Trans.R180)
        hole_cell_poly_1 = hole_cell_poly_0.transformed(hole_trans)
        hexagon_cell_poly_1 = hexagon_cell_poly_0.transformed(hole_trans)
        hole_shiftcell_poly_1 = hole_shiftcell_poly_0.transformed(hole_trans)

        # create the photonic crystal with shifts and waveguides
        for j in range(-n + 1, n):
            if j % 2 == 0:
                for i in range(-n, n + 1):
                    # waveguide
                    if (j == k * wg_dis and i > 3) or (j == wg_dis and i != 0):
                        hole_x = abs(i) / i * (abs(i) - 0.5) * a
                        hole_y = j * a * math.sqrt(3) / 2
                        hole_trans = pya.Trans(Trans.R0, hole_x, hole_y)
                        hole_t_0 = hexagon_cell_poly_0.transformed(hole_trans)
                        hole_t_1 = hexagon_cell_poly_1.transformed(hole_trans)
                        hole.insert(hole_t_0)
                        hole.insert(hole_t_1)
                    # filling the edges with half cell
                    elif i in (-n, n) and wg_dis % 2 == 1:
                        hole_x = abs(i) / i * (abs(i) + 0.5) * a
                        hole_y = j * a * math.sqrt(3) / 2
                        hole_trans = pya.Trans(Trans.R0, hole_x, hole_y)
                        if i == -n:
                            hole_t = hole_cell_poly_0.transformed(hole_trans)
                        else:
                            hole_t = hole_cell_poly_1.transformed(hole_trans)
                        hole.insert(hole_t)
                        hole_x = abs(i) / i * (abs(i) - 0.5) * a
                        hole_y = j * a * math.sqrt(3) / 2
                        hole_trans = pya.Trans(Trans.R0, hole_x, hole_y)
                        hole_t_0 = hole_cell_poly_0.transformed(hole_trans)
                        hole_t_1 = hole_cell_poly_1.transformed(hole_trans)
                        hole.insert(hole_t_0)
                        hole.insert(hole_t_1)
                    # x shifts
                    elif j == 0 and i in (1, -1, 2, -2, 3, -3, 4, -4, 5, -5):
                        hole_x = abs(i) / i * (abs(i) - 0.5 + Sx[abs(i) - 1]) * a
                        hole_y = 0
                        hole_trans = pya.Trans(Trans.R0, hole_x, hole_y)
                        hole_t_0 = hole_shiftcell_poly_0.transformed(hole_trans)
                        hole_t_1 = hole_shiftcell_poly_1.transformed(hole_trans)
                        hole.insert(hole_t_0)
                        hole.insert(hole_t_1)
                    elif i != 0:
                        hole_x = abs(i) / i * (abs(i) - 0.5) * a
                        hole_y = j * a * math.sqrt(3) / 2
                        hole_trans = pya.Trans(Trans.R0, hole_x, hole_y)
                        hole_t_0 = hole_cell_poly_0.transformed(hole_trans)
                        hole_t_1 = hole_cell_poly_1.transformed(hole_trans)
                        hole.insert(hole_t_0)
                        hole.insert(hole_t_1)
            elif j % 2 == 1:
                for i in range(-n, n + 1):
                    # waveguide
                    if (j == k * wg_dis and i > 3) or j == wg_dis:
                        hole_x = i * a
                        hole_y = j * a * math.sqrt(3) / 2
                        hole_trans = pya.Trans(Trans.R0, hole_x, hole_y)
                        hole_t_0 = hexagon_cell_poly_0.transformed(hole_trans)
                        hole_t_1 = hexagon_cell_poly_1.transformed(hole_trans)
                        hole.insert(hole_t_0)
                        hole.insert(hole_t_1)
                    # filling the edges with half cell
                    elif wg_dis % 2 == 0 and i in (-n, n):
                        hole_x = i * a
                        hole_y = j * a * math.sqrt(3) / 2
                        hole_trans = pya.Trans(Trans.R0, hole_x, hole_y)
                        if i == -n:
                            hole_t = hole_cell_poly_0.transformed(hole_trans)
                        else:
                            hole_t = hole_cell_poly_1.transformed(hole_trans)
                        hole.insert(hole_t)
                    # y shifts
                    elif i == 0 and j in (1, -1, 3, -3):
                        hole_x = 0
                        hole_y = (
                            j * a * (math.sqrt(3) / 2) + abs(j) / j * a * Sy[abs(j) - 1]
                        )
                        hole_trans = pya.Trans(Trans.R0, hole_x, hole_y)
                        hole_t_0 = hole_shiftcell_poly_0.transformed(hole_trans)
                        hole_t_1 = hole_shiftcell_poly_1.transformed(hole_trans)
                        hole.insert(hole_t_0)
                        hole.insert(hole_t_1)
                    else:
                        hole_x = i * a
                        hole_y = j * a * math.sqrt(3) / 2
                        hole_trans = pya.Trans(Trans.R0, hole_x, hole_y)
                        hole_t_0 = hole_cell_poly_0.transformed(hole_trans)
                        hole_t_1 = hole_cell_poly_1.transformed(hole_trans)
                        hole.insert(hole_t_0)
                        hole.insert(hole_t_1)

        # print(hole_t_0)
        box_l = a / 2
        hole.insert(pya.Box(-box_l, -box_l, box_l, box_l))
        cover_box = pya.Box(-length_slab_x / 2, -a / 2, length_slab_x / 2, a / 2)
        box_y = n * a * math.sqrt(3) / 2
        cover_box_trans_0 = pya.Trans(Trans.R0, 0, box_y)
        cover_box_trans_1 = pya.Trans(Trans.R0, 0, -box_y)
        cover_box_t_0 = cover_box.transformed(cover_box_trans_0)
        cover_box_t_1 = cover_box.transformed(cover_box_trans_1)
        # hole.insert(pya.Box())
        self.cell.shapes(LayerSiN).insert(hole)
        self.cell.shapes(LayerSiN).insert(cover_box_t_0)
        self.cell.shapes(LayerSiN).insert(cover_box_t_1)
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
