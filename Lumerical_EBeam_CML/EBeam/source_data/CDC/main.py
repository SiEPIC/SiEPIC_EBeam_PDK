"""
    Contra-directional coupler Lumerical simulation flow
    see URL for documentation
    https://github.com/SiEPIC-Kits/SiEPIC_Photonics_Package/tree/master/SiEPIC_Photonics_Package/solvers_simulators/contraDC/Documentation

"""
# command line usage:

# python3 main.py PCell_parameters.xml
# where 
#   - PCell_parameters.xml = path to the XML file containing PCell parameters
# will simulate all the CDC PCells variants
# 
# python3 main.py PCell_parameters.xml 0
# where 
#   - PCell_parameters.xml = path to the XML file containing PCell parameters
#   - 0 = Variable 'ID' in the XML file. which component to simulate; can have multiple cells in one XML filepath. 
#
# python3 main.py 
#  will simulate with the default parameters 

# required Python modules:
# pip3 install numpy scipy matplotlib


# XML to Dict parser, from:
# https://stackoverflow.com/questions/2148119/how-to-convert-an-xml-string-to-a-dictionary-in-python/10077069
def etree_to_dict(t):
    from collections import defaultdict
    d = {t.tag: {} if t.attrib else None}
    children = list(t)
    if children:
        dd = defaultdict(list)
        for dc in map(etree_to_dict, children):
            for k, v in dc.items():
                dd[k].append(v)
        d = {t.tag: {k: v[0] if len(v) == 1 else v for k, v in dd.items()}}
    if t.attrib:
        d[t.tag].update(('@' + k, v) for k, v in t.attrib.items())
    if t.text:
        text = t.text.strip()
        if children or t.attrib:
            if text:
                d[t.tag]['#text'] = text
        else:
            d[t.tag] = text
    return d


#%% device parameters class constructor
class contra_DC():
    def __init__(self, *args):
        
        # physical geometry parameters
        self.w1 = 560e-9
        self.w2 = 440e-9
        self.dW1 = 40e-9
        self.dW2 = 20e-9
        self.gap = 150e-9
        self.period = 318e-9
        self.N = 1000

        self.thick_si = 220e-9
    
        self.slab = False
        self.thick_slab = 90e-9
    
        self.sinusoidal = False
    
        self.apodization = 2

        #behavioral parameters 
        self.pol = 'TE' # TE or TM
        self.alpha = 10
    
        #leave kappas as default if you wish the script to calculate it based on bandstructure
        self.kappa_contra = 30000 
        self.kappa_self1 = 2000
        self.kappa_self2 = 2000        

    def set_params(self, PCells_params, ID):
        
        # find the component 'ID' in the PCells_params dict
        for PCell_params in PCells_params:
            if PCell_params['Name'] == 'Contra-Directional Coupler' and PCell_params['ID'] == ID:
                print(PCell_params)
                self.w1 = float(PCell_params['wg1_width'])*1e-6
                self.w2 = float(PCell_params['wg2_width'])*1e-6
                self.dW1 = float(PCell_params['corrugation_width1'])*1e-6
                self.dW2 = float(PCell_params['corrugation_width2'])*1e-6
                self.gap = float(PCell_params['gap'])*1e-6
                self.period = float(PCell_params['grating_period'])*1e-6
                self.N = int(PCell_params['number_of_periods'])
                self.sinusoidal = bool(PCell_params['sinusoidal'])
                self.apodization = float(PCell_params['index'])

    def results(self, *args):
        self.E_thru = 0
        self.E_drop = 0
        self.wavelength = 0
        self.TransferMatrix = 0

#%% simulation parameters class constructor
class simulation():
    def __init__(self, *args):
        # make sure range is large enouh to capture all Bragg coupling conditions (both self-Bragg and contra-coupling)
        self.lambda_start = 1500e-9
        self.lambda_end = 1600e-9
#        self.resolution = 501
        self.resolution = 51
        
        self.deviceTemp = 300
        self.chipTemp = 300
        
        self.chirp = True
        
        self.central_lambda = 1550e-9



import xmltodict, sys
from collections import OrderedDict

# for XML import
import sys
from xml.etree import cElementTree as ET


#%% instantiate the class constructors        
device = contra_DC()
simulation = simulation()

# load the XML file, add an entry for the current parameters, save
def update_xml (device, simulation, sfile):
    import os
    
    # Load the XML file into an OrderedDict
    dir_path = os.path.dirname(os.path.realpath(__file__))
    filepath = os.path.join(dir_path,'CDC.xml')
    print('Loading component simulation database XML file: %s' % filepath)
    with open(filepath, 'r') as file:
        mydict = xmltodict.parse(file.read())
    if ( type(mydict['lumerical_lookup_table']['association'])==OrderedDict):
        print('Error: please ensure that the XML has 2 or more <association> entries.')
        exit()
                
    # Add an entry to the OrderedDict, in the Lumerical format
    mydict_add = OrderedDict([('design', OrderedDict([('value', [
        OrderedDict([('@name', 'wg1_width'), ('@type', 'double'), ('#text', str(device.w1))]), 
        OrderedDict([('@name', 'wg2_width'), ('@type', 'double'), ('#text', str(device.w2))]), 
        OrderedDict([('@name', 'corrugation_width1'), ('@type', 'double'), ('#text', str(device.dW1))]), 
        OrderedDict([('@name', 'corrugation_width2'), ('@type', 'double'), ('#text', str(device.dW2))]), 
        OrderedDict([('@name', 'gap'), ('@type', 'double'), ('#text', str(device.gap))]), 
        OrderedDict([('@name', 'grating_period'), ('@type', 'double'), ('#text', str(device.period))]), 
        OrderedDict([('@name', 'number_of_periods'), ('@type', 'int'), ('#text', str(device.N))]), 
        OrderedDict([('@name', 'sinusoidal'), ('@type', 'double'), ('#text', str(device.sinusoidal))]), 
        OrderedDict([('@name', 'index'), ('@type', 'double'), ('#text', str(device.apodization))]), 
        OrderedDict([('@name', 'lambda_start'), ('@type', 'double'), ('#text', str(simulation.lambda_start))]), 
        OrderedDict([('@name', 'lambda_end'), ('@type', 'double'), ('#text', str(simulation.lambda_end))]), 
        OrderedDict([('@name', 'resolution'), ('@type', 'double'), ('#text', str(simulation.resolution))])])])), 
        ('extracted', OrderedDict([('value', 
        OrderedDict([('@name', 'sparam'), ('@type', 'string'), ('#text', sfile)]))]))])
    mydict['lumerical_lookup_table']['association'].append ( mydict_add )
    
    # Convert the OrderedDict into XML
    xml_out = xmltodict.unparse(mydict, pretty=True)

    # Write the XML to a file
    f = open(filepath, "w")
    f.write(xml_out)
    f.close()
    print('Saved component simulation database XML file: %s' % filepath)

def sfilename(device,simulation):
    return 'w1=%s,w2=%s,dW1=%s,dW2=%s,gap=%s,p=%s,N=%s,s=%s,a=%s,l1=%s,l2=%s,ln=%s.dat' % (
        int(device.w1*1e6), int(device.w2*1e6), int(device.dW1*1e6), int(device.dW2*1e6), 
        int(device.gap*1e6), int(device.period*1e6), device.N, int(device.sinusoidal), 
        str(device.apodization), int(simulation.lambda_start*1e6), int(simulation.lambda_end*1e6), int(simulation.resolution), 
        )    

#%% load parameters from XML files
# can pass an XML file with these parameters, as an argument to python on the command line
PCells_params=[]
if(len(sys.argv)>1):
    filepath = sys.argv[1]
    print('Loading XML file: %s' % filepath)
    with open(filepath, 'r') as file:
        d=etree_to_dict(ET.XML(file.read()))['PCells']
#        print(len(d))
#        print(d)
        if type(d['PCell'])==list:
            PCells_params = d['PCell']
        elif len(d)==1:
            PCells_params = [d['PCell']]
        else:
            print('Error: problem with XML file')
            exit()

    IDs = []
    if(len(sys.argv)>2):  # argument is one component to simulate; otherwise simulate all of them.
        IDs = [sys.argv[2]]
    else:
        for PCell_params in PCells_params:
#            print(PCell_params)
            if PCell_params['Name'] == 'Contra-Directional Coupler':
                IDs.append(PCell_params['ID'])
else:
    IDs = [0]

import dispersion_analysis
import analysis
import contraDC_CMT_TMM

for ID in IDs:
    # load parameters from XML
    device.set_params(PCells_params, ID)
    
    #%% main program
    [waveguides, simulation] = dispersion_analysis.phaseMatch_analysis(device, simulation)
    device = dispersion_analysis.kappa_analysis(device, simulation, waveguides, sim_type = 'EME', close = False)
    device = contraDC_CMT_TMM.contraDC_model(device, simulation, waveguides)
    
    #%% analysis and export parameters
    analysis.plot_all(device, simulation)
    sfile = sfilename(device,simulation)
    S = analysis.gen_sparams(device, simulation, sfile)
    print('Saved sparameter file: %s' % sfile)
    update_xml (device, simulation, sfile)
    analysis.performance(S)
    
    