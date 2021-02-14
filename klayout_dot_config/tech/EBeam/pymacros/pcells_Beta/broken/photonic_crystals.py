# Import KLayout Python API methods:
# Box, Point, Polygon, Text, Trans, LayerInfo, etc
from pya import *
import pya
import math

from SiEPIC.utils import get_technology, get_technology_by_name
from SiEPIC.utils import arc, arc_wg, arc_to_waveguide, points_per_circle#,layout
 
    
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