

"""
KLayout-SiEPIC library for photonic crystals, UBC and SFU


*******
PCells:
*******

1) swg_fc
 - sub-wavelength grating (SWG) fibre coupler (FC)


NOTE: after changing the code, the macro needs to be rerun to install the new
implementation. The macro is also set to "auto run" to install the PCell 
when KLayout is run.

Version history:

2017/07/07 Timothy Richards (Simon Fraser University, BC, Canada) and Adam DeAbreu (Simon Fraser University, BC, Canada)
 - swg_fc PCell

2017/07/07 Lukas Chrostowski
 - library definition and github repo

2017/07/09 Jaspreet Jhoja
  - Added Cavity Hole Pcell

2017/07/09 Jingda Wu
 - Added 2D H0 Photonic crystal cavity with single bus waveguide and pins

2017/07/10 Megan Nantel 
- Added waveguide with impedance matching tapers for transition from external waveguide to Photonic crystal W1 waveguide 

2017/07/10 Jingda Wu
- Improved generation efficiency by using single hole as a cell

2017/07/12 Megan Nantel 
- Added the H0c test structure that includes grating couplers, waveguides, and H0c 

2017/07/12 Jingda Wu
- Added L3 cavity with double bus waveguide and pins
- Added a drop bus to H0 cavity(coupling between waveguide?)
- Simplified code for generation

2017/07/12 Lukas Chrostowski
 - SWGFC litho test structure
 
2017/07/13 Megan Nantel 
- grating coupler to grating coupler reference test structure 
- photonic crystal with only W1 waveguide 
- photonic crystal W1 reference test structure 

2017/07/16 Jingda Wu
- Adaptive cavity generation under difference waveguide location
- Able to choose the number of waveguides per PhC cavity
- Added etch layer (12,0) on PhC slabs
- Added H0 cavity with oxide buffer, reduced the vertices (32->20) for holes due to much smaller hole radius
- Deleteted cavity hole class
- Added hexagon half cell and hexagon with hole half cell for PhC generation, in case needed
- Added H0 cavity generated with hexagon cells
- Added PhC test pattern

2017/08/19 Jingda Wu
- Added suspension anchor areas for the cavities with undercut

2018/02/14 Lukas Chrostowski
- Upgrade to KLayout 0.25 and SiEPIC-Tools v0.3.x, updating layers to SiEPIC-EBeam v0.3.0+



"""

# Import KLayout Python API methods:
# Box, Point, Polygon, Text, Trans, LayerInfo, etc
from pya import *
import pya
import math

from SiEPIC.utils import get_technology, get_technology_by_name
from SiEPIC.utils import arc, arc_wg, arc_to_waveguide, points_per_circle


# -------------------------------------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------------------------------------- #



class swg_fc_test(pya.PCellDeclarationHelper):
  """
  Sub-wavelength-grating fibre coupler PCell litho test structure.

  2017/07/12: Lukas Chrostowski, initial version, based on swg_fc by Tim

  Input: 
  
  """

  def __init__(self):

    # Important: initialize the super class
    super(swg_fc_test, self).__init__()

    # declare the parameters  
    self.param("wavelength", self.TypeDouble, "Design Wavelength (micron)", default = 2.9)  
    self.param("n_t", self.TypeDouble, "Fiber Mode", default = 1.0)
    self.param("n_e", self.TypeDouble, "Grating Index Parameter", default = 3.1)
    self.param("angle_e", self.TypeDouble, "Taper Angle (deg)", default = 20.0)
    self.param("grating_length", self.TypeDouble, "Grating Length (micron)", default = 3.0)
    self.param("taper_length", self.TypeDouble, "Taper Length (micron)", default = 32.0)
    self.param("dc", self.TypeDouble, "Duty Cycle", default = 0.488193)
    self.param("period", self.TypeDouble, "Grating Period", default = 1.18939)
    self.param("ff", self.TypeDouble, "Fill Factor", default = 0.244319)
    self.param("t", self.TypeDouble, "Waveguide Width (micron)", default = 1.0)
    self.param("theta_c", self.TypeDouble, "Insertion Angle (deg)", default = 8.0)
    self.param("fab_error", self.TypeDouble, "Fab Process error max (micron)", default = 0.05)

    
    # Layer parameters
    TECHNOLOGY = get_technology_by_name('EBeam')
    self.param("layer", self.TypeLayer, "Layer", default = TECHNOLOGY['Waveguide'])
    self.param("pinrec", self.TypeLayer, "PinRec Layer", default = TECHNOLOGY['PinRec'])
    self.param("devrec", self.TypeLayer, "DevRec Layer", default = TECHNOLOGY['DevRec'])
    self.param("textl", self.TypeLayer, "Text Layer", default = TECHNOLOGY['Text'])

  def display_text_impl(self):
    # Provide a descriptive text for the cell
    return "swg_fc_test_%.1f-%.2f-%.2f-%.2f-%.2f-%.2f-%.2f-%.2f" % \
    (self.wavelength, self.theta_c, self.period, self.dc, self.ff, self.angle_e, self.taper_length, self.t)
    
#    return "temporary placeholder"
    
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
    LayerSiN = ly.layer(self.layer)
    LayerPinRecN = ly.layer(self.pinrec)
    LayerDevRecN = ly.layer(self.devrec)
    LayerTextN = ly.layer(self.textl)

    from math import pi, cos, sin, log, sqrt, tan
    
    lambda_0 = self.wavelength                   ##um wavelength of light
    pin_length = 0.5                 ##um extra nub for the waveguid attachment
    
    # Geometry
    wh = self.period*self.dc                   ##thick grating
    wl = self.ff*(self.period - wh)            ## thin grating
    spacing = (self.period - wh - wl)/2   ##space between thick and thin
    
    gc_number = int(round(self.grating_length/self.period)) ##number of periods
    gc_number = 3
    e = self.n_t*sin((pi/180)*self.theta_c)/self.n_e
    N = round(self.taper_length*(1+e)*self.n_e/lambda_0) ##allows room for the taper

    start = (pi - (pi/180)*self.angle_e/2)
    stop = (pi + (pi/180)*self.angle_e/2)
              
    # Draw coupler grating.
    for j in range(gc_number):

        # number of points in the arcs:
        # calculate such that the vertex & edge placement error is < 0.5 nm.
        #   see "SiEPIC_EBeam_functions - points_per_circle" for more details
        radius = N*lambda_0 / ( self.n_e*( 1 - e )) + j*self.period + spacing
        seg_points = int(points_per_circle(radius/dbu)/360.*self.angle_e) # number of points grating arc
        theta_up = []
        for m in range(seg_points+1):    
          theta_up = theta_up + [start + m*(stop-start)/seg_points]
        theta_down = theta_up[::-1]
        
        ##small one
        r_up = []
        r_down = []
        rng = range(len(theta_up))
        
        # find the divider to get desired fab error:
        th = min(theta_up)
        div = (2*sin(th)/self.fab_error)*(N*lambda_0 / ( self.n_e*( 1 - e*cos(th) )) + j*self.period + spacing)
        err = (2*sin(th)/div)*(N*lambda_0 / ( self.n_e*( 1 - e*cos(th) )) + j*self.period + spacing)
#        print("div %s, err (double check) %s" % (div, err))

        for k in rng:
          th = theta_up[k]
#          print("%s, %s, %s" % (th, sin(th), 1+sin(th)/10.) )
          r_up = r_up +  [(1-sin(th)/div) *(N*lambda_0 / ( self.n_e*( 1 - e*cos(th) )) + j*self.period + spacing)]
        for k in rng[::-1]:
          th = theta_up[k]
#          print("%s, %s, %s" % (th, sin(th), 1+sin(th)/10.) )
          r_down = r_down +  [(1+sin(th)/div) *(N*lambda_0 / ( self.n_e*( 1 - e*cos(th) )) + j*self.period + spacing)]
    
        xr = []
        yr = []
        for k in range(len(theta_up)):
          xr = xr + [r_up[k]*cos(theta_up[k])]
          yr = yr + [r_up[k]*sin(theta_up[k])]
    
        xl = []
        yl = []
        for k in range(len(theta_down)):
          xl = xl + [(r_down[k] + wl)*cos(theta_down[k])]
          yl = yl + [(r_down[k] + wl)*sin(theta_down[k])]
    
        x = xr + xl
        y = yr + yl
    
        pts = []
        for i in range(len(x)):
            pts.append(Point.from_dpoint(pya.DPoint(x[i]/dbu, y[i]/dbu)))
        #small_one = core.Boundary(points)
        
        polygon = Polygon(pts)
        shapes(LayerSiN).insert(polygon)

        if j==1:         
          # text label dimensions, for minor grating:
          # top 
          shapes(LayerTextN).insert(Text("%0.0f"%((wl+self.fab_error)*1000), Trans(Trans.R0, xl[0]/dbu,yl[0]/dbu))).text_size = 0.2/dbu
          # btm 
          shapes(LayerTextN).insert(Text("%0.0f"%((wl-self.fab_error)*1000), Trans(Trans.R0, xl[-1]/dbu,yl[-1]/dbu))).text_size = 0.2/dbu
          # mid 
          shapes(LayerTextN).insert(Text("%0.0f"%((wl)*1000), Trans(Trans.R0, xl[int(len(theta_up)/2)]/dbu,yl[int(len(theta_up)/2)]/dbu))).text_size = 0.2/dbu
        
        
        ##big one
        r_up = []
        r_down = []
        
        # find the divider to get desired fab error:
        th = min(theta_up)
        div = (2*sin(th)/self.fab_error)*(N*lambda_0 / ( self.n_e*( 1 - e*cos(th) )) + j*self.period + 2*spacing+wl)
        err = (2*sin(th)/div)*(N*lambda_0 / ( self.n_e*( 1 - e*cos(th) )) + j*self.period + 2*spacing+wl)
#        print("div %s, err (double check) %s" % (div, err))

        rng = range(len(theta_up))
        for k in rng:
          th = theta_up[k]
          r_up = r_up +  [(1-sin(th)/div) *(N*lambda_0 / ( self.n_e*( 1 - e*cos(th) )) + j*self.period + 2*spacing+wl)]
        for k in rng[::-1]:
          th = theta_up[k]
          r_down = r_down +  [(1+sin(th)/div) *(N*lambda_0 / ( self.n_e*( 1 - e*cos(th) )) + j*self.period + 2*spacing+wl)]
    
        xr = []
        yr = []
        for k in range(len(theta_up)):
          xr = xr + [r_up[k]*cos(theta_up[k])]
          yr = yr + [r_up[k]*sin(theta_up[k])]
    
        xl = []
        yl = []
        for k in range(len(theta_down)):
          xl = xl + [(r_down[k] + wh)*cos(theta_down[k])]
          yl = yl + [(r_down[k] + wh)*sin(theta_down[k])]
    
        x = xr + xl
        y = yr + yl
        
        pts = []
        for i in range(len(x)):
            pts.append(Point.from_dpoint(pya.DPoint(x[i]/dbu, y[i]/dbu)))
        
        polygon = Polygon(pts)
        shapes(LayerSiN).insert(polygon)
      
        if j==1:         
          # text label dimensions, for major grating:
          # top 
          shapes(LayerTextN).insert(Text("%0.0f"%((wh+self.fab_error)*1000), Trans(Trans.R0, xl[0]/dbu,yl[0]/dbu))).text_size = 0.2/dbu
          # btm 
          shapes(LayerTextN).insert(Text("%0.0f"%((wh-self.fab_error)*1000), Trans(Trans.R0, xl[-1]/dbu,yl[-1]/dbu))).text_size = 0.2/dbu
          # mid 
          shapes(LayerTextN).insert(Text("%0.0f"%((wh)*1000), Trans(Trans.R0, xl[int(len(theta_up)/2)]/dbu,yl[int(len(theta_up)/2)]/dbu))).text_size = 0.2/dbu


# -------------------------------------------------------------------------------------------------------------------------------------------------- #
# -------------------------------------------------------------------------------------------------------------------------------------------------- #

class swg_fc(pya.PCellDeclarationHelper):
  """
  Sub-wavelength-grating fibre coupler PCell implementation.
  Analytical design based on "Grating Coupler Design Based on Silicon-On-Insulator", Yun Wang (2013). Master's Thesis, University of British Columbia, Canada
  Some PCell implementation adapted from the SiEPIC_EBeam library by Dr. Lukas Chrostowski, University of British Columbia, Canada
 
  Separate modelling (e.g. Lumerical MODE) is required to determine the "grating effective index" parameter for a given device layer thickness,
  cladding type, and period/duty cycle/fill factor.

  Script written by Timothy Richards (Simon Fraser University, BC, Canada) and Adam DeAbreu (Simon Fraser University, BC, Canada)

  Changelog

  2017-07-07 - initial publish
  2017-07-07 - change library & component names; commit to github

  TO-DO:
  - implement mode solver here, or call Lumerical MODE to calculate

  Input: 
  
  """

  def __init__(self):

    # Important: initialize the super class
    super(swg_fc, self).__init__()

    # declare the parameters  
    self.param("wavelength", self.TypeDouble, "Design Wavelength (micron)", default = 2.9)  
    self.param("n_t", self.TypeDouble, "Fiber Mode", default = 1.0)
    self.param("n_e", self.TypeDouble, "Grating Index Parameter", default = 3.1)
    self.param("angle_e", self.TypeDouble, "Taper Angle (deg)", default = 20.0)
    self.param("grating_length", self.TypeDouble, "Grating Length (micron)", default = 32.0)
    self.param("taper_length", self.TypeDouble, "Taper Length (micron)", default = 32.0)
    self.param("dc", self.TypeDouble, "Duty Cycle", default = 0.488193)
    self.param("period", self.TypeDouble, "Grating Period", default = 1.18939)
    self.param("ff", self.TypeDouble, "Fill Factor", default = 0.244319)
    self.param("t", self.TypeDouble, "Waveguide Width (micron)", default = 1.0)
    self.param("theta_c", self.TypeDouble, "Insertion Angle (deg)", default = 8.0)
    self.param("w_err", self.TypeDouble, "Width Error (micron)", default = -0.06)
    
    # Width scale parameter is a first pass attempt at designing for length contraction
    # at cryogenic temperature. It is applied BEFORE the width error; this is because
    # the order of operations in the reverse is over/under-etch, then cool and contract.
    # So first scale so that target width is reached after contraction, then add
    # fabrication error so that the scaled width is reached.
    self.param("w_scale", self.TypeDouble, "Width Scale", default = 1.0)
    
    # Layer parameters
    TECHNOLOGY = get_technology_by_name('EBeam')
    self.param("layer", self.TypeLayer, "Layer", default = TECHNOLOGY['Waveguide'])
    self.param("pinrec", self.TypeLayer, "PinRec Layer", default = TECHNOLOGY['PinRec'])
    self.param("devrec", self.TypeLayer, "DevRec Layer", default = TECHNOLOGY['DevRec'])
    self.param("textl", self.TypeLayer, "Text Layer", default = TECHNOLOGY['Text'])

  def display_text_impl(self):
    # Provide a descriptive text for the cell
    return "swg_fc_%.1f-%.2f-%.2f-%.2f-%.2f-%.2f-%.2f-%.2f" % \
    (self.wavelength, self.theta_c, self.period, self.dc, self.ff, self.angle_e, self.taper_length, self.t)
    
#    return "temporary placeholder"
    
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
    LayerSiN = ly.layer(self.layer)
    LayerPinRecN = ly.layer(self.pinrec)
    LayerDevRecN = ly.layer(self.devrec)
    LayerTextN = ly.layer(self.textl)

    from math import pi, cos, sin, log, sqrt, tan
    
    lambda_0 = self.wavelength                   ##um wavelength of light
    pin_length = 0.5                 ##um extra nub for the waveguide attachment
    
    # Geometry
    wh = self.period*self.dc                   ##thick grating
    wl = self.ff*(self.period - wh)            ## thin grating

    # Width scale parameter is a first pass attempt at designing for length contraction
    # at cryogenic temperature. It is applied BEFORE the width error; this is because
    # the order of operations in the reverse is over/under-etch, then cool and contract.
    # So first scale so that target width is reached after contraction, then add
    # fabrication error so that the scaled width is reached.
    
    wh = (wh*self.w_scale + self.w_err)
    wl = (wl*self.w_scale + self.w_err)
    
    spacing = (self.period - wh - wl)/2   ##space between thick and thin
    
    gc_number = int(round(self.grating_length/self.period)) ##number of periods
    e = self.n_t*sin((pi/180)*self.theta_c)/self.n_e
    N = round(self.taper_length*(1+e)*self.n_e/lambda_0) ##allows room for the taper

    start = (pi - (pi/180)*self.angle_e/2)
    stop = (pi + (pi/180)*self.angle_e/2)
              
    # Draw coupler grating.
    for j in range(gc_number):

        # number of points in the arcs:
        # calculate such that the vertex & edge placement error is < 0.5 nm.
        #   see "SiEPIC_EBeam_functions - points_per_circle" for more details
        radius = N*lambda_0 / ( self.n_e*( 1 - e )) + j*self.period + spacing
        seg_points = int(points_per_circle(radius/dbu)/360.*self.angle_e) # number of points grating arc
        theta_up = []
        for m in range(seg_points+1):    
          theta_up = theta_up + [start + m*(stop-start)/seg_points]
        theta_down = theta_up[::-1]

        ##small one
        r_up = []
        r_down = []
        for k in range(len(theta_up)):
          r_up = r_up + [N*lambda_0 / ( self.n_e*( 1 - e*cos(float(theta_up[k])) )) + j*self.period + spacing]
        r_down = r_up[::-1]
    
        xr = []
        yr = []
        for k in range(len(theta_up)):
          xr = xr + [r_up[k]*cos(theta_up[k])]
          yr = yr + [r_up[k]*sin(theta_up[k])]
    
        xl = []
        yl = []
        for k in range(len(theta_down)):
          xl = xl + [(r_down[k] + wl)*cos(theta_down[k])]
          yl = yl + [(r_down[k] + wl)*sin(theta_down[k])]
    
        x = xr + xl
        y = yr + yl
    
        pts = []
        for i in range(len(x)):
            pts.append(Point.from_dpoint(pya.DPoint(x[i]/dbu, y[i]/dbu)))
        #small_one = core.Boundary(points)
        
        polygon = Polygon(pts)
        shapes(LayerSiN).insert(polygon)
        
        ##big one
        r_up = []
        r_down = []
        for k in range(len(theta_up)):
          r_up = r_up + [N*lambda_0 / ( self.n_e*( 1 - e*cos(float(theta_up[k])) )) + j*self.period + 2*spacing+ wl]
        r_down = r_up[::-1]
    
        xr = []
        yr = []
        for k in range(len(theta_up)):
          xr = xr + [r_up[k]*cos(theta_up[k])]
          yr = yr + [r_up[k]*sin(theta_up[k])]
    
        xl = []
        yl = []
        for k in range(len(theta_down)):
          xl = xl + [(r_down[k] + wh)*cos(theta_down[k])]
          yl = yl + [(r_down[k] + wh)*sin(theta_down[k])]
    
        x = xr + xl
        y = yr + yl
        
        pts = []
        for i in range(len(x)):
            pts.append(Point.from_dpoint(pya.DPoint(x[i]/dbu, y[i]/dbu)))
        
        polygon = Polygon(pts)
        shapes(LayerSiN).insert(polygon)
      
    # Taper section
    r_up = []
    r_down = []
    for k in range(len(theta_up)):  
      r_up = r_up + [N*lambda_0 / ( self.n_e*( 1 - e*cos(float(theta_up[k])) ))]
    r_down = r_up[::-1]
     
    xl = []
    yl = []  
    for k in range(len(theta_down)):
      xl = xl + [(r_down[k])*cos(theta_down[k])]
      yl = yl + [(r_down[k])*sin(theta_down[k])]
      
    yr = [self.t/2., self.t/2., -self.t/2., -self.t/2.]
    
    yl_abs = []
    for k in range(len(yl)):
      yl_abs = yl_abs + [abs(yl[k])]
    
    y_max = max(yl_abs)
    iy_max = yl_abs.index(y_max)
      
    L_o = (y_max - self.t/2)/tan((pi/180)*self.angle_e/2)
      
    xr = [L_o+xl[iy_max], 0, 0, L_o+xl[iy_max]]
     
    x = xr + xl
    y = yr + yl  

    pts = []
    for i in range(len(x)):
      pts.append(Point.from_dpoint(pya.DPoint(x[i]/dbu, y[i]/dbu)))
    
    polygon = Polygon(pts)
    shapes(LayerSiN).insert(polygon)


    # Pin on the waveguide:
    pin_length = 200
    x = 0
    t = Trans(x,0)
    pin = pya.Path([Point(-pin_length/2,0), Point(pin_length/2,0)], self.t/dbu)
    pin_t = pin.transformed(t)
    shapes(LayerPinRecN).insert(pin_t)
    text = Text ("pin1", t)
    shape = shapes(LayerPinRecN).insert(text)
    shape.text_size = 0.4/dbu


    # Device recognition layer 
    yr = sin(start) * (N*lambda_0 / ( self.n_e*( 1 - e*cos(float(start)) )) + gc_number*self.period + spacing)
    box1 = Box(-(self.grating_length+self.taper_length)/dbu-pin_length*2, yr/dbu, 0, -yr/dbu)
    shapes(LayerDevRecN).insert(box1)


class H0c(pya.PCellDeclarationHelper):
  """
  Input: length, width
  """
  import numpy
  
  def __init__(self):

    # Important: initialize the super class
    super(H0c, self).__init__()

    self.param("a", self.TypeDouble, "lattice constant (microns)", default = 0.744)     
    self.param("n", self.TypeInt, "Number of holes in x and y direction", default = 30)     
    self.param("r", self.TypeDouble, "hole radius (microns)", default = 0.179)
    self.param("wg_dis", self.TypeInt, "Waveguide distance (number of holes)", default = 3)
    self.param("n_bus", self.TypeInt, "Bus number, 1 or 2 ", default = 2)
    self.param("n_vertices", self.TypeInt, "Vertices of a hole", default = 32)                                
    self.param("S1x", self.TypeDouble, "S1x shift", default = 0.28)     
    self.param("S2x", self.TypeDouble, "S2x shift", default = 0.193)     
    self.param("S3x", self.TypeDouble, "S3x shift", default = 0.194)     
    self.param("S4x", self.TypeDouble, "S4x shift", default = 0.162)
    self.param("S5x", self.TypeDouble, "S5x shift", default = 0.113)
    self.param("S1y", self.TypeDouble, "S1y shift", default = -0.016)
    self.param("S2y", self.TypeDouble, "S2y shift", default = 0.134)
    self.param("etch_condition", self.TypeInt, "etch = 1 if etch box, etch = 2 if no etch box", default = 1)  
    
    TECHNOLOGY = get_technology_by_name('EBeam')
    self.param("layer", self.TypeLayer, "Layer", default = TECHNOLOGY['Waveguide'])
    self.param("pinrec", self.TypeLayer, "PinRec Layer", default = TECHNOLOGY['PinRec'])
    self.param("devrec", self.TypeLayer, "DevRec Layer", default = TECHNOLOGY['DevRec'])
    self.param("textl", self.TypeLayer, "Text Layer", default = TECHNOLOGY['Text'])
    self.param("etch", self.TypeLayer, "oxide etch layer", default = pya.LayerInfo(12, 0))

  def display_text_impl(self):
    # Provide a descriptive text for the cell
    return "H0c_a%s-r%.3f-wg_dis%.3f-n%.3f" % \
    (self.a, self.r, self.wg_dis, self.n)
  
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

    # Fetch all the parameters:
    a = self.a/dbu
    r = self.r/dbu
    wg_dis = self.wg_dis+1
    n_vertices = self.n_vertices
    n_bus = self.n_bus
    n = int(math.ceil(self.n/2))
    Sx = [self.S1x,self.S2x,self.S3x,self.S4x,self.S5x]
    Sy = [self.S1y,0,self.S2y]
    etch_condition = self.etch_condition 
    
    if n_bus == 1:
      Sx = [0,0,0,0,0]
      Sy = [0,0,0]
    
    if wg_dis%2 == 0:
      length_slab_x = (2*n-1)*a
    else:
      length_slab_x = 2*n*a
    
    length_slab_y = 2*(wg_dis+10)*a*math.sqrt(3)/2
    
    length_anchor_y = length_slab_y + 20 * a
    length_anchor_x = length_slab_x + 20 * a
    
    n_x = n
    n_y = wg_dis+10

    # Define Si slab and hole region for future subtraction
    Si_slab = pya.Region()
    Si_slab.insert(pya.Box(-length_anchor_x/2, -length_anchor_y/2, length_anchor_x/2, length_anchor_y/2))
    hole = pya.Region()
    hole_r = r
    trench = pya.Region()
    
    #add the trenches for waveguide connection
    trench_width = 20/dbu
    trench_height = 9*a*math.sqrt(3)/2
    wg_pos = a*math.sqrt(3)/2*wg_dis
    
    trench.insert(pya.Box(-trench_width-length_slab_x/2, wg_pos-trench_height/2, -length_slab_x/2, wg_pos+trench_height/2))
    trench.insert(pya.Box(length_slab_x/2, wg_pos-trench_height/2, trench_width+length_slab_x/2, wg_pos+trench_height/2))
    
    if n_bus == 2:
      wg_pos_2 = -a*math.sqrt(3)/2*wg_dis
      trench.insert(pya.Box(length_slab_x/2, wg_pos_2-trench_height/2, trench_width+length_slab_x/2, wg_pos_2+trench_height/2))

    # function to generate points to create a circle
    def circle(x,y,r):
      npts = n_vertices
      theta = 2 * math.pi / npts # increment, in radians
      pts = []
      for i in range(0, npts):
        pts.append(Point.from_dpoint(pya.DPoint((x+r*math.cos(i*theta))/1, (y+r*math.sin(i*theta))/1)))
      return pts
     
    # raster through all holes with shifts and waveguide 
    
    hole_cell = circle(0,0,hole_r)
    hole_poly = pya.Polygon(hole_cell)  

    for j in range(-n_y,n_y+1):
      if j%2 == 0 and j != wg_dis:
        for i in range(-n_x,n_x+1):
          if j == -wg_dis and i > 3 and n_bus == 2:
            None 
          elif j == 0 and i in (1,-1,2,-2,3,-3,4,-4,5,-5):
            hole_x = abs(i)/i*(abs(i)-0.5+Sx[abs(i)-1])*a
            hole_y = 0 
            hole_trans = pya.Trans(Trans.R0, hole_x,hole_y)
            hole_t = hole_poly.transformed(hole_trans)
            hole.insert(hole_t)           
          elif i!=0:
            hole_x = abs(i)/i*(abs(i)-0.5)*a
            hole_y = j*a*math.sqrt(3)/2
            hole_trans = pya.Trans(Trans.R0, hole_x,hole_y)
            hole_t = hole_poly.transformed(hole_trans)
            hole.insert(hole_t) 
      elif j%2 == 1 and j != wg_dis:
        for i in range(-n_x,n_x+1):
          if j == -wg_dis and i > 3 and n_bus == 2:
            None
          elif i == 0 and j in (1,-1,3,-3):
            hole_x = 0
            hole_y = j*a*(math.sqrt(3)/2)+abs(j)/j*a*Sy[abs(j)-1]
            hole_trans = pya.Trans(Trans.R0, hole_x,hole_y)
            hole_t = hole_poly.transformed(hole_trans)
            hole.insert(hole_t) 
          else:  
            hole_x = i*a
            hole_y = j*a*math.sqrt(3)/2
            hole_trans = pya.Trans(Trans.R0, hole_x,hole_y)
            hole_t = hole_poly.transformed(hole_trans)
            hole.insert(hole_t) 
            
    phc = Si_slab - hole - trench
    self.cell.shapes(LayerSiN).insert(phc)
    
    if etch_condition == 1 :
      box_etch = pya.Box(-(length_slab_x/2-3000), -(length_slab_y/2-3000), length_slab_x/2-3000, length_slab_y/2-3000)
      self.cell.shapes(LayerEtch).insert(box_etch)
    
    # Pins on the waveguide:    
    pin_length = 200
    pin_w = a
    
    t = pya.Trans(Trans.R0, -length_slab_x/2,wg_pos)
    pin = pya.Path([pya.Point(pin_length/2, 0), pya.Point(-pin_length/2, 0)], pin_w)
    pin_t = pin.transformed(t)
    self.cell.shapes(LayerPinRecN).insert(pin_t)
    text = pya.Text ("pin1", t)
    shape = self.cell.shapes(LayerPinRecN).insert(text)
    shape.text_size = 0.4/dbu

    t = pya.Trans(Trans.R0, length_slab_x/2,wg_pos)
    pin = pya.Path([pya.Point(-pin_length/2, 0), pya.Point(pin_length/2, 0)], pin_w)
    pin_t = pin.transformed(t)
    self.cell.shapes(LayerPinRecN).insert(pin_t)
    text = pya.Text ("pin2", t)
    shape = self.cell.shapes(LayerPinRecN).insert(text)
    shape.text_size = 0.4/dbu
    
    #pin for drop waveguide
    if n_bus == 2:
      t = pya.Trans(Trans.R0, length_slab_x/2,-wg_pos)
      pin_t = pin.transformed(t)
      self.cell.shapes(LayerPinRecN).insert(pin_t)
      text = pya.Text ("pin3", t)
      shape = self.cell.shapes(LayerPinRecN).insert(text)
      shape.text_size = 0.4/dbu

    # Create the device recognition layer -- make it 1 * wg_width away from the waveguides.
    points = [[-length_slab_x/2,0], [length_slab_x/2, 0]]
    points = [Point(each[0], each[1]) for each in points]
    path = Path(points, length_slab_y)   
    self.cell.shapes(LayerDevRecN).insert(path.simple_polygon())

class L3c(pya.PCellDeclarationHelper):
  """
  Input: length, width
  """
  import numpy
  
  def __init__(self):

    # Important: initialize the super class
    super(L3c, self).__init__()

    self.param("a", self.TypeDouble, "lattice constant (microns)", default = 0.720)     
    self.param("n", self.TypeInt, "Number of holes in x and y direction", default = 30)     
    self.param("r", self.TypeDouble, "hole radius (microns)", default = 0.181)
    self.param("wg_dis", self.TypeInt, "Waveguide distance (number of holes)", default = 3) 
    self.param("n_bus", self.TypeInt, "Bus number, 1 or 2 ", default = 2)
    self.param("n_vertices", self.TypeInt, "Vertices of a hole", default = 32)            
    self.param("S1x", self.TypeDouble, "S1x shift", default = 0.337)     
    self.param("S2x", self.TypeDouble, "S2x shift", default = 0.27)     
    self.param("S3x", self.TypeDouble, "S3x shift", default = 0.088)     
    self.param("S4x", self.TypeDouble, "S4x shift", default = 0.323)
    self.param("S5x", self.TypeDouble, "S5x shift", default = 0.173)
    TECHNOLOGY = get_technology_by_name('EBeam')
    self.param("layer", self.TypeLayer, "Layer", default = TECHNOLOGY['Waveguide'])
    self.param("pinrec", self.TypeLayer, "PinRec Layer", default = TECHNOLOGY['PinRec'])
    self.param("devrec", self.TypeLayer, "DevRec Layer", default = TECHNOLOGY['DevRec'])
    self.param("textl", self.TypeLayer, "Text Layer", default = TECHNOLOGY['Text'])
    self.param("etch", self.TypeLayer, "oxide etch layer", default = pya.LayerInfo(12, 0))

  def display_text_impl(self):
    # Provide a descriptive text for the cell
    return "L3 Cavity_a%s-r%.3f-wg_dis%.3f-n%.3f" % \
    (self.a, self.r, self.wg_dis, self.n)
  
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

    # Fetch all the parameters:
    a = self.a/dbu
    r = self.r/dbu
    wg_dis = self.wg_dis+1
    n_vertices = self.n_vertices
    n_bus = self.n_bus    
    n = int(math.ceil(self.n/2))
    Sx = [self.S1x,self.S2x,self.S3x,self.S4x,self.S5x]
    if n_bus == 1:
      Sx = [0,0,0,0,0]
      Sy = [0,0,0]    
    
    if wg_dis%2 == 0:
      length_slab_x = 2*n*a
    else:
      length_slab_x = (2*n-1)*a

    length_slab_y = 2*(wg_dis+10)*a*math.sqrt(3)/2
    
    length_anchor_y = length_slab_y + 20 * a
    length_anchor_x = length_slab_x + 20 * a
    
    n_x = n
    n_y = wg_dis+10

    # Define Si slab and hole region for future subtraction
    Si_slab = pya.Region()
    Si_slab.insert(pya.Box(-length_anchor_x/2, -length_anchor_y/2, length_anchor_x/2, length_anchor_y/2))
    hole = pya.Region()
    hole_r = r
    trench = pya.Region()
    
    #add the trenches for waveguide connection
    trench_width = 20/dbu
    trench_height = 9*a*math.sqrt(3)/2
    wg_pos = a*math.sqrt(3)/2*wg_dis
    
    trench.insert(pya.Box(-trench_width-length_slab_x/2, wg_pos-trench_height/2, -length_slab_x/2, wg_pos+trench_height/2))
    trench.insert(pya.Box(length_slab_x/2, wg_pos-trench_height/2, trench_width+length_slab_x/2, wg_pos+trench_height/2))
    
    if n_bus == 2:
      wg_pos_2 = -a*math.sqrt(3)/2*wg_dis
      trench.insert(pya.Box(length_slab_x/2, wg_pos_2-trench_height/2, trench_width+length_slab_x/2, wg_pos_2+trench_height/2))
    
    # function to generate points to create a circle
    def circle(x,y,r):
      npts = n_vertices
      theta = 2 * math.pi / npts # increment, in radians
      pts = []
      for i in range(0, npts):
        pts.append(Point.from_dpoint(pya.DPoint((x+r*math.cos(i*theta))/1, (y+r*math.sin(i*theta))/1)))
      return pts
     
    # raster through all holes with shifts and waveguide 
    
    hole_cell = circle(0,0,hole_r)
    hole_poly = pya.Polygon(hole_cell)  

    for j in range(-n_y,n_y+1):
      if j%2 == 0 and j != wg_dis:
        for i in range(-n_x,n_x+1):
          if j == -wg_dis and i > 3 and n_bus == 2:
            None
          elif j == 0 and i in (-1,0,1):
            None
          elif j == 0 and i in (2,-2,3,-3,4,-4,5,-5,6,-6):
            hole_x = (i+(abs(i)/i)*Sx[abs(i)-2])*a
            hole_y = 0 
            hole_trans = pya.Trans(Trans.R0, hole_x,hole_y)
            hole_t = hole_poly.transformed(hole_trans)
            hole.insert(hole_t)           
          else:
            hole_x = i*a
            hole_y = j*a*math.sqrt(3)/2
            hole_trans = pya.Trans(Trans.R0, hole_x,hole_y)
            hole_t = hole_poly.transformed(hole_trans)
            hole.insert(hole_t) 
      elif j%2 == 1 and j != wg_dis:
        for i in range(-n_x,n_x+1):
          if j == -wg_dis and i > 3 and n_bus == 2:
            None
          elif i != 0:
            hole_x = abs(i)/i*(abs(i)-0.5)*a
            hole_y = j*a*math.sqrt(3)/2
            hole_trans = pya.Trans(Trans.R0, hole_x,hole_y)
            hole_t = hole_poly.transformed(hole_trans)
            hole.insert(hole_t)  
            
    phc = Si_slab - hole - trench
    self.cell.shapes(LayerSiN).insert(phc)
    box_etch = pya.Box(-(length_slab_x/2-3000), -(length_slab_y/2-3000), length_slab_x/2-3000, length_slab_y/2-3000)
    self.cell.shapes(LayerEtch).insert(box_etch)

    # Pins on the waveguide:    
    pin_length = 200
    pin_w = a
    
    t = pya.Trans(Trans.R0, -length_slab_x/2,wg_pos)
    pin = pya.Path([pya.Point(pin_length/2, 0), pya.Point(-pin_length/2, 0)], pin_w)
    pin_t = pin.transformed(t)
    self.cell.shapes(LayerPinRecN).insert(pin_t)
    text = pya.Text ("pin1", t)
    shape = self.cell.shapes(LayerPinRecN).insert(text)
    shape.text_size = 0.4/dbu

    t = pya.Trans(Trans.R0, length_slab_x/2,wg_pos)
    pin = pya.Path([pya.Point(-pin_length/2, 0), pya.Point(pin_length/2, 0)], pin_w)
    pin_t = pin.transformed(t)
    self.cell.shapes(LayerPinRecN).insert(pin_t)
    text = pya.Text ("pin2", t)
    shape = self.cell.shapes(LayerPinRecN).insert(text)
    shape.text_size = 0.4/dbu
    
    #pin for drop waveguide
    if n_bus == 2:
      t = pya.Trans(Trans.R0, length_slab_x/2,-wg_pos)
      pin_t = pin.transformed(t)
      self.cell.shapes(LayerPinRecN).insert(pin_t)
      text = pya.Text ("pin3", t)
      shape = self.cell.shapes(LayerPinRecN).insert(text)
      shape.text_size = 0.4/dbu

    # Create the device recognition layer -- make it 1 * wg_width away from the waveguides.
    points = [[-length_slab_x/2,0], [length_slab_x/2, 0]]
    points = [Point(each[0], each[1]) for each in points]
    path = Path(points, length_slab_y)   
    self.cell.shapes(LayerDevRecN).insert(path.simple_polygon())

class H0c_oxide(pya.PCellDeclarationHelper):
  """
  Input: length, width
  """
  import numpy
  
  def __init__(self):

    # Important: initialize the super class
    super(H0c_oxide, self).__init__()

    self.param("a", self.TypeDouble, "lattice constant (microns)", default = 0.690)     
    self.param("n", self.TypeInt, "Number of holes in x and y direction", default = 30)     
    self.param("r", self.TypeDouble, "hole radius (microns)", default = 0.125)
    self.param("wg_dis", self.TypeInt, "Waveguide distance (number of holes)", default = 3)
    self.param("n_bus", self.TypeInt, "Bus number, 1 or 2 ", default = 2)
    self.param("n_vertices", self.TypeInt, "Vertices of a hole", default = 20)                                
    self.param("S1x", self.TypeDouble, "S1x shift", default = 0.28)     
    self.param("S2x", self.TypeDouble, "S2x shift", default = 0.193)     
    self.param("S3x", self.TypeDouble, "S3x shift", default = 0.194)     
    self.param("S4x", self.TypeDouble, "S4x shift", default = 0.162)
    self.param("S5x", self.TypeDouble, "S5x shift", default = 0.113)
    self.param("S1y", self.TypeDouble, "S1y shift", default = -0.016)
    self.param("S2y", self.TypeDouble, "S2y shift", default = 0.134)
    TECHNOLOGY = get_technology_by_name('EBeam')
    self.param("layer", self.TypeLayer, "Layer", default = TECHNOLOGY['Waveguide'])
    self.param("pinrec", self.TypeLayer, "PinRec Layer", default = TECHNOLOGY['PinRec'])
    self.param("devrec", self.TypeLayer, "DevRec Layer", default = TECHNOLOGY['DevRec'])
    self.param("textl", self.TypeLayer, "Text Layer", default = TECHNOLOGY['Text'])

  def display_text_impl(self):
    # Provide a descriptive text for the cell
    return "H0c_oxide_a%s-r%.3f-wg_dis%.3f-n%.3f" % \
    (self.a, self.r, self.wg_dis, self.n)
  
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

    # Fetch all the parameters:
    a = self.a/dbu
    r = self.r/dbu
    wg_dis = self.wg_dis+1
    n_vertices = self.n_vertices
    n_bus = self.n_bus
    n = int(math.ceil(self.n/2))
    Sx = [self.S1x,self.S2x,self.S3x,self.S4x,self.S5x]
    Sy = [self.S1y,0,self.S2y]
    if n_bus == 1:
      Sx = [0,0,0,0,0]
      Sy = [0,0,0]
          
    if wg_dis%2 == 0:
      length_slab_x = (2*n-1)*a
    else:
      length_slab_x = 2*n*a
    
    length_slab_y = 2*(wg_dis+15)*a*math.sqrt(3)/2
    
    n_x = n
    n_y = wg_dis+10

    # Define Si slab and hole region for future subtraction
    Si_slab = pya.Region()
    Si_slab.insert(pya.Box(-length_slab_x/2, -length_slab_y/2, length_slab_x/2, length_slab_y/2))
    hole = pya.Region()
    hole_r = r

    # function to generate points to create a circle
    def circle(x,y,r):
      npts = n_vertices
      theta = 2 * math.pi / npts # increment, in radians
      pts = []
      for i in range(0, npts):
        pts.append(Point.from_dpoint(pya.DPoint((x+r*math.cos(i*theta))/1, (y+r*math.sin(i*theta))/1)))
      return pts
     
    # raster through all holes with shifts and waveguide 
    
    hole_cell = circle(0,0,hole_r)
    hole_poly = pya.Polygon(hole_cell)  

    for j in range(-n_y,n_y+1):
      if j%2 == 0 and j != wg_dis:
        for i in range(-n_x,n_x+1):
          if j == -wg_dis and i > 3 and n_bus == 2:
            None 
          elif j == 0 and i in (1,-1,2,-2,3,-3,4,-4,5,-5):
            hole_x = abs(i)/i*(abs(i)-0.5+Sx[abs(i)-1])*a
            hole_y = 0 
            hole_trans = pya.Trans(Trans.R0, hole_x,hole_y)
            hole_t = hole_poly.transformed(hole_trans)
            hole.insert(hole_t)           
          elif i!=0:
            hole_x = abs(i)/i*(abs(i)-0.5)*a
            hole_y = j*a*math.sqrt(3)/2
            hole_trans = pya.Trans(Trans.R0, hole_x,hole_y)
            hole_t = hole_poly.transformed(hole_trans)
            hole.insert(hole_t) 
      elif j%2 == 1 and j != wg_dis:
        for i in range(-n_x,n_x+1):
          if j == -wg_dis and i > 3 and n_bus == 2:
            None
          elif i == 0 and j in (1,-1,3,-3):
            hole_x = 0
            hole_y = j*a*(math.sqrt(3)/2)+abs(j)/j*a*Sy[abs(j)-1]
            hole_trans = pya.Trans(Trans.R0, hole_x,hole_y)
            hole_t = hole_poly.transformed(hole_trans)
            hole.insert(hole_t) 
          else:  
            hole_x = i*a
            hole_y = j*a*math.sqrt(3)/2
            hole_trans = pya.Trans(Trans.R0, hole_x,hole_y)
            hole_t = hole_poly.transformed(hole_trans)
            hole.insert(hole_t) 
            
    phc = Si_slab - hole
    self.cell.shapes(LayerSiN).insert(phc)
    
    # Pins on the waveguide:    
    pin_length = 200
    pin_w = a
    wg_pos = a*math.sqrt(3)/2*wg_dis
    
    t = pya.Trans(Trans.R0, -length_slab_x/2,wg_pos)
    pin = pya.Path([pya.Point(pin_length/2, 0), pya.Point(-pin_length/2, 0)], pin_w)
    pin_t = pin.transformed(t)
    self.cell.shapes(LayerPinRecN).insert(pin_t)
    text = pya.Text ("pin1", t)
    shape = self.cell.shapes(LayerPinRecN).insert(text)
    shape.text_size = 0.4/dbu

    t = pya.Trans(Trans.R0, length_slab_x/2,wg_pos)
    pin = pya.Path([pya.Point(-pin_length/2, 0), pya.Point(pin_length/2, 0)], pin_w)
    pin_t = pin.transformed(t)
    self.cell.shapes(LayerPinRecN).insert(pin_t)
    text = pya.Text ("pin2", t)
    shape = self.cell.shapes(LayerPinRecN).insert(text)
    shape.text_size = 0.4/dbu
    
    #pin for drop waveguide
    if n_bus == 2:
      t = pya.Trans(Trans.R0, length_slab_x/2,-wg_pos)
      pin_t = pin.transformed(t)
      self.cell.shapes(LayerPinRecN).insert(pin_t)
      text = pya.Text ("pin3", t)
      shape = self.cell.shapes(LayerPinRecN).insert(text)
      shape.text_size = 0.4/dbu

    # Create the device recognition layer -- make it 1 * wg_width away from the waveguides.
    points = [[-length_slab_x/2,0], [length_slab_x/2, 0]]
    points = [Point(each[0], each[1]) for each in points]
    path = Path(points, length_slab_y)   
    self.cell.shapes(LayerDevRecN).insert(path.simple_polygon())
    
    
class PhC_test(pya.PCellDeclarationHelper):
  """
  Input: length, width
  """
  import numpy
    
  def __init__(self):

    # Important: initialize the super class
    super(PhC_test, self).__init__()

    self.param("a", self.TypeDouble, "lattice constant (microns)", default = 0.744)     
    self.param("n", self.TypeInt, "Number of holes in x and y direction", default = 5)     
    self.param("r", self.TypeDouble, "hole radius (microns)", default = 0.179)
    self.param("n_sweep", self.TypeInt, "Different sizes of holes", default = 13)
    self.param("n_vertices", self.TypeInt, "Vertices of a hole", default = 32)                                
    TECHNOLOGY = get_technology_by_name('EBeam')
    self.param("layer", self.TypeLayer, "Layer", default = TECHNOLOGY['Waveguide'])
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

class Hole_cell_half(pya.PCellDeclarationHelper):
  """
  Input: length, width
  """
  import numpy
  
  def __init__(self):

    # Important: initialize the super class
    super(Hole_cell_half, self).__init__()

    self.param("a", self.TypeDouble, "lattice constant (microns)", default = 0.744)     
    self.param("r", self.TypeDouble, "hole radius (microns)", default = 0.179)
    TECHNOLOGY = get_technology_by_name('EBeam')
    self.param("layer", self.TypeLayer, "Layer", default = TECHNOLOGY['Waveguide'])
    self.param("pinrec", self.TypeLayer, "PinRec Layer", default = TECHNOLOGY['PinRec'])
    self.param("devrec", self.TypeLayer, "DevRec Layer", default = TECHNOLOGY['DevRec'])
    self.param("textl", self.TypeLayer, "Text Layer", default = TECHNOLOGY['Text'])

  def display_text_impl(self):
    # Provide a descriptive text for the cell
    return "Cavity Hole Cell_a%s-r%.3f" % \
    (self.a, self.r)
  
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

    # Fetch all the parameters:
    a = self.a/dbu
    r = self.r/dbu

    # function to generate points to create a circle
    def hexagon_hole_half(a,r): 
      npts = 10    
      theta_div = math.pi/3
      theta_div_hole = math.pi/npts
      triangle_length = a/math.sqrt(3)
      pts = []
      for i in range(0,4):
        pts.append(Point.from_dpoint(pya.DPoint(triangle_length*math.cos(i*theta_div-math.pi/2), triangle_length*math.sin(i*theta_div-math.pi/2))))
      for i in range(0, npts+1):
        pts.append(Point.from_dpoint(pya.DPoint(r*math.cos(math.pi/2-i*theta_div_hole), r*math.sin(math.pi/2-i*theta_div_hole))))
      return pts
 
    hole_cell = pya.Region()
    hole_cell_pts = hexagon_hole_half(a,r)
    hole_cell_poly_half = pya.Polygon(hole_cell_pts)

    #hole_cell.insert(hole_cell_poly_0)
    
    self.cell.shapes(LayerSiN).insert(hole_cell_poly_half)
    
 
class Hexagon_cell_half(pya.PCellDeclarationHelper):
  """
  Input: length, width
  """
  import numpy
  
  def __init__(self):

    # Important: initialize the super class
    super(Hexagon_cell_half, self).__init__()

    self.param("a", self.TypeDouble, "lattice constant (microns)", default = 0.744)     
    self.param("r", self.TypeDouble, "hole radius (microns)", default = 0.179)
    TECHNOLOGY = get_technology_by_name('EBeam')
    self.param("layer", self.TypeLayer, "Layer", default = TECHNOLOGY['Waveguide'])
    self.param("pinrec", self.TypeLayer, "PinRec Layer", default = TECHNOLOGY['PinRec'])
    self.param("devrec", self.TypeLayer, "DevRec Layer", default = TECHNOLOGY['DevRec'])
    self.param("textl", self.TypeLayer, "Text Layer", default = TECHNOLOGY['Text'])

  def display_text_impl(self):
    # Provide a descriptive text for the cell
    return "Cavity Hole Cell_a%s-r%.3f" % \
    (self.a, self.r)
  
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

    # Fetch all the parameters:
    a = self.a/dbu
    r = self.r/dbu

    # function to generate points to create a circle
    def hexagon_half(a): 
      theta_div = math.pi/3
      triangle_length = a/math.sqrt(3)
      pts = []
      for i in range(0,4):
        pts.append(Point.from_dpoint(pya.DPoint(triangle_length*math.cos(i*theta_div-math.pi/2), triangle_length*math.sin(i*theta_div-math.pi/2))))
      return pts      
 
    hexagon_pts = hexagon_half(a)
    hexagon_cell_poly_half = pya.Polygon(hexagon_pts)

    #hole_cell.insert(hole_cell_poly_0)
    
    self.cell.shapes(LayerSiN).insert(hexagon_cell_poly_half)
    

class wg_triangle_tapers(pya.PCellDeclarationHelper):
  """
  The PCell declaration for the strip waveguide taper.
  """

  def __init__(self):

    # Important: initialize the super class
    super(wg_triangle_tapers, self).__init__()

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
    
    
def layout_waveguide_abs(cell, layer, points, w, radius):
    # create a path, then convert to a polygon waveguide with bends
    # cell: cell into which to place the waveguide
    # layer: layer to draw on
    # points: array of vertices, absolute coordinates on the current cell
    # w: waveguide width
    
    # example usage:
    # cell = pya.Application.instance().main_window().current_view().active_cellview().cell
    # LayerSi = LayerInfo(1, 0)
    # points = [ [15, 2.75], [30, 2.75] ]  # units of microns.
    # layout_waveguide_abs(cell, LayerSi, points, 0.5, 10)

    if MODULE_NUMPY:  
      # numpy version
      points=n.array(points)  
      start_point=points[0]
      points = points - start_point  
    else:  
      # without numpy:
      start_point=[]
      start_point.append(points[0][0])
      start_point.append(points[0][1]) 
      for i in range(0,2):
        for j in range(0,len(points)):
          points[j][i] -= start_point[i]
    
    layout_waveguide_rel(cell, layer, start_point, points, w, radius)


def layout_waveguide_rel(cell, layer, start_point, points, w, radius):
    # create a path, then convert to a polygon waveguide with bends
    # cell: cell into which to place the waveguide
    # layer: layer to draw on
    # start_point: starting vertex for the waveguide
    # points: array of vertices, relative to start_point
    # w: waveguide width
    
    # example usage:
    # cell = pya.Application.instance().main_window().current_view().active_cellview().cell
    # LayerSi = LayerInfo(1, 0)
    # points = [ [15, 2.75], [30, 2.75] ]  # units of microns.
    # layout_waveguide_rel(cell, LayerSi, [0,0], points, 0.5, 10)

    
    #print("* layout_waveguide_rel(%s, %s, %s, %s)" % (cell.name, layer, w, radius) )

    ly = cell.layout() 
    dbu = cell.layout().dbu

    start_point=[start_point[0]/dbu, start_point[1]/dbu]

    a1 = []
    for p in points:
      a1.append (pya.DPoint(float(p[0]), float(p[1])))
  
    wg_path = pya.DPath(a1, w)

    npoints = points_per_circle(radius/dbu)
    param = { "npoints": npoints, "radius": float(radius), "path": wg_path, "layer": layer }

    pcell = ly.create_cell("ROUND_PATH", "Basic", param )

    # Configure the cell location
    trans = Trans(Point(start_point[0], start_point[1]))

    # Place the PCell
    cell.insert(pya.CellInstArray(pcell.cell_index(), trans))
    

    
class H0c_Test_Structure(pya.PCellDeclarationHelper):
    
  """
  The PCell declaration for the test structure with grating couplers and waveguides and a photonic crystal cavity
  """

  def __init__(self):

    # Important: initialize the super class
    super(H0c_Test_Structure, self).__init__()
    
    #taper/wg parameters
    self.param("tri_base", self.TypeDouble, "Taper Triangle Base (microns)", default = 0.363)
    self.param("tri_height", self.TypeDouble, "Taper Triangle Height (microns)", default = 0.426)
    self.param("taper_wg_length", self.TypeDouble, "Taper Length (microns)", default = 5)
    self.param("wg_bend_radius", self.TypeDouble, "Waveguide Bend Radius (microns)", default = 15)

    #photonic crystal cavity 
    self.param("a", self.TypeDouble, "lattice constant (microns)", default = 0.744)     
    self.param("n", self.TypeInt, "Number of holes in x and y direction", default = 30)     
    self.param("r", self.TypeDouble, "hole radius (microns)", default = 0.179)
    self.param("wg_dis", self.TypeInt, "Waveguide distance (number of holes)", default = 3)        
    self.param("S1x", self.TypeDouble, "S1x shift", default = 0.28)     
    self.param("S2x", self.TypeDouble, "S2x shift", default = 0.193)     
    self.param("S3x", self.TypeDouble, "S3x shift", default = 0.194)     
    self.param("S4x", self.TypeDouble, "S4x shift", default = 0.162)
    self.param("S5x", self.TypeDouble, "S5x shift", default = 0.113)
    self.param("S1y", self.TypeDouble, "S1y shift", default = -0.016)
    self.param("S2y", self.TypeDouble, "S2y shift", default = 0.134)
    self.param("phc_xdis", self.TypeDouble, "Distance from GC to middle of Cavity", default = 35)
    
    #GC parameters 
    self.param("wavelength", self.TypeDouble, "Design Wavelength (micron)", default = 2.9)  
    self.param("n_t", self.TypeDouble, "Fiber Mode", default = 1.0)
    self.param("n_e", self.TypeDouble, "Grating Index Parameter", default = 3.1)
    self.param("angle_e", self.TypeDouble, "Taper Angle (deg)", default = 20.0)
    self.param("grating_length", self.TypeDouble, "Grating Length (micron)", default = 32.0)
    self.param("taper_length", self.TypeDouble, "Taper Length (micron)", default = 32.0)
    self.param("dc", self.TypeDouble, "Duty Cycle", default = 0.488193)
    self.param("period", self.TypeDouble, "Grating Period", default = 1.18939)
    self.param("ff", self.TypeDouble, "Fill Factor", default = 0.244319)
    self.param("t", self.TypeDouble, "Waveguide Width (micron)", default = 1.0)
    self.param("theta_c", self.TypeDouble, "Insertion Angle (deg)", default = 8.0)
    
    #Layer Parameters
    TECHNOLOGY = get_technology_by_name('EBeam')
    self.param("layer", self.TypeLayer, "Layer", default = TECHNOLOGY['Waveguide'])
    self.param("pinrec", self.TypeLayer, "PinRec Layer", default = TECHNOLOGY['PinRec'])
    self.param("devrec", self.TypeLayer, "DevRec Layer", default = TECHNOLOGY['DevRec'])
    self.param("textl", self.TypeLayer, "Text Layer", default = TECHNOLOGY['Text'])

  def can_create_from_shape_impl(self):
    return False
    
  def produce_impl(self):
    # This is the main part of the implementation: create the layout

    # fetch the parameters
    dbu = self.layout.dbu
    ly = self.layout
    cell = self.cell
    shapes = self.cell.shapes
    
    LayerSi = self.layer
    LayerSiN = ly.layer(self.layer)
    LayerPinRecN = ly.layer(self.pinrec)
    LayerDevRecN = ly.layer(self.devrec)
    LayerTextN = ly.layer(self.textl)
    
    a = self.a 
    n = self.n 
    wg_dis = self.wg_dis
    phc_xdis = self.phc_xdis
    wg_bend_radius = self.wg_bend_radius
    wg_width = self.t
    
    if (wg_dis)%2 == 0:
      length_slab_x = n*a
    else:
      length_slab_x = (n-1)*a
      
    half_slab_x = length_slab_x/2
    

    param_phc = {"a": self.a, "n": self.n, "r": self.r, "wg_dis": self.wg_dis, 
      "S1x": self.S1x, "S2x": self.S2x,"S3x": self.S3x,"S4x": self.S4x,"S5x": self.S5x, 
      "S1y": self.S1y,"S2y": self.S2y,  
      "layer": LayerSi, "pinrec": self.pinrec, "devrec": self.devrec} 
    pcell_phc = ly.create_cell("H0 cavity with waveguide", "SiQL_PCells", param_phc )                              
    t_phc = Trans(Trans.R0,phc_xdis/dbu,(127)/dbu-(math.sqrt(3)/2*a*(wg_dis+1))/dbu) 
    instance = cell.insert(pya.CellInstArray(pcell_phc.cell_index(), t_phc))

    param_GC = {"wavelength": self.wavelength, "n_t":self.n_t, "n_e":self.n_e, "angle_e":self.angle_e, 
      "grating_length":self.grating_length, "taper_length":self.taper_length, "dc":self.dc, "period":self.period, 
      "ff":self.ff, "t":self.t, "theta_c":self.theta_c,
      "layer": LayerSi, "pinrec": self.pinrec, "devrec": self.devrec} 
    pcell_GC = ly.create_cell("SWG Fibre Coupler", "SiQL_PCells", param_GC )
    t_GC = Trans(Trans.R0, 0,0)
    instance = cell.insert(pya.CellInstArray(pcell_GC.cell_index(), t_GC, Point(0,127/dbu), Point(0,0), 3, 1))
    
    param_taper = {"tri_base": self.tri_base, "tri_height":self.tri_height, 
      "taper_wg_length":self.taper_wg_length, "silayer":LayerSi, 
      "pinrec": self.pinrec, "devrec": self.devrec}
    pcell_taper = ly.create_cell("Waveguide Triangle Tapers","SiQL_PCells",param_taper)
    t_taper1 = Trans(Trans.R0,(phc_xdis-half_slab_x)/dbu,(127)/dbu)
    instance = cell.insert(pya.CellInstArray(pcell_taper.cell_index(), t_taper1))
    
    pcell_taper2 = ly.create_cell("Waveguide Triangle Tapers","SiQL_PCells",param_taper)
    t_taper2 = Trans(Trans.R180, (phc_xdis+half_slab_x)/dbu,(127)/dbu)
    instance = cell.insert(pya.CellInstArray(pcell_taper2.cell_index(), t_taper2))
    
    pcell_taper3 = ly.create_cell("Waveguide Triangle Tapers","SiQL_PCells",param_taper)
    t_taper3 = Trans(Trans.R180, (phc_xdis+half_slab_x)/dbu,(127-2*(wg_dis+1)*math.sqrt(3)/2*a)/dbu)
    instance = cell.insert(pya.CellInstArray(pcell_taper3.cell_index(), t_taper3))
    
    # gc middle to in port     
    points = [ [0, 127], [ phc_xdis-half_slab_x-self.taper_wg_length , 127] ] 
    layout_waveguide_abs(cell, LayerSi, points, wg_width, wg_bend_radius)
    
    # gc top to through port     
    points2 = [ [0, 254], [ (phc_xdis+half_slab_x+self.taper_wg_length)+wg_bend_radius , 254], [ (phc_xdis+half_slab_x+self.taper_wg_length)+wg_bend_radius , 127], [ (phc_xdis+half_slab_x+self.taper_wg_length) , 127]  ] 
    layout_waveguide_abs(cell, LayerSi, points2, wg_width, wg_bend_radius)
    
    # gc bottom to coupled port     
    points3 = [ [0, 0], [ (phc_xdis+half_slab_x+self.taper_wg_length)+wg_bend_radius , 0], [ (phc_xdis+half_slab_x+self.taper_wg_length)+wg_bend_radius , 127-2*(wg_dis+1)*a*math.sqrt(3)/2], [ (phc_xdis+half_slab_x+self.taper_wg_length) , 127-2*(wg_dis+1)*a*math.sqrt(3)/2]  ] 
    layout_waveguide_abs(cell, LayerSi, points3, wg_width, wg_bend_radius)

class H0c_oxide_Test_Structure(pya.PCellDeclarationHelper):
    
  """
  The PCell declaration for the test structure with grating couplers and waveguides and a photonic crystal cavity
  """

  def __init__(self):

    # Important: initialize the super class
    super(H0c_oxide_Test_Structure, self).__init__()
    
    #taper/wg parameters
    self.param("tri_base", self.TypeDouble, "Taper Triangle Base (microns)", default = 0.363)
    self.param("tri_height", self.TypeDouble, "Taper Triangle Height (microns)", default = 0.426)
    self.param("taper_wg_length", self.TypeDouble, "Taper Length (microns)", default = 5)
    self.param("wg_bend_radius", self.TypeDouble, "Waveguide Bend Radius (microns)", default = 15)

    #photonic crystal cavity 
    self.param("a", self.TypeDouble, "lattice constant (microns)", default = 0.690)     
    self.param("n", self.TypeInt, "Number of holes in x and y direction", default = 30)     
    self.param("r", self.TypeDouble, "hole radius (microns)", default = 0.125)
    self.param("wg_dis", self.TypeInt, "Waveguide distance (number of holes)", default = 3)
    self.param("n_bus", self.TypeInt, "Bus number, 1 or 2 ", default = 2)
    self.param("n_vertices", self.TypeInt, "Vertices of a hole", default = 20)                                
    self.param("S1x", self.TypeDouble, "S1x shift", default = 0.28)     
    self.param("S2x", self.TypeDouble, "S2x shift", default = 0.193)     
    self.param("S3x", self.TypeDouble, "S3x shift", default = 0.194)     
    self.param("S4x", self.TypeDouble, "S4x shift", default = 0.162)
    self.param("S5x", self.TypeDouble, "S5x shift", default = 0.113)
    self.param("S1y", self.TypeDouble, "S1y shift", default = -0.016)
    self.param("S2y", self.TypeDouble, "S2y shift", default = 0.134)
    self.param("phc_xdis", self.TypeDouble, "Distance from GC to middle of Cavity", default = 35)
    
    #GC parameters 
    self.param("wavelength", self.TypeDouble, "Design Wavelength (micron)", default = 2.9)  
    self.param("n_t", self.TypeDouble, "Fiber Mode", default = 1.0)
    self.param("n_e", self.TypeDouble, "Grating Index Parameter", default = 3.1)
    self.param("angle_e", self.TypeDouble, "Taper Angle (deg)", default = 20.0)
    self.param("grating_length", self.TypeDouble, "Grating Length (micron)", default = 32.0)
    self.param("taper_length", self.TypeDouble, "Taper Length (micron)", default = 32.0)
    self.param("dc", self.TypeDouble, "Duty Cycle", default = 0.488193)
    self.param("period", self.TypeDouble, "Grating Period", default = 1.18939)
    self.param("ff", self.TypeDouble, "Fill Factor", default = 0.244319)
    self.param("t", self.TypeDouble, "Waveguide Width (micron)", default = 1.0)
    self.param("theta_c", self.TypeDouble, "Insertion Angle (deg)", default = 8.0)
    
    #Layer Parameters
    TECHNOLOGY = get_technology_by_name('EBeam')
    self.param("layer", self.TypeLayer, "Layer", default = TECHNOLOGY['Waveguide'])
    self.param("pinrec", self.TypeLayer, "PinRec Layer", default = TECHNOLOGY['PinRec'])
    self.param("devrec", self.TypeLayer, "DevRec Layer", default = TECHNOLOGY['DevRec'])
    self.param("textl", self.TypeLayer, "Text Layer", default = TECHNOLOGY['Text'])

  def can_create_from_shape_impl(self):
    return False
    
  def produce_impl(self):
    # This is the main part of the implementation: create the layout

    # fetch the parameters
    dbu = self.layout.dbu
    ly = self.layout
    cell = self.cell
    shapes = self.cell.shapes
    
    LayerSi = self.layer
    LayerSiN = ly.layer(LayerSi)
    
    a = self.a 
    n = self.n 
    wg_dis = self.wg_dis
    phc_xdis = self.phc_xdis
    wg_bend_radius = self.wg_bend_radius
    wg_width = self.t
    
    if (wg_dis)%2 == 0:
      length_slab_x = n*a
    else:
      length_slab_x = (n-1)*a
      
    half_slab_x = length_slab_x/2
    

    param_phc = {"a": self.a, "n": self.n, "r": self.r, "wg_dis": self.wg_dis,   
      "layer": LayerSi, "pinrec": self.pinrec, "devrec": self.devrec} 
    pcell_phc = ly.create_cell("H0 cavity with waveguide, no etching", "SiQL_PCells", param_phc )                              
    t_phc = Trans(Trans.R0,phc_xdis/dbu,(127)/dbu-(math.sqrt(3)/2*a*(wg_dis+1))/dbu) 
    instance = cell.insert(pya.CellInstArray(pcell_phc.cell_index(), t_phc))

    param_GC = {"wavelength": self.wavelength, "n_t":self.n_t, "n_e":self.n_e, "angle_e":self.angle_e, 
      "grating_length":self.grating_length, "taper_length":self.taper_length, "dc":self.dc, "period":self.period, 
      "ff":self.ff, "t":self.t, "theta_c":self.theta_c,
      "layer": LayerSi, "pinrec": self.pinrec, "devrec": self.devrec} 
    pcell_GC = ly.create_cell("SWG Fibre Coupler", "SiQL_PCells", param_GC )
    t_GC = Trans(Trans.R0, 0,0)
    instance = cell.insert(pya.CellInstArray(pcell_GC.cell_index(), t_GC, Point(0,127/dbu), Point(0,0), 3, 1))
    
    param_taper = {"tri_base": self.tri_base, "tri_height":self.tri_height, 
      "taper_wg_length":self.taper_wg_length, "silayer":LayerSi, 
      "pinrec": self.pinrec, "devrec": self.devrec}
    pcell_taper = ly.create_cell("Waveguide Triangle Tapers","SiQL_PCells",param_taper)
    t_taper1 = Trans(Trans.R0,(phc_xdis-half_slab_x)/dbu,(127)/dbu)
    instance = cell.insert(pya.CellInstArray(pcell_taper.cell_index(), t_taper1))
    
    pcell_taper2 = ly.create_cell("Waveguide Triangle Tapers","SiQL_PCells",param_taper)
    t_taper2 = Trans(Trans.R180, (phc_xdis+half_slab_x)/dbu,(127)/dbu)
    instance = cell.insert(pya.CellInstArray(pcell_taper2.cell_index(), t_taper2))
    
    pcell_taper3 = ly.create_cell("Waveguide Triangle Tapers","SiQL_PCells",param_taper)
    t_taper3 = Trans(Trans.R180, (phc_xdis+half_slab_x)/dbu,(127-2*(wg_dis+1)*math.sqrt(3)/2*a)/dbu)
    instance = cell.insert(pya.CellInstArray(pcell_taper3.cell_index(), t_taper3))
    
    # gc middle to in port     
    points = [ [0, 127], [ phc_xdis-half_slab_x-self.taper_wg_length , 127] ] 
    layout_waveguide_abs(cell, LayerSi, points, wg_width, wg_bend_radius)
    
    # gc top to through port     
    points2 = [ [0, 254], [ (phc_xdis+half_slab_x+self.taper_wg_length)+wg_bend_radius , 254], [ (phc_xdis+half_slab_x+self.taper_wg_length)+wg_bend_radius , 127], [ (phc_xdis+half_slab_x+self.taper_wg_length) , 127]  ] 
    layout_waveguide_abs(cell, LayerSi, points2, wg_width, wg_bend_radius)
    
    # gc bottom to coupled port     
    points3 = [ [0, 0], [ (phc_xdis+half_slab_x+self.taper_wg_length)+wg_bend_radius , 0], [ (phc_xdis+half_slab_x+self.taper_wg_length)+wg_bend_radius , 127-2*(wg_dis+1)*a*math.sqrt(3)/2], [ (phc_xdis+half_slab_x+self.taper_wg_length) , 127-2*(wg_dis+1)*a*math.sqrt(3)/2]  ] 
    layout_waveguide_abs(cell, LayerSi, points3, wg_width, wg_bend_radius)

class L3c_Test_Structure(pya.PCellDeclarationHelper):
    
  """
  The PCell declaration for the test structure with grating couplers and waveguides and a photonic crystal cavity
  """

  def __init__(self):

    # Important: initialize the super class
    super(L3c_Test_Structure, self).__init__()
    
    #taper parameters
    self.param("tri_base", self.TypeDouble, "Taper Triangle Base (microns)", default = 0.363)
    self.param("tri_height", self.TypeDouble, "Taper Triangle Height (microns)", default = 0.426)
    self.param("taper_wg_length", self.TypeDouble, "Taper Length (microns)", default = 5)
    self.param("w", self.TypeDouble, "Waveguide Width", default = 1.0)
    self.param("wg_bend_radius", self.TypeDouble, "Waveguide Bend Radius (microns)", default = 15)

    #photonic crystal cavity 
    self.param("a", self.TypeDouble, "lattice constant (microns)", default = 0.720)     
    self.param("n", self.TypeInt, "Number of holes in x and y direction", default = 34)     
    self.param("r", self.TypeDouble, "hole radius (microns)", default = 0.181)
    self.param("wg_dis", self.TypeInt, "Waveguide distance (number of holes)", default = 3)        
    self.param("S1x", self.TypeDouble, "S1x shift", default = 0.337)     
    self.param("S2x", self.TypeDouble, "S2x shift", default = 0.27)     
    self.param("S3x", self.TypeDouble, "S3x shift", default = 0.088)     
    self.param("S4x", self.TypeDouble, "S4x shift", default = 0.323)
    self.param("S5x", self.TypeDouble, "S5x shift", default = 0.0173)
    self.param("phc_xdis", self.TypeDouble, "Distance from GC to middle of Cavity", default = 35)
    
    #GC parameters 
    self.param("wavelength", self.TypeDouble, "Design Wavelength (micron)", default = 2.9)  
    self.param("n_t", self.TypeDouble, "Fiber Mode", default = 1.0)
    self.param("n_e", self.TypeDouble, "Grating Index Parameter", default = 3.1)
    self.param("angle_e", self.TypeDouble, "Taper Angle (deg)", default = 20.0)
    self.param("grating_length", self.TypeDouble, "Grating Length (micron)", default = 32.0)
    self.param("taper_length", self.TypeDouble, "Taper Length (micron)", default = 32.0)
    self.param("dc", self.TypeDouble, "Duty Cycle", default = 0.488193)
    self.param("period", self.TypeDouble, "Grating Period", default = 1.18939)
    self.param("ff", self.TypeDouble, "Fill Factor", default = 0.244319)
    self.param("t", self.TypeDouble, "Waveguide Width (micron)", default = 1.0)
    self.param("theta_c", self.TypeDouble, "Insertion Angle (deg)", default = 8.0)
    
    #Layer Parameters
    TECHNOLOGY = get_technology_by_name('EBeam')
    self.param("layer", self.TypeLayer, "Layer", default = TECHNOLOGY['Waveguide'])
    self.param("pinrec", self.TypeLayer, "PinRec Layer", default = TECHNOLOGY['PinRec'])
    self.param("devrec", self.TypeLayer, "DevRec Layer", default = TECHNOLOGY['DevRec'])
    self.param("textl", self.TypeLayer, "Text Layer", default = TECHNOLOGY['Text'])

  def can_create_from_shape_impl(self):
    return False
    
  def produce_impl(self):
    # This is the main part of the implementation: create the layout

    # fetch the parameters
    dbu = self.layout.dbu
    ly = self.layout
    cell = self.cell
    shapes = self.cell.shapes
    
    LayerSi = self.layer
    LayerSiN = ly.layer(self.layer)
    LayerPinRecN = ly.layer(self.pinrec)
    LayerDevRecN = ly.layer(self.devrec)
    LayerTextN = ly.layer(self.textl)
    
    a = self.a 
    n = self.n 
    wg_dis = self.wg_dis
    phc_xdis = self.phc_xdis
    wg_bend_radius = self.wg_bend_radius
    wg_width = self.w

    if wg_dis%2 == 0:
      length_slab_x = (n-1)*a
    else:
      length_slab_x = n*a
      
    half_slab_x = length_slab_x/2

    param_phc = {"a": self.a, "n": self.n, "r": self.r, "wg_dis": self.wg_dis, "S1x":self.S1x, "S2x":self.S2x, "S3x":self.S3x, "S4x":self.S4x, "S5x":self.S5x,  
      "layer": self.layer, "pinrec": self.pinrec, "devrec": self.devrec} 
    pcell_phc = ly.create_cell("L3 cavity with waveguide", "SiQL_PCells", param_phc )                             
    t1 = Trans(Trans.R0,phc_xdis/dbu,(127)/dbu-(math.sqrt(3)/2*a*(wg_dis+1))/dbu) 
    instance = cell.insert(pya.CellInstArray(pcell_phc.cell_index(), t1))

    param_GC = {"wavelength": self.wavelength, "n_t":self.n_t, "n_e":self.n_e, "angle_e":self.angle_e, 
      "grating_length":self.grating_length, "taper_length":self.taper_length, "dc":self.dc, "period":self.period, 
      "ff":self.ff, "t":self.t, "theta_c":self.theta_c,
      "layer": LayerSi, "pinrec": self.pinrec, "devrec": self.devrec} 
    pcell_GC = ly.create_cell("SWG Fibre Coupler", "SiQL_PCells", param_GC )
    t_GC = Trans(Trans.R0, 0,0)
    instance = cell.insert(pya.CellInstArray(pcell_GC.cell_index(), t_GC, Point(0,127/dbu), Point(0,0), 3, 1))
    
    param_taper = {"tri_base": self.tri_base, "tri_height":self.tri_height, 
      "taper_wg_length":self.taper_wg_length, "wg_width": self.w, "silayer":LayerSi, 
      "pinrec": self.pinrec, "devrec": self.devrec}
    pcell_taper = ly.create_cell("Waveguide Triangle Tapers","SiQL_PCells",param_taper)
    t_taper1 = Trans(Trans.R0,(phc_xdis-half_slab_x)/dbu,(127)/dbu)
    instance = cell.insert(pya.CellInstArray(pcell_taper.cell_index(), t_taper1))
    
    pcell_taper2 = ly.create_cell("Waveguide Triangle Tapers","SiQL_PCells",param_taper)
    t_taper2 = Trans(Trans.R180, (phc_xdis+half_slab_x)/dbu,(127)/dbu)
    instance = cell.insert(pya.CellInstArray(pcell_taper2.cell_index(), t_taper2))
    
    pcell_taper3 = ly.create_cell("Waveguide Triangle Tapers","SiQL_PCells",param_taper)
    t_taper3 = Trans(Trans.R180, (phc_xdis+half_slab_x)/dbu,(127-2*(wg_dis+1)*math.sqrt(3)/2*a)/dbu)
    instance = cell.insert(pya.CellInstArray(pcell_taper3.cell_index(), t_taper3))

    # gc middle to in port     
    points = [ [0, 127], [ phc_xdis-half_slab_x-self.taper_wg_length , 127] ] 
    layout_waveguide_abs(cell, LayerSi, points, wg_width, wg_bend_radius)
    
    # gc top to through port     
    points2 = [ [0, 254], [ (phc_xdis+half_slab_x+self.taper_wg_length)+wg_bend_radius , 254], [ (phc_xdis+half_slab_x+self.taper_wg_length)+wg_bend_radius , 127], [ (phc_xdis+half_slab_x+self.taper_wg_length) , 127]  ] 
    layout_waveguide_abs(cell, LayerSi, points2, wg_width, wg_bend_radius)
    
    # gc bottom to coupled port     
    points3 = [ [0, 0], [ (phc_xdis+half_slab_x+self.taper_wg_length)+wg_bend_radius , 0], [ (phc_xdis+half_slab_x+self.taper_wg_length)+wg_bend_radius , 127-2*(wg_dis+1)*a*math.sqrt(3)/2], [ (phc_xdis+half_slab_x+self.taper_wg_length) , 127-2*(wg_dis+1)*a*math.sqrt(3)/2]  ] 
    layout_waveguide_abs(cell, LayerSi, points3, wg_width, wg_bend_radius)
    
class GC_to_GC_ref1(pya.PCellDeclarationHelper):
    
  """
  The PCell declaration for the test structure with grating couplers and waveguides and a photonic crystal cavity
  """

  def __init__(self):

    # Important: initialize the super class
    super(GC_to_GC_ref1, self).__init__()

    #other waveguide parameters 
    self.param("wg_radius", self.TypeDouble, "Waveguide Radius (microns)", default = 15)
    self.param("wg_width", self.TypeDouble, "Waveguide x Distance (microns)", default = 1)
    self.param("wg_xdis", self.TypeDouble, "Waveguide x Distance (microns)", default = 5)   
    
    #Layer Parameters
    TECHNOLOGY = get_technology_by_name('EBeam')
    self.param("layer", self.TypeLayer, "Layer", default = TECHNOLOGY['Waveguide'])
    self.param("pinrec", self.TypeLayer, "PinRec Layer", default = TECHNOLOGY['PinRec'])
    self.param("devrec", self.TypeLayer, "DevRec Layer", default = TECHNOLOGY['DevRec'])
    self.param("textl", self.TypeLayer, "Text Layer", default = TECHNOLOGY['Text'])
    
  def can_create_from_shape_impl(self):
    return False
    
  def produce_impl(self):
    # This is the main part of the implementation: create the layout

    # fetch the parameters
    dbu = self.layout.dbu
    ly = self.layout
    cell = self.cell
    shapes = self.cell.shapes
    
    LayerSi = self.layer
    LayerSiN = ly.layer(self.layer)
    LayerPinRecN = ly.layer(self.pinrec)
    LayerDevRecN = ly.layer(self.devrec)
    LayerTextN = ly.layer(self.textl)
    
    wg_r = self.wg_radius
    wg_w = self.wg_width
    wg_xdis = self.wg_xdis 
    
    #uses the default parameters for the GC 
    param_GC = { "layer": LayerSi, "pinrec": self.pinrec, "devrec": self.devrec} 
    pcell_GC = ly.create_cell("SWG Fibre Coupler", "SiQL_PCells", param_GC )
    t_GC = Trans(Trans.R0, 0,0)
    instance = cell.insert(pya.CellInstArray(pcell_GC.cell_index(), t_GC, Point(0,127/dbu), Point(0,0), 2, 1))
     
    points = [ [0, 0], [wg_r+wg_xdis, 0],[wg_r+wg_xdis, 127], [ 0,127]] 
    layout_waveguide_abs(cell, LayerSi, points, wg_w, wg_r)
    
    
class PhC_W1wg(pya.PCellDeclarationHelper):
  """
  Input: length, width
  """
  import numpy
  
  def __init__(self):

    # Important: initialize the super class
    super(PhC_W1wg, self).__init__()

    self.param("a", self.TypeDouble, "lattice constant (microns)", default = 0.744)     
    self.param("n", self.TypeInt, "Number of holes in x and y direction", default = 30)     
    self.param("r", self.TypeDouble, "hole radius (microns)", default = 0.179)
    self.param("wg_dis", self.TypeInt, "Waveguide distance (number of holes)", default = 2)
    self.param("n_vertices", self.TypeInt, "Vertices of a hole", default = 32)    
    self.param("etch_condition", self.TypeInt, "Etch = 1, No Etch = 2", default = 1)                            
    
    TECHNOLOGY = get_technology_by_name('EBeam')
    self.param("layer", self.TypeLayer, "Layer", default = TECHNOLOGY['Waveguide'])
    self.param("pinrec", self.TypeLayer, "PinRec Layer", default = TECHNOLOGY['PinRec'])
    self.param("devrec", self.TypeLayer, "DevRec Layer", default = TECHNOLOGY['DevRec'])
    self.param("textl", self.TypeLayer, "Text Layer", default = TECHNOLOGY['Text'])
    self.param("etch", self.TypeLayer, "oxide etch layer", default = pya.LayerInfo(12, 0))
  
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

    # Fetch all the parameters:
    a = self.a/dbu
    r = self.r/dbu
    wg_dis = self.wg_dis+1
    n_vertices = self.n_vertices
    n = int(math.ceil(self.n/2))
    n_bus = 1
    etch_condition = self.etch_condition
    
    if n_bus == 1:
      Sx = [0,0,0,0,0]
      Sy = [0,0,0]
    
    if wg_dis%2 == 0:
      length_slab_x = (2*n-1)*a
    else:
      length_slab_x = 2*n*a
    
    length_slab_y = 2*(wg_dis+15)*a*math.sqrt(3)/2
    
    n_x = n
    n_y = wg_dis+10

    # Define Si slab and hole region for future subtraction
    Si_slab = pya.Region()
    Si_slab.insert(pya.Box(-length_slab_x/2, -length_slab_y/2, length_slab_x/2, length_slab_y/2))
    hole = pya.Region()
    hole_r = r

    # add suspension beams
    beam_width = 3/dbu
    beam_length = 20/dbu
    beam_x_0 = 8*a
    beam_y_0 = beam_length/2+length_slab_y/2-5000
    
    for i in (-1,1):
      for j in (-1,1):
        beam_x = i*beam_x_0
        beam_y = j*beam_y_0
        Si_slab.insert(pya.Box(-beam_width/2+beam_x, -length_slab_y/2+beam_y, beam_width/2+beam_x, length_slab_y/2+beam_y))
        
    # function to generate points to create a circle
    def circle(x,y,r):
      npts = n_vertices
      theta = 2 * math.pi / npts # increment, in radians
      pts = []
      for i in range(0, npts):
        pts.append(Point.from_dpoint(pya.DPoint((x+r*math.cos(i*theta))/1, (y+r*math.sin(i*theta))/1)))
      return pts
     
    # raster through all holes with shifts and waveguide 
    
    hole_cell = circle(0,0,hole_r)
    hole_poly = pya.Polygon(hole_cell)  

    for j in range(-n_y,n_y+1):
      if j%2 == 0 and j != wg_dis:
        for i in range(-n_x,n_x+1):
          if j == -wg_dis and i > 3 and n_bus == 2:
            None 
          elif j == 0 and i in (1,-1,2,-2,3,-3,4,-4,5,-5):
            hole_x = abs(i)/i*(abs(i)-0.5+Sx[abs(i)-1])*a
            hole_y = 0 
            hole_trans = pya.Trans(Trans.R0, hole_x,hole_y)
            hole_t = hole_poly.transformed(hole_trans)
            hole.insert(hole_t)           
          elif i!=0:
            hole_x = abs(i)/i*(abs(i)-0.5)*a
            hole_y = j*a*math.sqrt(3)/2
            hole_trans = pya.Trans(Trans.R0, hole_x,hole_y)
            hole_t = hole_poly.transformed(hole_trans)
            hole.insert(hole_t) 
      elif j%2 == 1 and j != wg_dis:
        for i in range(-n_x,n_x+1):
          if j == -wg_dis and i > 3 and n_bus == 2:
            None
          elif i == 0 and j in (1,-1,3,-3):
            hole_x = 0
            hole_y = j*a*(math.sqrt(3)/2)+abs(j)/j*a*Sy[abs(j)-1]
            hole_trans = pya.Trans(Trans.R0, hole_x,hole_y)
            hole_t = hole_poly.transformed(hole_trans)
            hole.insert(hole_t) 
          else:  
            hole_x = i*a
            hole_y = j*a*math.sqrt(3)/2
            hole_trans = pya.Trans(Trans.R0, hole_x,hole_y)
            hole_t = hole_poly.transformed(hole_trans)
            hole.insert(hole_t) 
            
    phc = Si_slab - hole
    self.cell.shapes(LayerSiN).insert(phc)
    if etch_condition == 1:
      box_etch = pya.Box(-(length_slab_x/2-3000), -(length_slab_y/2-6000), length_slab_x/2-3000, length_slab_y/2-6000)
      self.cell.shapes(LayerEtch).insert(box_etch)
    
    # Pins on the waveguide:    
    pin_length = 200
    pin_w = a
    wg_pos = a*math.sqrt(3)/2*wg_dis
    
    t = pya.Trans(Trans.R0, -length_slab_x/2,wg_pos)
    pin = pya.Path([pya.Point(-pin_length/2, 0), pya.Point(pin_length/2, 0)], pin_w)
    pin_t = pin.transformed(t)
    self.cell.shapes(LayerPinRecN).insert(pin_t)
    text = pya.Text ("pin1", t)
    shape = self.cell.shapes(LayerPinRecN).insert(text)
    shape.text_size = 0.4/dbu

    t = pya.Trans(Trans.R0, length_slab_x/2,wg_pos)
    pin_t = pin.transformed(t)
    self.cell.shapes(LayerPinRecN).insert(pin_t)
    text = pya.Text ("pin2", t)
    shape = self.cell.shapes(LayerPinRecN).insert(text)
    shape.text_size = 0.4/dbu
    
    #pin for drop waveguide
    if n_bus == 2:
      t = pya.Trans(Trans.R0, length_slab_x/2,-wg_pos)
      pin_t = pin.transformed(t)
      self.cell.shapes(LayerPinRecN).insert(pin_t)
      text = pya.Text ("pin3", t)
      shape = self.cell.shapes(LayerPinRecN).insert(text)
      shape.text_size = 0.4/dbu

    # Create the device recognition layer -- make it 1 * wg_width away from the waveguides.
    points = [[-length_slab_x/2,0], [length_slab_x/2, 0]]
    points = [Point(each[0], each[1]) for each in points]
    path = Path(points, length_slab_y)   
    self.cell.shapes(LayerDevRecN).insert(path.simple_polygon())

    
class PhC_W1wg_reference(pya.PCellDeclarationHelper):
  """
  Input: length, width
  """
  import numpy
  
  def __init__(self):

    # Important: initialize the super class
    super(PhC_W1wg_reference, self).__init__()
   
    
    #phc parameters 
    self.param("a", self.TypeDouble, "lattice constant (microns)", default = 0.744)     
    self.param("n", self.TypeInt, "Number of holes in x and y direction", default = 30)     
    self.param("r", self.TypeDouble, "hole radius (microns)", default = 0.179)
    self.param("wg_dis", self.TypeInt, "Waveguide distance (number of holes)", default = 2)
    self.param("n_vertices", self.TypeInt, "Vertices of a hole", default = 32)    
    self.param("etch_condition", self.TypeInt, "Etch = 1, No Etch = 2", default = 1)   
    self.param("phc_xdis", self.TypeDouble, "Distance to middle of phc", default = 35)
    
    #other waveguide parameters 
    self.param("wg_radius", self.TypeDouble, "Waveguide Radius (microns)", default = 15)  
    self.param("wg_width", self.TypeDouble, "Waveguide Radius (microns)", default = 1)  
    
    #taper parameters
    self.param("tri_base", self.TypeDouble, "Taper Triangle Base (microns)", default = 0.363)
    self.param("tri_height", self.TypeDouble, "Taper Triangle Height (microns)", default = 0.426)
    self.param("taper_wg_length", self.TypeDouble, "Taper Length (microns)", default = 5) 
    
    #Layer Parameters
    TECHNOLOGY = get_technology_by_name('EBeam')
    self.param("layer", self.TypeLayer, "Layer", default = TECHNOLOGY['Waveguide'])
    self.param("pinrec", self.TypeLayer, "PinRec Layer", default = TECHNOLOGY['PinRec'])
    self.param("devrec", self.TypeLayer, "DevRec Layer", default = TECHNOLOGY['DevRec'])
    self.param("textl", self.TypeLayer, "Text Layer", default = TECHNOLOGY['Text'])
    self.param("etch", self.TypeLayer, "oxide etch layer", default = pya.LayerInfo(12, 0))
    
  def can_create_from_shape_impl(self):
    return False
    
  def produce_impl(self):
    # This is the main part of the implementation: create the layout

    # fetch the parameters
    dbu = self.layout.dbu
    ly = self.layout
    cell = self.cell
    shapes = self.cell.shapes
    
    LayerSi = self.layer
    LayerSiN = ly.layer(self.layer)
    LayerPinRecN = ly.layer(self.pinrec)
    LayerDevRecN = ly.layer(self.devrec)
    LayerTextN = ly.layer(self.textl)
    
    wg_r = self.wg_radius
    wg_w = self.wg_width
    phc_xdis = self.phc_xdis 
    wg_dis = self.wg_dis 
    a = self.a 
    w = self.wg_width 
    n = self.n 
    etch_condition = self.etch_condition
    
    param_GC = {"layer": LayerSi, 
      "pinrec": self.pinrec, "devrec": self.devrec} 
    pcell_GC = ly.create_cell("SWG Fibre Coupler", "SiQL_PCells", param_GC )
    t_GC = Trans(Trans.R0, 0,0)
    instance = cell.insert(pya.CellInstArray(pcell_GC.cell_index(), t_GC, Point(0,127/dbu), Point(0,0), 2, 1))
     
    
    if etch_condition == 1:
      param_phc = { "a": self.a, "n":self.n, "r":self.r, "n_bus": 1, "wg_dis":wg_dis, "etch_condition":etch_condition, "layer": LayerSi, 
        "n_vertices":self.n_vertices, "pinrec": self.pinrec, "devrec": self.devrec, "etch":self.etch} 
      pcell_phc = ly.create_cell("H0 cavity with waveguide", "SiQL_PCells", param_phc ) 
      t = Trans(Trans.R0,phc_xdis/dbu,0-((wg_dis+1)*math.sqrt(3)/2*a)/dbu) 
      instance = cell.insert(pya.CellInstArray(pcell_phc.cell_index(), t))
    else: 
      param_phc = { "a": self.a, "n":self.n, "r":self.r, "n_bus": 1, "wg_dis":wg_dis, "layer": LayerSi, 
        "n_vertices":self.n_vertices, "pinrec": self.pinrec, "devrec": self.devrec, "etch":self.etch} 
      pcell_phc = ly.create_cell("H0 cavity with waveguide, no etching", "SiQL_PCells", param_phc ) 
      t = Trans(Trans.R0,phc_xdis/dbu,0-((wg_dis+1)*math.sqrt(3)/2*a)/dbu) 
      instance = cell.insert(pya.CellInstArray(pcell_phc.cell_index(), t))
      
    
    param_taper = {"tri_base": self.tri_base, "tri_height":self.tri_height, 
      "taper_wg_length":self.taper_wg_length, "wg_width": w, "silayer":LayerSi, 
      "pinrec": self.pinrec, "devrec": self.devrec}
    pcell_taper = ly.create_cell("Waveguide Triangle Tapers","SiQL_PCells",param_taper)
    t_taper1 = Trans(Trans.R0,(phc_xdis-n*a/2)/dbu,0)
    instance = cell.insert(pya.CellInstArray(pcell_taper.cell_index(), t_taper1))
    
    pcell_taper2 = ly.create_cell("Waveguide Triangle Tapers","SiQL_PCells",param_taper)
    t_taper2 = Trans(Trans.R180, (phc_xdis+n*a/2)/dbu,0)
    instance = cell.insert(pya.CellInstArray(pcell_taper2.cell_index(), t_taper2))
    
    points = [ [0, 0], [phc_xdis-n*a/2-self.taper_wg_length ,0]] 
    layout_waveguide_abs(cell, LayerSi, points, wg_w, wg_r)
    
    points2 = [[phc_xdis+n*a/2+self.taper_wg_length,0],[phc_xdis+n*a/2+self.taper_wg_length+wg_r,0], [phc_xdis+n*a/2+self.taper_wg_length+wg_r,127], [0,127] ] 
    layout_waveguide_abs(cell, LayerSi, points2, wg_w, wg_r)
    
class H0c_new(pya.PCellDeclarationHelper):
  """
  Input: length, width
  """
  import numpy
  
  def __init__(self):

    # Important: initialize the super class
    super(H0c_new, self).__init__()

    self.param("a", self.TypeDouble, "lattice constant (microns)", default = 0.744)     
    self.param("n", self.TypeInt, "Number of holes in x and y direction", default = 30)     
    self.param("r", self.TypeDouble, "hole radius (microns)", default = 0.179)
    self.param("wg_dis", self.TypeInt, "Waveguide distance (number of holes)", default = 3)        
    self.param("S1x", self.TypeDouble, "S1x shift", default = 0.28)     
    self.param("S2x", self.TypeDouble, "S2x shift", default = 0.193)     
    self.param("S3x", self.TypeDouble, "S3x shift", default = 0.194)     
    self.param("S4x", self.TypeDouble, "S4x shift", default = 0.162)
    self.param("S5x", self.TypeDouble, "S5x shift", default = 0.113)
    self.param("S1y", self.TypeDouble, "S1y shift", default = -0.016)
    self.param("S2y", self.TypeDouble, "S2y shift", default = 0.134)
    self.param("bus_number",  self.TypeInt, "2 for double, 1 for single, max 2", default = 2)
    TECHNOLOGY = get_technology_by_name('EBeam')
    self.param("layer", self.TypeLayer, "Layer", default = TECHNOLOGY['Waveguide'])
    self.param("pinrec", self.TypeLayer, "PinRec Layer", default = TECHNOLOGY['PinRec'])
    self.param("devrec", self.TypeLayer, "DevRec Layer", default = TECHNOLOGY['DevRec'])
    self.param("textl", self.TypeLayer, "Text Layer", default = TECHNOLOGY['Text'])

  def display_text_impl(self):
    # Provide a descriptive text for the cell
    return "H0 Cavity_a%s-r%.3f-wg_dis%.3f-n%.3f" % \
    (self.a, self.r, self.wg_dis, self.n)
  
  def coerce_parameters_impl(self):
    pass

  def can_create_from_shape(self, layout, shape, layer):
    return False
    
  def produce_impl(self):
    
    # fetch the parameters
    dbu = self.layout.dbu
    ly = self.layout
    bus_n = self.bus_number
    
    LayerSi = self.layer
    LayerSiN = ly.layer(self.layer)
    LayerPinRecN = ly.layer(self.pinrec)
    LayerDevRecN = ly.layer(self.devrec)
    LayerTextN = ly.layer(self.textl)
        
    a = self.a/dbu
    r = self.r/dbu
    wg_dis = self.wg_dis+1
    n = int(math.ceil(self.n/2))
    Sx = [self.S1x,self.S2x,self.S3x,self.S4x,self.S5x]
    Sy = [self.S1y,0,self.S2y]
    if wg_dis%2 == 0:
      length_slab_x = 2*n*a
    else:
      length_slab_x = (2*n+1)*a
    
    length_slab_y = 2*(n-2)*a

    if bus_n == 2:
      k = -1
    else:
      k = 1
    
    #function to creat polygon pts for right half of a hole in a hexagon unit cell
    def hexagon_hole_half(a,r): 
      npts = 10    
      theta_div = math.pi/3
      theta_div_hole = math.pi/npts
      triangle_length = a/math.sqrt(3)
      pts = []
      for i in range(0,4):
        pts.append(Point.from_dpoint(pya.DPoint(triangle_length*math.cos(i*theta_div-math.pi/2), triangle_length*math.sin(i*theta_div-math.pi/2))))
      for i in range(0, npts+1):
        pts.append(Point.from_dpoint(pya.DPoint(r*math.cos(math.pi/2-i*theta_div_hole), r*math.sin(math.pi/2-i*theta_div_hole))))
      return pts
    
    def hexagon_shifthole_half(a,r): 
      npts = 10    
      theta_div = math.pi/3
      theta_div_hole = math.pi/npts
      triangle_length = a*1.235/math.sqrt(3)
      pts = []
      for i in range(0,4):
        pts.append(Point.from_dpoint(pya.DPoint(triangle_length*math.cos(i*theta_div-math.pi/2), triangle_length*math.sin(i*theta_div-math.pi/2))))
      for i in range(0, npts+1):
        pts.append(Point.from_dpoint(pya.DPoint(r*math.cos(math.pi/2-i*theta_div_hole), r*math.sin(math.pi/2-i*theta_div_hole))))
      return pts
    
    #function to creat polygon pts for right half of a hexagon unit cell      
    def hexagon_half(a): 
      theta_div = math.pi/3
      triangle_length = a/math.sqrt(3)
      pts = []
      for i in range(0,4):
        pts.append(Point.from_dpoint(pya.DPoint(triangle_length*math.cos(i*theta_div-math.pi/2), triangle_length*math.sin(i*theta_div-math.pi/2))))
      return pts      
    
    #create the right and left half of the hole and hexagon cells
    #hole_cell = pya.Region()
    #hexagon_cell = pya.Region()
    hole = pya.Region()
    
    hole_cell_pts = hexagon_hole_half(a,r)
    hexagon_pts = hexagon_half(a)
    hole_shiftcell_pts = hexagon_shifthole_half(a,r)
    hole_cell_poly_0 = pya.Polygon(hole_cell_pts)
    hexagon_cell_poly_0 = pya.Polygon(hexagon_pts)
    hole_shiftcell_poly_0 = pya.Polygon(hole_shiftcell_pts)

    hole_trans = pya.Trans(pya.Trans.R180)
    hole_cell_poly_1 = hole_cell_poly_0.transformed(hole_trans)
    hexagon_cell_poly_1 = hexagon_cell_poly_0.transformed(hole_trans)    
    hole_shiftcell_poly_1 = hole_shiftcell_poly_0.transformed(hole_trans)
        
    #create the photonic crystal with shifts and waveguides
    for j in range(-n+1,n):
      if j%2 == 0:
        for i in range(-n,n+1):
          #waveguide          
          if (j == k*wg_dis and i > 3) or (j == wg_dis and i != 0):
            hole_x = abs(i)/i*(abs(i)-0.5)*a
            hole_y = j*a*math.sqrt(3)/2
            hole_trans = pya.Trans(Trans.R0, hole_x,hole_y)
            hole_t_0 = hexagon_cell_poly_0.transformed(hole_trans)
            hole_t_1 = hexagon_cell_poly_1.transformed(hole_trans)            
            hole.insert(hole_t_0)
            hole.insert(hole_t_1)
          #filling the edges with half cell
          elif i in (-n,n) and wg_dis%2 == 1:
            hole_x = abs(i)/i*(abs(i)+0.5)*a
            hole_y = j*a*math.sqrt(3)/2
            hole_trans = pya.Trans(Trans.R0, hole_x,hole_y)
            if i == -n:         
              hole_t = hole_cell_poly_0.transformed(hole_trans)
            else:
              hole_t = hole_cell_poly_1.transformed(hole_trans)
            hole.insert(hole_t)
            hole_x = abs(i)/i*(abs(i)-0.5)*a
            hole_y = j*a*math.sqrt(3)/2
            hole_trans = pya.Trans(Trans.R0, hole_x,hole_y)
            hole_t_0 = hole_cell_poly_0.transformed(hole_trans)
            hole_t_1 = hole_cell_poly_1.transformed(hole_trans)
            hole.insert(hole_t_0)  
            hole.insert(hole_t_1)             
          #x shifts
          elif j == 0 and i in (1,-1,2,-2,3,-3,4,-4,5,-5):
            hole_x = abs(i)/i*(abs(i)-0.5+Sx[abs(i)-1])*a
            hole_y = 0 
            hole_trans = pya.Trans(Trans.R0, hole_x,hole_y)
            hole_t_0 = hole_shiftcell_poly_0.transformed(hole_trans)
            hole_t_1 = hole_shiftcell_poly_1.transformed(hole_trans)
            hole.insert(hole_t_0)  
            hole.insert(hole_t_1)                    
          elif i!=0:
            hole_x = abs(i)/i*(abs(i)-0.5)*a
            hole_y = j*a*math.sqrt(3)/2
            hole_trans = pya.Trans(Trans.R0, hole_x,hole_y)
            hole_t_0 = hole_cell_poly_0.transformed(hole_trans)
            hole_t_1 = hole_cell_poly_1.transformed(hole_trans)
            hole.insert(hole_t_0)  
            hole.insert(hole_t_1)
      elif j%2 == 1:
        for i in range(-n,n+1):
          #waveguide
          if (j == k*wg_dis and i > 3) or j == wg_dis:
            hole_x = i*a
            hole_y = j*a*math.sqrt(3)/2
            hole_trans = pya.Trans(Trans.R0, hole_x,hole_y)
            hole_t_0 = hexagon_cell_poly_0.transformed(hole_trans)
            hole_t_1 = hexagon_cell_poly_1.transformed(hole_trans)
            hole.insert(hole_t_0)
            hole.insert(hole_t_1)
          #filling the edges with half cell
          elif wg_dis%2 == 0 and i in (-n,n):
            hole_x = i*a
            hole_y = j*a*math.sqrt(3)/2
            hole_trans = pya.Trans(Trans.R0, hole_x,hole_y) 
            if i == -n:           
              hole_t = hole_cell_poly_0.transformed(hole_trans)
            else:
              hole_t = hole_cell_poly_1.transformed(hole_trans)
            hole.insert(hole_t)               
          #y shifts
          elif i == 0 and j in (1,-1,3,-3):
            hole_x = 0
            hole_y = j*a*(math.sqrt(3)/2)+abs(j)/j*a*Sy[abs(j)-1]
            hole_trans = pya.Trans(Trans.R0, hole_x,hole_y)
            hole_t_0 = hole_shiftcell_poly_0.transformed(hole_trans)
            hole_t_1 = hole_shiftcell_poly_1.transformed(hole_trans)
            hole.insert(hole_t_0)  
            hole.insert(hole_t_1)
          else:  
            hole_x = i*a
            hole_y = j*a*math.sqrt(3)/2
            hole_trans = pya.Trans(Trans.R0, hole_x,hole_y)
            hole_t_0 = hole_cell_poly_0.transformed(hole_trans)
            hole_t_1 = hole_cell_poly_1.transformed(hole_trans)
            hole.insert(hole_t_0)  
            hole.insert(hole_t_1)
    
    #print(hole_t_0)
    box_l = a/2
    hole.insert(pya.Box(-box_l,-box_l,box_l,box_l))
    cover_box = pya.Box(-length_slab_x/2, -a/2, length_slab_x/2, a/2) 
    box_y = n*a*math.sqrt(3)/2  
    cover_box_trans_0 = pya.Trans(Trans.R0, 0,box_y)
    cover_box_trans_1 = pya.Trans(Trans.R0, 0,-box_y) 
    cover_box_t_0 = cover_box.transformed(cover_box_trans_0) 
    cover_box_t_1 = cover_box.transformed(cover_box_trans_1)     
    #hole.insert(pya.Box())    
    self.cell.shapes(LayerSiN).insert(hole)
    self.cell.shapes(LayerSiN).insert(cover_box_t_0)
    self.cell.shapes(LayerSiN).insert(cover_box_t_1)      
    # Pins on the waveguide:    
    pin_length = 200
    pin_w = a
    wg_pos = a*math.sqrt(3)/2*wg_dis
    
    t = pya.Trans(Trans.R0, -length_slab_x/2,wg_pos)
    pin = pya.Path([pya.Point(-pin_length/2, 0), pya.Point(pin_length/2, 0)], pin_w)
    pin_t = pin.transformed(t)
    self.cell.shapes(LayerPinRecN).insert(pin_t)
    text = pya.Text ("pin1", t)
    shape = self.cell.shapes(LayerPinRecN).insert(text)
    shape.text_size = 0.4/dbu

    t = pya.Trans(Trans.R0, length_slab_x/2,wg_pos)
    pin_t = pin.transformed(t)
    self.cell.shapes(LayerPinRecN).insert(pin_t)
    text = pya.Text ("pin2", t)
    shape = self.cell.shapes(LayerPinRecN).insert(text)
    shape.text_size = 0.4/dbu
    
    #pin for drop waveguide
    t = pya.Trans(Trans.R0, length_slab_x/2,-wg_pos)
    pin_t = pin.transformed(t)
    self.cell.shapes(LayerPinRecN).insert(pin_t)
    text = pya.Text ("pin3", t)
    shape = self.cell.shapes(LayerPinRecN).insert(text)
    shape.text_size = 0.4/dbu

    # Create the device recognition layer -- make it 1 * wg_width away from the waveguides.
    points = [[-length_slab_x/2,0], [length_slab_x/2, 0]]
    points = [Point(each[0], each[1]) for each in points]
    path = Path(points, length_slab_y)   
    self.cell.shapes(LayerDevRecN).insert(path.simple_polygon())
      
