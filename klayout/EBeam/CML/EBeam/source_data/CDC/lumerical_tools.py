"""
    lumerical_tools.py
    Contra-directional coupler Lumerical simulation flow
    see [] for documentation

    Author: Mustafa Hammood   ; mustafa@siepic.com   ; mustafa@ece.ubc.ca
    SiEPIC Kits Ltd. 2019     ; University of British Columbia
            
"""


#%% find lumapi 
import sys, os, platform

mode = None # variable for the Lumerical Python API

# Lumerical Python API path on system

cwd = os.getcwd()

if platform.system() == 'Darwin':
    path_app = '/Applications'
elif platform.system() == 'Linux':
    path_app = '/opt'
elif platform.system() == 'Windows': 
    path_app = 'C:\\Program Files'
else:
    print('Not a supported OS')
    exit()


# Application folder paths containing Lumerical
p = [s for s in os.listdir(path_app) if "Lumerical" in s]
# check sub-folders for lumapi.py
import fnmatch
for dir_path in p:
    search_str = 'lumapi.py'
    matches = []
    for root, dirnames, filenames in os.walk(os.path.join(path_app,dir_path), followlinks=True):
        for filename in fnmatch.filter(filenames, search_str):
            matches.append(root)
    if matches:
        lumapi_path = matches[0]
if not lumapi_path in sys.path:
    sys.path.append(lumapi_path)
#    os.chdir(lumapi_path)

print('Lumerical lumapi.py path: %s' % lumapi_path)

import lumapi

dir_path = os.path.dirname(os.path.realpath(__file__))
print('Simulation project path: %s' % dir_path)


#%% run MODE for dispersion analysis
def run_mode(contraDC, simulation_setup, close = False):
    global mode
    if not(mode):
        mode = lumapi.open('mode')
    
    # feed parameters into model
    command = "gap = %s; width_1 = %s; width_2 = %s; thick_Si = %s; period = %s;" 
    lumapi.evalScript(mode, command
                      % (contraDC.gap, contraDC.w1, contraDC.w2, contraDC.thick_si, contraDC.period))
    
    command = "wavelength = %s; wavelength_stop = %s;" 
    lumapi.evalScript(mode,"wavelength = %s; wavelength_stop = %s;"
                      % (simulation_setup.lambda_start, simulation_setup.lambda_end))
    
    if contraDC.pol == 'TE':
        lumapi.evalScript(mode,"pol = 'TE';")
    elif contraDC.pol == 'TM':
        lumapi.evalScript(mode,"pol = 'TM';")
 
    if contraDC.slab == True:
        lumapi.evalScript(mode,"slab = 1;")
        lumapi.evalScript(mode,"thick_Slab = %s;" % (contraDC.thick_slab))
    else:
        lumapi.evalScript(mode,"slab = 0;")
        lumapi.evalScript(mode,"thick_Slab = 0;")

    # run dispersion analysis script
    lumapi.evalScript(mode,"cd('%s');"%dir_path)
    lumapi.evalScript(mode,'dispersion_2WG;')
    
    # contra-directional coupling
    neff_data = lumapi.getVar(mode, 'n_eff_data')
    lambda_fit = lumapi.getVar(mode, 'lambda_fit')
    ng_contra = lumapi.getVar(mode, 'ng0')
    
    # self-coupling
    ng1 = lumapi.getVar(mode, 'ng0_self1')
    ng2 = lumapi.getVar(mode, 'ng0_self2')
    lambda_self1 = lumapi.getVar(mode, 'self1_lambda')
    lambda_self2 = lumapi.getVar(mode, 'self2_lambda')
    
    if close == True:
        lumapi.close(mode)
    
    return [neff_data, lambda_fit, ng_contra, ng1, ng2, lambda_self1, lambda_self2]

#%% run MODE for EME simulation of device
def run_EME(contraDC, simulation_setup, close = False):
    global mode
    if not(mode):
        mode = lumapi.open('mode')
    
    projectname = 'ContraDC_EME'
    filename = 'ContraDC_EMEscript'
    
    command ='cd("%s");'%dir_path
    command += 'min_wavelength=%s;'%simulation_setup.lambda_start
    command += 'max_wavelength=%s;'%simulation_setup.lambda_end
    command += 'ACCURATE=%s;'%int(simulation_setup.accuracy)
    command += 'grating_period=%s;'%contraDC.period
    command += 'Wa=%s;'%contraDC.w1
    command += 'Wb=%s;'%contraDC.w2
    command += 'dWa=%s;'%contraDC.dW1
    command += 'dWb=%s;'%contraDC.dW2
    command += 'gap=%s;'%contraDC.gap
    command += 'number_of_periods=%s;'%contraDC.N
    
    command += 'wl_ref = %s;'%simulation_setup.central_lambda
    
    if contraDC.pol == 'TE':
        command += "pol='TE';"
    else:
        command += "pol='TM';"
        
    command += "load('%s');"%projectname
    command += '%s;'%filename
   
    print(command)
    lumapi.evalScript(mode, command)
    
    delta_lambda_contra = lumapi.getVar(mode,"delta_lambda")
    lambda_contra = lumapi.getVar(mode,"lambda0")
    
    delta_lambda_self1 = lumapi.getVar(mode,"delta_lambda_self1")
    delta_lambda_self2 = lumapi.getVar(mode,"delta_lambda_self2")
    
    # return the MODE project file to its small size
    command ='switchtolayout; save;'
    # select('EME::Ports::port_1'); cleardataset; select('EME::Ports::port_2'); cleardataset; 
    lumapi.evalScript(mode, command)
    
    if close == True:
        lumapi.close(mode)

    return [delta_lambda_contra, delta_lambda_self1, delta_lambda_self2, lambda_contra]

#%% run FDTD for bandstructure simulation of device
def run_FDTD(contraDC, simulation_setup, close = False):
    c = 299792458           #[m/s]
    frequency_start = c/simulation_setup.lambda_end
    frequency_end = c/simulation_setup.lambda_start
    
    fdtd = lumapi.open('fdtd')#,hide=True)
    filename = 'contraDC_bandstructure'
        
    lumapi.evalScript(fdtd,"load('%s'); setnamed('::model','gap',%s); setnamed('::model','ax',%s); setnamed('::model','sinusoidal',%s)" 
                      % (filename, contraDC.gap,  contraDC.period, contraDC.sinusoidal))
    
    if contraDC.slab == True:
        lumapi.evalScript(fdtd,"setnamed('::model','slab',1); setnamed('::model','slab_thickness',%s);" % (contraDC.thick_slab))
    
    if contraDC.sinusoidal == True:
        lumapi.evalScript(fdtd,"setnamed('::mode','sinusoidal',1);")
        
    lumapi.evalScript(fdtd,"setnamed('::model','bus1_width',%s); setnamed('::model','bus1_delta',%s); setnamed('::model','bus2_width',%s); setnamed('::model','bus2_delta',%s);setnamed('::model','si_thickness',%s);"
                      % (contraDC.w1, contraDC.dW1, contraDC.w2, contraDC.dW2, contraDC.thick_si))
    
    lumapi.evalScript(fdtd,"setnamed('::model','f1',%s); setnamed('::model','f2',%s);"
                      % (frequency_start, frequency_end))
    lumapi.evalScript(fdtd,"cd('%s');"%dir_path)
    lumapi.evalScript(fdtd,'kappa_bandstructure;')

    delta_lambda_contra = lumapi.getVar(fdtd,"delta_lambda")
    lambda_contra = lumapi.getVar(fdtd,"lambda0")
    
    delta_lambda_self1 = lumapi.getVar(fdtd,"delta_lambda_self1")
    delta_lambda_self2 = lumapi.getVar(fdtd,"delta_lambda_self2")
    
    if close == True:    
        lumapi.close(fdtd)
    
    return [delta_lambda_contra, delta_lambda_self1, delta_lambda_self2, lambda_contra]

#%% run MODE to generate S-parameters .dat file
def generate_dat( contraDC, simulation_setup, S_Matrix, sfile, close = False ):
    global mode
    if not(mode):
        mode = lumapi.open('mode')
    
    # feed polarization into model
    if contraDC.pol == 'TE':
        lumapi.evalScript(mode,"mode_label = 'TE'; mode_ID = '1';")
    elif contraDC.pol == 'TM':
        lumapi.evalScript(mode,"mode_label = 'TM'; mode_ID = '2';")
        
    # run write sparams script
    lumapi.evalScript(mode,"cd('%s'); sfile = '%s'; " % (dir_path, sfile) )
    lumapi.evalScript(mode,'write_sparams;')
    
    if close == True:
        lumapi.close(mode)
    
#    run_INTC()
    return

#%% run INTERCONNECT with compact model loaded
def run_INTC(close = False):
    intc = lumapi.open('interconnect')
    
    print(dir_path)
    svg_file = "contraDC.svg"
    sparam_file = "ContraDC_sparams.dat"
    command ='cd("%s");'%dir_path
    command += 'switchtodesign; new; deleteall; \n'
    command +='addelement("Optical N Port S-Parameter"); createcompound; select("COMPOUND_1");\n'
    command += 'component = "contraDC"; set("name",component); \n' 
    command += 'seticon(component,"%s");\n' %(svg_file)
    command += 'select(component+"::SPAR_1"); set("load from file", true);\n'
    command += 'set("s parameters filename", "%s");\n' % (sparam_file)
    command += 'set("load from file", false);\n'
    command += 'set("passivity", "enforce");\n'
    
    command += 'addport(component, "%s", "Bidirectional", "Optical Signal", "%s",%s);\n' %("Port 1",'Left',0.25)
    command += 'connect(component+"::RELAY_%s", "port", component+"::SPAR_1", "port %s");\n' % (1, 1)
    command += 'addport(component, "%s", "Bidirectional", "Optical Signal", "%s",%s);\n' %("Port 2",'Left',0.75)
    command += 'connect(component+"::RELAY_%s", "port", component+"::SPAR_1", "port %s");\n' % (2, 2)
    command += 'addport(component, "%s", "Bidirectional", "Optical Signal", "%s",%s);\n' %("Port 3",'Right',0.25)
    command += 'connect(component+"::RELAY_%s", "port", component+"::SPAR_1", "port %s");\n' % (3, 3)
    command += 'addport(component, "%s", "Bidirectional", "Optical Signal", "%s",%s);\n' %("Port 4",'Right',0.75)
    command += 'connect(component+"::RELAY_%s", "port", component+"::SPAR_1", "port %s");\n' % (4, 4)
    command += 'save("CDC");\n'
    
    print('INTERCONNECT: save CDC')
    
    lumapi.evalScript(intc, command)

    if close == True:
        command = 'exit(2);\n'
        lumapi.evalScript(intc, command)
        lumapi.close(intc)
        
    
    return