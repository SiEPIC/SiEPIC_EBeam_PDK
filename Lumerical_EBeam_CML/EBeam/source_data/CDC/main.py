"""
    Contra-directional coupler Lumerical simulation flow
    see URL for documentation
    https://github.com/SiEPIC-Kits/SiEPIC_Photonics_Package/tree/master/SiEPIC_Photonics_Package/solvers_simulators/contraDC/Documentation

"""
# command line usage:
# python3 main.py PCell_parameters.xml 0
# where 
#   - PCell_parameters.xml = path to the XML file containing PCell parameters
#   - 0 = index number within the XML; can have multiple cells in one XML file

import dispersion_analysis, contraDC_CMT_TMM, analysis

#%% device parameters class constructor
class contra_DC():
    def __init__(self, *args):
        
        # for XML import
        import sys
        from xml.etree import cElementTree as ET

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
        
        # can pass an XML file with these parameters, as an argument to python on the command line
        if(len(sys.argv)>2):
            filepath = sys.argv[1]
            with open(filepath, 'r') as file:
                d = etree_to_dict(ET.XML(file.read()))
            print('Found %s PCells'%len(d['PCells']['PCell']))
            for PCell_params in d['PCells']['PCell']:
                print(PCell_params)
                if PCell_params['Name'] == 'Contra-Directional Coupler' and PCell_params['ID'] == sys.argv[2]:
                    print('CDC, gap=%s'%PCell_params['gap'])
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
        self.resolution = 501
        
        self.deviceTemp = 300
        self.chipTemp = 300
        
        self.chirp = True
        
        self.central_lambda = 1550e-9

#%% instantiate the class constructors        
device = contra_DC()
simulation = simulation()

#%% main program
[waveguides, simulation] = dispersion_analysis.phaseMatch_analysis(device, simulation)
device = dispersion_analysis.kappa_analysis(device, simulation, waveguides, sim_type = 'EME', close = False)
device = contraDC_CMT_TMM.contraDC_model(device, simulation, waveguides)

#%% analysis and export parameters
analysis.plot_all(device, simulation)
S = analysis.gen_sparams(device, simulation)
analysis.performance(S)