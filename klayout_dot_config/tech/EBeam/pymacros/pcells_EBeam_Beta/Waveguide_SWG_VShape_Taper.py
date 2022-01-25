# Sean Lam
# seanlm@student.ubc.callable
# Copyright 2022 Sean Lam
# SWG V-shaped Taper

from . import *
from pya import *

class Waveguide_SWG_VShape_Taper(pya.PCellDeclarationHelper):

  def __init__(self):
    # Important: initialize the super class
    super(Waveguide_SWG_VShape_Taper, self).__init__()
    # declare the parameters
    from SiEPIC.utils import get_technology_by_name
    TECHNOLOGY = get_technology_by_name('EBeam')
    self.param("radius", self.TypeDouble, "Radius", default = 5)
    self.param("length", self.TypeDouble, "Length", default = 15)
    self.param("width", self.TypeDouble, "Core Width Start", default = 0.5)
    self.param("width_start", self.TypeBoolean, "Core Width Starts on Left (True) / Right (False)", default = True)
    self.param("outer_width", self.TypeDouble, "Outer Width Start", default = 2)
    self.param("outer_width_start", self.TypeBoolean, "Outer Width Starts on Left (True) / Right (False)", default = True)
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
    self.cellName="Waveguide_SWG_VShape_Taper"
    
  def display_text_impl(self):
    # Provide a descriptive text for the cell
    return "%s" % (self.cellName)
  
  def coerce_parameters_impl(self):
    from SiEPIC.extend import to_itype
    from math import cos, sin, pi, sqrt
    print("EBeam.Waveguide_SWG_VShape_Taper coerce parameters")
    
    dbu = self.layout.dbu
    min_f = self.min_f
    
    # Get params
    swg_width_center = max([to_itype(self.duty*self.period, dbu), to_itype(sqrt(2*min_f**2), dbu)])
    x_second = max([to_itype(self.period, dbu), to_itype(sqrt(2*min_f**2), dbu)])
    
    self.outer_period = (to_itype(2*self.period, dbu)) # nm
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
    pass
        
  def produce_impl(self):

    from SiEPIC.utils.layout import layout_waveguide2
    from SiEPIC.utils import  angle_vector
    from math import cos, sin, pi, sqrt
    from operator import xor, inv
    import pya
    from SiEPIC.extend import to_itype
    from SiEPIC._globals import PIN_LENGTH
    
    # print("EBeam.Waveguide_SWG_VShape_Taper")
    
    from SiEPIC.utils import get_technology_by_name
    TECHNOLOGY = get_technology_by_name('EBeam')
    
    ly = self.layout
    dbu = self.layout.dbu
    wg_width = to_itype(self.width,dbu)
    shapes = self.cell.shapes
    min_f = self.min_f # Minimum Feature Size
    min_s = self.min_s # Minimum Spacing

    if not (len(self.layers)==len(self.widths) and len(self.layers)==len(self.offsets) and len(self.offsets)==len(self.widths)):
      raise Exception("There must be an equal number of layers, widths and offsets")
    
    # Get Layer
    LayerSiN = ly.layer(self.layer)
    
    # Get params
    x_init = to_itype(0, dbu)
    y_init = to_itype(0, dbu)
    
    swg_width_center = max([to_itype(self.duty*self.period, dbu), to_itype(sqrt(2*min_f**2), dbu)])
    swg_width_outer = max([to_itype(self.duty*self.period, dbu), to_itype(min_f, dbu)])
    diff = abs(swg_width_center - swg_width_outer)
    x_second = max([to_itype(self.period, dbu), to_itype(sqrt(2*min_f**2), dbu)])
    
    if self.outer_width_start:
      ext_outer = 0
      ext_outer_delta = self.outer_width/(self.length/(2*self.period))
    else:
      ext_outer = self.outer_width
      ext_outer_delta = -self.outer_width/(self.length/(2*self.period))
    
    if self.width_start:
      ext_inner = 0
      ext_inner_delta = (self.width/2 - self.min_f/2)/(self.length/self.period)
    else:
      ext_inner = self.width/2 - self.min_f/2
      ext_inner_delta = -(self.width/2 - self.min_f/2)/(self.length/self.period)
    
    # Draw input waveguide
    if self.width_start:
      pts0 = [Point(x_init, to_itype(self.width/2, dbu) + to_itype(ext_outer, dbu)),
              Point(x_init, -to_itype(self.width/2, dbu)),
             Point(swg_width_center, -to_itype(self.width/2, dbu)),
             Point(swg_width_center, -to_itype(self.width/2 - min_f, dbu)),
             Point(to_itype(self.width/2 - min_f, dbu) + swg_width_center, y_init),
             Point(swg_width_outer, to_itype(self.width/2 - min_f, dbu) + diff),
             Point(swg_width_outer, to_itype(self.width/2, dbu) + to_itype(ext_outer, dbu))]
      PolySeg0 = Polygon(pts0)
      shapes(LayerSiN).insert(PolySeg0.transform(ICplxTrans(x_init, y_init)))      
    
    # Draw single segment period
    pts1 = [Point(x_init, to_itype(self.width/2, dbu) + to_itype(ext_outer, dbu)),
           Point(x_init, to_itype(self.width/2 - min_f, dbu)),
           Point(to_itype(self.width/2 - min_f, dbu), y_init),
           Point(x_init, -to_itype(self.width/2 - min_f, dbu)),
           Point(x_init, -to_itype(self.width/2, dbu)),
           Point(swg_width_center, -to_itype(self.width/2, dbu)),
           Point(swg_width_center, -to_itype(self.width/2 - min_f, dbu)),
           Point(to_itype(self.width/2 - min_f, dbu) + swg_width_center, y_init),
           Point(swg_width_outer, to_itype(self.width/2 - min_f, dbu) + diff),
           Point(swg_width_outer, to_itype(self.width/2, dbu) + to_itype(ext_outer, dbu))]
    PolySeg1 = Polygon(pts1)
    shapes(LayerSiN).insert(PolySeg1.transform(ICplxTrans(x_init, y_init)))
                
    pts2 = [Point(to_itype(self.period, dbu), -to_itype(self.width/2, dbu) - to_itype(ext_outer, dbu)),
           Point(to_itype(self.period, dbu), -to_itype(self.width/2 - min_f, dbu)),
           Point(to_itype(self.period + self.width/2 - min_f, dbu),y_init),
           Point(to_itype(self.period, dbu), to_itype(self.width/2 - min_f, dbu)),
           Point(to_itype(self.period, dbu), to_itype(self.width/2, dbu)),
           Point(to_itype(self.period, dbu) + swg_width_center, to_itype(self.width/2, dbu)),
           Point(to_itype(self.period, dbu) + swg_width_center, to_itype(self.width/2 - min_f, dbu)),
           Point(to_itype(self.period + self.width/2 - min_f, dbu) + swg_width_center, y_init),
           Point(to_itype(self.period, dbu) + swg_width_outer, -to_itype(self.width/2 - min_f, dbu) - diff),
           Point(to_itype(self.period, dbu) + swg_width_outer, -to_itype(self.width/2, dbu) - to_itype(ext_outer, dbu))]       
    PolySeg2 = Polygon(pts2)
    shapes(LayerSiN).insert(PolySeg2.transform(ICplxTrans(x_init, y_init)))
    
    ext_outer += ext_outer_delta
    
    # Draw connecting segment between main segments
    pts3 = [Point(x_init + swg_width_outer/2, to_itype(self.width/2, dbu)),
            Point(x_init + swg_width_outer/2, to_itype(self.width/2 - min_f, dbu)),
            Point(to_itype(self.width/2 - min_f, dbu) + swg_width_center/2, y_init),
            Point(x_init + swg_width_outer/2, -to_itype(self.width/2 - min_f, dbu)),
            Point(x_init + swg_width_outer/2, -to_itype(self.width/2, dbu)),
            Point(x_init + swg_width_outer/2 + to_itype(self.period, dbu), -to_itype(self.width/2, dbu)),
            Point(x_init + swg_width_outer/2 + to_itype(self.period, dbu), -to_itype(self.width/2 - min_f, dbu)),
            Point(x_init + swg_width_outer/2 + to_itype(self.period + self.width/2 - min_f, dbu), y_init),
            Point(x_init + swg_width_outer/2 + to_itype(self.period, dbu), to_itype(self.width/2 - min_f, dbu)),
            Point(x_init + swg_width_outer/2 + to_itype(self.period, dbu), to_itype(self.width/2, dbu))]
    PolySeg3 = Polygon(pts3)
    BoxSeg3 = PolySeg3.bbox()
    BoxSeg3.top = BoxSeg3.top - to_itype(ext_inner, dbu)
    BoxSeg3.bottom = BoxSeg3.bottom + to_itype(ext_inner, dbu)
    ext_inner += ext_inner_delta
    
    A1 = Region(PolySeg3)
    B1 = Region(BoxSeg3)
    C1 = B1 & A1
    
    shapes(LayerSiN).insert(C1.transform_icplx(ICplxTrans(x_init, y_init)))
                
    pts4 = [Point(to_itype(self.period, dbu) + x_init + swg_width_outer/2, to_itype(self.width/2, dbu)),
            Point(to_itype(self.period, dbu) + x_init + swg_width_outer/2, to_itype(self.width/2 - min_f, dbu)),
            Point(to_itype(self.period, dbu) + to_itype(self.width/2 - min_f, dbu) + swg_width_center/2, y_init),
            Point(to_itype(self.period, dbu) + x_init + swg_width_outer/2, -to_itype(self.width/2 - min_f, dbu)),
            Point(to_itype(self.period, dbu) + x_init + swg_width_outer/2, -to_itype(self.width/2, dbu)),
            Point(x_init + swg_width_outer/2 + to_itype(2*self.period, dbu), -to_itype(self.width/2, dbu)),
            Point(x_init + swg_width_outer/2 + to_itype(2*self.period, dbu), -to_itype(self.width/2 - min_f, dbu)),
            Point(x_init + swg_width_outer/2 + to_itype(2*self.period + self.width/2 - min_f, dbu), y_init),
            Point(x_init + swg_width_outer/2 + to_itype(2*self.period, dbu), to_itype(self.width/2 - min_f, dbu)),
            Point(x_init + swg_width_outer/2 + to_itype(2*self.period, dbu), to_itype(self.width/2, dbu))]   
    PolySeg4 = Polygon(pts4)
    BoxSeg4 = PolySeg4.bbox()
    BoxSeg4.top = BoxSeg4.top - to_itype(ext_inner, dbu)
    BoxSeg4.bottom = BoxSeg4.bottom + to_itype(ext_inner, dbu)
    ext_inner += ext_inner_delta
    
    A2 = Region(PolySeg4)
    B2 = Region(BoxSeg4)
    C2 = B2 & A2
    
    shapes(LayerSiN).insert(C2.transform(ICplxTrans(x_init, y_init)))
    
    self.outer_period = to_itype(2*self.period, dbu) # nm
    self.outer_duty = swg_width_center/self.outer_period
    
    
    x1 = to_itype(0, dbu)
    x2 = to_itype(0, dbu)
    dx = to_itype(2*self.period, dbu)
    
    y = 0
    tol = dx
    # Create SWG waveguide until we reach next point
    while abs(x1 + x_init - to_itype(self.length, dbu)) > tol and abs(x2 + x_init - to_itype(self.length, dbu)) > tol:
      ## Add main segments
      pts1 = [Point(x_init, to_itype(self.width/2, dbu) + to_itype(ext_outer, dbu)),
         Point(x_init, to_itype(self.width/2 - min_f, dbu)),
         Point(to_itype(self.width/2 - min_f, dbu), y_init),
         Point(x_init, -to_itype(self.width/2 - min_f, dbu)),
         Point(x_init, -to_itype(self.width/2, dbu)),
         Point(swg_width_center, -to_itype(self.width/2, dbu)),
         Point(swg_width_center, -to_itype(self.width/2 - min_f, dbu)),
         Point(to_itype(self.width/2 - min_f, dbu) + swg_width_center, y_init),
         Point(swg_width_outer, to_itype(self.width/2 - min_f, dbu) + diff),
         Point(swg_width_outer, to_itype(self.width/2, dbu) + to_itype(ext_outer, dbu))]
      PolySeg1 = Polygon(pts1)
      shapes(LayerSiN).insert(PolySeg1.transformed(ICplxTrans(x1,0)))
                  
      pts2 = [Point(to_itype(self.period, dbu), -to_itype(self.width/2, dbu) - to_itype(ext_outer, dbu)),
             Point(to_itype(self.period, dbu), -to_itype(self.width/2 - min_f, dbu)),
             Point(to_itype(self.period + self.width/2 - min_f, dbu),y_init),
             Point(to_itype(self.period, dbu), to_itype(self.width/2 - min_f, dbu)),
             Point(to_itype(self.period, dbu), to_itype(self.width/2, dbu)),
             Point(to_itype(self.period, dbu) + swg_width_center, to_itype(self.width/2, dbu)),
             Point(to_itype(self.period, dbu) + swg_width_center, to_itype(self.width/2 - min_f, dbu)),
             Point(to_itype(self.period + self.width/2 - min_f, dbu) + swg_width_center, y_init),
             Point(to_itype(self.period, dbu) + swg_width_outer, -to_itype(self.width/2 - min_f, dbu) - diff),
             Point(to_itype(self.period, dbu) + swg_width_outer, -to_itype(self.width/2, dbu) - to_itype(ext_outer, dbu))]       
      PolySeg2 = Polygon(pts2)
      shapes(LayerSiN).insert(PolySeg2.transformed(ICplxTrans(x2,0)))
  
      ext_outer += ext_outer_delta
      
      ## Add center segments
      # Add seg1
      BoxSeg3 = PolySeg3.bbox()
      BoxSeg3.top = BoxSeg3.top - to_itype(ext_inner, dbu)
      BoxSeg3.bottom = BoxSeg3.bottom + to_itype(ext_inner, dbu)
      if (BoxSeg3.top - BoxSeg3.bottom) < to_itype(self.min_f, dbu):
        BoxSeg3.top = to_itype(self.min_f/2, dbu)
        BoxSeg3.bottom = -to_itype(self.min_f/2, dbu)
      else:
        ext_inner += ext_inner_delta
      
      A1 = Region(PolySeg3)
      B1 = Region(BoxSeg3)
      C1 = B1 & A1 
      shapes(LayerSiN).insert(C1.transformed(ICplxTrans(x1,0)))
      
      # Add seg2
      BoxSeg4 = PolySeg4.bbox()
      BoxSeg4.top = BoxSeg4.top - to_itype(ext_inner, dbu)
      BoxSeg4.bottom = BoxSeg4.bottom + to_itype(ext_inner, dbu)
      if (BoxSeg4.top - BoxSeg4.bottom) < to_itype(self.min_f, dbu):
        BoxSeg4.top = to_itype(self.min_f/2, dbu)
        BoxSeg4.bottom = -to_itype(self.min_f/2, dbu)
      else:
        ext_inner += ext_inner_delta
      
      A2 = Region(PolySeg4)
      B2 = Region(BoxSeg4)
      C2 = B2 & A2 
      shapes(LayerSiN).insert(C2.transformed(ICplxTrans(x2,0)))
      x1 += dx
      x2 += dx
    
    if not self.width_start:
      shapes(LayerSiN).insert(C2.bbox().transformed(ICplxTrans(x2 - to_itype(self.period*2, dbu),0)))
    
    # Get PinRec layer
    LayerPinRecN = self.layout.layer(TECHNOLOGY['PinRec'])
    
    # Get points
    pts = [Point(x_init, y_init), Point(x_init + to_itype(self.length, dbu), y_init)]
    
    pt0 = pts[0]
    
    t1 = Trans(angle_vector(pts[0]-pts[-1])/90, False, pt0)
    self.cell.shapes(LayerPinRecN).insert(Path([Point(-PIN_LENGTH/2, 0), Point(PIN_LENGTH/2, 0)], wg_width).transformed(t1))
    self.cell.shapes(LayerPinRecN).insert(Text("pin1", t1, PIN_LENGTH, -1))
    
    pt1 = pts[-1]
    pt1.x = x2 - to_itype(min_f - 1.5*self.period, dbu)#+ to_itype(min_f + self.period, dbu)
    t = Trans(angle_vector(pts[-1]-pts[0])/90, False, pt1)
    self.cell.shapes(LayerPinRecN).insert(Path([Point(-PIN_LENGTH/2, 0), Point(PIN_LENGTH/2, 0)], wg_width).transformed(t))
    self.cell.shapes(LayerPinRecN).insert(Text("pin2", t, PIN_LENGTH, -1))

    LayerDevRecN = self.layout.layer(TECHNOLOGY['DevRec'])
    
    # Create the device recognition layer -- make it 1 * wg_width away from the waveguides.
    dev = Box(to_itype(0,dbu), -to_itype(self.width/2+self.outer_width, dbu), x2, to_itype(self.width/2+self.outer_width, dbu) )
    shapes(LayerDevRecN).insert(dev)
    
    # Compact model information
    angle_vec = angle_vector(pts[0]-pts[-1])/90
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
      'Spice_param:taper_length=%.3fu wg_width=%.3fu points="%s" radius=%s' %\
        (self.length, self.width, pts_txt,self.radius ), t, 0.1*wg_width, -1  )
    text.halign=halign
    shape = self.cell.shapes(LayerDevRecN).insert(text)
    t = Trans(angle, False, pt4)
    text = Text ( \
      'Length=%.3fu' %(self.length), t, 0.5*wg_width, -1  )
    text.halign=halign
    shape = self.cell.shapes(LayerDevRecN).insert(text)