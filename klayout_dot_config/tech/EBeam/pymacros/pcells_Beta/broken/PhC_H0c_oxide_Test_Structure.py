from pya import *
import pya
import math

from SiEPIC.utils import get_technology, get_technology_by_name
from SiEPIC.utils import arc, arc_wg, arc_to_waveguide, points_per_circle#,layout

class PhC_H0c_oxide_Test_Structure(pya.PCellDeclarationHelper):
    
  """
  The PCell declaration for the test structure with grating couplers and waveguides and a photonic crystal cavity
  """

  def __init__(self):

    # Important: initialize the super class
    super(PhC_H0c_oxide_Test_Structure, self).__init__()
    
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

 