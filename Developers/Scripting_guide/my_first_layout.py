from pya import *

# Example layout function
def bent_bragg_layout():

  # Configure parameter sweep  
  pol = 'te'
  if pol == 'te':
    r = 20
    w = 0.5
    gap = 0.2
    
    wg_bend_radius = 5
  
  # Import functions from SiEPIC-Tools, and get technology details
  from SiEPIC.utils import select_paths, get_layout_variables
  TECHNOLOGY, lv, ly, cell = get_layout_variables()
  dbu = ly.dbu
  from SiEPIC.extend import to_itype
  from SiEPIC.scripts import path_to_waveguide
  
  # Layer mapping:
  LayerSiN = ly.layer(TECHNOLOGY['Si'])
  fpLayerN = cell.layout().layer(TECHNOLOGY['FloorPlan'])
  TextLayerN = cell.layout().layer(TECHNOLOGY['Text'])
  
  # Draw the floor plan
  cell.shapes(fpLayerN).insert(Box(0,0, 610/dbu, 405/dbu))
  
  #** Create the device under test (directional coupler)
  top_cell = cell
  
  pcell = ly.create_cell("ebeam_dc_halfring_straight", "EBeam", { "r": r, "w": w, "g": gap, "bustype": 0 } )
  
  x_pos_device = 100
  y_pos_device = 100
  
  t = Trans(Trans.R90, x_pos_device/dbu, to_itype(y_pos_device,dbu))
  
  cell.insert(CellInstArray(pcell.cell_index(),t))


  #** input/out GCs
  GC_array = ly.create_cell("ebeam_gc_te1550", "EBeam").cell_index() 
  GC_pitch = 127
  x_pos_GC = 33.1
  y_pos_GC = 21.4/2
  t = Trans(Trans.R0, x_pos_GC/dbu, to_itype(y_pos_GC,dbu))
  
  cell.insert(CellInstArray(GC_array, t, DPoint(0,GC_pitch).to_itype(dbu), DPoint(0,0).to_itype(dbu), 4, 1))
  

  #** routing
  pts = [DPoint(x_pos_GC, y_pos_GC), DPoint(x_pos_device, y_pos_GC) ,DPoint(x_pos_device,y_pos_device-r-0.75), ]
  dpath = DPath(pts, 0.5).transformed(DTrans(DTrans.R0,0,0))
  cell.shapes(LayerSiN).insert(dpath.to_itype(dbu))
  
  # do the other 3!
  
  
bent_bragg_layout()