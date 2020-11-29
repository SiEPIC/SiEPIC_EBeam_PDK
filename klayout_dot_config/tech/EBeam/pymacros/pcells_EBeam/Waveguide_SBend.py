from . import *

class Waveguide_SBend(pya.PCellDeclarationHelper):
  """
  Input: 
  """
  def __init__(self):


    # Important: initialize the super class
    super(Waveguide_SBend, self).__init__()
    TECHNOLOGY = get_technology_by_name('EBeam')

    # declare the parameters
    self.param("length", self.TypeDouble, "Waveguide length", default = 10.0)     
    self.param("height", self.TypeDouble, "Waveguide offset height", default = 2)     
    self.param("wg_width", self.TypeDouble, "Waveguide width (microns)", default = 0.5)     
    self.param("radius", self.TypeDouble, "Waveguide bend radius (microns)", default = 5)     
    self.param("layer", self.TypeLayer, "Layer", default = TECHNOLOGY['Si'])
    self.param("pinrec", self.TypeLayer, "PinRec Layer", default = TECHNOLOGY['PinRec'])
    self.param("devrec", self.TypeLayer, "DevRec Layer", default = TECHNOLOGY['DevRec'])


  def display_text_impl(self):
    # Provide a descriptive text for the cell
    return "Waveguide_SBend_%s-%.3f" % \
    (self.length, self.wg_width)
  
  def coerce_parameters_impl(self):
    pass


  def can_create_from_shape(self, layout, shape, layer):
    return False
    
  def produce_impl(self):
  
    # fetch the parameters
    dbu = self.layout.dbu
    ly = self.layout
    shapes = self.cell.shapes

    from SiEPIC.utils.layout import layout_waveguide_sbend

    LayerSi = self.layer
    LayerSiN = ly.layer(LayerSi)
    LayerPinRecN = ly.layer(self.pinrec)
    LayerDevRecN = ly.layer(self.devrec)

    length = self.length / dbu
    w = self.wg_width / dbu
    r = self.radius / dbu
    h = self.height / dbu
   
    waveguide_length = layout_waveguide_sbend(self.cell, LayerSiN, pya.Trans(Trans.R0, 0,0), w, r, h, length)
    
    from SiEPIC._globals import PIN_LENGTH as pin_length

    # Pins on the waveguide:
    x = waveguide_length
    t = Trans(Trans.R0, x,h)
    pin = Path([Point(-pin_length/2,0), Point(pin_length/2,0)], w)
    pin_t = pin.transformed(t)
    shapes(LayerPinRecN).insert(pin_t)
    text = Text ("pin2", t)
    shape = shapes(LayerPinRecN).insert(text)
    shape.text_size = 0.4/dbu
    shape.text_halign = 2

    x = 0
    t = Trans(Trans.R0, x,0)
    pin = Path([Point(pin_length/2,0), Point(-pin_length/2,0)], w)
    pin_t = pin.transformed(t)
    shapes(LayerPinRecN).insert(pin_t)
    text = Text ("pin1", t)
    shape = shapes(LayerPinRecN).insert(text)
    shape.text_size = 0.4/dbu


    # Compact model information
    t = Trans(Trans.R0, 0, 0)
    text = Text ('Lumerical_INTERCONNECT_library=Design kits/EBeam', t)
    shape = shapes(LayerDevRecN).insert(text)
    shape.text_size = 0.1/dbu
    t = Trans(Trans.R0, 0, w*2)
    text = Text ('Component=ebeam_wg_integral_1550', t)
    shape = shapes(LayerDevRecN).insert(text)
    shape.text_size = 0.1/dbu
    t = Trans(Trans.R0, 0, -w*2)
    text = Text \
      ('Spice_param:wg_length=%.3fu wg_width=%.3fu' %\
      (waveguide_length*dbu, self.wg_width), t )
    shape = shapes(LayerDevRecN).insert(text)
    shape.text_size = 0.1/dbu
#    t = Trans(Trans.R0, 0, -w*3)
#    text = Text ('Extra length = %.4fu, Shortest length = %.4fu' % (straight_l*dbu, (length-2*straight_l)*dbu), t )
#    shape = shapes(LayerDevRecN).insert(text)
#    shape.text_size = 0.1/dbu

    # Create the device recognition layer -- make it 1 * wg_width away from the waveguides.
    box1 = Box(0, min(-w*3,h-w*3), waveguide_length, max(w*3,h+w*3))
    shapes(LayerDevRecN).insert(box1)
    
#    print('2020/11/28 update')