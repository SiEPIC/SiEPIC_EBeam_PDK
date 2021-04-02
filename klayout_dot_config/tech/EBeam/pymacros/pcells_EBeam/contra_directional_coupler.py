from . import *
from pya import *

def make_pin(cell, name, center, w, pin_length, layer, vertical = 0):
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
  
class contra_directional_coupler(pya.PCellDeclarationHelper):
  """
  Author:   Mustafa Hammood, 2018
            Mustafa@siepic.com
  """

  def __init__(self):
    # Important: initialize the super class
    super(contra_directional_coupler, self).__init__()
    TECHNOLOGY = get_technology_by_name('EBeam')

    # declare the parameters
    self.param("number_of_periods", self.TypeInt, "Number of grating periods", default = 300)     
    self.param("grating_period", self.TypeDouble, "Grating period (microns)", default = 0.317)
    self.param("gap", self.TypeDouble, "Gap (microns)", default = 0.15)          
    self.param("corrugation_width1", self.TypeDouble, "Waveguide 1 Corrugration width (microns)", default = 0.03)
    self.param("corrugation_width2", self.TypeDouble, "Waveguide 2 Corrugration width (microns)", default = 0.04)          
    self.param("AR", self.TypeBoolean, "Anti-Reflection Design", default =True)
    self.param("sinusoidal", self.TypeBoolean, "Grating Type (Rectangular=False, Sinusoidal=True)", default = False)     
    self.param("wg1_width", self.TypeDouble, "Waveguide 1 width", default = 0.45)
    self.param("wg2_width", self.TypeDouble, "Waveguide 2 width", default = 0.55)
    self.param("sbend",self.TypeBoolean, "Include S-bends", default = 1)          
    self.param("apodization_index", self.TypeDouble, "Gaussian Apodization Index", default = 2.8)
    self.param("port_w", self.TypeDouble, "Port Waveguide width", default = 0.5)
    self.param("accuracy", self.TypeBoolean, "Simulation Accuracy (on = high, off = fast)", default = True)
    self.param("layer", self.TypeLayer, "Layer", default = TECHNOLOGY['Waveguide'])
    self.param("pinrec", self.TypeLayer, "PinRec Layer", default = TECHNOLOGY['PinRec'])
    self.param("devrec", self.TypeLayer, "DevRec Layer", default = TECHNOLOGY['DevRec'])
    
#    self.param("textl", self.TypeLayer, "Text Layer", default = LayerInfo(10, 0))

  def display_text_impl(self):
    # Provide a descriptive text for the cell
    return "contra_directional_coupler_%sN-%.1fnm period" % \
    (self.number_of_periods, self.grating_period*1000)
  
  def coerce_parameters_impl(self):
    pass

  def can_create_from_shape(self, layout, shape, layer):
    return False
    
  def produce_impl(self):
    import math
    try:
      from SiEPIC.utils.layout import layout_waveguide_sbend, layout_taper
    except:
      from siepic_tools.utils.layout import layout_waveguide_sbend, layout_taper
  
    # fetch the parameters
    dbu = self.layout.dbu
    ly = self.layout
    shapes = self.cell.shapes

    LayerSi = self.layer
    LayerSiN = ly.layer(LayerSi)
    LayerPinRecN = ly.layer(self.pinrec)
    LayerDevRecN = ly.layer(self.devrec)

    from SiEPIC.extend import to_itype
    
    # Draw the Bragg grating (bottom):
    box_width = int(round(self.grating_period/2/dbu))
    grating_period = int(round(self.grating_period/dbu))

    w = to_itype(self.wg1_width,dbu)
    GaussianIndex = self.apodization_index
    half_w = w/2
    half_corrugation_w = to_itype(self.corrugation_width1/2,dbu)
    
    y_offset_top = -w/2 - to_itype(self.gap/2, dbu)

    if self.AR:
      misalignment = grating_period/2
    else:
      misalignment = 0

    N = self.number_of_periods
    if self.sinusoidal:
      npoints_sin = 40
      for i in range(0,self.number_of_periods):
        x = (round((i * self.grating_period)/dbu))
        profileFunction = math.exp( -0.5*(2*GaussianIndex*(i-N/2)/(N))**2 )
        profile = int(round(self.corrugation_width1/2/dbu))*profileFunction;      
        box1 = Box(x, y_offset_top , x + box_width, y_offset_top + half_w+profile)
        pts1 = [Point(x,y_offset_top)]
        pts3 = [Point(x + misalignment,y_offset_top)]
        
        for i1 in range(0,npoints_sin+1):
          x1 = i1 * 2* math.pi / npoints_sin
          y1 = round(profile*math.sin(x1))
          x1 = round(x1/2/math.pi*grating_period)
          pts1.append( Point(x + x1,y_offset_top + half_w+y1 ) )
          pts3.append( Point(x + misalignment + x1,y_offset_top - half_w-y1 ) )
          
        pts1.append( Point(x + grating_period, y_offset_top) )
        pts3.append( Point(x + grating_period + misalignment, y_offset_top) )
        shapes(LayerSiN).insert(Polygon(pts1))
        shapes(LayerSiN).insert(Polygon(pts3))
      length = x + grating_period + misalignment
      if misalignment > 0:
        # extra piece at the end:
        box2 = Box(x + grating_period, y_offset_top, length, y_offset_top + half_w)
        shapes(LayerSiN).insert(box2)
        # extra piece at the beginning:
        box3 = Box(0, y_offset_top, misalignment, y_offset_top -half_w)
        shapes(LayerSiN).insert(box3)

    else:
      for i in range(0,self.number_of_periods):
        x = int(round((i * self.grating_period)/dbu))
        
        profileFunction = math.exp( -0.5*(2*GaussianIndex*(i-N/2)/(N))**2 )
        profile = int(round(self.corrugation_width1/2/dbu))*profileFunction
                
        box1 = Box(x, y_offset_top, x + box_width,y_offset_top +  to_itype(half_w+profile,dbu*1000))
        box2 = Box(x + box_width, y_offset_top , x + grating_period, y_offset_top + to_itype(half_w-profile,dbu*1000))
        box3 = Box(x + misalignment, y_offset_top , x + box_width + misalignment, y_offset_top + to_itype(-half_w-profile,dbu*1000))
        box4 = Box(x + box_width + misalignment, y_offset_top , x + grating_period + misalignment, y_offset_top + to_itype(-half_w+profile,dbu*1000))
        shapes(LayerSiN).insert(box1)
        shapes(LayerSiN).insert(box2)
        shapes(LayerSiN).insert(box3)
        shapes(LayerSiN).insert(box4)
      length = x + grating_period + misalignment
      if misalignment > 0:
        # extra piece at the end:
        box2 = Box(x + grating_period, y_offset_top , length,y_offset_top +  half_w)
        shapes(LayerSiN).insert(box2)
        # extra piece at the beginning:
        box3 = Box(0,y_offset_top , misalignment, y_offset_top -half_w)
        shapes(LayerSiN).insert(box3)

    vertical_offset = int(round(self.wg2_width/2/dbu))+int(round(self.gap/2/dbu))
    
    if misalignment > 0:
      t = Trans(Trans.R0, 0,vertical_offset)
    else:
      t = Trans(Trans.R0, 0,vertical_offset)
    
    # Draw the Bragg grating (top):
    box_width = int(round(self.grating_period/2/dbu))
    grating_period = int(round(self.grating_period/dbu))
    w = to_itype(self.wg2_width,dbu)
    half_w = w/2
    half_corrugation_w = int(round(self.corrugation_width2/2/dbu))
    
    N = self.number_of_periods
    if self.sinusoidal:
      npoints_sin = 40
      for i in range(0,self.number_of_periods):
        x = (round((i * self.grating_period)/dbu))
        profileFunction = math.exp( -0.5*(2*GaussianIndex*(i-N/2)/(N))**2 )
        profile = int(round(self.corrugation_width2/2/dbu))*profileFunction;
        box1 = Box(x, 0, x + box_width, -half_w+profile).transformed(t)
        pts1 = [Point(x,0)]
        pts3 = [Point(x + misalignment,0)]
        for i1 in range(0,npoints_sin+1):
          x1 = i1 * 2* math.pi / npoints_sin
          y1 = round(profile*math.sin(x1))
          x1 = round(x1/2/math.pi*grating_period)
#          print("x: %s, y: %s" % (x1,y1))
          pts1.append( Point(x + x1,-half_w-y1 ) )
          pts3.append( Point(x + misalignment + x1,+half_w+y1 ) )
        pts1.append( Point(x + grating_period, 0) )
        pts3.append( Point(x + grating_period + misalignment, 0) )
        shapes(LayerSiN).insert(Polygon(pts1).transformed(t))
        shapes(LayerSiN).insert(Polygon(pts3).transformed(t))
      length = x + grating_period + misalignment
      if misalignment > 0:
        # extra piece at the end:
        box2 = Box(x + grating_period, 0, length, -half_w).transformed(t)
        shapes(LayerSiN).insert(box2)
        # extra piece at the beginning:
        box3 = Box(0, 0, misalignment, half_w).transformed(t)
        shapes(LayerSiN).insert(box3)

    else:
      for i in range(0,self.number_of_periods):
        x = int(round((i * self.grating_period)/dbu))
        profileFunction = math.exp( -0.5*(2*GaussianIndex*(i-N/2)/(N))**2 )
        profile = int(round(self.corrugation_width2/2/dbu))*profileFunction;
        box1 = Box(x, 0, x + box_width, -half_w-profile).transformed(t)
        box2 = Box(x + box_width, 0, x + grating_period, -half_w+profile).transformed(t)
        box3 = Box(x + misalignment, 0, x + box_width + misalignment, half_w+profile).transformed(t)
        box4 = Box(x + box_width + misalignment, 0, x + grating_period + misalignment, half_w-profile).transformed(t)
        shapes(LayerSiN).insert(box1)
        shapes(LayerSiN).insert(box2)
        shapes(LayerSiN).insert(box3)
        shapes(LayerSiN).insert(box4)
      length = x + grating_period + misalignment
      if misalignment > 0:
        # extra piece at the end:
        box2 = Box(x + grating_period, 0, length, -half_w).transformed(t)
        shapes(LayerSiN).insert(box2)
        # extra piece at the beginning:
        box3 = Box(0, 0, misalignment, half_w).transformed(t)
        shapes(LayerSiN).insert(box3)
        
    # Create the pins on the waveguides, as short paths:
    from SiEPIC._globals import PIN_LENGTH as pin_length

    w1 = to_itype(self.wg1_width,dbu)
    w2 = to_itype(self.wg2_width,dbu)
    if self.sbend:

      port_w = to_itype(self.port_w,dbu)
      sbend_r = 25000; sbend_length = 15000
      sbend_offset= 2*port_w + port_w - (w1+w2)/2 - int(round(self.gap/dbu))
      taper_length = 20*max(abs(w1-port_w), abs(w2-port_w))
      
      t = Trans(Trans.R180, 0,y_offset_top)
      layout_waveguide_sbend(self.cell, LayerSiN, t, w1, sbend_r, sbend_offset, sbend_length)
      t = Trans(Trans.R0, -sbend_length-taper_length,y_offset_top-sbend_offset)
      layout_taper(self.cell, LayerSiN, t,  port_w, w1, taper_length)
      x = -sbend_length-taper_length
      y = y_offset_top-sbend_offset
      make_pin(self.cell, "opt1", [x,y], port_w, pin_length, LayerPinRecN, vertical = 0)
      
      t = Trans(Trans.R180, 0,vertical_offset)
      layout_taper(self.cell, LayerSiN, t,  w2, w2, sbend_length/2)
      t = Trans(Trans.R180, -sbend_length/2,vertical_offset)
      layout_taper(self.cell, LayerSiN, t,  w2, port_w, taper_length+sbend_length/2)
      x = -taper_length-sbend_length
      y = vertical_offset
      make_pin(self.cell, "opt2", [x,y], port_w, pin_length, LayerPinRecN, vertical = 0)

      t = Trans(Trans.R0, length,y_offset_top )
      layout_waveguide_sbend(self.cell, LayerSiN, t, w1, sbend_r, -sbend_offset, sbend_length)
      t = Trans(Trans.R0, length+sbend_length,y_offset_top-sbend_offset)
      layout_taper(self.cell, LayerSiN, t, w1, port_w, taper_length)
      x = length+sbend_length+taper_length
      y = y_offset_top-sbend_offset
      make_pin(self.cell, "opt3", [x,y], port_w, -pin_length, LayerPinRecN, vertical = 0)

      
      t = Trans(Trans.R0, length, vertical_offset)
      layout_taper(self.cell, LayerSiN, t,  w2, w2, sbend_length/2)
      t = Trans(Trans.R0, length+sbend_length/2, vertical_offset)
      layout_taper(self.cell, LayerSiN, t,  w2, port_w, taper_length+sbend_length/2)
      x = length+taper_length+sbend_length
      y = vertical_offset
      make_pin(self.cell, "opt4", [x,y], port_w, -pin_length, LayerPinRecN, vertical = 0)

    else:
      x = 0
      y = y_offset_top
      make_pin(self.cell, "opt1", [x,y], w1, pin_length, LayerPinRecN, vertical = 0)

      y = vertical_offset
      make_pin(self.cell, "opt2", [x,y], w2, pin_length, LayerPinRecN, vertical = 0)

      x = length
      y = y_offset_top
      make_pin(self.cell, "opt3", [x,y], w1, -pin_length, LayerPinRecN, vertical = 0)

      x = length
      y = vertical_offset
      make_pin(self.cell, "opt4", [x,y], w2, -pin_length, LayerPinRecN, vertical = 0)

    # Compact model information
    t = Trans(Trans.R0, 10, 0)
    text = Text ('Lumerical_INTERCONNECT_library=Design kits/ebeam', t)
    shape = shapes(LayerDevRecN).insert(text)
    shape.text_size = 0.1/dbu
    t = Trans(Trans.R0, 10, 500)
    text = Text ('Component=contra_directional_coupler', t)
    shape = shapes(LayerDevRecN).insert(text)
    shape.text_size = 0.1/dbu
    t = Trans(Trans.R0, 10, -500)
    text = Text \
      ('Spice_param:number_of_periods=%s grating_period=%.3fu wg1_width=%.3fu wg2_width=%.3fu corrugation_width1=%.3fu corrugation_width2=%.3fu gap=%.3fu apodization_index=%.3f AR=%s sinusoidal=%s accuracy=%s' %\
      (self.number_of_periods, self.grating_period, self.wg1_width, self.wg2_width, self.corrugation_width1, self.corrugation_width2, self.gap, self.apodization_index, int(self.AR), int(self.sinusoidal), int(self.accuracy)), t )
    shape = shapes(LayerDevRecN).insert(text)
    shape.text_size = 0.1/dbu

    # Create the device recognition layer -- make it 1 * wg_width away from the waveguides.
    if self.sbend:
      box = pya.Box(pya.Point(-taper_length-sbend_length, vertical_offset+3/2*port_w),pya.Point(length+taper_length+sbend_length, y_offset_top-sbend_offset-3/2*port_w))
    else:
       box = pya.Box(pya.Point(0, vertical_offset+3/2*(w1+w2)/2),pya.Point(length, y_offset_top-3/2*(w1+w2)/2))     
    shapes(LayerDevRecN).insert(box)
    