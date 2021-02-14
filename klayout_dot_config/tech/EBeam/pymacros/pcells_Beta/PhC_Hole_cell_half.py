from pya import *
import pya
import math

from SiEPIC.utils import get_technology, get_technology_by_name
from SiEPIC.utils import arc, arc_wg, arc_to_waveguide, points_per_circle#,layout

class PhC_Hole_cell_half(pya.PCellDeclarationHelper):
  """
  Input: length, width
  """
  import numpy
  
  def __init__(self):

    # Important: initialize the super class
    super(PhC_Hole_cell_half, self).__init__()

    self.param("a", self.TypeDouble, "lattice constant (microns)", default = 0.744)     
    self.param("r", self.TypeDouble, "hole radius (microns)", default = 0.179)
    TECHNOLOGY = get_technology_by_name('EBeam')
    self.param("layer", self.TypeLayer, "Layer", default = TECHNOLOGY['Waveguide'])
    self.param("pinrec", self.TypeLayer, "PinRec Layer", default = TECHNOLOGY['PinRec'])
    self.param("devrec", self.TypeLayer, "DevRec Layer", default = TECHNOLOGY['DevRec'])
    self.param("textl", self.TypeLayer, "Text Layer", default = TECHNOLOGY['Text'])

  def display_text_impl(self):
    # Provide a descriptive text for the cell
    return "Cavity Hole Cell_a%s-r%.3f" % \
    (self.a, self.r)
  
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
    a = self.a/dbu
    r = self.r/dbu

    # function to generate points to create a circle
    def hexagon_hole_half(a,r): 
      npts = 10    
      theta_div = math.pi/3
      theta_div_hole = math.pi/npts
      triangle_length = a/math.sqrt(3)
      pts = []
      for i in range(0,4):
        pts.append(Point.from_dpoint(pya.DPoint(triangle_length*math.cos(i*theta_div-math.pi/2), triangle_length*math.sin(i*theta_div-math.pi/2))))
      for i in range(0, npts+1):
        pts.append(Point.from_dpoint(pya.DPoint(r*math.cos(math.pi/2-i*theta_div_hole), r*math.sin(math.pi/2-i*theta_div_hole))))
      return pts
 
    hole_cell = pya.Region()
    hole_cell_pts = hexagon_hole_half(a,r)
    hole_cell_poly_half = pya.Polygon(hole_cell_pts)

    #hole_cell.insert(hole_cell_poly_0)
    
    self.cell.shapes(LayerSiN).insert(hole_cell_poly_half)
    