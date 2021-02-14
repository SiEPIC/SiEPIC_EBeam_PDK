from pya import *
import pya
import math

from SiEPIC.utils import get_technology, get_technology_by_name
from SiEPIC.utils import arc, arc_wg, arc_to_waveguide, points_per_circle#,layout

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
    
 