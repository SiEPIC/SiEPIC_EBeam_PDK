"""
    analysis.py
    Contra-directional coupler Lumerical simulation flow
    see [] for documentation

    Author: Mustafa Hammood   ; mustafa@siepic.com   ; mustafa@ece.ubc.ca
    SiEPIC Kits Ltd. 2019     ; University of British Columbia
            
"""
#%% import dependencies
import numpy as np
import scipy.io as sio
import lumerical_tools

#%% run all plots
def plot_all( contraDC, simulation):
    amplitude(contraDC, simulation)
    phase(contraDC, simulation)
    group_delay(contraDC, simulation)
    
    return

#%% plot amplitude response (log scale)
def amplitude( contraDC, simulation, plot = False):
    
    thruAmplitude = 10*np.log10(np.abs(contraDC.E_Thru[0,:])**2)
    dropAmplitude = 10*np.log10(np.abs(contraDC.E_Drop[0,:])**2)
    
    if plot == True:
        import matplotlib.pyplot as plt
        plt.figure()
        plt.plot(contraDC.wavelength[:]*1e9, thruAmplitude, label='Through Port')
        plt.plot(contraDC.wavelength[:]*1e9, dropAmplitude, label='Drop Port')
        plt.legend()
        plt.ylabel('Response (dB)')
        plt.xlabel('Wavelength (nm)')

    return [thruAmplitude, dropAmplitude]

#%% plot phase response
def phase( contraDC, simulation, plot = False):
    thruPhase = np.unwrap(np.angle(contraDC.E_Thru))
    dropPhase = np.unwrap(np.angle(contraDC.E_Drop))
    
    if plot == True:
        import matplotlib.pyplot as plt
        plt.figure()
        plt.plot(contraDC.wavelength[:]*1e9, thruPhase[0,:], label='Through Port Phase')
        plt.plot(contraDC.wavelength[:]*1e9, dropPhase[0,:], label='Drop Port Phase')
        plt.legend()
        plt.ylabel('Phase')
        plt.xlabel('Wavelength (nm)')
        
    return [thruPhase, dropPhase]

#%% plot group delay response
def group_delay( contraDC, simulation, plot = True):
    [thruPhase, dropPhase] = phase(contraDC, simulation, False)
    
    c = 299792458           #[m/s]
    frequency = c / contraDC.wavelength
    omega = frequency*2*np.pi
    
    dropGroupDelay = -np.diff(dropPhase)/np.diff(omega)
    thruGroupDelay = -np.diff(thruPhase)/np.diff(omega)
    
    if plot == False:
        import matplotlib.pyplot as plt
        plt.figure()
        plt.plot(contraDC.wavelength[:-1]*1e9, 1e12*thruGroupDelay[0,:], label='Through Port Group Delay')
        plt.plot(contraDC.wavelength[:-1]*1e9, 1e12*dropGroupDelay[0,:], label='Drop Port Group Delay')
        plt.legend()
        plt.ylabel('Group Delay (ps)')
        plt.xlabel('Wavelength (nm)')
        
    return [thruGroupDelay, dropGroupDelay]

#%% bandwidth analysis
# find nearest index to value in a numpy array
def find_nearest(array, value):
    array = np.asarray(array)
    idx = (np.abs(array - value)).argmin()
    return idx

# find bandwidth of a given response
def bandwidth( response, wavelength, limit):
    
    center_index = find_nearest( response, max(response))
    isInBand = response>max(response) - limit

    leftBound = center_index

    while isInBand[leftBound] == 1:
        leftBound = leftBound-1

    rightBound=center_index

    while isInBand[rightBound] == 1:
        rightBound = rightBound+1

    bandwidth = wavelength[rightBound] - wavelength[leftBound]
    
    return bandwidth

# find performance of the device
def performance( S ):
    
    try:
        #find 3 dB bandwidth of drop port
        bw_3dB = bandwidth( 10*np.log10(np.abs(S['S21'])**2), S['lambda'],  3)
        #find 20 dB bandwidth of drop port
        bw_20dB = bandwidth( 10*np.log10(np.abs(S['S21'])**2), S['lambda'],  20)
    
        print("######## Contra-DC Analysis ########")
        print("3 dB bandwidth = %s nm"%bw_3dB)
        print("20 dB bandwidth = %s nm"%bw_20dB)
    
        return [bw_3dB, bw_20dB]
    except:
        print('cannot compute the bandwidths')
        
#%% generate S-parameters
# Source: J. Frei, X.-D. Cai, and S. Muller. Multiport s-parameter and 
# T-parameter conversion with symmetry extension. IEEE Transactions on 
# Microwave Theory and Techniques, 56(11):2493?2504, 2008.

def gen_sparams( contraDC, simulation, sfile, run_INTC = True):
    import os
    T = contraDC.TransferMatrix
    lambda0 = contraDC.wavelength*1e9
    f =  299792458/lambda0
    
    span = lambda0.__len__()
    T11 = T[0][0][:span]; T11 = np.matrix.transpose(T11)
    T12 = T[0][1][:span]; T12 = np.matrix.transpose(T12)
    T13 = T[0][2][:span]; T13 = np.matrix.transpose(T13)
    T14 = T[0][3][:span]; T14 = np.matrix.transpose(T14)
    
    T21 = T[1][0][:span]; T21 = np.matrix.transpose(T21)
    T22 = T[1][1][:span]; T22 = np.matrix.transpose(T22)
    T23 = T[1][2][:span]; T23 = np.matrix.transpose(T23)
    T24 = T[1][3][:span]; T24 = np.matrix.transpose(T24)

    T31 = T[2][0][:span]; T31 = np.matrix.transpose(T31)
    T32 = T[2][1][:span]; T32 = np.matrix.transpose(T32)
    T33 = T[2][2][:span]; T33 = np.matrix.transpose(T33)
    T34 = T[2][3][:span]; T34 = np.matrix.transpose(T34)

    T41 = T[3][0][:span]; T41 = np.matrix.transpose(T41)
    T42 = T[3][1][:span]; T42 = np.matrix.transpose(T42)
    T43 = T[3][2][:span]; T43 = np.matrix.transpose(T43)
    T44 = T[3][3][:span]; T44 = np.matrix.transpose(T44)
    
    S11=(T13*T44-T14*T43)/(T33*T44-T34*T43)
    S21=(T23*T44-T24*T43)/(T33*T44-T34*T43)
    S31=(T44)/(T33*T44-T34*T43)
    S41=(-T43)/(T33*T44-T34*T43)
    
    S12=(T14*T33-T13*T34)/(T33*T44-T34*T43)
    S22=(T24*T33-T23*T34)/(T33*T44-T34*T43)
    S32=(-T34)/(T33*T44-T34*T43)
    S42=(T33)/(T33*T44-T34*T43)
    
    S13=(T11*T33*T44-T11*T34*T43-T13*T44*T31+T13*T34*T41+T14*T43*T31-T14*T33*T41)/(T33*T44-T34*T43)
    S23=(T21*T33*T44-T21*T34*T43-T23*T44*T31+T23*T34*T41+T24*T43*T31-T24*T33*T41)/(T33*T44-T34*T43)
    S33=(T34*T41-T44*T31)/(T33*T44-T34*T43)
    S43=(T43*T31-T33*T41)/(T33*T44-T34*T43)

    S14=(T12*T33*T44-T12*T34*T43-T13*T44*T32+T13*T34*T42+T14*T43*T32-T14*T33*T42)/(T33*T44-T34*T43)
    S24=(T22*T33*T44-T22*T34*T43-T23*T44*T32+T23*T34*T42+T24*T43*T32-T24*T33*T42)/(T33*T44-T34*T43)
    S34=(T34*T42-T44*T32)/(T33*T44-T34*T43)
    S44=(T43*T32-T33*T42)/(T33*T44-T34*T43)
    
    S = {}
    S['f'] = np.matrix.transpose(f)
    S['lambda'] = np.matrix.transpose(lambda0)
    
    S['S11'] = S11
    S['S21'] = S21
    S['S31'] = S31
    S['S41'] = S41

    S['S12'] = S12
    S['S22'] = S22
    S['S32'] = S32
    S['S42'] = S42
    
    S['S13'] = S13
    S['S23'] = S23
    S['S33'] = S33
    S['S43'] = S43

    S['S14'] = S14
    S['S24'] = S24
    S['S34'] = S34
    S['S44'] = np.matrix.transpose(S44)
    
    dir_path = os.path.dirname(os.path.realpath(__file__))
    sio.savemat(os.path.join(dir_path,'ContraDC_sparams.mat'), S)
    
    # create .dat file for circuit simulations
    lumerical_tools.generate_dat(contraDC, simulation, S, sfile)
    
    return S