"""
KLayout-SiEPIC library for photonic crystals, UBC and SFU


*******
PCells:
*******

1) swg_fc
 - sub-wavelength grating (SWG) fibre coupler (FC)


NOTE: after changing the code, the macro needs to be rerun to install the new
implementation. The macro is also set to "auto run" to install the PCell
when KLayout is run.

Version history:

2017/07/07 Timothy Richards (Simon Fraser University, BC, Canada) and Adam DeAbreu (Simon Fraser University, BC, Canada)
 - swg_fc PCell

2017/07/07 Lukas Chrostowski
 - library definition and github repo

2017/07/09 Jaspreet Jhoja
  - Added Cavity Hole Pcell

2017/07/09 Jingda Wu
 - Added 2D H0 Photonic crystal cavity with single bus waveguide and pins

2017/07/10 Megan Nantel
- Added waveguide with impedance matching tapers for transition from external waveguide to Photonic crystal W1 waveguide

2017/07/10 Jingda Wu
- Improved generation efficiency by using single hole as a cell

2017/07/12 Megan Nantel
- Added the H0c test structure that includes grating couplers, waveguides, and H0c

2017/07/12 Jingda Wu
- Added L3 cavity with double bus waveguide and pins
- Added a drop bus to H0 cavity(coupling between waveguide?)
- Simplified code for generation

2017/07/12 Lukas Chrostowski
 - SWGFC litho test structure

2017/07/13 Megan Nantel
- grating coupler to grating coupler reference test structure
- photonic crystal with only W1 waveguide
- photonic crystal W1 reference test structure

2017/07/16 Jingda Wu
- Adaptive cavity generation under difference waveguide location
- Able to choose the number of waveguides per PhC cavity
- Added etch layer (12,0) on PhC slabs
- Added H0 cavity with oxide buffer, reduced the vertices (32->20) for holes due to much smaller hole radius
- Deleteted cavity hole class
- Added hexagon half cell and hexagon with hole half cell for PhC generation, in case needed
- Added H0 cavity generated with hexagon cells
- Added PhC test pattern

2017/08/19 Jingda Wu
- Added suspension anchor areas for the cavities with undercut

2018/02/14 Lukas Chrostowski
- Upgrade to KLayout 0.25 and SiEPIC-Tools v0.3.x, updating layers to SiEPIC-EBeam v0.3.0+

2021/04/01 lukas
- moved phc and swg cells to beta library


"""

# Import KLayout Python API methods:
# Box, Point, Polygon, Text, Trans, LayerInfo, etc
from pya import *
import pya
import math

from SiEPIC.utils import get_technology_by_name
from SiEPIC.utils import points_per_circle  # ,layout


# -------------------------------------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------------------------------------- #


class PhC_test(pya.PCellDeclarationHelper):
    """
    Input: length, width
    """

    import numpy

    def __init__(self):
        # Important: initialize the super class
        super(PhC_test, self).__init__()

        self.param("a", self.TypeDouble, "lattice constant (microns)", default=0.744)
        self.param("n", self.TypeInt, "Number of holes in x and y direction", default=5)
        self.param("r", self.TypeDouble, "hole radius (microns)", default=0.179)
        self.param("n_sweep", self.TypeInt, "Different sizes of holes", default=13)
        self.param("n_vertices", self.TypeInt, "Vertices of a hole", default=32)
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

    # def display_text_impl(self):
    # Provide a descriptive text for the cell
    # return "PhC resolution test_a%s-r%.3f-n%.3f" % \
    # (self.a, self.r, self.n)

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
        TextLayerN = ly.layer(self.textl)

        # Fetch all the parameters:
        a = self.a / dbu
        r = self.r / dbu
        n_vertices = self.n_vertices
        n = int(math.ceil(self.n / 2))
        # print(n)
        n_sweep = self.n_sweep
        n_x = n
        n_y = n

        # Define Si slab and hole region for future subtraction
        Si_slab = pya.Region()
        hole = pya.Region()
        ruler = pya.Region()
        # hole_r = [r+50,r}
        """
      # translate to array (to pv)
      pv = []
      for p in pcell_decl.get_parameters():
        if p.name in param:
          pv.append(param[p.name])
        else:
          pv.append(p.default)

      pcell_var = self.layout.add_pcell_variant(lib, pcell_decl.id(), pv)
      t_text = pya.Trans(x_offset-2*a_k, -y_offset-a_k*0.5)
      self.cell.insert(pya.CellInstArray(pcell_var, t_text))      
      
      for m in range(0,28):        
        ruler.insert(pya.Box(-x_width+x_offset_2+x_spacing*m, -y_height+y_offset, x_width+x_offset_2+x_spacing*m, y_height+y_offset))
        if m > 23:
          None
        else:
          ruler.insert(pya.Box(-y_height+x_offset_3, -x_width-y_offset_2+x_spacing*m, y_height+x_offset_3, x_width-y_offset_2+x_spacing*m))
        
      for j in range(-n_y,n_y+1):
        if j%2 == 0:
          for i in range(-n_x,n_x+1):
            if i!=0:
              hole_x = abs(i)/i*(abs(i)-0.5)*a_k+x_offset
              hole_y = j*a_k*math.sqrt(3)/2
              hole_trans = pya.Trans(Trans.R0, hole_x,hole_y)
              hole_t = hole_poly.transformed(hole_trans)
              hole.insert(hole_t)
            #print(hole_t) 
        elif j%2 == 1:
          for i in range(-n_x,n_x+1): 
            hole_x = i*a_k+x_offset
            hole_y = j*a_k*math.sqrt(3)/2
            hole_trans = pya.Trans(Trans.R0, hole_x,hole_y)
            hole_t = hole_poly.transformed(hole_trans)
            hole.insert(hole_t) 
        
    phc = Si_slab - hole
    phc = phc + ruler
    self.cell.shapes(LayerSiN).insert(phc)
"""


class Hole_cell_half(pya.PCellDeclarationHelper):
    """
    Input: length, width
    """

    import numpy

    def __init__(self):
        # Important: initialize the super class
        super(Hole_cell_half, self).__init__()

        self.param("a", self.TypeDouble, "lattice constant (microns)", default=0.744)
        self.param("r", self.TypeDouble, "hole radius (microns)", default=0.179)
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
        return "Cavity Hole Cell_a%s-r%.3f" % (self.a, self.r)

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

        # Fetch all the parameters:
        a = self.a / dbu
        r = self.r / dbu

        # function to generate points to create a circle
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

        hole_cell = pya.Region()
        hole_cell_pts = hexagon_hole_half(a, r)
        hole_cell_poly_half = pya.Polygon(hole_cell_pts)

        # hole_cell.insert(hole_cell_poly_0)

        self.cell.shapes(LayerSiN).insert(hole_cell_poly_half)


class Hexagon_cell_half(pya.PCellDeclarationHelper):
    """
    Input: length, width
    """

    import numpy

    def __init__(self):
        # Important: initialize the super class
        super(Hexagon_cell_half, self).__init__()

        self.param("a", self.TypeDouble, "lattice constant (microns)", default=0.744)
        self.param("r", self.TypeDouble, "hole radius (microns)", default=0.179)
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
        return "Cavity Hole Cell_a%s-r%.3f" % (self.a, self.r)

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

        # Fetch all the parameters:
        a = self.a / dbu
        r = self.r / dbu

        # function to generate points to create a circle
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

        hexagon_pts = hexagon_half(a)
        hexagon_cell_poly_half = pya.Polygon(hexagon_pts)

        # hole_cell.insert(hole_cell_poly_0)

        self.cell.shapes(LayerSiN).insert(hexagon_cell_poly_half)


class wg_triangle_tapers(pya.PCellDeclarationHelper):
    """
    The PCell declaration for the strip waveguide taper.
    """

    def __init__(self):
        # Important: initialize the super class
        super(wg_triangle_tapers, self).__init__()

        # declare the parameters
        self.param(
            "tri_base", self.TypeDouble, "Triangle Base (microns)", default=0.363
        )
        self.param(
            "tri_height", self.TypeDouble, "Triangle Height (microns)", default=0.426
        )
        self.param(
            "taper_wg_length", self.TypeDouble, "Waveguide Length (microns)", default=5
        )
        self.param("wg_width", self.TypeDouble, "Waveguide Width (microns)", default=1)
        TECHNOLOGY = get_technology_by_name("EBeam")
        self.param("silayer", self.TypeLayer, "Layer", default=TECHNOLOGY["Si"])
        self.param(
            "pinrec", self.TypeLayer, "PinRec Layer", default=TECHNOLOGY["PinRec"]
        )
        self.param(
            "devrec", self.TypeLayer, "DevRec Layer", default=TECHNOLOGY["DevRec"]
        )
        self.param("textl", self.TypeLayer, "Text Layer", default=TECHNOLOGY["Text"])

    def display_text_impl(self):
        # Provide a descriptive text for the cell
        return "waveguide_triangular_tapers_%.3f-%.3f" % (
            self.taper_wg_length,
            self.wg_width,
        )

    def can_create_from_shape_impl(self):
        return False

    def produce(self, layout, layers, parameters, cell):
        """
        coerce parameters (make consistent)
        """
        self._layers = layers
        self.cell = cell
        self._param_values = parameters
        self.layout = layout
        shapes = self.cell.shapes

        # cell: layout cell to place the layout
        # LayerSiN: which layer to use
        # w: waveguide width
        # length units in dbu

        # fetch the parameters
        dbu = self.layout.dbu
        ly = self.layout

        LayerSi = self.silayer
        LayerSiN = ly.layer(self.silayer)
        LayerPinRecN = ly.layer(self.pinrec)
        LayerDevRecN = ly.layer(self.devrec)
        LayerTextN = ly.layer(self.textl)

        base = int(round(self.tri_base / dbu))
        height = int(round(self.tri_height / dbu))
        l = int(round(self.taper_wg_length / dbu))
        w = int(round(self.wg_width / dbu))

        pts = [
            Point(-l, w / 2),
            Point(-base, w / 2),
            Point(0, w / 2 + height),
            Point(0, -(w / 2 + height)),
            Point(-base, -w / 2),
            Point(-l, -w / 2),
        ]
        shapes(LayerSiN).insert(Polygon(pts))

        # Pins on the bus waveguide side:
        pin_length = 200
        if l < pin_length + 1:
            pin_length = int(l / 3)
            pin_length = math.ceil(pin_length / 2.0) * 2
        if pin_length == 0:
            pin_length = 2

        t = Trans(Trans.R0, -l, 0)
        pin = pya.Path([Point(-pin_length / 2, 0), Point(pin_length / 2, 0)], w)
        pin_t = pin.transformed(t)
        shapes(LayerPinRecN).insert(pin_t)
        text = Text("pin1", t)
        shape = shapes(LayerPinRecN).insert(text)
        shape.text_size = 0.4 / dbu

        t = Trans(Trans.R0, 0, 0)
        pin_t = pin.transformed(t)
        shapes(LayerPinRecN).insert(pin_t)
        text = Text("pin2", t)
        shape = shapes(LayerPinRecN).insert(text)
        shape.text_size = 0.4 / dbu

        # Create the device recognition layer -- make it 1 * wg_width away from the waveguides.
        # box1 = Box(w/2+height, -(w/2+height), -l, -1)
        # shapes(LayerDevRecN).insert(box1)

        return "wg_triangle_taper"


def layout_waveguide_abs(cell, layer, points, w, radius):
    # create a path, then convert to a polygon waveguide with bends
    # cell: cell into which to place the waveguide
    # layer: layer to draw on
    # points: array of vertices, absolute coordinates on the current cell
    # w: waveguide width

    # example usage:
    # cell = pya.Application.instance().main_window().current_view().active_cellview().cell
    # LayerSi = LayerInfo(1, 0)
    # points = [ [15, 2.75], [30, 2.75] ]  # units of microns.
    # layout_waveguide_abs(cell, LayerSi, points, 0.5, 10)

    if MODULE_NUMPY:
        # numpy version
        points = n.array(points)
        start_point = points[0]
        points = points - start_point
    else:
        # without numpy:
        start_point = []
        start_point.append(points[0][0])
        start_point.append(points[0][1])
        for i in range(0, 2):
            for j in range(0, len(points)):
                points[j][i] -= start_point[i]

    layout_waveguide_rel(cell, layer, start_point, points, w, radius)


def layout_waveguide_rel(cell, layer, start_point, points, w, radius):
    # create a path, then convert to a polygon waveguide with bends
    # cell: cell into which to place the waveguide
    # layer: layer to draw on
    # start_point: starting vertex for the waveguide
    # points: array of vertices, relative to start_point
    # w: waveguide width

    # example usage:
    # cell = pya.Application.instance().main_window().current_view().active_cellview().cell
    # LayerSi = LayerInfo(1, 0)
    # points = [ [15, 2.75], [30, 2.75] ]  # units of microns.
    # layout_waveguide_rel(cell, LayerSi, [0,0], points, 0.5, 10)

    # print("* layout_waveguide_rel(%s, %s, %s, %s)" % (cell.name, layer, w, radius) )

    ly = cell.layout()
    dbu = cell.layout().dbu

    start_point = [start_point[0] / dbu, start_point[1] / dbu]

    a1 = []
    for p in points:
        a1.append(pya.DPoint(float(p[0]), float(p[1])))

    wg_path = pya.DPath(a1, w)

    npoints = points_per_circle(radius / dbu)
    param = {
        "npoints": npoints,
        "radius": float(radius),
        "path": wg_path,
        "layer": layer,
    }

    pcell = ly.create_cell("ROUND_PATH", "Basic", param)

    # Configure the cell location
    trans = Trans(Point(start_point[0], start_point[1]))

    # Place the PCell
    cell.insert(pya.CellInstArray(pcell.cell_index(), trans))


class H0c_Test_Structure(pya.PCellDeclarationHelper):
    """
    The PCell declaration for the test structure with grating couplers and waveguides and a photonic crystal cavity
    """

    def __init__(self):
        # Important: initialize the super class
        super(H0c_Test_Structure, self).__init__()

        # taper/wg parameters
        self.param(
            "tri_base", self.TypeDouble, "Taper Triangle Base (microns)", default=0.363
        )
        self.param(
            "tri_height",
            self.TypeDouble,
            "Taper Triangle Height (microns)",
            default=0.426,
        )
        self.param(
            "taper_wg_length", self.TypeDouble, "Taper Length (microns)", default=5
        )
        self.param(
            "wg_bend_radius",
            self.TypeDouble,
            "Waveguide Bend Radius (microns)",
            default=15,
        )

        # photonic crystal cavity
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
            "phc_xdis",
            self.TypeDouble,
            "Distance from GC to middle of Cavity",
            default=35,
        )

        # GC parameters
        self.param(
            "wavelength", self.TypeDouble, "Design Wavelength (micron)", default=2.9
        )
        self.param("n_t", self.TypeDouble, "Fiber Mode", default=1.0)
        self.param("n_e", self.TypeDouble, "Grating Index Parameter", default=3.1)
        self.param("angle_e", self.TypeDouble, "Taper Angle (deg)", default=20.0)
        self.param(
            "grating_length", self.TypeDouble, "Grating Length (micron)", default=32.0
        )
        self.param(
            "taper_length", self.TypeDouble, "Taper Length (micron)", default=32.0
        )
        self.param("dc", self.TypeDouble, "Duty Cycle", default=0.488193)
        self.param("period", self.TypeDouble, "Grating Period", default=1.18939)
        self.param("ff", self.TypeDouble, "Fill Factor", default=0.244319)
        self.param("t", self.TypeDouble, "Waveguide Width (micron)", default=1.0)
        self.param("theta_c", self.TypeDouble, "Insertion Angle (deg)", default=8.0)

        # Layer Parameters
        TECHNOLOGY = get_technology_by_name("EBeam")
        self.param("layer", self.TypeLayer, "Layer", default=TECHNOLOGY["Si"])
        self.param(
            "pinrec", self.TypeLayer, "PinRec Layer", default=TECHNOLOGY["PinRec"]
        )
        self.param(
            "devrec", self.TypeLayer, "DevRec Layer", default=TECHNOLOGY["DevRec"]
        )
        self.param("textl", self.TypeLayer, "Text Layer", default=TECHNOLOGY["Text"])

    def can_create_from_shape_impl(self):
        return False

    def produce_impl(self):
        # This is the main part of the implementation: create the layout

        # fetch the parameters
        dbu = self.layout.dbu
        ly = self.layout
        cell = self.cell
        shapes = self.cell.shapes

        LayerSi = self.layer
        LayerSiN = ly.layer(self.layer)
        LayerPinRecN = ly.layer(self.pinrec)
        LayerDevRecN = ly.layer(self.devrec)
        LayerTextN = ly.layer(self.textl)

        a = self.a
        n = self.n
        wg_dis = self.wg_dis
        phc_xdis = self.phc_xdis
        wg_bend_radius = self.wg_bend_radius
        wg_width = self.t

        if (wg_dis) % 2 == 0:
            length_slab_x = n * a
        else:
            length_slab_x = (n - 1) * a

        half_slab_x = length_slab_x / 2

        param_phc = {
            "a": self.a,
            "n": self.n,
            "r": self.r,
            "wg_dis": self.wg_dis,
            "S1x": self.S1x,
            "S2x": self.S2x,
            "S3x": self.S3x,
            "S4x": self.S4x,
            "S5x": self.S5x,
            "S1y": self.S1y,
            "S2y": self.S2y,
            "layer": LayerSi,
            "pinrec": self.pinrec,
            "devrec": self.devrec,
        }
        pcell_phc = ly.create_cell("H0 cavity with waveguide", "SiQL_PCells", param_phc)
        t_phc = Trans(
            Trans.R0,
            phc_xdis / dbu,
            (127) / dbu - (math.sqrt(3) / 2 * a * (wg_dis + 1)) / dbu,
        )
        instance = cell.insert(pya.CellInstArray(pcell_phc.cell_index(), t_phc))

        param_GC = {
            "wavelength": self.wavelength,
            "n_t": self.n_t,
            "n_e": self.n_e,
            "angle_e": self.angle_e,
            "grating_length": self.grating_length,
            "taper_length": self.taper_length,
            "dc": self.dc,
            "period": self.period,
            "ff": self.ff,
            "t": self.t,
            "theta_c": self.theta_c,
            "layer": LayerSi,
            "pinrec": self.pinrec,
            "devrec": self.devrec,
        }
        pcell_GC = ly.create_cell("SWG Fibre Coupler", "SiQL_PCells", param_GC)
        t_GC = Trans(Trans.R0, 0, 0)
        instance = cell.insert(
            pya.CellInstArray(
                pcell_GC.cell_index(), t_GC, Point(0, 127 / dbu), Point(0, 0), 3, 1
            )
        )

        param_taper = {
            "tri_base": self.tri_base,
            "tri_height": self.tri_height,
            "taper_wg_length": self.taper_wg_length,
            "silayer": LayerSi,
            "pinrec": self.pinrec,
            "devrec": self.devrec,
        }
        pcell_taper = ly.create_cell(
            "Waveguide Triangle Tapers", "SiQL_PCells", param_taper
        )
        t_taper1 = Trans(Trans.R0, (phc_xdis - half_slab_x) / dbu, (127) / dbu)
        instance = cell.insert(pya.CellInstArray(pcell_taper.cell_index(), t_taper1))

        pcell_taper2 = ly.create_cell(
            "Waveguide Triangle Tapers", "SiQL_PCells", param_taper
        )
        t_taper2 = Trans(Trans.R180, (phc_xdis + half_slab_x) / dbu, (127) / dbu)
        instance = cell.insert(pya.CellInstArray(pcell_taper2.cell_index(), t_taper2))

        pcell_taper3 = ly.create_cell(
            "Waveguide Triangle Tapers", "SiQL_PCells", param_taper
        )
        t_taper3 = Trans(
            Trans.R180,
            (phc_xdis + half_slab_x) / dbu,
            (127 - 2 * (wg_dis + 1) * math.sqrt(3) / 2 * a) / dbu,
        )
        instance = cell.insert(pya.CellInstArray(pcell_taper3.cell_index(), t_taper3))

        # gc middle to in port
        points = [[0, 127], [phc_xdis - half_slab_x - self.taper_wg_length, 127]]
        layout_waveguide_abs(cell, LayerSi, points, wg_width, wg_bend_radius)

        # gc top to through port
        points2 = [
            [0, 254],
            [(phc_xdis + half_slab_x + self.taper_wg_length) + wg_bend_radius, 254],
            [(phc_xdis + half_slab_x + self.taper_wg_length) + wg_bend_radius, 127],
            [(phc_xdis + half_slab_x + self.taper_wg_length), 127],
        ]
        layout_waveguide_abs(cell, LayerSi, points2, wg_width, wg_bend_radius)

        # gc bottom to coupled port
        points3 = [
            [0, 0],
            [(phc_xdis + half_slab_x + self.taper_wg_length) + wg_bend_radius, 0],
            [
                (phc_xdis + half_slab_x + self.taper_wg_length) + wg_bend_radius,
                127 - 2 * (wg_dis + 1) * a * math.sqrt(3) / 2,
            ],
            [
                (phc_xdis + half_slab_x + self.taper_wg_length),
                127 - 2 * (wg_dis + 1) * a * math.sqrt(3) / 2,
            ],
        ]
        layout_waveguide_abs(cell, LayerSi, points3, wg_width, wg_bend_radius)


class H0c_oxide_Test_Structure(pya.PCellDeclarationHelper):
    """
    The PCell declaration for the test structure with grating couplers and waveguides and a photonic crystal cavity
    """

    def __init__(self):
        # Important: initialize the super class
        super(H0c_oxide_Test_Structure, self).__init__()

        # taper/wg parameters
        self.param(
            "tri_base", self.TypeDouble, "Taper Triangle Base (microns)", default=0.363
        )
        self.param(
            "tri_height",
            self.TypeDouble,
            "Taper Triangle Height (microns)",
            default=0.426,
        )
        self.param(
            "taper_wg_length", self.TypeDouble, "Taper Length (microns)", default=5
        )
        self.param(
            "wg_bend_radius",
            self.TypeDouble,
            "Waveguide Bend Radius (microns)",
            default=15,
        )

        # photonic crystal cavity
        self.param("a", self.TypeDouble, "lattice constant (microns)", default=0.690)
        self.param(
            "n", self.TypeInt, "Number of holes in x and y direction", default=30
        )
        self.param("r", self.TypeDouble, "hole radius (microns)", default=0.125)
        self.param(
            "wg_dis", self.TypeInt, "Waveguide distance (number of holes)", default=3
        )
        self.param("n_bus", self.TypeInt, "Bus number, 1 or 2 ", default=2)
        self.param("n_vertices", self.TypeInt, "Vertices of a hole", default=20)
        self.param("S1x", self.TypeDouble, "S1x shift", default=0.28)
        self.param("S2x", self.TypeDouble, "S2x shift", default=0.193)
        self.param("S3x", self.TypeDouble, "S3x shift", default=0.194)
        self.param("S4x", self.TypeDouble, "S4x shift", default=0.162)
        self.param("S5x", self.TypeDouble, "S5x shift", default=0.113)
        self.param("S1y", self.TypeDouble, "S1y shift", default=-0.016)
        self.param("S2y", self.TypeDouble, "S2y shift", default=0.134)
        self.param(
            "phc_xdis",
            self.TypeDouble,
            "Distance from GC to middle of Cavity",
            default=35,
        )

        # GC parameters
        self.param(
            "wavelength", self.TypeDouble, "Design Wavelength (micron)", default=2.9
        )
        self.param("n_t", self.TypeDouble, "Fiber Mode", default=1.0)
        self.param("n_e", self.TypeDouble, "Grating Index Parameter", default=3.1)
        self.param("angle_e", self.TypeDouble, "Taper Angle (deg)", default=20.0)
        self.param(
            "grating_length", self.TypeDouble, "Grating Length (micron)", default=32.0
        )
        self.param(
            "taper_length", self.TypeDouble, "Taper Length (micron)", default=32.0
        )
        self.param("dc", self.TypeDouble, "Duty Cycle", default=0.488193)
        self.param("period", self.TypeDouble, "Grating Period", default=1.18939)
        self.param("ff", self.TypeDouble, "Fill Factor", default=0.244319)
        self.param("t", self.TypeDouble, "Waveguide Width (micron)", default=1.0)
        self.param("theta_c", self.TypeDouble, "Insertion Angle (deg)", default=8.0)

        # Layer Parameters
        TECHNOLOGY = get_technology_by_name("EBeam")
        self.param("layer", self.TypeLayer, "Layer", default=TECHNOLOGY["Si"])
        self.param(
            "pinrec", self.TypeLayer, "PinRec Layer", default=TECHNOLOGY["PinRec"]
        )
        self.param(
            "devrec", self.TypeLayer, "DevRec Layer", default=TECHNOLOGY["DevRec"]
        )
        self.param("textl", self.TypeLayer, "Text Layer", default=TECHNOLOGY["Text"])

    def can_create_from_shape_impl(self):
        return False

    def produce_impl(self):
        # This is the main part of the implementation: create the layout

        # fetch the parameters
        dbu = self.layout.dbu
        ly = self.layout
        cell = self.cell
        shapes = self.cell.shapes

        LayerSi = self.layer
        LayerSiN = ly.layer(LayerSi)

        a = self.a
        n = self.n
        wg_dis = self.wg_dis
        phc_xdis = self.phc_xdis
        wg_bend_radius = self.wg_bend_radius
        wg_width = self.t

        if (wg_dis) % 2 == 0:
            length_slab_x = n * a
        else:
            length_slab_x = (n - 1) * a

        half_slab_x = length_slab_x / 2

        param_phc = {
            "a": self.a,
            "n": self.n,
            "r": self.r,
            "wg_dis": self.wg_dis,
            "layer": LayerSi,
            "pinrec": self.pinrec,
            "devrec": self.devrec,
        }
        pcell_phc = ly.create_cell(
            "H0 cavity with waveguide, no etching", "SiQL_PCells", param_phc
        )
        t_phc = Trans(
            Trans.R0,
            phc_xdis / dbu,
            (127) / dbu - (math.sqrt(3) / 2 * a * (wg_dis + 1)) / dbu,
        )
        instance = cell.insert(pya.CellInstArray(pcell_phc.cell_index(), t_phc))

        param_GC = {
            "wavelength": self.wavelength,
            "n_t": self.n_t,
            "n_e": self.n_e,
            "angle_e": self.angle_e,
            "grating_length": self.grating_length,
            "taper_length": self.taper_length,
            "dc": self.dc,
            "period": self.period,
            "ff": self.ff,
            "t": self.t,
            "theta_c": self.theta_c,
            "layer": LayerSi,
            "pinrec": self.pinrec,
            "devrec": self.devrec,
        }
        pcell_GC = ly.create_cell("SWG Fibre Coupler", "SiQL_PCells", param_GC)
        t_GC = Trans(Trans.R0, 0, 0)
        instance = cell.insert(
            pya.CellInstArray(
                pcell_GC.cell_index(), t_GC, Point(0, 127 / dbu), Point(0, 0), 3, 1
            )
        )

        param_taper = {
            "tri_base": self.tri_base,
            "tri_height": self.tri_height,
            "taper_wg_length": self.taper_wg_length,
            "silayer": LayerSi,
            "pinrec": self.pinrec,
            "devrec": self.devrec,
        }
        pcell_taper = ly.create_cell(
            "Waveguide Triangle Tapers", "SiQL_PCells", param_taper
        )
        t_taper1 = Trans(Trans.R0, (phc_xdis - half_slab_x) / dbu, (127) / dbu)
        instance = cell.insert(pya.CellInstArray(pcell_taper.cell_index(), t_taper1))

        pcell_taper2 = ly.create_cell(
            "Waveguide Triangle Tapers", "SiQL_PCells", param_taper
        )
        t_taper2 = Trans(Trans.R180, (phc_xdis + half_slab_x) / dbu, (127) / dbu)
        instance = cell.insert(pya.CellInstArray(pcell_taper2.cell_index(), t_taper2))

        pcell_taper3 = ly.create_cell(
            "Waveguide Triangle Tapers", "SiQL_PCells", param_taper
        )
        t_taper3 = Trans(
            Trans.R180,
            (phc_xdis + half_slab_x) / dbu,
            (127 - 2 * (wg_dis + 1) * math.sqrt(3) / 2 * a) / dbu,
        )
        instance = cell.insert(pya.CellInstArray(pcell_taper3.cell_index(), t_taper3))

        # gc middle to in port
        points = [[0, 127], [phc_xdis - half_slab_x - self.taper_wg_length, 127]]
        layout_waveguide_abs(cell, LayerSi, points, wg_width, wg_bend_radius)

        # gc top to through port
        points2 = [
            [0, 254],
            [(phc_xdis + half_slab_x + self.taper_wg_length) + wg_bend_radius, 254],
            [(phc_xdis + half_slab_x + self.taper_wg_length) + wg_bend_radius, 127],
            [(phc_xdis + half_slab_x + self.taper_wg_length), 127],
        ]
        layout_waveguide_abs(cell, LayerSi, points2, wg_width, wg_bend_radius)

        # gc bottom to coupled port
        points3 = [
            [0, 0],
            [(phc_xdis + half_slab_x + self.taper_wg_length) + wg_bend_radius, 0],
            [
                (phc_xdis + half_slab_x + self.taper_wg_length) + wg_bend_radius,
                127 - 2 * (wg_dis + 1) * a * math.sqrt(3) / 2,
            ],
            [
                (phc_xdis + half_slab_x + self.taper_wg_length),
                127 - 2 * (wg_dis + 1) * a * math.sqrt(3) / 2,
            ],
        ]
        layout_waveguide_abs(cell, LayerSi, points3, wg_width, wg_bend_radius)


class L3c_Test_Structure(pya.PCellDeclarationHelper):
    """
    The PCell declaration for the test structure with grating couplers and waveguides and a photonic crystal cavity
    """

    def __init__(self):
        # Important: initialize the super class
        super(L3c_Test_Structure, self).__init__()

        # taper parameters
        self.param(
            "tri_base", self.TypeDouble, "Taper Triangle Base (microns)", default=0.363
        )
        self.param(
            "tri_height",
            self.TypeDouble,
            "Taper Triangle Height (microns)",
            default=0.426,
        )
        self.param(
            "taper_wg_length", self.TypeDouble, "Taper Length (microns)", default=5
        )
        self.param("w", self.TypeDouble, "Waveguide Width", default=1.0)
        self.param(
            "wg_bend_radius",
            self.TypeDouble,
            "Waveguide Bend Radius (microns)",
            default=15,
        )

        # photonic crystal cavity
        self.param("a", self.TypeDouble, "lattice constant (microns)", default=0.720)
        self.param(
            "n", self.TypeInt, "Number of holes in x and y direction", default=34
        )
        self.param("r", self.TypeDouble, "hole radius (microns)", default=0.181)
        self.param(
            "wg_dis", self.TypeInt, "Waveguide distance (number of holes)", default=3
        )
        self.param("S1x", self.TypeDouble, "S1x shift", default=0.337)
        self.param("S2x", self.TypeDouble, "S2x shift", default=0.27)
        self.param("S3x", self.TypeDouble, "S3x shift", default=0.088)
        self.param("S4x", self.TypeDouble, "S4x shift", default=0.323)
        self.param("S5x", self.TypeDouble, "S5x shift", default=0.0173)
        self.param(
            "phc_xdis",
            self.TypeDouble,
            "Distance from GC to middle of Cavity",
            default=35,
        )

        # GC parameters
        self.param(
            "wavelength", self.TypeDouble, "Design Wavelength (micron)", default=2.9
        )
        self.param("n_t", self.TypeDouble, "Fiber Mode", default=1.0)
        self.param("n_e", self.TypeDouble, "Grating Index Parameter", default=3.1)
        self.param("angle_e", self.TypeDouble, "Taper Angle (deg)", default=20.0)
        self.param(
            "grating_length", self.TypeDouble, "Grating Length (micron)", default=32.0
        )
        self.param(
            "taper_length", self.TypeDouble, "Taper Length (micron)", default=32.0
        )
        self.param("dc", self.TypeDouble, "Duty Cycle", default=0.488193)
        self.param("period", self.TypeDouble, "Grating Period", default=1.18939)
        self.param("ff", self.TypeDouble, "Fill Factor", default=0.244319)
        self.param("t", self.TypeDouble, "Waveguide Width (micron)", default=1.0)
        self.param("theta_c", self.TypeDouble, "Insertion Angle (deg)", default=8.0)

        # Layer Parameters
        TECHNOLOGY = get_technology_by_name("EBeam")
        self.param("layer", self.TypeLayer, "Layer", default=TECHNOLOGY["Si"])
        self.param(
            "pinrec", self.TypeLayer, "PinRec Layer", default=TECHNOLOGY["PinRec"]
        )
        self.param(
            "devrec", self.TypeLayer, "DevRec Layer", default=TECHNOLOGY["DevRec"]
        )
        self.param("textl", self.TypeLayer, "Text Layer", default=TECHNOLOGY["Text"])

    def can_create_from_shape_impl(self):
        return False

    def produce_impl(self):
        # This is the main part of the implementation: create the layout

        # fetch the parameters
        dbu = self.layout.dbu
        ly = self.layout
        cell = self.cell
        shapes = self.cell.shapes

        LayerSi = self.layer
        LayerSiN = ly.layer(self.layer)
        LayerPinRecN = ly.layer(self.pinrec)
        LayerDevRecN = ly.layer(self.devrec)
        LayerTextN = ly.layer(self.textl)

        a = self.a
        n = self.n
        wg_dis = self.wg_dis
        phc_xdis = self.phc_xdis
        wg_bend_radius = self.wg_bend_radius
        wg_width = self.w

        if wg_dis % 2 == 0:
            length_slab_x = (n - 1) * a
        else:
            length_slab_x = n * a

        half_slab_x = length_slab_x / 2

        param_phc = {
            "a": self.a,
            "n": self.n,
            "r": self.r,
            "wg_dis": self.wg_dis,
            "S1x": self.S1x,
            "S2x": self.S2x,
            "S3x": self.S3x,
            "S4x": self.S4x,
            "S5x": self.S5x,
            "layer": self.layer,
            "pinrec": self.pinrec,
            "devrec": self.devrec,
        }
        pcell_phc = ly.create_cell("L3 cavity with waveguide", "SiQL_PCells", param_phc)
        t1 = Trans(
            Trans.R0,
            phc_xdis / dbu,
            (127) / dbu - (math.sqrt(3) / 2 * a * (wg_dis + 1)) / dbu,
        )
        instance = cell.insert(pya.CellInstArray(pcell_phc.cell_index(), t1))

        param_GC = {
            "wavelength": self.wavelength,
            "n_t": self.n_t,
            "n_e": self.n_e,
            "angle_e": self.angle_e,
            "grating_length": self.grating_length,
            "taper_length": self.taper_length,
            "dc": self.dc,
            "period": self.period,
            "ff": self.ff,
            "t": self.t,
            "theta_c": self.theta_c,
            "layer": LayerSi,
            "pinrec": self.pinrec,
            "devrec": self.devrec,
        }
        pcell_GC = ly.create_cell("SWG Fibre Coupler", "SiQL_PCells", param_GC)
        t_GC = Trans(Trans.R0, 0, 0)
        instance = cell.insert(
            pya.CellInstArray(
                pcell_GC.cell_index(), t_GC, Point(0, 127 / dbu), Point(0, 0), 3, 1
            )
        )

        param_taper = {
            "tri_base": self.tri_base,
            "tri_height": self.tri_height,
            "taper_wg_length": self.taper_wg_length,
            "wg_width": self.w,
            "silayer": LayerSi,
            "pinrec": self.pinrec,
            "devrec": self.devrec,
        }
        pcell_taper = ly.create_cell(
            "Waveguide Triangle Tapers", "SiQL_PCells", param_taper
        )
        t_taper1 = Trans(Trans.R0, (phc_xdis - half_slab_x) / dbu, (127) / dbu)
        instance = cell.insert(pya.CellInstArray(pcell_taper.cell_index(), t_taper1))

        pcell_taper2 = ly.create_cell(
            "Waveguide Triangle Tapers", "SiQL_PCells", param_taper
        )
        t_taper2 = Trans(Trans.R180, (phc_xdis + half_slab_x) / dbu, (127) / dbu)
        instance = cell.insert(pya.CellInstArray(pcell_taper2.cell_index(), t_taper2))

        pcell_taper3 = ly.create_cell(
            "Waveguide Triangle Tapers", "SiQL_PCells", param_taper
        )
        t_taper3 = Trans(
            Trans.R180,
            (phc_xdis + half_slab_x) / dbu,
            (127 - 2 * (wg_dis + 1) * math.sqrt(3) / 2 * a) / dbu,
        )
        instance = cell.insert(pya.CellInstArray(pcell_taper3.cell_index(), t_taper3))

        # gc middle to in port
        points = [[0, 127], [phc_xdis - half_slab_x - self.taper_wg_length, 127]]
        layout_waveguide_abs(cell, LayerSi, points, wg_width, wg_bend_radius)

        # gc top to through port
        points2 = [
            [0, 254],
            [(phc_xdis + half_slab_x + self.taper_wg_length) + wg_bend_radius, 254],
            [(phc_xdis + half_slab_x + self.taper_wg_length) + wg_bend_radius, 127],
            [(phc_xdis + half_slab_x + self.taper_wg_length), 127],
        ]
        layout_waveguide_abs(cell, LayerSi, points2, wg_width, wg_bend_radius)

        # gc bottom to coupled port
        points3 = [
            [0, 0],
            [(phc_xdis + half_slab_x + self.taper_wg_length) + wg_bend_radius, 0],
            [
                (phc_xdis + half_slab_x + self.taper_wg_length) + wg_bend_radius,
                127 - 2 * (wg_dis + 1) * a * math.sqrt(3) / 2,
            ],
            [
                (phc_xdis + half_slab_x + self.taper_wg_length),
                127 - 2 * (wg_dis + 1) * a * math.sqrt(3) / 2,
            ],
        ]
        layout_waveguide_abs(cell, LayerSi, points3, wg_width, wg_bend_radius)


class GC_to_GC_ref1(pya.PCellDeclarationHelper):
    """
    The PCell declaration for the test structure with grating couplers and waveguides and a photonic crystal cavity
    """

    def __init__(self):
        # Important: initialize the super class
        super(GC_to_GC_ref1, self).__init__()

        # other waveguide parameters
        self.param(
            "wg_radius", self.TypeDouble, "Waveguide Radius (microns)", default=15
        )
        self.param(
            "wg_width", self.TypeDouble, "Waveguide x Distance (microns)", default=1
        )
        self.param(
            "wg_xdis", self.TypeDouble, "Waveguide x Distance (microns)", default=5
        )

        # Layer Parameters
        TECHNOLOGY = get_technology_by_name("EBeam")
        self.param("layer", self.TypeLayer, "Layer", default=TECHNOLOGY["Si"])
        self.param(
            "pinrec", self.TypeLayer, "PinRec Layer", default=TECHNOLOGY["PinRec"]
        )
        self.param(
            "devrec", self.TypeLayer, "DevRec Layer", default=TECHNOLOGY["DevRec"]
        )
        self.param("textl", self.TypeLayer, "Text Layer", default=TECHNOLOGY["Text"])

    def can_create_from_shape_impl(self):
        return False

    def produce_impl(self):
        # This is the main part of the implementation: create the layout

        # fetch the parameters
        dbu = self.layout.dbu
        ly = self.layout
        cell = self.cell
        shapes = self.cell.shapes

        LayerSi = self.layer
        LayerSiN = ly.layer(self.layer)
        LayerPinRecN = ly.layer(self.pinrec)
        LayerDevRecN = ly.layer(self.devrec)
        LayerTextN = ly.layer(self.textl)

        wg_r = self.wg_radius
        wg_w = self.wg_width
        wg_xdis = self.wg_xdis

        # uses the default parameters for the GC
        param_GC = {"layer": LayerSi, "pinrec": self.pinrec, "devrec": self.devrec}
        pcell_GC = ly.create_cell("SWG Fibre Coupler", "SiQL_PCells", param_GC)
        t_GC = Trans(Trans.R0, 0, 0)
        # instance = cell.insert(pya.place_cell(pcell_GC, t_GC, Point(0,127/dbu), Point(0,0), 2, 1))
        # instance=place_cell(cell,pcell_GC,[0.5,0.5])
        cell.insert(
            pya.CellInstArray(pcell_GC.cell_index(), pya.Trans(pya.Trans.R0, 0, 0))
        )
        print("test")
        return

        points = [[0, 0], [wg_r + wg_xdis, 0], [wg_r + wg_xdis, 127], [0, 127]]
        # layout_waveguide_abs(cell, LayerSi, points, wg_w, wg_r)


class PhC_W1wg_reference(pya.PCellDeclarationHelper):
    """
    Input: length, width
    """

    import numpy

    def __init__(self):
        # Important: initialize the super class
        super(PhC_W1wg_reference, self).__init__()

        # phc parameters
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
        self.param("phc_xdis", self.TypeDouble, "Distance to middle of phc", default=35)

        # other waveguide parameters
        self.param(
            "wg_radius", self.TypeDouble, "Waveguide Radius (microns)", default=15
        )
        self.param("wg_width", self.TypeDouble, "Waveguide Radius (microns)", default=1)

        # taper parameters
        self.param(
            "tri_base", self.TypeDouble, "Taper Triangle Base (microns)", default=0.363
        )
        self.param(
            "tri_height",
            self.TypeDouble,
            "Taper Triangle Height (microns)",
            default=0.426,
        )
        self.param(
            "taper_wg_length", self.TypeDouble, "Taper Length (microns)", default=5
        )

        # Layer Parameters
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

    def can_create_from_shape_impl(self):
        return False

    def produce_impl(self):
        # This is the main part of the implementation: create the layout

        # fetch the parameters
        dbu = self.layout.dbu
        ly = self.layout
        cell = self.cell
        shapes = self.cell.shapes

        LayerSi = self.layer
        LayerSiN = ly.layer(self.layer)
        LayerPinRecN = ly.layer(self.pinrec)
        LayerDevRecN = ly.layer(self.devrec)
        LayerTextN = ly.layer(self.textl)

        wg_r = self.wg_radius
        wg_w = self.wg_width
        phc_xdis = self.phc_xdis
        wg_dis = self.wg_dis
        a = self.a
        w = self.wg_width
        n = self.n
        etch_condition = self.etch_condition

        param_GC = {"layer": LayerSi, "pinrec": self.pinrec, "devrec": self.devrec}
        pcell_GC = ly.create_cell("SWG Fibre Coupler", "SiQL_PCells", param_GC)
        t_GC = Trans(Trans.R0, 0, 0)
        instance = cell.insert(
            pya.CellInstArray(
                pcell_GC.cell_index(), t_GC, Point(0, 127 / dbu), Point(0, 0), 2, 1
            )
        )

        if etch_condition == 1:
            param_phc = {
                "a": self.a,
                "n": self.n,
                "r": self.r,
                "n_bus": 1,
                "wg_dis": wg_dis,
                "etch_condition": etch_condition,
                "layer": LayerSi,
                "n_vertices": self.n_vertices,
                "pinrec": self.pinrec,
                "devrec": self.devrec,
                "etch": self.etch,
            }
            pcell_phc = ly.create_cell(
                "H0 cavity with waveguide", "SiQL_PCells", param_phc
            )
            t = Trans(
                Trans.R0,
                phc_xdis / dbu,
                0 - ((wg_dis + 1) * math.sqrt(3) / 2 * a) / dbu,
            )
            instance = cell.insert(pya.CellInstArray(pcell_phc.cell_index(), t))
        else:
            param_phc = {
                "a": self.a,
                "n": self.n,
                "r": self.r,
                "n_bus": 1,
                "wg_dis": wg_dis,
                "layer": LayerSi,
                "n_vertices": self.n_vertices,
                "pinrec": self.pinrec,
                "devrec": self.devrec,
                "etch": self.etch,
            }
            pcell_phc = ly.create_cell(
                "H0 cavity with waveguide, no etching", "SiQL_PCells", param_phc
            )
            t = Trans(
                Trans.R0,
                phc_xdis / dbu,
                0 - ((wg_dis + 1) * math.sqrt(3) / 2 * a) / dbu,
            )
            instance = cell.insert(pya.CellInstArray(pcell_phc.cell_index(), t))

        param_taper = {
            "tri_base": self.tri_base,
            "tri_height": self.tri_height,
            "taper_wg_length": self.taper_wg_length,
            "wg_width": w,
            "silayer": LayerSi,
            "pinrec": self.pinrec,
            "devrec": self.devrec,
        }
        pcell_taper = ly.create_cell(
            "Waveguide Triangle Tapers", "SiQL_PCells", param_taper
        )
        t_taper1 = Trans(Trans.R0, (phc_xdis - n * a / 2) / dbu, 0)
        instance = cell.insert(pya.CellInstArray(pcell_taper.cell_index(), t_taper1))

        pcell_taper2 = ly.create_cell(
            "Waveguide Triangle Tapers", "SiQL_PCells", param_taper
        )
        t_taper2 = Trans(Trans.R180, (phc_xdis + n * a / 2) / dbu, 0)
        instance = cell.insert(pya.CellInstArray(pcell_taper2.cell_index(), t_taper2))

        points = [[0, 0], [phc_xdis - n * a / 2 - self.taper_wg_length, 0]]
        layout_waveguide_abs(cell, LayerSi, points, wg_w, wg_r)

        points2 = [
            [phc_xdis + n * a / 2 + self.taper_wg_length, 0],
            [phc_xdis + n * a / 2 + self.taper_wg_length + wg_r, 0],
            [phc_xdis + n * a / 2 + self.taper_wg_length + wg_r, 127],
            [0, 127],
        ]
        layout_waveguide_abs(cell, LayerSi, points2, wg_w, wg_r)
