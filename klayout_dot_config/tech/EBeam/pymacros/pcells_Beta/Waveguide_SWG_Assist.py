"""
    Sub-wavelength-assisted waveguide PCell
    
    Author:     Mustafa Hammood
    Email:      Mustafa@siepic.com
    Affl:       SiEPIC Kits Ltd.
    Copyright 2021
"""

import pya
from pya import *
from SiEPIC.utils import get_technology_by_name

def make_pin(cell, name, center, w, pin_length, layer, vertical = 0):
  """Handy method to create a pin on a device to avoid repetitive code.

  Args:
      cell (pya cell): cell to create the pin on
      name (string): name of the pin
      center (list): center of the pin in dbu. Format: [x, y]
      w (int): width of the pin in dbu
      pin_length (int): length of the pin in dbu, change the sign to determine pin direction. Default is left-to-right.
      layer (pya layer): layer to create the pin on
      vertical (int, optional): flag to determine if pin is vertical or horizontal. Defaults to 0.
  """
  if vertical == 0:
    p1 = pya.Point(center[0]+pin_length/2, center[1])
    p2 = pya.Point(center[0]-pin_length/2, center[1])
  elif vertical == 1:
    p1 = pya.Point(center[0], center[1]+pin_length/2)
    p2 = pya.Point(center[0], center[1]-pin_length/2)
    
  pin = pya.Path([p1,p2],w)
  t = Trans(Trans.R0, center[0],center[1])
  text = Text (name, t)
  shape = cell.shapes(layer).insert(text)
  shape.text_size = 0.1
  cell.shapes(layer).insert(pin)

  return shape

class Waveguide_SWG_Assist(pya.PCellDeclarationHelper):

  def __init__(self):

    # Important: initialize the super class
    super(Waveguide_SWG_Assist, self).__init__()
    TECHNOLOGY = get_technology_by_name('EBeam')

    # declare the parameters
    self.param("length", self.TypeDouble, "Waveguide length", default = 10.0)     
    self.param("target_period", self.TypeDouble, "Target period (microns)", default = 0.200)     
    self.param("swg_wg_width", self.TypeDouble, "SWG Waveguide width", default = 0.5)     
    self.param("strip_wg_width", self.TypeDouble, "Strip Waveguide width", default = 0.06)     
    self.param("duty", self.TypeDouble, "Duty Cycle (0 to 1)", default = 0.5)
    self.param("layer", self.TypeLayer, "Layer", default = TECHNOLOGY['Waveguide'])
    self.param("pinrec", self.TypeLayer, "PinRec Layer", default = TECHNOLOGY['PinRec'])
    self.param("devrec", self.TypeLayer, "DevRec Layer", default = TECHNOLOGY['DevRec'])

  def display_text_impl(self):
    # Provide a descriptive text for the cell
    return "Waveguide_SWG_Assist_%s-%.3f-%.3f-%.3f-%.3f" % \
    (self.length, self.target_period, self.swg_wg_width, self.strip_wg_width, self.duty)
  
  def coerce_parameters_impl(self):
    pass

  def can_create_from_shape(self, layout, shape, layer):
    return False
    
  def produce_impl(self):
  
    # fetch the parameters
    dbu = self.layout.dbu
    ly = self.layout
    shapes = self.cell.shapes

    LayerSi = self.layer
    LayerSiN = ly.layer(LayerSi)
    LayerPinRecN = ly.layer(self.pinrec)
    LayerDevRecN = ly.layer(self.devrec)

    # Determine the period such that the waveguide length is as desired.  Slight adjustment to period
    N_boxes = int(round(self.length / self.target_period-0.5))
    grating_period = self.length / (N_boxes) / dbu

    # Draw the Bragg grating:
    box_width = int(round(grating_period*self.duty))
    
    w = self.swg_wg_width / dbu
    half_w = w/2
    for i in range(0,N_boxes+1):
      x = int(round((i * grating_period - box_width/2)))
      box1 = Box(x, -half_w, x + box_width, half_w)
      shapes(LayerSiN).insert(box1)
    length = self.length / dbu

    # Strip waveguide:
    w_strip = self.strip_wg_width / dbu
    if w_strip > 0:
        box1 = Box(0, -w_strip/2, length, w_strip/2)
        shapes(LayerSiN).insert(box1)

    # Create the device recognition layer
    points = [pya.Point(0,0), pya.Point(length, 0)]
    path = pya.Path(points,w)
    path = pya.Path(points,w*3)
    shapes(LayerDevRecN).insert(path.simple_polygon())

    # Pins on the waveguide:
    from SiEPIC._globals import PIN_LENGTH as pin_length
    make_pin(self.cell, "opt1", [0,0], w, pin_length, LayerPinRecN)
    make_pin(self.cell, "opt2", [length,0], w, -pin_length, LayerPinRecN)


    # Compact model information
    t = Trans(Trans.R0, 0, -w*1.5 +0.1/dbu)
    text = Text ('Lumerical_INTERCONNECT_library=Design kits/ebeam', t)
    shape = shapes(LayerDevRecN).insert(text)
    shape.text_size = 0.1/dbu
    t = Trans(Trans.R0, 0, -w*1.5 +0.2/dbu)
    text = Text ('Component=NO_MODEL_AVAILABLE', t)
    shape = shapes(LayerDevRecN).insert(text)
    shape.text_size = 0.1/dbu
    t = Trans(Trans.R0, 0, -w*1.5)
    text = Text \
      ('Spice_param:length=%.3fu target_period=%.3fu grating_period=%.3fu swg_wg_width=%.3fu strip_wg_width=%.3fu duty=%.3f ' %\
      (self.length, self.target_period, round(grating_period)*dbu, self.swg_wg_width, self.strip_wg_width, self.duty), t )
    shape = shapes(LayerDevRecN).insert(text)
    shape.text_size = 0.1/dbu

