"""
    dispersion_analysis.py
    Contra-directional coupler Lumerical simulation flow
    see [] for documentation

    Author: Mustafa Hammood   ; mustafa@siepic.com   ; mustafa@ece.ubc.ca
    SiEPIC Kits Ltd. 2019     ; University of British Columbia
            
"""
#%% import dependencies
import lumerical_tools
import numpy as np

#%% phase matching analysis        
def phaseMatch_analysis(contraDC, simulation_setup, plot = False):
    [neff_data, lambda_fit, ng_contra, ng1, ng2, lambda_self1, lambda_self2] = lumerical_tools.run_mode( contraDC, simulation_setup)

    neff1_fit = np.polyfit(lambda_fit[:,0], neff_data[:,0],1)
    neff2_fit = np.polyfit(lambda_fit[:,0], neff_data[:,1],1)

    neff1 = np.polyval(neff1_fit, lambda_fit)
    neff2 = np.polyval(neff2_fit, lambda_fit)
    neff_avg = (neff1+neff2)/2
    phaseMatch = lambda_fit/(2*contraDC.period)

    # find contra-directional coupling wavelength
    tol = 1e-3
    phaseMatchindex = np.where(abs(phaseMatch-neff_avg)<tol); phaseMatchindex=phaseMatchindex[0]
    phaseMatchindex = phaseMatchindex[int(phaseMatchindex.size/2)]
    lambda_phaseMatch = lambda_fit[phaseMatchindex]
    simulation_setup.central_lambda = lambda_phaseMatch

    # average effective indices at phase match
    neff1_phaseMatch = neff1[phaseMatchindex]
    neff1_dispersion = neff1_fit[0]
    neff2_phaseMatch = neff2[phaseMatchindex]
    neff2_dispersion = neff2_fit[0]

    #%% plot phase match (optional)
    if plot == True:
        import matplotlib.pyplot as plt
        plt.figure()
        plt.plot(lambda_fit*1e9, phaseMatch, '-.', label='Phase matching condition')
        plt.plot(lambda_fit*1e9, neff1, label='Waveguide 1 effective index')
        plt.plot(lambda_fit*1e9, neff2, label='Waveguide 2 effective index')
        plt.plot(lambda_fit*1e9, neff_avg, linewidth=4,label='Average waveguides effective index')
        plt.axvline(x=lambda_phaseMatch*1e9, linestyle=':',label='Contra-directional coupling wavelength')
        plt.legend()
        plt.ylabel('Effective Index')
        plt.xlabel('Wavelength (nm)')
    
    waveguide_params = [neff1_phaseMatch[0], neff1_dispersion, neff2_phaseMatch[0], neff2_dispersion, ng_contra, ng1, ng2, lambda_self1, lambda_self2]
    
    return [waveguide_params, simulation_setup]

#%% coupling coefficient (kappa) analysis        `
def get_kappa(delta_lambda, lambda0, ng):
    kappa = np.pi*ng*delta_lambda/(lambda0**2)
    return kappa

def kappa_analysis(contraDC, simulation_setup, waveguides, sim_type = 'FDTD', close = True):
    
    ng_contra = waveguides[4]
    ng1 = waveguides[5]
    ng2 = waveguides[6]
    lambda_self1 = waveguides[7]
    lambda_self2 = waveguides[8]
        
    if sim_type == 'FDTD':
        [delta_lambda_contra, delta_lambda_self1, delta_lambda_self2, lambda_contra] = lumerical_tools.run_FDTD(contraDC, simulation_setup, close)
        
    else:
        [delta_lambda_contra, delta_lambda_self1, delta_lambda_self2, lambda_contra] = lumerical_tools.run_EME(contraDC, simulation_setup, close)
        
    contraDC.kappa_contra = get_kappa(delta_lambda_contra, lambda_contra, ng_contra)
    contraDC.kappa_self1 = get_kappa(delta_lambda_self1, lambda_self1, ng1)/10
    contraDC.kappa_self2 = get_kappa(delta_lambda_self2, lambda_self2, ng2)/10     
    return contraDC