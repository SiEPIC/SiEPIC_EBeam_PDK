import pya
from pya import *
from SiEPIC.utils import get_technology, get_technology_by_name
from SiEPIC.utils import arc, arc_wg, arc_to_waveguide, points_per_circle#,layout
import math

class phc_test(pya.PCellDeclarationHelper):
  """
  Input: length, width
  """
  import numpy
    
  def __init__(self):

    # Important: initialize the super class
    super(phc_test, self).__init__()

    self.param("a", self.TypeDouble, "lattice constant (microns)", default = 0.744)     
    self.param("n", self.TypeInt, "Number of holes in x and y direction", default = 5)     
    self.param("r", self.TypeDouble, "hole radius (microns)", default = 0.179)
    self.param("n_sweep", self.TypeInt, "Different sizes of holes", default = 13)
    self.param("n_vertices", self.TypeInt, "Vertices of a hole", default = 32)                                
    TECHNOLOGY = get_technology_by_name('EBeam')
    self.param("layer", self.TypeLayer, "Layer", default = TECHNOLOGY['Si'])
    self.param("pinrec", self.TypeLayer, "PinRec Layer", default = TECHNOLOGY['PinRec'])
    self.param("devrec", self.TypeLayer, "DevRec Layer", default = TECHNOLOGY['DevRec'])
    self.param("textl", self.TypeLayer, "Text Layer", default = TECHNOLOGY['Text'])
    self.param("etch", self.TypeLayer, "oxide etch layer", default = pya.LayerInfo(12, 0))


  #def display_text_impl(self):
    # Provide a descriptive text for the cell
   # return "PhC resolution test_a%s-r%.3f-n%.3f" % \
    #(self.a, self.r, self.n)
  
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
    a = self.a/dbu
    r = self.r/dbu
    n_vertices = self.n_vertices
    n = int(math.ceil(self.n/2))
    #print(n)
    n_sweep = self.n_sweep
    n_x = n
    n_y = n
  

    # Define Si slab and hole region for future subtraction
    Si_slab = pya.Region()
    hole = pya.Region()
    ruler = pya.Region()
    #hole_r = [r+50,r}
    '''
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
'''
