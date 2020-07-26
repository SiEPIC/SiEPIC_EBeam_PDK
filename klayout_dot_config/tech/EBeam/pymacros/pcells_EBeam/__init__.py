import os, sys
from pathlib import Path
import SiEPIC
try: 
  import siepic_tools
except:
  pass

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
  lyp_filepath = Path(str(Path(os.path.dirname(os.path.realpath(__file__))).parent) + r"/klayout_Layers_GSiP.lyp")
  print(lyp_filepath)

from pya import Box, Point, Polygon, Text, Trans, LayerInfo, \
    PCellDeclarationHelper, DPoint, DPath, Path, ShapeProcessor, \
    Library, CellInstArray

path = os.path.dirname(os.path.abspath(__file__))

# import all pcells in the directory
for py in [f[:-3] for f in os.listdir(path) if f.endswith('.py') and f != '__init__.py']:
  mod = __import__('.'.join([__name__, py]), fromlist=[py])
  classes = [getattr(mod, x) for x in dir(mod) if isinstance(getattr(mod, x), type)]
  for cls in classes:
      setattr(sys.modules[__name__], cls.__name__, cls)

      