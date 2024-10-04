import pya
from pya import *
from SiEPIC.utils import get_technology_by_name
import math


class phc_gc_hex(pya.PCellDeclarationHelper):
    """
    Input: length, width
    """

    import numpy

    def __init__(self):
        # Important: initialize the super class
        super(phc_gc_hex, self).__init__()

        self.param("a", self.TypeDouble, "lattice constant (microns)", default=0.243)
        self.param("x", self.TypeInt, "Number of holes in x direction", default=78)
        self.param("y", self.TypeInt, "Number of holes in y direction", default=50)
        self.param("r", self.TypeDouble, "hole radius (microns)", default=0.0735)
        self.param("vertices", self.TypeInt, "Number of vertices in circle", default=32)
        TECHNOLOGY = get_technology_by_name("EBeam")
        self.param("positive", self.TypeInt, "Positive", default=False)
        self.param("apodized", self.TypeInt, "apodized", default=False)
        self.param(
            "feature_size",
            self.TypeDouble,
            "minimum feature size (microns)",
            default=0.06,
        )
        self.param("layer", self.TypeLayer, "Layer", default=TECHNOLOGY["Si"])
        self.param(
            "pinrec", self.TypeLayer, "PinRec Layer", default=TECHNOLOGY["PinRec"]
        )
        self.param(
            "devrec", self.TypeLayer, "DevRec Layer", default=TECHNOLOGY["DevRec"]
        )
        self.param("textl", self.TypeLayer, "Text Layer", default=TECHNOLOGY["Text"])
        self.param(
            "invert", self.TypeLayer, "Layer to invert", default=TECHNOLOGY["Si"]
        )

    def display_text_impl(self):
        # Provide a descriptive text for the cell
        return "phc_gc_hex_a%s-r%.3f" % (self.a, self.r)

    def coerce_parameters_impl(self):
        pass

    def can_create_from_shape(self, layout, shape, layer):
        return False

    def produce_impl(self):
        debug = False
        # fetch the parameters
        dbu = self.layout.dbu
        ly = self.layout

        LayerSi = self.layer
        LayerSiN = ly.layer(self.layer)
        LayerPinRecN = ly.layer(self.pinrec)
        LayerDevRecN = ly.layer(self.devrec)
        LayerTextN = ly.layer(self.textl)
        LayerInvert = ly.layer(self.invert)
        n_vertices = int(self.vertices)
        a = self.a / dbu
        r = self.r / dbu
        n_x = int(math.ceil(self.x / 2))
        n_y = int(math.ceil(self.y / 2))
        positive = bool(self.positive)
        minimum_feature = self.feature_size
        apodized = bool(self.apodized)
        length_slab_x = 2 * n_x * a

        length_slab_y = 2 * (n_y - 2) * a

        k = 2

        # function to creat polygon pts for right half of a hole in a hexagon unit cell

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

        # Define Si slab and hole region for future subtraction
        Si_slab = pya.Region()
        Si_slab.insert(
            pya.Box(
                -length_slab_x / 2 + a * 2,
                -length_slab_y / 2,
                length_slab_x / 2 - a,
                length_slab_y / 2,
            )
        )
        hole = pya.Region()
        hole_r = r

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

        import numpy as np

        def gaussian(x, mu, sig):
            return (
                1.0
                / (np.sqrt(2.0 * np.pi) * sig)
                * np.exp(-np.power((x - mu) / sig, 2.0) / 2)
            )

        # raster through all holes with shifts and waveguide

        for j in range(-n_y, n_y + 1):
            if j % 2 == 0:
                skip = 0
                apodization = 0
                for i in range(-n_x, n_x + 1):
                    if i == 0:
                        continue
                    if skip == 0:
                        skip = 1
                        continue
                    elif skip == 1:
                        skip = 2
                        continue
                    elif skip == 2:
                        skip = 3
                        apodization = apodization + 1
                        continue
                    elif skip == 3:
                        skip = 1

                    # radius=r/gaussian(float(i)/(2*(n_x+1)),2*(n_x+1),10)
                    location = float(i)
                    location = abs(location)
                    # radius=r/gaussian(location/(2*(n_x+1)),2*(n_x+1),0.02)
                    # radius=(((2*n_x)-abs(i+n_x+3)*r)/(2*n_x))
                    radius = (float(apodization) / ((n_x * 2 / 3) - 1)) * r
                    if radius < minimum_feature * 500:
                        radius = minimum_feature * 500
                    if apodized == False:
                        radius = r

                        # radius=minimum_feature
                    hole_cell = circle(0, 0, radius)
                    hole_poly = pya.Polygon(hole_cell)
                    if debug:
                        print("x1 " + str(apodization))
                    hole_x = abs(i) / i * (abs(i) - 0.5) * a
                    hole_y = j * a * math.sqrt(3) / 2
                    hole_trans = pya.Trans(Trans.R0, hole_x, hole_y)
                    hole_t = hole_poly.transformed(hole_trans)
                    hole.insert(hole_t)
            elif j % 2 == 1:
                skipodd = 0
                apodization = 0
                for i in range(-n_x, n_x + 1):
                    if i == -n_x:
                        continue
                    if i == n_x:
                        continue
                    if skipodd == 0:
                        skipodd = 1
                        continue
                    elif skipodd == 1:
                        skipodd = 2
                        apodization = apodization + 1
                        continue
                    elif skipodd == 2:
                        skipodd = 3
                    elif skipodd == 3:
                        skipodd = 1

                    # radius=(((2*n_x)-abs(i+n_x+3)*r)/(2*n_x))
                    radius = (float(apodization) / ((n_x * 2 / 3) - 1)) * r
                    if radius < minimum_feature * 500:
                        radius = minimum_feature * 500
                    if apodized == False:
                        radius = r

                        # radius=minimum_feature
                    # radius=r*(float(abs(i))/(2*(n_x+1)))
                    hole_cell = circle(0, 0, radius)
                    hole_poly = pya.Polygon(hole_cell)
                    if debug:
                        print("x2 " + str(apodization))
                        print("p " + str(n_x))
                    hole_x = i * a
                    hole_y = j * a * math.sqrt(3) / 2
                    hole_trans = pya.Trans(Trans.R0, hole_x, hole_y)
                    hole_t = hole_poly.transformed(hole_trans)
                    hole.insert(hole_t)
        if positive == True:
            phc = hole
        else:
            phc = Si_slab - hole
        self.cell.shapes(LayerSiN).insert(phc)

        # print(hole_t_0)
        box_l = a / 2

        # Pins on the waveguide:
        pin_length = 200
        pin_w = a

        t = pya.Trans(Trans.R0, -length_slab_x / 2 + a * 2, 0)
        pin = pya.Path(
            [pya.Point(-pin_length / 2, 0), pya.Point(pin_length / 2, 0)], pin_w
        )
        pin_t = pin.transformed(t)
        self.cell.shapes(LayerPinRecN).insert(pin_t)
        text = pya.Text("pin1", t)
        shape = self.cell.shapes(LayerPinRecN).insert(text)
        shape.text_size = 0.4 / dbu

        # Create the device recognition layer -- make it 1 * wg_width away from the waveguides.
        points = [[-length_slab_x / 2 + a * 2, 0], [length_slab_x / 2 - a, 0]]
        points = [Point(each[0], each[1]) for each in points]
        path = Path(points, length_slab_y)
        self.cell.shapes(LayerDevRecN).insert(path.simple_polygon())

        if positive == True:
            self.cell.shapes(LayerInvert).insert(path.simple_polygon())

        return

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
        skip = 1
        skip2 = 0
        # create the photonic crystal with shifts and waveguides
        for j in range(-y + 1, y):
            if j % 2 == 0:
                for i in range(-x, x + 1):
                    # waveguide
                    if j == k and i > 3:
                        hole_x = abs(i) / i * (abs(i) - 0.5) * a
                        hole_y = j * a * math.sqrt(3) / 2
                        hole_trans = pya.Trans(Trans.R0, hole_x, hole_y)
                        hole_t_0 = hole_cell_poly_0.transformed(hole_trans)
                        hole_t_1 = hole_cell_poly_1.transformed(hole_trans)
                        hole.insert(hole_t_0)
                        hole.insert(hole_t_1)
                    # filling the edges with half cell

                    elif i != 0:
                        hole_x = abs(i) / i * (abs(i) - 0.5) * a
                        hole_y = j * a * math.sqrt(3) / 2
                        hole_trans = pya.Trans(Trans.R0, hole_x, hole_y)
                        hole_t_0 = hole_cell_poly_0.transformed(hole_trans)
                        hole_t_1 = hole_cell_poly_1.transformed(hole_trans)
                        hole.insert(hole_t_0)
                        hole.insert(hole_t_1)
            elif j % 2 == 1:
                for i in range(-x, x + 1):
                    if skip == 0 and i % 3 == 0:
                        skip = 1
                        continue
                    if skip == 1:
                        skip = 2
                        continue
                    if skip == 2:
                        skip = 0

                    if i == -x:
                        hole_x = abs(i) / i * (abs(i) - 0.5) * a
                        hole_y = j * a * math.sqrt(3) / 2
                        hole_trans = pya.Trans(Trans.R0, hole_x, hole_y)
                        hole_t_1 = hexagon_cell_poly_1.transformed(hole_trans)
                        hole.insert(hole_t_1)
                    if i == x:
                        hole_x = abs(i) / i * (abs(i) - 0.5) * a
                        hole_y = j * a * math.sqrt(3) / 2
                        hole_trans = pya.Trans(Trans.R0, hole_x, hole_y)
                        hole_t_0 = hexagon_cell_poly_0.transformed(hole_trans)
                        hole.insert(hole_t_0)
                    # waveguide
                    if j == k and i > 3:
                        hole_x = i * a
                        hole_y = j * a * math.sqrt(3) / 2
                        hole_trans = pya.Trans(Trans.R0, hole_x, hole_y)
                        hole_t_0 = hexagon_cell_poly_0.transformed(hole_trans)
                        hole_t_1 = hexagon_cell_poly_1.transformed(hole_trans)
                        hole.insert(hole_t_0)
                        hole.insert(hole_t_1)
                    # filling the edges with half cell
                    elif i in (-x, x):
                        hole_x = i * a
                        hole_y = j * a * math.sqrt(3) / 2
                        hole_trans = pya.Trans(Trans.R0, hole_x, hole_y)
                        if i == -x:
                            hole_t = hole_cell_poly_0.transformed(hole_trans)
                        else:
                            hole_t = hole_cell_poly_1.transformed(hole_trans)
                        hole.insert(hole_t)

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

        cover_box = pya.Box(-length_slab_x / 2, -a / 2, length_slab_x / 2, a / 2)
        box_y = y * a * math.sqrt(3) / 2
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

        t = pya.Trans(Trans.R0, -length_slab_x / 2, 0)
        pin = pya.Path(
            [pya.Point(-pin_length / 2, 0), pya.Point(pin_length / 2, 0)], pin_w
        )
        pin_t = pin.transformed(t)
        self.cell.shapes(LayerPinRecN).insert(pin_t)
        text = pya.Text("pin1", t)
        shape = self.cell.shapes(LayerPinRecN).insert(text)
        shape.text_size = 0.4 / dbu

        # Create the device recognition layer -- make it 1 * wg_width away from the waveguides.
        points = [[-length_slab_x / 2, 0], [length_slab_x / 2, 0]]
        points = [Point(each[0], each[1]) for each in points]
        path = Path(points, length_slab_y)
        self.cell.shapes(LayerDevRecN).insert(path.simple_polygon())
