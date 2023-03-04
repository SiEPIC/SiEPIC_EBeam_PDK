"""
    contraDC_CMT_TMM.py
    Contra-directional coupler Lumerical simulation flow
    see URL for documentation
    https://github.com/SiEPIC-Kits/SiEPIC_Photonics_Package/tree/master/SiEPIC_Photonics_Package/solvers_simulators/contraDC/Documentation

"""
#%% import dependencies
import cmath, math
import sys, os, time
import numpy as np
import scipy.linalg

#%% linear algebra numpy manipulation functions
# Takes a 4*4 matrix and switch the first 2 inputs with first 2 outputs
def switchTop( P ):
    P_FF = np.asarray([[P[0][0],P[0][1]],[P[1][0],P[1][1]]])
    P_FG = np.asarray([[P[0][2],P[0][3]],[P[1][2],P[1][3]]])
    P_GF = np.asarray([[P[2][0],P[2][1]],[P[3][0],P[3][1]]])
    P_GG = np.asarray([[P[2][2],P[2][3]],[P[3][2],P[3][3]]])
    
    H1 = P_FF-np.matmul(np.matmul(P_FG,np.linalg.matrix_power(P_GG,-1)),P_GF)
    H2 = np.matmul(P_FG,np.linalg.matrix_power(P_GG,-1))
    H3 = np.matmul(-np.linalg.matrix_power(P_GG,-1),P_GF)
    H4 = np.linalg.matrix_power(P_GG,-1)
    H = np.vstack((np.hstack((H1,H2)),np.hstack((H3,H4))))
    
    return H

# Swap columns of a given array
def swap_cols(arr, frm, to):
    arr[:,[frm, to]] = arr[:,[to, frm]]
    return arr

# Swap rows of a given array
def swap_rows(arr, frm, to):
    arr[[frm, to],:] = arr[[to, frm],:]
    return arr
    
#%% the bread and butter
def contraDC_model(contraDC, simulation_setup, waveguides,plot = False, progress=False):
    
    #%% System constants Constants
    c = 299792458           #[m/s]
    dneffdT = 1.87E-04      #[/K] assuming dneff/dn=1 (well confined mode)
    j = cmath.sqrt(-1)      # imaginary
    
    neffwg1 = waveguides[0]
    Dneffwg1 = waveguides[1]
    neffwg2 = waveguides[2]
    Dneffwg2 = waveguides[3]
    
    ApoFunc=np.exp(-np.linspace(0,1,num=1000)**2)     #Function used for apodization (window function)

    mirror = False                #makes the apodization function symetrical
    N_seg = 501                   #Number of flat steps in the coupling profile
    
    if simulation_setup.chirp == True:
        rch= 0.04                        #random chirping, maximal fraction of index randomly changing each segment
        lch= 0.2                         #linear chirp across the length of the device
        kch= -.1                        #coupling dependant chirp, normalized to the max coupling
    else:
        rch= 0                        #random chirping, maximal fraction of index randomly changing each segment
        lch= 0                         #linear chirp across the length of the device
        kch= 0                        #coupling dependant chirp, normalized to the max coupling
        
        
    neff_detuning_factor = 1
    
    #%% calculate waveguides propagation constants
    alpha_e = 100*contraDC.alpha/10*math.log(10)
    neffThermal = dneffdT*(simulation_setup.deviceTemp-simulation_setup.chipTemp)

    # Waveguides models
    Lambda = np.linspace(simulation_setup.lambda_start, simulation_setup.lambda_end, num=simulation_setup.resolution)

    neff_a_data = neffwg1+Dneffwg1*(Lambda-simulation_setup.central_lambda)
    neff_a_data = neff_a_data*neff_detuning_factor+neffThermal
    neff_b_data=neffwg2+Dneffwg2*(Lambda-simulation_setup.central_lambda)
    neff_b_data = neff_b_data*neff_detuning_factor+neffThermal
    Lambda_data_left=Lambda
    Lambda_data_right=Lambda

    beta_data_left=2*math.pi/Lambda_data_left*neff_a_data
    beta_data_right=2*math.pi/Lambda_data_right*neff_b_data

    #%% makes sense until HERE

    beta_left=np.interp(Lambda, Lambda_data_left, beta_data_left); betaL=beta_left
    beta_right=np.interp(Lambda, Lambda_data_right, beta_data_right); betaR=beta_right    
  
    # Calculating reflection wavelenghts
    period = contraDC.period
    
    f= 2*math.pi/(beta_left+beta_right) #=grating period at phase match
    minimum = min(abs(f-period)) #index of closest value
    idx = np.where(abs(f-period) == minimum)
    beta12Wav = Lambda.item(idx[0][0])
  
    f= 2*math.pi/(2*beta_left)
    minimum = min(abs(f-period))
    idx = np.where(abs(f-period) == minimum)
    beta1Wav = Lambda.item(idx[0][0])
  
    f= 2*math.pi/(2*beta_right)
    minimum = min(abs(f-period))
    idx = np.where(abs(f-period) == minimum)
    beta2Wav = Lambda.item(idx[0][0])
    
    T =      np.zeros((1, Lambda.size),dtype=complex)
    R =      np.zeros((1, Lambda.size),dtype=complex)
    T_co =   np.zeros((1, Lambda.size),dtype=complex)
    R_co =   np.zeros((1, Lambda.size),dtype=complex)
    
    E_Thru = np.zeros((1, Lambda.size),dtype=complex)
    E_Drop = np.zeros((1, Lambda.size),dtype=complex)
    
    mode_kappa_a1=1
    mode_kappa_a2=0 #no initial cross coupling
    mode_kappa_b2=1
    mode_kappa_b1=0
  
    LeftRightTransferMatrix = np.zeros((4,4,Lambda.size),dtype=complex)
    TopDownTransferMatrix = np.zeros((4,4,Lambda.size),dtype=complex)
    InOutTransferMatrix = np.zeros((4,4,Lambda.size),dtype=complex)
  
    # Apodization & segmenting
    a = contraDC.apodization
    l_seg = contraDC.N*period/N_seg
    L_seg=l_seg
    n_apodization=np.arange(N_seg)+0.5
    zaxis= (np.arange(N_seg))*l_seg

    if  a!=0:
        kappa_apodG=np.exp(-a*((n_apodization)-0.5*N_seg)**2/N_seg**2)
        ApoFunc=kappa_apodG

        profile= (ApoFunc-min(ApoFunc))/(max(ApoFunc)-(min(ApoFunc))) # normalizes the profile

        n_profile = np.linspace(0,N_seg,profile.size)
        profile=np.interp(n_apodization, n_profile, profile)

        kappaMin = contraDC.kappa_contra*profile[0]
        kappaMax = contraDC.kappa_contra
    
        kappa_apod=kappaMin+(kappaMax-kappaMin)*profile
        
        if plot == True:
                import matplotlib.pyplot as plt
                plt.figure()
                plt.plot(zaxis*1e6, kappa_apod)
                plt.ylabel('kappa profile')
                plt.xlabel('Length (um)')
    else:
        kappa_apod = contraDC.kappa_contra*np.ones(N_seg)
        profile = np.ones(N_seg)

            
    lengthLambda=Lambda.size
    
    kappa_12max= max(kappa_apod)
    
    couplingChirpFrac= profile*kch/100 - kch/100
    lengthChirpFrac = np.linspace(-1,1,N_seg)*lch/100
    chirpDev = 1 + couplingChirpFrac + lengthChirpFrac
    randomChirpFrac = np.random.rand(1,N_seg)*rch/100; randomChirpFrac = randomChirpFrac[0,:]
    
    if plot == True:
        import matplotlib.pyplot as plt
        plt.figure()
        plt.plot(zaxis*1e6, couplingChirpFrac, label="Coupling chirp")
        plt.plot(zaxis*1e6, lengthChirpFrac, label="Length chirp")
        plt.plot(zaxis*1e6, randomChirpFrac, label="Random chirp")
        plt.plot(zaxis*1e6, couplingChirpFrac+lengthChirpFrac+randomChirpFrac, label="Total chirp")
        plt.ylabel('Chirp fraction (%)')
        plt.xlabel('Length (um)')
        plt.legend()
        
    n=np.arange(N_seg)
  
#%% Beautiful Progress Bar
    #https://stackoverflow.com/questions/3173320/text-progress-bar-in-the-console
    #Thank Greenstick.
    
    if progress:
        # A List of Items
        progressbar_width = lengthLambda
        # Initial call to print 0% progress
        printProgressBar(0, progressbar_width, prefix = 'Progress:', suffix = 'Complete', length = 50)
            
    for ii in range(lengthLambda):
        if progress:
            #Update Bar
            printProgressBar(ii + 1, progressbar_width, prefix = 'Progress:', suffix = 'Complete', length = 50)

        print('Progress: %s / %s' %(ii+1, lengthLambda) ) 

        randomChirp = randomChirpFrac
        chirpWL = chirpDev + randomChirp
        
        P=1
  
        for n in range(N_seg):
            L_0=(n)*l_seg

            kappa_12=kappa_apod.item(n)
            #kappa_21=conj(kappa_12); #unused: forward coupling!
            kappa_11=contraDC.kappa_self1
            kappa_22=contraDC.kappa_self2
      
            beta_del_1=beta_left*chirpWL.item(n)-math.pi/period-j*alpha_e/2
            beta_del_2=beta_right*chirpWL.item(n)-math.pi/period-j*alpha_e/2

            # S1 = Matrix of propagation in each guide & direction
            S_1=[  [j*beta_del_1.item(ii), 0, 0, 0], [0, j*beta_del_2.item(ii), 0, 0],
                   [0, 0, -j*beta_del_1.item(ii), 0],[0, 0, 0, -j*beta_del_2.item(ii)]]

            # S2 = transfert matrix
            S_2=  [[-j*beta_del_1.item(ii),  0,  -j*kappa_11*np.exp(j*2*beta_del_1.item(ii)*L_0),  -j*kappa_12*np.exp(j*(beta_del_1.item(ii)+beta_del_2.item(ii))*L_0)],
                   [0,  -j*beta_del_2.item(ii),  -j*kappa_12*np.exp(j*(beta_del_1.item(ii)+beta_del_2.item(ii))*L_0),  -j*kappa_22*np.exp(j*2*beta_del_2.item(ii)*L_0)],
                   [j*np.conj(kappa_11)*np.exp(-j*2*beta_del_1.item(ii)*L_0),  j*np.conj(kappa_12)*np.exp(-j*(beta_del_1.item(ii)+beta_del_2.item(ii))*L_0),  j*beta_del_1.item(ii),  0],
                   [j*np.conj(kappa_12)*np.exp(-j*(beta_del_1.item(ii)+beta_del_2.item(ii))*L_0),  j*np.conj(kappa_22)*np.exp(-j*2*beta_del_2.item(ii)*L_0),  0,  j*beta_del_2.item(ii)]]

            P0=np.matmul(scipy.linalg.expm(np.asarray(S_1)*l_seg),scipy.linalg.expm(np.asarray(S_2)*l_seg))
            if n == 0:
                P1 = P0*P
            else:
                P1 = np.matmul(P0,P)
                
            P = P1
            
        LeftRightTransferMatrix[:,:,ii] = P
        
        # Calculating In Out Matrix
        # Matrix Switch, flip inputs 1&2 with outputs 1&2
        H = switchTop( P )
        InOutTransferMatrix[:,:,ii] = H
        
        # Calculate Top Down Matrix
        P2 = P
        # switch the order of the inputs/outputs
        P2=np.vstack((P2[3][:], P2[1][:], P2[2][:], P2[0][:])) # switch rows
        P2=swap_cols(P2,1,2) # switch columns
        # Matrix Switch, flip inputs 1&2 with outputs 1&2
        P3 = switchTop( P2 )
        # switch the order of the inputs/outputs
        P3=np.vstack((P3[3][:], P3[0][:], P3[2][:], P3[1][:])) # switch rows
        P3=swap_cols(P3,2,3) # switch columns
        P3=swap_cols(P3,1,2) # switch columns

        TopDownTransferMatrix[:,:,ii] = P3
        T[0,ii] = H[0,0]*mode_kappa_a1+H[0,1]*mode_kappa_a2
        R[0,ii] = H[3,0]*mode_kappa_a1+H[3,1]*mode_kappa_a2

        T_co[0,ii] = H[1,0]*mode_kappa_a1+H[1,0]*mode_kappa_a2
        R_co[0,ii] = H[2,0]*mode_kappa_a1+H[2,1]*mode_kappa_a2

        E_Thru[0,ii] = mode_kappa_a1*T[0,ii]+mode_kappa_a2*T_co[0,ii]
        E_Drop[0,ii] = mode_kappa_b1*R_co[0,ii] + mode_kappa_b2*R[0,ii]

        #%% return results
        contraDC.E_Thru = E_Thru
        contraDC.E_Drop = E_Drop
        contraDC.wavelength = Lambda
        contraDC.TransferMatrix = LeftRightTransferMatrix
        
    return contraDC

# Print iterations progress
def printProgressBar (iteration, total, prefix = '', suffix = '', decimals = 1, length = 100, fill = '█'):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print('\r%s |%s| %s%% %s' % (prefix, bar, percent, suffix), end = '\r')
    # Print New Line on Complete
    if iteration == total: 
        print()