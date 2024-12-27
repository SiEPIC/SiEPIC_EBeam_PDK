# $autorun

version = "0.4.30"

print('SiEPIC-EBeam-PDK Python module: pymacros, v%s' % version)

from SiEPIC.scripts import load_klayout_library

verbose=False

tech='EBeam'

# Load the library
load_klayout_library(tech, 'EBeam', "v%s, Components with models" % version, 'gds/EBeam','pymacros/pcells_EBeam', 
    verbose=verbose)
load_klayout_library(tech, 'EBeam_Beta', "v%s, Beta components" % version, 'gds/EBeam_Beta','pymacros/pcells_EBeam_Beta', verbose=verbose)
load_klayout_library(tech, 'EBeam-Dream', "v%s, Dream Photonics" % version, 'gds/EBeam_Dream','pymacros/pcells_EBeam_Dream', verbose=verbose)
load_klayout_library(tech, 'EBeam-SiN', "v%s, Silicon Nitride" % version, 'gds/EBeam_SiN','pymacros/pcells_SiN', verbose=verbose)
load_klayout_library(tech, 'EBeam-ANT', "v%s, ANT components" % version, 'gds/ANT','', verbose=verbose)


