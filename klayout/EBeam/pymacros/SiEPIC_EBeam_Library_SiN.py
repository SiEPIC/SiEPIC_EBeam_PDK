"""
This file is part of the SiEPIC_EBeam_PDK
by Lukas Chrostowski, et al., (c) 2023

This file implements a library called "EBeam-SiN", for silicon nitride


Version history:

Lukas Chrostowski, 2023/01/24
 - Creation of a new library for Silicon Nitride devices
 - directional coupler PCell for 895 nm
 - Added SiN waveguide to WAVEGUIDES.XML

Lukas Chrostowski, 2023/11
 - components for 1550 and 1310
 - waveguides for 1550 and 1310
 - compound waveguide
 - compatibility with PyPI usage of KLayout

"""

verbose = False

if verbose:
    print("siepic_ebeam_library_SiN")

from pya import *
import os
import pathlib
import sys

dir_path = os.path.dirname(os.path.realpath(__file__))
if dir_path not in sys.path:
    sys.path.append(dir_path)

files = [
    f
    for f in os.listdir(
        os.path.join(os.path.dirname(os.path.realpath(__file__)), "pcells_SiN")
    )
    if ".py" in pathlib.Path(f).suffixes and "__init__" not in f
]
import pcells_SiN  ### folder name ###
import importlib

importlib.invalidate_caches()
pcells_ = []
for f in files:
    module = "pcells_SiN.%s" % f.replace(".py", "")  ### folder name ###
    if verbose:
        print(" - found module: %s" % module)
    m = importlib.import_module(module)
    if verbose:
        print(m)
    pcells_.append(importlib.reload(m))


class siepic_ebeam_library_hubbard(Library):
    """
    The library where we will put the PCells and GDS into
    """

    def __init__(self):
        tech_name = "EBeam"
        library = tech_name + "-SiN"
        self.technology = tech_name

        # Set the description
        self.description = "v0.4.22, Silicon Nitride"

        if verbose:
            print("Initializing '%s' Library, %s" % (library, self.description))

        # Save the path, used for loading WAVEGUIDES.XML
        import os

        self.path = os.path.dirname(os.path.realpath(__file__))

        # Import all the GDS files from the tech folder
        import os
        import fnmatch

        dir_path = os.path.normpath(
            os.path.join(
                os.path.dirname(os.path.realpath(__file__)), "../gds/EBeam_SiN"
            )
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
        for m in pcells_:
            mm = m.__name__.replace("pcells_SiN.", "")
            mm2 = m.__name__ + "." + mm + "()"
            if verbose:
                print(" - register_pcell %s, %s" % (mm, mm2))
            self.layout().register_pcell(mm, eval(mm2))
        if verbose:
            print(" done with pcells")

        # Register us the library with the technology name
        # If a library with that name already existed, it will be replaced then.
        self.register(library)


# Instantiate and register the library
siepic_ebeam_library_hubbard()
