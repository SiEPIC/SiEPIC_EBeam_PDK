# Sean Lam
# seanlm@student.ubc.ca
# Copyright 2022 Sean Lam
# SWG V-shaped

from . import *
from pya import *

class Waveguide_SWG_VShape(pya.PCellDeclarationHelper):

  def __init__(self):
    # Important: initialize the super class
    super(Waveguide_SWG_VShape, self).__init__()
    # declare the parameters
    from SiEPIC.utils import get_technology_by_name
    TECHNOLOGY = get_technology_by_name('EBeam')
    self.param("path", self.TypeShape, "Path", default = DPath([DPoint(0,0), DPoint(10,0)], 0.5))
    self.param("radius", self.TypeDouble, "Radius", default = 5)
    self.param("width", self.TypeDouble, "Core Width", default = 0.5)
    self.param("outer_width", self.TypeDouble, "Outer Width", default = 1.0)
    self.param("duty", self.TypeDouble, "Duty Cycle", default = 0.5)
    self.param("outer_duty", self.TypeDouble, "Outer Duty Cycle", readonly = True) 
    self.param("period", self.TypeDouble, "Period", default = 0.2)
    self.param("outer_period", self.TypeDouble, "Outer Period", readonly = True) 
    self.param("adiab", self.TypeBoolean, "Adiabatic", default = False)
    self.param("bezier", self.TypeDouble, "Bezier Parameter", default = 0.35)
    self.param("min_f", self.TypeDouble, "Min Feature Size", default = 0.06)
    self.param("min_s", self.TypeDouble, "Min Feature Size", default = 0.07)
    self.param("layer", self.TypeLayer, "Layer", default = TECHNOLOGY['Si'])
    self.param("layers", self.TypeList, "Layers", default = ['Waveguide'])
    self.param("widths", self.TypeList, "Widths", default =  [0.5])
    self.param("offsets", self.TypeList, "Offsets", default = [0])
    self.param("CML", self.TypeString, "Compact Model Library (CML)", default = 'EBeam')
    self.param("model", self.TypeString, "CML Model name", default = 'ebeam_wg_swg_vshape_1550') 
    self.cellName="Waveguide"
    
  def display_text_impl(self):
    # Provide a descriptive text for the cell
    return "%s_%s" % (self.cellName, self.path)
  
  def coerce_parameters_impl(self):
    from SiEPIC.extend import to_itype
    from math import cos, sin, pi, sqrt
    print("EBeam.Waveguide_SWG_VShape coerce parameters")
    
    dbu = self.layout.dbu
    min_f = self.min_f
    
    # Get params
    swg_width_center = max([to_itype(self.duty*self.period, dbu), to_itype(sqrt(2*min_f**2), dbu)])
    x_second = max([to_itype(self.period, dbu), to_itype(sqrt(2*min_f**2), dbu)])
    
    self.outer_period = (to_itype(self.period, dbu) + swg_width_center) # nm
    self.outer_duty = swg_width_center/self.outer_period
    
    if 0:
        TECHNOLOGY = get_technology_by_name('EBeam')
        dbu = self.layout.dbu
        wg_width = to_itype(self.width,dbu)
        for lr in range(0, len(self.layers)):
          layer = self.layout.layer(TECHNOLOGY[self.layers[lr]])
          width = to_itype(self.widths[lr],dbu)
          # check to make sure that the waveguide with parameters are consistent in both places
          if self.layout.layer(TECHNOLOGY['Waveguide']) == layer:
            if width != wg_width:
              self.widths[lr] = self.width
          # check to make sure that the DevRec is bigger than the waveguide width
          if self.layout.layer(TECHNOLOGY['DevRec']) == layer:
            if width < wg_width:
              self.widths[lr] = self.width*2
              
  def can_create_from_shape_impl(self):
    return self.shape.is_path()

  def transformation_from_shape_impl(self):
    return Trans(Trans.R0,0,0)

  def parameters_from_shape_impl(self):
    self.path = self.shape.dpath
        
  def produce_impl(self):

    from SiEPIC.utils.layout import layout_waveguide2
    from SiEPIC.utils import  angle_vector
    from math import cos, sin, pi, sqrt
    import pya
    from SiEPIC.extend import to_itype
    from SiEPIC._globals import PIN_LENGTH
    
    # print("EBeam.Waveguide_SWG_VShape")
    
    from SiEPIC.utils import get_technology_by_name
    TECHNOLOGY = get_technology_by_name('EBeam')
    
    ly = self.layout
    dbu = self.layout.dbu
    wg_width = to_itype(self.width,dbu)
    path = self.path.to_itype(dbu)
    shapes = self.cell.shapes
    min_f = self.min_f # Minimum Feature Size
    min_s = self.min_s # Minimum Spacing

    if not (len(self.layers)==len(self.widths) and len(self.layers)==len(self.offsets) and len(self.offsets)==len(self.widths)):
      raise Exception("There must be an equal number of layers, widths and offsets")
    path.unique_points()
    pts = path.get_points()
    
    # Get Layer
    LayerSiN = ly.layer(self.layer)
    
    # Get params
    swg_width_center = max([to_itype(self.duty*self.period, dbu), to_itype(sqrt(2*min_f**2), dbu)])
    swg_width_outer = max([to_itype(self.duty*self.period, dbu), to_itype(min_f, dbu)])
    diff = abs(swg_width_center - swg_width_outer)
    x_second = max([to_itype(self.period, dbu), to_itype(sqrt(2*min_f**2), dbu)])
    pts = path.get_points()
    
    # Draw single segment period
    pts1 = [Point(0, to_itype(self.width/2 + self.outer_width, dbu)),
           Point(0, to_itype(self.width/2 - min_f, dbu)),
           Point(to_itype(self.width/2 - min_f, dbu), 0),
           Point(0, -to_itype(self.width/2 - min_f, dbu)),
           Point(0, -to_itype(self.width/2, dbu)),
           Point(swg_width_center, -to_itype(self.width/2, dbu)),
           Point(swg_width_center, -to_itype(self.width/2 - min_f, dbu)),
           Point(to_itype(self.width/2 - min_f, dbu) + swg_width_center, 0),
           Point(swg_width_outer, to_itype(self.width/2 - min_f, dbu) + diff),
           Point(swg_width_outer, to_itype(self.width/2 + self.outer_width, dbu))]
    PolySeg1 = Polygon(pts1)
    shapes(LayerSiN).insert(PolySeg1.transform(ICplxTrans(pts[0].x, pts[0].y)))
           
           
    pts2 = [Point(to_itype(self.period, dbu), -to_itype(self.width/2 + self.outer_width, dbu)),
           Point(to_itype(self.period, dbu), -to_itype(self.width/2 - min_f, dbu)),
           Point(to_itype(self.period + self.width/2 - min_f, dbu),0),
           Point(to_itype(self.period, dbu), to_itype(self.width/2 - min_f, dbu)),
           Point(to_itype(self.period, dbu), to_itype(self.width/2, dbu)),
           Point(to_itype(self.period, dbu) + swg_width_center, to_itype(self.width/2, dbu)),
           Point(to_itype(self.period, dbu) + swg_width_center, to_itype(self.width/2 - min_f, dbu)),
           Point(to_itype(self.period + self.width/2 - min_f, dbu) + swg_width_center, 0),
           Point(to_itype(self.period, dbu) + swg_width_outer, -to_itype(self.width/2 - min_f, dbu) - diff),
           Point(to_itype(self.period, dbu) + swg_width_outer, -to_itype(self.width/2 + self.outer_width, dbu))]       
    PolySeg2 = Polygon(pts2)
    shapes(LayerSiN).insert(PolySeg2.transform(ICplxTrans(pts[0].x, pts[0].y)))
    
    self.outer_period = (to_itype(self.period, dbu) + swg_width_center) # nm
    self.outer_duty = swg_width_center/self.outer_period
    
    
    x1 = 0
    x2 = 0
    dx = 2*self.period
    
    y = 0
    tol = dx
    for i in range(1, len(pts)):
      # Create SWG waveguide until we reach next point
      if (pts[i].x > (to_itype(x1,dbu) + pts[0].x)) and (pts[i].x > (to_itype(x2,dbu) + pts[0].x)):
        while abs(to_itype(x1,dbu) + pts[0].x - pts[i].x) > to_itype(tol, dbu) and abs(to_itype(x2,dbu) + pts[0].x - pts[i].x) > to_itype(tol, dbu):
          shapes(LayerSiN).insert(PolySeg1.transformed(ICplxTrans(to_itype(x1,dbu),0)))
          shapes(LayerSiN).insert(PolySeg2.transformed(ICplxTrans(to_itype(x2,dbu),0)))
          x1 += dx
          x2 += dx
          
      elif (pts[i].x < (to_itype(x1,dbu) + pts[0].x)) and (pts[i].x < (to_itype(x2,dbu) + pts[0].x)):
        while abs(to_itype(x1,dbu) + pts[0].x - pts[i].x) > to_itype(tol, dbu) and abs(to_itype(x2,dbu) + pts[0].x - pts[i].x) > to_itype(tol, dbu):
          shapes(LayerSiN).insert(PolySeg1.transformed(ICplxTrans(to_itype(x1,dbu),0)))
          shapes(LayerSiN).insert(PolySeg2.transformed(ICplxTrans(to_itype(x2,dbu),0)))
          x1 -= dx
          x2 -= dx
    
    
    # Draw the waveguide geometry, new in SiEPIC-Tools v0.3.64
    waveguide_length = 0

    
    LayerPinRecN = self.layout.layer(TECHNOLOGY['PinRec'])
    
    pt0 = pts[0]
    pt0.x = pt0.x + to_itype(self.period, dbu) + swg_width_center/2 - PIN_LENGTH/2
    t1 = Trans(angle_vector(pts[0]-pts[1])/90, False, pt0)
    self.cell.shapes(LayerPinRecN).insert(Path([Point(-PIN_LENGTH/2, 0), Point(PIN_LENGTH/2, 0)], wg_width).transformed(t1))
    self.cell.shapes(LayerPinRecN).insert(Text("pin1", t1, PIN_LENGTH, -1))
    
    pt1 = pts[-1]
    pt1.x = to_itype(x2,dbu) - to_itype(self.width/2 - min_f, dbu) + (to_itype(self.period, dbu)) + 5
    t = Trans(angle_vector(pts[-1]-pts[-2])/90, False, pt1)
    self.cell.shapes(LayerPinRecN).insert(Path([Point(-PIN_LENGTH/2, 0), Point(PIN_LENGTH/2, 0)], wg_width).transformed(t))
    self.cell.shapes(LayerPinRecN).insert(Text("pin2", t, PIN_LENGTH, -1))

    LayerDevRecN = self.layout.layer(TECHNOLOGY['DevRec'])
    
    # Create the device recognition layer -- make it 1 * wg_width away from the waveguides.
    dev = Box(to_itype(0,dbu), -to_itype(self.width/2+self.outer_width, dbu), to_itype(x2, dbu), to_itype(self.width/2+self.outer_width, dbu) )
    shapes(LayerDevRecN).insert(dev)

    # Compact model information
    angle_vec = angle_vector(pts[0]-pts[1])/90
    halign = 0 # left
    angle=0
    if angle_vec == 0: # horizontal
      halign = 2 # right
      angle=0
      dpt = Point(0, 0.2*wg_width)
    if angle_vec == 2: # horizontal
      halign = 0 # left
      angle = 0
      dpt=Point(0, 0.2*wg_width)
    if angle_vec == 1: # vertical
      halign = 2 # right
      angle = 1
      dpt=Point(0.2*wg_width,0)
    if angle_vec == -1: # vertical
      halign = 0 # left
      angle = 1
      dpt=Point(0.2*wg_width,0)
    pt2=pts[0] + dpt
    pt3=pts[0] - dpt
    pt4=pts[0] - 2*dpt
    pt5=pts[0] + 2*dpt
      

    t = Trans(angle, False, pt5)
    text = Text ('cellName=%s' % self.cellName, t, 0.1*wg_width, -1)
    text.halign=halign
    shape = self.cell.shapes(LayerDevRecN).insert(text)
    t = Trans(angle, False, pt3) 
    text = Text ('Lumerical_INTERCONNECT_library=Design kits/%s' % self.CML, t, 0.1*wg_width, -1)
    text.halign=halign
    shape = self.cell.shapes(LayerDevRecN).insert(text)
    t = Trans(angle, False, pt2)
    text = Text ('Component=%s' % self.model, t, 0.1*wg_width, -1)
    text.halign=halign
    shape = self.cell.shapes(LayerDevRecN).insert(text)
    t = Trans(angle, False, pts[0])
    pts_txt = str([ [round(p.to_dtype(dbu).x,3), round(p.to_dtype(dbu).y,3)] for p in pts ]).replace(', ',',')
    text = Text ( \
      'Spice_param:wg_length=%.3fu wg_width=%.3fu points="%s" radius=%s' %\
        (waveguide_length, self.width, pts_txt,self.radius ), t, 0.1*wg_width, -1  )
    text.halign=halign
    shape = self.cell.shapes(LayerDevRecN).insert(text)
    t = Trans(angle, False, pt4)
    text = Text ( \
      'Length=%.3fu' %(waveguide_length), t, 0.5*wg_width, -1  )
    text.halign=halign
    shape = self.cell.shapes(LayerDevRecN).insert(text)