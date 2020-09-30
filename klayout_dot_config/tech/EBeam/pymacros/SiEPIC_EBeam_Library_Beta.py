"""
This file is part of the SiEPIC_EBeam_PDK
by Lukas Chrostowski, et al., (c) 2015-2017

This Python file implements a library called "SiEPIC-EBeam-dev"
# - Development components, e.g., Layout only with no Compact Model.
 - Fixed GDS cell components: imported from SiEPIC-EBeam-dev.gds
 - PCells:
    DirectionalCoupler_SeriesRings, DirectionalCoupler_SeriesRings())
    ebeam_dc_halfring_arc, ebeam_dc_halfring_arc())
    DoubleBus_Ring, DoubleBus_Ring())
    TestStruct_DoubleBus_Ring, TestStruct_DoubleBus_Ring())
    TestStruct_DoubleBus_Ring2, TestStruct_DoubleBus_Ring2())
    Waveguide_Route, Waveguide_Route())
    Waveguide_Route_simple, Waveguide_Route_simple())
    Waveguide_Arc, Waveguide_Arc())
    Bent_Coupled_Half_Ring, Bent_Coupled_Half_Ring())
    Bent_CDC_Half_Ring, Bent_CDC_Half_Ring())
    Bezier_Bend, Bezier_Bend())
    Cavity Hole, cavity_hole())
    Tapered Ring, Tapered_Ring())
    Focusing Sub-wavelength grating coupler (fswgc), fswgc() )
    SWG_waveguide, SWG_waveguide())
    SWG_to_strip_waveguide, SWG_to_strip_waveguide())
    strip_to_slot, strip_to_slot() )
    spiral, spiral())
    Waveguide_SBend, Waveguide_SBend())
    ebeam_irph_mrr: in-resonator photoconductive heater, in a ring resonator
    ebeam_irph_wg: in-resonator photoconductive heater, in a straight waveguide


NOTE: after changing the code, the macro needs to be rerun to install the new
implementation. The macro is also set to "auto run" to install the PCell 
when KLayout is run.

Crash warning:
 https://www.klayout.de/forum/comments.php?DiscussionID=734&page=1#Item_13
 This library has nested PCells. Running this macro with a layout open may
 cause it to crash. Close the layout first before running.

*******
GDS:
*******
imported from SiEPIC-EBeam.gds

*******
PCells:
*******

1) Double-bus ring resonator
class TestStruct_DoubleBus_Ring
class DoubleBus_Ring
def layout_Ring(cell, layer, x, y, r, w, npoints):

2) Waveguide Taper
class ebeam_taper_te1550

3) Bragg grating waveguide
class Bragg_waveguide

Also includes additional functions:

1) code for waveguide bends:
def layout_waveguide_abs(cell, layer, points, w, radius):
def layout_waveguide_rel(cell, layer, start_point, points, w, radius):

2) function for making polygon text
def layout_pgtext(cell, layer, x, y, text, mag):

3) functions for inspecting PCell parameters
def PCell_get_parameter_list ( cell_name, library_name ):
def PCell_get_parameters ( pcell ):


Version history:

Lukas Chrostowski           2015/11/05 - 2015/11/10
 - Double-bus ring resonator
 - waveguide bends
 - PCell parameter functions
 - polygon text
 - PCell calling another PCell - TestStruct_DoubleBus_Ring

Lukas Chrostowski           2015/11/14
 - fix for rounding error in "DoubleBus_Ring"

Lukas Chrostowski           2015/11/15
 - fix for Python 3.4: print("xxx")
 
Lukas Chrostowski           2015/11/17
 - update "layout_waveguide_rel" to use the calculated points_per_circle(radius)

Lukas Chrostowski           2016/05/27
 - SWG_waveguide
 - SWG_to_strip_waveguide

Lukas Chrostowski           2016/06/11
 - spiral

S. Preble                   2016/08/26
 - Double Bus Ring Pin's shifted - text now is in the middle of the pin path
 
Timothy Richards, Adam DeAbreu, Lukas Chrostowski  2017/07/11
 -  Focusing Sub-wavelength grating coupler PCell.

Lukas Chrostowski 2017/12/16
 - compatibility with KLayout 0.25 and SiEPIC-Tools

Mustafa Hammood 2018/02/06
 - EBeam-Dev updates and fixes for compatibility with KLayout 0.25 and SiEPIC-Tools

Lukas Chrostowski 2020/04/03
 - SWG_assisted_Strip_WG based on SWG waveguide: adds a strip waveguide
   
Mustafa Hammood 2020/06/26
 - major refactoring of pcells into individual sub files

todo:
replace:     
 layout_arc_wg_dbu(self.cell, Layerm1N, x0,y0, r_m1_in, w_m1_in, angle_min_doping, angle_max_doping)
with:
 self.cell.shapes(Layerm1N).insert(Polygon(arc(w_m1_in, angle_min_doping, angle_max_doping) + [Point(0, 0)]).transformed(t))
"""


'''
def layout_waveguide_abs(cell, layer, points, w, radius):
    # create a path, then convert to a polygon waveguide with bends
    # cell: cell into which to place the waveguide
    # layer: layer to draw on
    # points: array of vertices, absolute coordinates on the current cell
    # w: waveguide width
    
    # example usage:
    # cell = Application.instance().main_window().current_view().active_cellview().cell
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
    # cell = Application.instance().main_window().current_view().active_cellview().cell
    # LayerSi = LayerInfo(1, 0)
    # points = [ [15, 2.75], [30, 2.75] ]  # units of microns.
    # layout_waveguide_rel(cell, LayerSi, [0,0], points, 0.5, 10)

    
    print("* layout_waveguide_rel(%s, %s, %s, %s)" % (cell.name, layer, w, radius) )

    ly = cell.layout() 
    dbu = cell.layout().dbu

    start_point=[start_point[0]/dbu, start_point[1]/dbu]

    a1 = []
    for p in points:
      a1.append (DPoint(float(p[0]), float(p[1])))
  
    wg_path = DPath(a1, w)

    npoints = points_per_circle(radius/dbu)
    param = { "npoints": npoints, "radius": float(radius), "path": wg_path, "layer": layer }

    pcell = ly.create_cell("ROUND_PATH", "Basic", param )

    # Configure the cell location
    trans = Trans(Point(start_point[0], start_point[1]))

    # Place the PCell
    cell.insert(CellInstArray(pcell.cell_index(), trans))
'''

'''
class Waveguide_Route_simple(pya.PCellDeclarationHelper):
  """
  The PCell declaration for a waveguide route
  """

  def __init__(self):

    # Important: initialize the super class
    super(Waveguide_Route_simple, self).__init__()
    TECHNOLOGY = get_technology_by_name('EBeam')

    # declare the parameters
    self.param("layer", self.TypeLayer, "Layer", default = TECHNOLOGY['Waveguide'])
    self.param("path", self.TypeShape, "", default = DPath([DPoint(0,0), DPoint(10,0), DPoint(10,10)], 0.5)  )
    self.param("radius", self.TypeDouble, "Radius", default = 5)

  def display_text_impl(self):
    # Provide a descriptive text for the cell
    return "Waveguide_Route_simple_%s" % self.path
  
  def coerce_parameters_impl(self):
    pass

  def can_create_from_shape(self, layout, shape, layer):
    return shape.is_path()

  def transformation_from_shape(self, layout, shape, layer):
    return Trans(Trans.R0, 0,0)

  def parameters_from_shape(self, layout, shape, layer):
    self._param_values = []
    for pd in self._param_decls:
      self._param_values.append(pd.default)
    
    dbu = layout.dbu
    print("Waveguide_Route_simple.parameters_from_shape")
    print(shape.path)
    points = points_mult(path_to_Dpoints(shape.path), dbu)
    self.path = points_to_Dpath(points, shape.path.width*dbu)

    # Waveguide radius should be specified in the cell in which the Path_to_Waveguide is called
    # using a "User Properties" defined via the Cells window.
    # if missing, a dialog is presented.
    cell = shape.cell
    radius_str = cell.property("radius")  
    if radius_str:
      radius = float(radius_str)
      print("Radius taken from cell {%s} = %s" % (cell.name, radius) )
    else:
      radius = InputDialog.ask_double_ex("Bend Radius", "Enter the bend radius (microns):", 5, 1, 500, 3)
      if radius == None:
        radius = 10.0
      else:
        print("Radius taken from the InputDialog = %s; for next time, saved in cell {%s}." % (radius, cell.name) )
        cell.set_property("radius", str(radius))
    self.radius = radius
    
    return self._param_values  
        
    
  def produce_impl(self):
  
    # fetch the parameters
    dbu = self.layout.dbu
    ly = self.layout

    LayerSi = self.layer
    LayerSiN = ly.layer(LayerSi)

    print("Waveguide:")
    print(self.path)
#    points = points_mult(path_to_Dpoints(self.path), 1/dbu)  # convert from microns to dbu

    points = path_to_Dpoints(self.path) 
#    w = self.path.width/dbu   # w in dbu
#    path = points_to_path(points,w)

    layout_waveguide_abs(self.cell, self.layer, points, self.path.width, self.radius)
'''    
    
'''
legacy pcell has been replaced by Waveguide in SiEPIC General library
class Waveguide_Route(pya.PCellDeclarationHelper):
  """
  The PCell declaration for a waveguide route
  """

  def __init__(self):

    # Important: initialize the super class
    super(Waveguide_Route, self).__init__()
    TECHNOLOGY = get_technology_by_name('EBeam')

    # declare the parameters
    self.param("layer", self.TypeLayer, "Layer", default = TECHNOLOGY['Waveguide'])
    self.param("path", self.TypeShape, "", default = DPath([DPoint(0,0), DPoint(10,0), DPoint(10,10)], 0.5)  )
    self.param("radius", self.TypeDouble, "Radius", default = 5)

  def display_text_impl(self):
    # Provide a descriptive text for the cell
    return "Waveguide_Route_%s" % self.path
  
  def coerce_parameters_impl(self):
    pass

  def can_create_from_shape(self, layout, shape, layer):
    return shape.is_path()

  def transformation_from_shape(self, layout, shape, layer):
#    return Trans(shape.bbox().center())
    return Trans(Trans.R0, 0,0)

  def parameters_from_shape(self, layout, shape, layer):
    shapes = self.cell.shapes
    self._param_values = []
    for pd in self._param_decls:
      self._param_values.append(pd.default)
    
    dbu = layout.dbu
    print("Waveguide_Route.parameters_from_shape")
    print(shape.path)
    points = points_mult(path_to_Dpoints(shape.path), dbu)
    self.path = points_to_Dpath(points, shape.path.width*dbu)

    # Waveguide radius should be specified in the cell in which the Path_to_Waveguide is called
    # using a "User Properties" defined via the Cells window.
    # if missing, a dialog is presented.
    cell = shape.cell
    radius_str = cell.property("radius")  
    if radius_str:
      radius = float(radius_str)
      print("Radius taken from cell {%s} = %s" % (cell.name, radius) )
    else:
      radius = InputDialog.ask_double_ex("Bend Radius", "Enter the bend radius (microns):", 5, 1, 500, 3)
      if radius == None:
        radius = 10.0
      else:
        print("Radius taken from the InputDialog = %s; for next time, saved in cell {%s}." % (radius, cell.name) )
        cell.set_property("radius", str(radius))
    self.radius = radius
    
    return self._param_values  
        
    
  def produce_impl(self):
  
    # fetch the parameters
    dbu = self.layout.dbu
    ly = self.layout

    LayerSi = self.layer
    LayerSiN = ly.layer(LayerSi)

    print("Waveguide:")
    print(self.path)
    points = points_mult(path_to_Dpoints(self.path), 1/dbu)  # convert from microns to dbu
    
    # check the points to remove any co-linear points
    for i in range(len(points)-2, 0, -1):
      # if point i is colinear with its neighbours, remove it
      if check_point_in_segment(Point(*points[i-1]), Point(*points[i+1]), Point(*points[i])):
        # points.remove(i)
        pass
          
    w = self.path.width/dbu   # w in dbu
    path = points_to_path(points,w)

    # save the info on the bends we place.
    bends_pcell = []
    bends_instance = []
    
    for i in range(1,len(points)-1):
      # if point i is colinear with its neighbours, skip it
      if check_point_in_segment(Point(*points[i-1]), Point(*points[i+1]), Point(*points[i])):
        continue
        
      # Place Waveguide_Bend components at each corner:
      # determine rotation: +1 left, -1 right.
      rightvsleft_turn = ( ( angle_segments([points[i-1],points[i]], [points[i],points[i+1]])+90 ) % 360 - 90 ) / 90
      angle = ( angle_segment([points[i-1],points[i]]) ) / 90
      radius = self.radius
      seg_len = distance_xy ( points[i-1],points[i] )
      if (seg_len < radius) and i==1:  # for the first bend, only 1 segment
        radius = seg_len
      if (seg_len / 2 < radius) and i>1:  # for the middle bends, split the segment into two
        radius = seg_len / 2
      seg_len = distance_xy ( points[i],points[i+1] )
      if (seg_len  < radius) and i==len(points)-2:
        radius = seg_len 
      if (seg_len / 2 < radius) and i<len(points)-2:
        radius = seg_len / 2
      param = { "wg_width": self.path.width, "radius": radius, "silayer": LayerSi }
      pcell = ly.create_cell("Waveguide_Bend", "SiEPIC-EBeam PCells", param )
      trans = Trans(angle, True if rightvsleft_turn<0 else False, Point(*points[i]))
      instance = self.cell.insert(CellInstArray(pcell.cell_index(), trans))
      
#      PCell_get_parameters ( pcell )
      
      # Save info on bends
      bends_pcell.append ( pcell )
      bends_instance.append (instance)

    # Place the straight waveguide segments:
    for i in range(0,len(bends_instance)-1):

      # connect p2 of bend i with p1 of bend i+1

      # bend i+1, p2:
      pins = find_PCell_pins(bends_pcell[i])
      p2 = Point(pins['pin2_x'], pins['pin2_y'] )
#      p2 = bends_pcell[i].pcell_parameters_by_name()['p2'] # Point, within the PCell's coordinates
      p2t = bends_instance[i].trans.trans(p2) # Point, transformed based on PCell's instance tranformation

      # bend i, p1:
      pins = find_PCell_pins(bends_pcell[i+1])
      p1 = Point(pins['pin1_x'], pins['pin1_y'] )
#      p1 = bends_pcell[i+1].pcell_parameters_by_name()['p1'] 
      p1t = bends_instance[i+1].trans.trans(p1) 

      # find wg_length, and rotation
      angle = ( angle_segment([points[i+1],points[i+2]]) ) / 90
      wg_length = p2t.distance(p1t) # Path([p2, p1], w).length()
      if wg_length > 0:
        # place the waveguide:      
        param = { "wg_width": w, "wg_length": wg_length, "layer": LayerSi }
        pcell = ly.create_cell("Waveguide_Straight", "SiEPIC-EBeam PCells", param )
        p3 = Point ((p2t.x+p1t.x)/2, (p2t.y+p1t.y)/2) # midpoint of p2t p1t
        trans = Trans(angle, False, p3)
        self.cell.insert(CellInstArray(pcell.cell_index(), trans))      
        print("straight wg mid-section inst: %s, %s, %s, [%s];   bend: %s, %s, p2 %s" % (i, angle, wg_length, p3, bends_instance[i], bends_pcell[i], p2) )

    # put in the straight segment at the beginning of the path
    if len(bends_pcell) > 0:
      pins = find_PCell_pins(bends_pcell[0])
      p1 = Point(pins['pin1_x'], pins['pin1_y'] )
      p1t = bends_instance[0].trans.trans(p1) 
      p0 = Point(*points[0])
      angle = ( angle_segment([points[0],points[1]]) ) / 90
      wg_length = p0.distance(p1t) 
      if wg_length > 0:
        # place the waveguide:      
        p3 = Point ((p0.x+p1t.x)/2, (p0.y+p1t.y)/2) # midpoint
        param = { "wg_width": w, "wg_length": wg_length, "layer": LayerSi }
        pcell = ly.create_cell("Waveguide_Straight", "SiEPIC-EBeam PCells", param )
        trans = Trans(angle, False, p3)
        self.cell.insert(CellInstArray(pcell.cell_index(), trans))      
        print("straight wg end-section inst: %s, %s, %s, [%s]; " % (i, angle, wg_length, p3) )
        
      # put in the straight segment at the end of the path
      i=len(bends_instance)-2
      pins = find_PCell_pins(bends_pcell[i+1])
      p2 = Point(pins['pin2_x'], pins['pin2_y'] )
      p2t = bends_instance[i+1].trans.trans(p2) 
      p0 = Point(*points[i+3])
      angle = ( angle_segment([points[i+2],points[i+3]]) ) / 90
      wg_length = p0.distance(p2t) 
      if wg_length > 0:
        # place the waveguide:      
        p3 = Point ((p0.x+p2t.x)/2, (p0.y+p2t.y)/2) # midpoint
        param = { "wg_width": w, "wg_length": wg_length, "layer": LayerSi }
        pcell = ly.create_cell("Waveguide_Straight", "SiEPIC-EBeam PCells", param )
        trans = Trans(angle, False, p3)
        self.cell.insert(CellInstArray(pcell.cell_index(), trans))      
        print("straight wg end-section inst: %s, %s, %s, [%s]; " % (i, angle, wg_length, p3) )
    else:
      # just a straight section:
        p1 = Point(*points[0])
        p2 = Point(*points[len(points)-1])
        wg_length = p1.distance(p2) 
        angle = ( angle_segment([points[0],points[len(points)-1]]) ) / 90
        p3 = Point ((p1.x+p2.x)/2, (p1.y+p2.y)/2) # midpoint
        param = { "wg_width": w, "wg_length": wg_length, "layer": LayerSi }
        pcell = ly.create_cell("Waveguide_Straight", "SiEPIC-EBeam PCells", param )
        trans = Trans(angle, False, p3)
        self.cell.insert(CellInstArray(pcell.cell_index(), trans))      
        print("straight wg end-section inst:  %s, %s, [%s]; " % (angle, wg_length, p3) )

'''
import pcells_EBeam_Beta
from pya import *

class SiEPIC_EBeam_dev(Library):
  """
  The library where we will put the PCells and GDS into 
  """

  def __init__(self):

    tech_name = 'EBeam'
    library = tech_name+'_Beta'
    
    print("Initializing '%s' Library." % library)

    # Set the description
# windows only allows for a fixed width, short description 
    self.description = "v0.3.3, Beta components"
# OSX does a resizing:
#    self.description = "Beta layouts only"

    # Import all the GDS files from the tech folder "gds"
    import os, fnmatch
    dir_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../gds/development")
    search_str = '*' + '.gds'
    for root, dirnames, filenames in os.walk(dir_path, followlinks=True):
        for filename in fnmatch.filter([f.lower() for f in filenames], search_str):
            file1=os.path.join(root, filename)
            print(" - reading %s" % file1 )
            self.layout().read(file1)
    
    # Create the PCell declarations
    for attr, value in pcells_EBeam_Beta.__dict__.items():
        if '__module__' in dir(value):
            try:
                if value.__module__.split('.')[0] == 'pcells_EBeam_Beta' and attr != 'cls':
                    print('Registered pcell: '+attr)
                    self.layout().register_pcell(attr, value())
            except:
                pass

    # only need to reload if we are debugging, and are making changes to the code
    if sys.version_info[0] == 3:
        if sys.version_info[1] < 4:
            from imp import reload
        else:
            from importlib import reload
    elif sys.version_info[0] == 2:
        from imp import reload

    import PCMSpiral_PCells as spirals
    spirals = reload(spirals)
    
    self.layout().register_pcell("Spiral_BraggGrating", spirals.PCMSpiralBraggGrating())
    self.layout().register_pcell("Spiral_BraggGrating_Slab", spirals.PCMSpiralBraggGratingSlab())
    self.layout().register_pcell("Spiral_NoCenterBraggGrating", spirals.Spiral_NoCenterBraggGrating())
    self.layout().register_pcell("Spiral_CDC_BraggGrating", spirals.CDCSpiralBraggGrating())
    self.layout().register_pcell("SpiralWaveguide", spirals.SpiralWaveguide()) 


#    import Bragg_complex as Bragg_complex
#    Bragg_complex = reload(Bragg_complex)
#    self.layout().register_pcell("Bragg_phase_modulated", Bragg_complex.Bragg_phase_modulated())
#    self.layout().register_pcell("Bragg_Straight_from_file", Bragg_Straight_from_file())
    

    try:  # in case there are errors, e.g., missing numpy
      from photonic_crystals import photonic_crystals
      photonic_crystals = reload(photonic_crystals)
  
  #    self.layout().register_pcell("SWG Fibre Coupler - litho test", swg_fc_test())
      self.layout().register_pcell("SWG Fibre Grating Coupler", photonic_crystals.swg_fc())
      self.layout().register_pcell("PhC H0 cavity with waveguide", photonic_crystals.H0c())
      self.layout().register_pcell("PhC L3 cavity with waveguide", photonic_crystals.L3c())
      self.layout().register_pcell("PhC H0 cavity with waveguide, no etching", photonic_crystals.H0c_oxide())
      self.layout().register_pcell("PhC H0 cavity with waveguide, with hexagon cell", photonic_crystals.H0c_new())
      self.layout().register_pcell("PhC Grating Coupler", photonic_crystals.pc_gc_hex())      
  #    self.layout().register_pcell("PhC hole resolution test structure", photonic_crystals.PhC_test())
  #    self.layout().register_pcell("Half of the hole cell", photonic_crystals.Hole_cell_half())
  #    self.layout().register_pcell("Half of the hexagon cell", photonic_crystals.Hexagon_cell_half())
  #    self.layout().register_pcell("Waveguide Triangle Tapers", photonic_crystals.wg_triangle_tapers())
  #    self.layout().register_pcell("PhC H0c Test Structure", photonic_crystals.H0c_Test_Structure())
  #    self.layout().register_pcell("PhC H0c oxide Test Structure", photonic_crystals.H0c_oxide_Test_Structure())
  #    self.layout().register_pcell("PhC L3c Test Structure", photonic_crystals.L3c_Test_Structure())
  #    self.layout().register_pcell("Grating Coupler to Grating Coupler Reference Device", photonic_crystals.GC_to_GC_ref1())
      self.layout().register_pcell("PhC W1 Waveguide", photonic_crystals.PhC_W1wg()) 
  #    self.layout().register_pcell("PhC W1 Reference Structure", photonic_crystals.PhC_W1wg_reference())
    except:
      pass
    
    # Register us the library with the technology name
    # If a library with that name already existed, it will be replaced then.
    self.register(library)

    if int(Application.instance().version().split('.')[1]) > 24:
      # KLayout v0.25 introduced technology variable:
      self.technology=tech_name

    self.layout().add_meta_info(LayoutMetaInfo("path",os.path.realpath(__file__)))
    self.layout().add_meta_info(LayoutMetaInfo("technology",tech_name))

# Setup path to load .py files in present folder:
import os, inspect, sys
path = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
if not path in sys.path:
  sys.path.append(path)

# Instantiate and register the library
SiEPIC_EBeam_dev()