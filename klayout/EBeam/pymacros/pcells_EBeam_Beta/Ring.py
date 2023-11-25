import pya
import math
from . import *
from pya import *
from SiEPIC.utils import get_technology_by_name
     
class Ring(pya.PCellDeclarationHelper):
  def __init__(self):

    super(Ring, self).__init__()
    TECHNOLOGY = get_technology_by_name('EBeam')

    # declare the parameters
    self.param("silayer", self.TypeLayer, "Layer", default = TECHNOLOGY['Si'])
    self.param("r", self.TypeDouble, "Radius", default = 10)
    self.param("w", self.TypeDouble,"Width",default = 0.5)
    self.param("g", self.TypeDouble,"Gap",default = 0.2)
    self.param("b", self.TypeDouble,"Bus Length",default = 50)
    self.param("d", self.TypeBoolean, "Drop", default = False)
    self.param("n", self.TypeInt, "Number of points", default = 2048)     
    self.param("p",self.TypeLayer,"Pin Layer",default = pya.LayerInfo(1,10))     
    self.param("oxideopen", self.TypeLayer, "Oxide Open Layer", default = TECHNOLOGY['Oxide open (to BOX)'])
    self.param("devrec", self.TypeLayer, "Dev Rec Layer", default = TECHNOLOGY['DevRec'])

  def display_text_impl(self):
    return "Ring(R=" + ('%.3f' % self.r) + ",g=" + ('%g' % (1000*self.g)) + ")"
  
  def coerce_parameters_impl(self):
    pass

  def can_create_from_shape(self, layout, shape, layer):
    return False
  
  def produce_impl(self):
     
    # compute the arc
    # fetch the parameters
    from SiEPIC._globals import PIN_LENGTH
    from SiEPIC.extend import to_itype
    import math
    from pya import DPolygon

    pi  = math.pi
    # This is the main part of the implementation: create the layout

    dbu = self.layout.dbu
    ly = self.layout
    shapes = self.cell.shapes
    LayerCladN = ly.layer(self.clad)
    pts_o = []
    pts_i = []
    da = 2*pi / (self.n)
    r = self.r/dbu
    r2 = self.r
    w = self.w/dbu
    g = self.g/dbu
    b = self.b/dbu
      
    #create the circle
    for i in range(0,self.n+1):
      bend_ox = (r+w/2)*math.cos(i*da)
      bend_oy = (r+w/2)*math.sin(i*da)
      bend_ix = (r-w/2)*math.cos(i*da)
      bend_iy = (r-w/2)*math.sin(i*da)
      pts_o.append(pya.Point.from_dpoint(pya.DPoint(bend_ox,bend_oy)))
      pts_i.append(pya.Point.from_dpoint(pya.DPoint(bend_ix,bend_iy)))
    
    pts_o.append(pya.Point.from_dpoint(pya.DPoint(0,r+w/2)))
    pts_i.append(pya.Point.from_dpoint(pya.DPoint(0,r-w/2)))
    pts_o.append(pya.Point.from_dpoint(pya.DPoint(0,0)))
    pts_i.append(pya.Point.from_dpoint(pya.DPoint(0,0)))
    ring1=pya.Region()
    ring1.insert(pya.Polygon(pts_o))
    ring2=pya.Region()
    ring2.insert(pya.Polygon(pts_i))
    ring = ring1-ring2
    self.cell.shapes(self.l_layer).insert(ring)
    
    # draw oxide open 
    self.cell.shapes(ly.layer(self.oxideopen)).insert(pya.Box(DPoint(-to_itype(r2+5,dbu),-to_itype(r2+5,dbu)),DPoint(to_itype(r2+5,dbu),to_itype(r2+5,dbu))))
    
    #DEV BOX
    self.cell.shapes(ly.layer(self.devrec)).insert(Box(DPoint(-to_itype(r2+5,dbu),-to_itype(r2+5,dbu)),DPoint(to_itype(r2+5,dbu),to_itype(r2+5,dbu))))

    #insert bus waveguide
    box1 = pya.Region()
    xa = -b/2
    xb = b/2
    ya = -r-w/2-g-w
    yb = -r-w/2-g
    box1.insert(pya.Box(xa,ya,xb,yb))
    self.cell.shapes(self.l_layer).insert(box1) 
    
   #add the left bus pin
    xp1 = -0.05/self.layout.dbu
    xp2 = 0.05/self.layout.dbu
    yp1 = ya+2/dbu+w/2
    p1 = [Point(xa+xp2,yp1),Point(xa+xp1,yp1)]
    p1c = Point(xa,yp1)
    self.set_p1=p1c
    self.p1=p1c
    pin=Path(p1,w)
    t = Trans(Trans.R0,xa,yp1)
    self.cell.shapes(self.p_layer).insert(pin)
    text=Text("pin1",t)
    self.cell.shapes(self.p_layer).insert(text)
    
    #add the right bus pin
    p2 = [Point(xb+xp1,yp1),Point(xb+xp2,yp1)]
    p2c = Point(xb,yp1)
    self.set_p2=p2c
    self.p2=p2c
    pin=Path(p2,w)
    t = Trans(Trans.R180,xb,yp1)
    self.cell.shapes(self.p_layer).insert(pin)
    text=Text("pin2",t)
    self.cell.shapes(self.p_layer).insert(text)
    
    #insert drop port
    if self.d == True:
      box2 = pya.Region()
      xa = -b/2
      xb = b/2
      ya = r+w/2+g
      yb = r+w/2+g+w
      box2.insert(pya.Box(xa,ya,xb,yb))
      self.cell.shapes(self.l_layer).insert(box2)
      
      box2n = pya.Region()
      xa = -b/2
      xb = b/2
      ya = r+w/2+g-2/dbu
      yb = r+w/2+g+w+2/dbu
      box2n.insert(pya.Box(xa,ya,xb,yb))
      self.cell.shapes(LayerCladN).insert(box2n) 
      
      #add the left drop pin
      xp1 = -0.05/self.layout.dbu
      xp2 = 0.05/self.layout.dbu
      yp1 = ya+w/2+2/dbu
      p1 = [Point(xa+xp2,yp1),Point(xa+xp1,yp1)]
      p1c = Point(xa,yp1)
      self.set_p1=p1c
      self.p1=p1c
      pin=Path(p1,w)
      t = Trans(Trans.R0,xa,yp1)
      self.cell.shapes(self.p_layer).insert(pin)
      text=Text("pin3",t)
      self.cell.shapes(self.p_layer).insert(text)
    
      #add the right drop pin
      p2 = [Point(xb+xp1,yp1),Point(xb+xp2,yp1)]
      p2c = Point(xb,yp1)
      self.set_p2=p2c
      self.p2=p2c
      pin=Path(p2,w)
      t = Trans(Trans.R180,xb,yp1)
      self.cell.shapes(self.p_layer).insert(pin)
      text=Text("pin4",t)
      self.cell.shapes(self.p_layer).insert(text)