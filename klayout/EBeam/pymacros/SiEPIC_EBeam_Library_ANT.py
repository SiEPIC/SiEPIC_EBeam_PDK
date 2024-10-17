"""
This file is part of the SiEPIC_EBeam_PDK
by Lukas Chrostowski, et al., (c) 2015-2023

This file implements a library called "EBeam-ANT", consisting of components that are biased to work the best with ANT process.
"""

verbose = False
if verbose:
    print("SiEPIC_EBeam_Library_ANT")

from pya import *
import os
import sys

dir_path = os.path.dirname(os.path.realpath(__file__))
if dir_path not in sys.path:
    sys.path.append(dir_path)

# files = [f for f in os.listdir(os.path.join(os.path.dirname(os.path.realpath(__file__)),'pcells_EBeam_ANT')) if '.py' in pathlib.Path(f).suffixes  and '__init__' not in f]
# import pcells_EBeam_ANT ### folder name ###
# import importlib
# importlib.invalidate_caches()
# pcells_=[]
# for f in files:
#    module = 'pcells_EBeam_ANT.%s' % f.replace('.py','')  ### folder name ###
#    print(' - found module: %s' % module)
#    m = importlib.import_module(module)
#    print(m)
#    pcells_.append(importlib.reload(m))


class SiEPIC_EBeam_Library_ANT(Library):
    """
    The library where we will put the PCells and GDS into
    """

    def __init__(self):
        tech_name = "EBeam"
        library = tech_name + "-ANT"
        self.technology = tech_name

        if verbose:
            print("Initializing '%s' Library." % library)

        # Set the description
        self.description = "v0.4.22, ANT components"

        # Save the path, used for loading WAVEGUIDES.XML
        import os

        self.path = os.path.dirname(os.path.realpath(__file__))

        # Import all the GDS files from the tech folder
        import os
        import fnmatch

        dir_path = os.path.normpath(
            os.path.join(os.path.dirname(os.path.realpath(__file__)), "../gds/ANT")
        )
        if verbose:
            print("  library path: %s" % dir_path)
        search_str = "*.[Oo][Aa][Ss]"  # OAS
        for root, dirnames, filenames in os.walk(dir_path, followlinks=True):
            for filename in fnmatch.filter(filenames, search_str):
                file1 = os.path.join(root, filename)
                if verbose:
                    print(" - reading %s" % file1)
                self.layout().read(file1)
        search_str = "*.[Gg][Dd][Ss]"  # GDS
        for root, dirnames, filenames in os.walk(dir_path, followlinks=True):
            for filename in fnmatch.filter(filenames, search_str):
                file1 = os.path.join(root, filename)
                if verbose:
                    print(" - reading %s" % file1)
                self.layout().read(file1)

        # Create the PCell declarations
        # for m in pcells_:
        #   mm = m.__name__.replace('pcells_EBeam_Beta.','')
        #  mm2 = m.__name__+'.'+mm+'()'
        # print(' - register_pcell %s, %s' % (mm,mm2))
        # self.layout().register_pcell(mm, eval(mm2))

        if verbose:
            print(" done with pcells")

        # Register us the library with the technology name
        # If a library with that name already existed, it will be replaced then.
        self.register(library)


# Instantiate and register the library
SiEPIC_EBeam_Library_ANT()
