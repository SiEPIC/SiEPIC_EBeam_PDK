import pya
from pya import *
from SiEPIC.utils import get_technology_by_name

class TestStruct_DoubleBus_Ring(pya.PCellDeclarationHelper):
  """
  The PCell declaration for the DoubleBus_Ring test structure with grating couplers and waveguides
  """

  def __init__(self):

    # Important: initialize the super class
    super(TestStruct_DoubleBus_Ring, self).__init__()
    self.technology_name = 'EBeam'
    TECHNOLOGY = get_technology_by_name(self.technology_name)

    # declare the parameters
    self.param("silayer", self.TypeLayer, "Layer", default = TECHNOLOGY['Si'])
    self.param("s", self.TypeShape, "", default = DPoint(0, 0))
    self.param("r", self.TypeDouble, "Radius", default = 10)
    self.param("w", self.TypeDouble, "Waveguide Width", default = 0.5)
    self.param("g", self.TypeDouble, "Gap", default = 0.2)
    self.param("npoints", self.TypeInt, "Number of points", default = 500)     
    self.param("textpolygon", self.TypeInt, "Draw text polygon label? 0/1", default = 1)
    self.param("textlayer", self.TypeLayer, "Text Layer", default = LayerInfo(10, 0))
    self.param("pinrec", self.TypeLayer, "PinRec Layer", default = TECHNOLOGY['PinRec'])
    self.param("devrec", self.TypeLayer, "DevRec Layer", default = TECHNOLOGY['DevRec'])

  def display_text_impl(self):
    # Provide a descriptive text for the cell
    return "TestStruct_DoubleBus_Ring(R=" + ('%s' % self.r) + ",g=" + ('%s' % (1000*self.g)) + ")"

  def can_create_from_shape_impl(self):
    return False

    
  def produce_impl(self):
    # This is the main part of the implementation: create the layout

    # fetch the parameters
    dbu = self.layout.dbu
    ly = self.layout
    cell = self.cell
    shapes = self.cell.shapes
    
    LayerSi = self.silayer
    LayerSiN = ly.layer(LayerSi)
    TextLayerN = ly.layer(self.textlayer)

    # Import cells from the SiEPIC GDS Library, and instantiate them

        
    # Ring resonator PCell
    r = self.r
    wg_width = self.w
    g = self.g
    y_ring = 127*3/2+r


#    pcell = ly.create_cell("DoubleBus_Ring", "SiEPIC", {"r": r, "w": wg_width, "g": g, "l": LayerSi})
#    print( "pcell: %s, %s" % (pcell.cell_index(), ly.cell_name(pcell.cell_index()) ) )
#    t = Trans(Trans.R270, 10 / dbu, y_ring / dbu) 
#    instance = cell.insert(CellInstArray(pcell.cell_index(), t))
#    print(instance.cell_index)


    self.layout.technology_name=self.technology_name

    lib = Library.library_by_name("EBeam_Beta","EBeam")
    if lib == None:
      raise Exception("Unknown lib 'EBeam_Beta'")

    pcell_decl = lib.layout().pcell_declaration("DoubleBus_Ring");
    if pcell_decl == None:
      raise Exception("Unknown PCell 'DoubleBus_Ring'")
    param = { 
      "r": r, 
      "w": wg_width, 
      "g": g,
      "silayer": LayerSi,
      "devrec": self.devrec, 
      "pinrec": self.pinrec
    }

    pv = []
    for p in pcell_decl.get_parameters():
      if p.name in param:
        pv.append(param[p.name])
      else:
        pv.append(p.default)
    # "fake PCell code" 
    pcell = ly.create_cell("Ring")
    pcell_decl.produce(ly, [ LayerSiN ], pv, pcell)
    t = Trans(Trans.R270, 10 / dbu, y_ring / dbu) 
    instance = cell.insert(CellInstArray(pcell.cell_index(), t))


    # Grating couplers, Ports 1, 2, 3, 4 (top-down):
    GC_name = "ebeam_gc_te1550"
    GC_imported = ly.cell(GC_name)
    if GC_imported == None:
      GC_imported = ly.create_cell(GC_name, "EBeam").cell_index()
    else:
      GC_imported = GC_imported.cell_index()  
    # print( "Cell: GC_imported: #%s" % GC_imported )
    t = Trans(Trans.R0, 0, 0)
    instance = cell.insert(CellInstArray(GC_imported, t, Point(0,127/dbu), Point(0,0), 4, 1))
    # print(instance.cell_index)

    # Label for automated measurements, laser on Port 2, detectors on Ports 1, 3, 4
    t = Trans(Trans.R0, 0, 127*2/dbu)
    text = Text ("opt_in_TE_1550_device_DoubleBusRing", t)
    shape = cell.shapes(TextLayerN).insert(text)
    shape.text_size = 3/dbu



    # Create paths for waveguides
    wg_bend_radius = 10

    # GC3 to bottom-left of ring
    points = [ [0, 127], [10,127], [10, y_ring-2*r-wg_width] ] 
    layout_waveguide_abs(cell, LayerSi, points, wg_width, wg_bend_radius)

    # GC4 to bottom-right of ring
    points = [ [0, 0], [10+2*r+2*g+2*wg_width,0], [10+2*r+2*g+2*wg_width, y_ring-2*r-wg_width]  ] 
    layout_waveguide_abs(cell, LayerSi, points, wg_width, 20)

    # GC2 to top-right of ring
    points = [ [10,y_ring], [10, 127*2], [0,127*2] ] 
    layout_waveguide_abs(cell, LayerSi, points, wg_width, wg_bend_radius)

    # GC1 to top-left of ring
    points = [ [0, 127*3], [10+2*r+2*g+2*wg_width,127*3], [10+2*r+2*g+2*wg_width, y_ring] ] 
    layout_waveguide_abs(cell, LayerSi, points, wg_width, 20)



    # print( "Done drawing the layout for - TestStruct_DoubleBus_Ring: %.3f-%g" % (r, g) )
