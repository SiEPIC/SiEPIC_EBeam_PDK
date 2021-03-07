from pya import *
import pya
import math

from SiEPIC.utils import get_technology, get_technology_by_name
from SiEPIC.utils import arc, arc_wg, arc_to_waveguide, points_per_circle#,layout

class PhC_GC_to_GC_ref1(pya.PCellDeclarationHelper):
    
  """
  The PCell declaration for the test structure with grating couplers and waveguides and a photonic crystal cavity
  """
  def __init__(self):

    # Important: initialize the super class
    super(PhC_GC_to_GC_ref1, self).__init__()

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
    #instance = cell.insert(pya.place_cell(pcell_GC, t_GC, Point(0,127/dbu), Point(0,0), 2, 1))
    #instance=place_cell(cell,pcell_GC,[0.5,0.5])
    cell.insert(pya.CellInstArray(pcell_GC.cell_index(),pya.Trans(pya.Trans.R0, 0, 0)))
    print("test")
    return
    
    points = [ [0, 0], [wg_r+wg_xdis, 0],[wg_r+wg_xdis, 127], [ 0,127]] 
    #layout_waveguide_abs(cell, LayerSi, points, wg_w, wg_r)
    