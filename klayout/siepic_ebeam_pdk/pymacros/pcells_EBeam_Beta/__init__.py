import os, sys
import SiEPIC
try: 
  import siepic_tools
except:
  pass

# import xml before lumapi (SiEPIC.lumerical), otherwise XML doesn't work:
from xml.etree import cElementTree

import math
from SiEPIC.utils import arc, arc_xy, arc_wg, arc_to_waveguide, points_per_circle
import pya
from SiEPIC.utils import get_technology, get_technology_by_name
# Import KLayout Python API methods:
# Box, Point, Polygon, Text, Trans, LayerInfo, etc
from pya import *
import pya

#import numpy as np
MODULE_NUMPY = False


op_tag = "" #operation tag which defines whether we are loading library in script or GUI env

try:
  # import pya from klayout
  import pya
  if("Application" in str(dir(pya))):
    from SiEPIC.utils import get_technology_by_name
    op_tag = "GUI" 
    #import pya functions
  else:
    raise ImportError

except:
  import klayout.db as pya
  from zeropdk import Tech
  op_tag = "script" 
  lyp_filepath = os.path(str(os.path(os.path.dirname(os.path.realpath(__file__))).parent) + r"/klayout_Layers_GSiP.lyp")
  print(lyp_filepath)

from pya import Box, Point, Polygon, Text, Trans, LayerInfo, \
    PCellDeclarationHelper, DPoint, DPath, Path, ShapeProcessor, \
    Library, CellInstArray

path = os.path.dirname(os.path.abspath(__file__))

def linspace_without_numpy(low, high, length):
    step = ((high-low) * 1.0 / length)
    return [low+i*step for i in range(length)]

def pin(w,pin_text, trans, LayerPinRecN, dbu, cell):
  """
  w: Waveguide Width, e.g., 500 (in dbu)
  pin_text: Pin Text, e.g., "pin1"
  trans: e.g., trans =  Trans(0, False, 0, 0)  - first number is 0, 1, 2, or 3.
  pinrec: PinRec Layer, e.g., layout.layer(TECHNOLOGY['PinRec']))
  devrec: DevRec Layer, e.g., layout.layer(TECHNOLOGY['DevRec']))
  """
  
  # Create the pin, as short paths:
  from SiEPIC._globals import PIN_LENGTH

  pin = trans*Path([Point(-PIN_LENGTH/2, 0), Point(PIN_LENGTH/2, 0)], w)
  cell.shapes(LayerPinRecN).insert(pin)
  text = Text (pin_text, trans)
  shape = cell.shapes(LayerPinRecN).insert(text)
  shape.text_size = w*0.8

  print("Done drawing the layout for - pin" )
