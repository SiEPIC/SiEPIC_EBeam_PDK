"""
This file is part of the SiEPIC_EBeam_PDK

NOTE: after changing the code, the macro needs to be rerun to install the new
implementation. The macro is also set to "auto run" to install the PCell 
when KLayout is run.
"""
import math
from SiEPIC.utils import get_technology, get_technology_by_name

# Import KLayout Python API methods:
# Box, Point, Polygon, Text, Trans, LayerInfo, etc
from pya import *

"""
class ebeam_Bent_Bragg(PCellDeclarationHelper):

  #The PCell declaration for the bent Bragg gratings pcell

  def __init__(self):

    # Important: initialize the super class
    super(ebeam_Bent_Bragg, self).__init__()
    TECHNOLOGY = get_technology_by_name('EBeam')

    # declare the parameters
    self.param("silayer", self.TypeLayer, "Si Layer", default = TECHNOLOGY['Waveguide'])
    self.param("silayer_gratings", self.TypeLayer, "Si Gratings Layer", default = TECHNOLOGY['31_Si_p6nm'])
    self.param("radius", self.TypeDouble, "Radius (um)", default = 25)
    self.param("width", self.TypeDouble, "Width (um)", default = 0.5)
    
    self.param("period", self.TypeDouble, "Gratings Period (nm)", default = 318)
    self.param("deltaW", self.TypeDouble, "Corrugation Width (um)", default = 0.04)
    
    self.param("gamma", self.TypeDouble, "N (number of corrugations)", default = 135)
    
    self.param("pinrec", self.TypeLayer, "PinRec Layer", default = TECHNOLOGY['PinRec'])
    self.param("devrec", self.TypeLayer, "DevRec Layer", default = TECHNOLOGY['DevRec'])


  def display_text_impl(self):
    # Provide a descriptive text for the cell
    return "Bent_Bragg(R=" + ('%.3f' % self.radius) + ")"

  def produce(self, layout, layers, parameters, cell):
    
    #coerce parameters (make consistent)
    
    self._layers = layers
    self.cell = cell
    self._param_values = parameters
    self.layout = layout


    # cell: layout cell to place the layout
    # LayerSiN: which layer to use
    # r: radius
    # w: waveguide width
    # length units in dbu

    from math import pi, cos, sin
    from SiEPIC.utils import arc_wg, arc_wg_xy
    from SiEPIC._globals import PIN_LENGTH
    
    # fetch the parameters
    dbu = self.layout.dbu
    ly = self.layout
    
    LayerSi = self.silayer
    LayerSiN_gratings = self.silayer_gratings_layer
    LayerSiN = self.silayer_layer
    LayerPinRecN = ly.layer(self.pinrec)
    LayerDevRecN = ly.layer(self.devrec)
    
    from SiEPIC.extend import to_itype
    w = to_itype(self.width,dbu)
    r = to_itype(self.radius,dbu)
    period = self.period
    deltaW = to_itype(self.deltaW,dbu)
    N = int(self.gamma)

    # Center of everything
    x = 0
    y = 0

    # Angle of  Bragg corrugated portion, also bend angle!
    periodAngle = (180/pi) * (period/2) /r 
    
    # Bend angle
    bendAngle = (180/pi) * (N*period/2) /r
    
    N_input = N;
    # Normalized number of corrugations to periodAngle
    N = N*periodAngle*2;

   # Bragg wide
    ii = periodAngle*2
    while ii < N+periodAngle*1.5:
      self.cell.shapes(LayerSiN_gratings).insert(arc_wg_xy(x,y, r, w+deltaW, 90+bendAngle-ii, 90+bendAngle-ii-periodAngle))
      ii = ii+periodAngle
      ii = ii+periodAngle


    # Bragg narrow
    ii = periodAngle
    while ii < N:
      self.cell.shapes(LayerSiN_gratings).insert(arc_wg_xy(x,y, r, w-deltaW, 90+bendAngle-ii, 90+bendAngle-ii-periodAngle))
      ii = ii+periodAngle
      ii = ii+periodAngle



    # bend non-corrugated left
    self.cell.shapes(LayerSiN).insert(arc_wg_xy(x,y, r, w, 180-(90-bendAngle), 180))
    
    # bend non-corrugated right
    self.cell.shapes(LayerSiN).insert(arc_wg_xy(x,y, r, w, 0, 90-bendAngle))
    
    bendAngleRad = (pi/180) * bendAngle
    
    # Create the pins, as short paths:
    from SiEPIC._globals import PIN_LENGTH as pin_length    
    
    # Pin on the bottom left side:
    p1 = [Point(x-r, pin_length/2 +y), Point(x-r, -pin_length/2 +y)]
    p1c = Point(x-r, y)
    self.set_p1 = p1c
    self.p1 = p1c
    pin = Path(p1, w)
    self.cell.shapes(LayerPinRecN).insert(pin)
    t = Trans(Trans.R0, x-r, y)
    text = Text ("opt1", t)
    shape = self.cell.shapes(LayerPinRecN).insert(text)
    shape.text_size = 0.4/dbu

    # Pin on the bottom right side:
    p2 = [Point(x+r, y+pin_length/2), Point(x+r,y-pin_length/2)]
    p2c = Point(x+r,y)
    self.set_p2 = p2c
    self.p2 = p2c
    pin = Path(p2, w)
    self.cell.shapes(LayerPinRecN).insert(pin)
    t = Trans(Trans.R0, x+r, y)
    text = Text ("opt2", t)
    shape = self.cell.shapes(LayerPinRecN).insert(text)
    shape.text_size = 0.4/dbu


    # Create the device recognition layer -- make it 1 * wg_width away from the waveguides.
    self.cell.shapes(LayerDevRecN).insert(arc_wg_xy(x ,y, r, w*5, 0, 180))

    


class SiEPIC_Demo(Library):
  
  #The library where we will put the PCells and GDS into 
  

  def __init__(self):
  
    tech_name = 'EBeam_Personal'
    library = tech_name
    
    print("Initializing '%s' Library." % library)

    # Set the description
# windows only allows for a fixed width, short description 
    self.description = ""
# OSX does a resizing:
    self.description = "This is my first library!"
       
    # Create the PCell declarations
    #self.layout().register_pcell("ebeam_Bent_Bragg", ebeam_Bent_Bragg())

    # Register the library with the technology name
    # If a library with that name already existed, it will be replaced then.
    self.register(library)

    self.technology='EBeam'
 
# Instantiate and register the library
SiEPIC_Demo()

"""