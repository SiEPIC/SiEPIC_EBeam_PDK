import pya
from SiEPIC.utils import get_technology_by_name
from pya import *

class spiral_SiN(pya.PCellDeclarationHelper):
  """
  Input: 
  """

  def __init__(self):

    # Important: initialize the super class
    super(spiral_SiN, self).__init__()
    TECHNOLOGY = get_technology_by_name('EBeam')

    # declare the parameters
    self.param("length", self.TypeDouble, "Target Waveguide length", default = 500)     
    self.param("wg_width", self.TypeDouble, "Waveguide width (microns)", default = 0.75)     
    self.param("min_radius", self.TypeDouble, "Minimum radius (microns)", default = 60)     
    self.param("wg_spacing", self.TypeDouble, "Waveguide spacing (microns)", default = 1)     
    self.param("spiral_ports", self.TypeInt, "Ports on the same side? 0/1", default = 0)
    self.param("layer", self.TypeLayer, "Layer", default = TECHNOLOGY['SiN'])
    self.param("pinrec", self.TypeLayer, "PinRec Layer", default = TECHNOLOGY['PinRec'])
    self.param("devrec", self.TypeLayer, "DevRec Layer", default = TECHNOLOGY['DevRec'])

  def display_text_impl(self):
    # Provide a descriptive text for the cell
    return "spiral_SiN_%s-%.3f-%.3f-%.3f" % \
    (self.length, self.wg_width, self.min_radius, self.wg_spacing)
  
  def coerce_parameters_impl(self):
    pass

  def can_create_from_shape(self, layout, shape, layer):
    return False
    
  def produce_impl(self):
    debug = False
    # fetch the parameters
    dbu = self.layout.dbu
    ly = self.layout
    shapes = self.cell.shapes

    LayerSi = self.layer
    LayerSiN = ly.layer(LayerSi)
    LayerPinRecN = ly.layer(self.pinrec)
    LayerDevRecN = ly.layer(self.devrec)

    # draw spiral
    from math import pi, cos, sin, log, sqrt
    
    # Archimedes spiral
    # r = b + a * theta
    b = self.min_radius
    spacing = self.wg_spacing+self.wg_width
    a = 2*spacing/(2*pi)

    # area, length, turn tracking for spiral
    area = 0
    spiral_length = 0
    turn = -1

    from SiEPIC.utils import points_per_circle, arc_wg_xy

    while spiral_length < self.length:
      turn +=1

      # Spiral #1
      pts = []
      # local radius:
      r = 2*b + a * turn * 2 * pi - self.wg_width/2
      # number of points per circle:
      npoints = int(points_per_circle(r))
      # increment, in radians, for each point:
      da = 2 * pi / npoints  
      # draw the inside edge of spiral
      for i in range(0, npoints+1):
        t = i*da
        xa = (a*t + r) * cos(t)
        ya = (a*t + r) * sin(t)
        pts.append(Point.from_dpoint(DPoint(xa/dbu, ya/dbu)))
      # draw the outside edge of spiral
      r = 2*b + a * turn * 2 * pi + self.wg_width/2
      npoints = int(points_per_circle(r))
      da = 2 * pi / npoints  
      for i in range(npoints, -1, -1):
        t = i*da
        xa = (a*t + r) * cos(t)
        ya = (a*t + r) * sin(t)
        pts.append(Point.from_dpoint(DPoint(xa/dbu, ya/dbu)))
      polygon = Polygon(pts)
      area += polygon.area()
      shapes(LayerSiN).insert(polygon)

      # Spiral #2
      pts = []
      # local radius:
      r = 2*b + a * turn * 2 * pi - self.wg_width/2 - spacing
      # number of points per circle:
      npoints = int(points_per_circle(r))
      # increment, in radians, for each point:
      da = 2 * pi / npoints  
      # draw the inside edge of spiral
      for i in range(0, npoints+1):
        t = i*da + pi
        xa = (a*t + r) * cos(t)
        ya = (a*t + r) * sin(t)
        pts.append(Point.from_dpoint(DPoint(xa/dbu, ya/dbu)))
      # draw the outside edge of spiral
      r = 2*b + a * turn * 2 * pi + self.wg_width/2  - spacing
      npoints = int(points_per_circle(r))
      da = 2 * pi / npoints  
      for i in range(npoints, -1, -1):
        t = i*da + pi
        xa = (a*t + r) * cos(t)
        ya = (a*t + r) * sin(t)
        pts.append(Point.from_dpoint(DPoint(xa/dbu, ya/dbu)))
      polygon = Polygon(pts)
      area += polygon.area()
      shapes(LayerSiN).insert(polygon)

      # waveguide length:
      spiral_length = area / self.wg_width * dbu*dbu + 2 * pi * self.min_radius

    if self.spiral_ports:
      # Spiral #1 extra 1/2 arm
      turn = turn + 1
      pts = []
      # local radius:
      r = 2*b + a * turn * 2 * pi - self.wg_width/2
      # number of points per circle:
      npoints = int(points_per_circle(r))
      # increment, in radians, for each point:
      da = pi / npoints  
      # draw the inside edge of spiral
      for i in range(0, npoints+1):
        t = i*da
        xa = (a*t + r) * cos(t)
        ya = (a*t + r) * sin(t)
        pts.append(Point.from_dpoint(DPoint(xa/dbu, ya/dbu)))
      # draw the outside edge of spiral
      r = 2*b + a * turn * 2 * pi + self.wg_width/2
      npoints = int(points_per_circle(r))
      da = pi / npoints  
      for i in range(npoints, -1, -1):
        t = i*da
        xa = (a*t + r) * cos(t)
        ya = (a*t + r) * sin(t)
        pts.append(Point.from_dpoint(DPoint(xa/dbu, ya/dbu)))
      polygon = Polygon(pts)
      area += polygon.area()
      shapes(LayerSiN).insert(polygon)
      turn = turn - 1
      # waveguide length:
      spiral_length = area / self.wg_width * dbu*dbu + 2 * pi * self.min_radius

    # Centre S-shape connecting waveguide        
    #layout_arc_wg_dbu(self.cell, LayerSiN, -b/dbu, 0, b/dbu, self.wg_width/dbu, 0, 180)
    self.cell.shapes(LayerSiN).insert(arc_wg_xy(-b/dbu, 0, b/dbu, self.wg_width/dbu, 0, 180))
    #layout_arc_wg_dbu(self.cell, LayerSiN, b/dbu, 0, b/dbu, self.wg_width/dbu, 180, 0)
    self.cell.shapes(LayerSiN).insert(arc_wg_xy(b/dbu, 0, b/dbu, self.wg_width/dbu, 180, 0))
    if debug:
        print("spiral length: %s microns" % spiral_length) 

    # Pins on the waveguide:
    from SiEPIC._globals import PIN_LENGTH as pin_length
    
    x = -(2*b + a * (turn+1) * 2 * pi)/dbu
    w = self.wg_width / dbu
    t = Trans(Trans.R0, x,0)
    pin = Path([Point(0,pin_length/2), Point(0,-pin_length/2)], w)
    pin_t = pin.transformed(t)
    shapes(LayerPinRecN).insert(pin_t)
    text = Text ("pin2", t)
    shape = shapes(LayerPinRecN).insert(text)
    shape.text_size = 0.4/dbu

    if self.spiral_ports:
      x = -(2*b + a * (turn+1.5) * 2 * pi)/dbu
    else:
      x = (2*b + a * (turn+1) * 2 * pi)/dbu
    t = Trans(Trans.R0, x,0)
    pin = Path([Point(0,-pin_length/2), Point(0,pin_length/2)], w)
    pin_t = pin.transformed(t)
    shapes(LayerPinRecN).insert(pin_t)
    text = Text ("pin1", t)
    shape = shapes(LayerPinRecN).insert(text)
    shape.text_size = 0.4/dbu

    # Compact model information
    t = Trans(Trans.R0, -abs(x), 0)
    text = Text ('Length=%.3fu' % spiral_length, t)
    shape = shapes(LayerDevRecN).insert(text)
    shape.text_size = abs(x)/8
    t = Trans(Trans.R0, 0, 0)
    text = Text ('Lumerical_INTERCONNECT_library=Design kits/ebeam_v1.2', t)
    shape = shapes(LayerDevRecN).insert(text)
    shape.text_size = 0.1/dbu
    t = Trans(Trans.R0, 0, w*2)
    text = Text ('Component=ebeam_wg_strip_1550', t)
    shape = shapes(LayerDevRecN).insert(text)
    shape.text_size = 0.1/dbu
    t = Trans(Trans.R0, 0, -w*2)
    text = Text \
      ('Spice_param:wg_length=%.3fu wg_width=%.3fu min_radius=%.3fu wg_spacing=%.3fu' %\
      (spiral_length, self.wg_width, (self.min_radius), self.wg_spacing), t )
    shape = shapes(LayerDevRecN).insert(text)
    shape.text_size = 0.1/dbu

    # Create the device recognition layer -- make it 1 * wg_width away from the waveguides.
    x = abs(x)
    npoints = int(points_per_circle(x) /10 )
    da = 2 * pi / npoints # increment, in radians
    r=x + 2 * self.wg_width/dbu
    pts = []
    for i in range(0, npoints+1):
      pts.append(Point.from_dpoint(DPoint(r*cos(i*da), r*sin(i*da))))
    shapes(LayerDevRecN).insert(Polygon(pts))

    # print("spiral done.")
