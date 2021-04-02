import os, sys
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
  lyp_filepath = os.path(str(os.path(os.path.dirname(os.path.realpath(__file__))).parent) + r"/EBeam.lyp")
  print(lyp_filepath)

