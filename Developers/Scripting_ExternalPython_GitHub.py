
# Code snipets to help with development of PCells and Scripted Layout

# SiEPIC - can be loaded from PyPI or in KLayout Application, or loaded from a local folder such as GitHub
import os, sys
path_GitHub = os.path.expanduser('~/Documents/GitHub/')
if os.path.exists(path_GitHub):
    path_siepic = os.path.join(path_GitHub, 'SiEPIC-Tools/klayout_dot_config/python')
    if not path_siepic in sys.path:
        sys.path.insert(0,path_siepic)  # put SiEPIC at the beginning so that it is overrides the system-installed module
import SiEPIC

