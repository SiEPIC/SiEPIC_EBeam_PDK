from pya import *
import pya
import math

from SiEPIC.utils import get_technology, get_technology_by_name
from SiEPIC.utils import arc, arc_wg, arc_to_waveguide, points_per_circle#,layout

class PhC_wg_triangle_tapers(pya.PCellDeclarationHelper):
  """
  The PCell declaration for the strip waveguide taper.
  """

  def __init__(self):

    # Important: initialize the super class
    super(PhC_wg_triangle_tapers, self).__init__()

    # declare the parameters
    self.param("tri_base", self.TypeDouble, "Triangle Base (microns)", default = 0.363)
    self.param("tri_height", self.TypeDouble, "Triangle Height (microns)", default = 0.426)
    self.param("taper_wg_length", self.TypeDouble, "Waveguide Length (microns)", default = 5)
    self.param("wg_width", self.TypeDouble, "Waveguide Width (microns)", default = 1)
    TECHNOLOGY = get_technology_by_name('EBeam')
    self.param("silayer", self.TypeLayer, "Layer", default = TECHNOLOGY['Waveguide'])
    self.param("pinrec", self.TypeLayer, "PinRec Layer", default = TECHNOLOGY['PinRec'])
    self.param("devrec", self.TypeLayer, "DevRec Layer", default = TECHNOLOGY['DevRec'])
    self.param("textl", self.TypeLayer, "Text Layer", default = TECHNOLOGY['Text'])
    
  def display_text_impl(self):
    # Provide a descriptive text for the cell
    return "waveguide_triangular_tapers_%.3f-%.3f" % (self.taper_wg_length, self.wg_width)
  
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
    
    base = int(round(self.tri_base/dbu))
    height = int(round(self.tri_height/dbu))
    l = int(round(self.taper_wg_length/dbu))
    w = int(round(self.wg_width/dbu)) 
    
    pts = [Point(-l,w/2), Point(-base,w/2), Point(0,w/2+height), Point(0,-(w/2+height)), Point(-base,-w/2),Point(-l,-w/2) ]
    shapes(LayerSiN).insert(Polygon(pts))
    
    # Pins on the bus waveguide side:
    pin_length = 200
    if l < pin_length+1:
      pin_length = int(l/3)
      pin_length = math.ceil(pin_length / 2.) * 2
    if pin_length == 0:
      pin_length = 2

    t = Trans(Trans.R0, -l,0)
    pin = pya.Path([Point(-pin_length/2, 0), Point(pin_length/2, 0)], w)
    pin_t = pin.transformed(t)
    shapes(LayerPinRecN).insert(pin_t)
    text = Text ("pin1", t)
    shape = shapes(LayerPinRecN).insert(text)
    shape.text_size = 0.4/dbu

    t = Trans(Trans.R0, 0,0)
    pin_t = pin.transformed(t)
    shapes(LayerPinRecN).insert(pin_t)
    text = Text ("pin2", t)
    shape = shapes(LayerPinRecN).insert(text)
    shape.text_size = 0.4/dbu
    
    # Create the device recognition layer -- make it 1 * wg_width away from the waveguides.
    #box1 = Box(w/2+height, -(w/2+height), -l, -1)
    #shapes(LayerDevRecN).insert(box1)


    return "wg_triangle_taper" 
    
    