# -*- coding: utf-8 -*-
"""
Created on Sun Aug 12 15:59:58 2018

@author: Mustafa Hammood
"""

import os,time, math
import numpy as np
#import matplotlib.pyplot as plt

#%% Parse data files
os.chdir("C:/Users/Mustafa/Desktop")

contraDC_params_file = open("contraDC_params","r")
contraDC_params = (contraDC_params_file.read()).split(",")
gap = float(contraDC_params[0])
W_1 = float(contraDC_params[1])
W_2 = float(contraDC_params[2])
dW_1 = float(contraDC_params[3])
dW_2 = float(contraDC_params[4])
period = float(contraDC_params[5])
a = float(contraDC_params[6])
N = float(contraDC_params[7])
contraDC_params_file.close()


contraDC_mode_file = open("contraDC_mode","r")
contraDC_mode = (contraDC_mode_file.read()).replace("[","").replace("]","").split(",")
n_eff1_fit = [float(contraDC_mode[0]), float(contraDC_mode[1])]
n_eff2_fit = [float(contraDC_mode[2]), float(contraDC_mode[3])]
n_g1_fit = [float(contraDC_mode[4]), float(contraDC_mode[5])]
n_g2_fit = [float(contraDC_mode[6]), float(contraDC_mode[7])]
contraDC_mode_file.close()

contraDC_fdtd_file = open("contraDC_fdtd","r")
contraDC_fdtd = (contraDC_fdtd_file.read()).replace("[","").replace("]","").split(",")
bandwidth = float(contraDC_fdtd[0])
lambda_0 = float(contraDC_fdtd[1])
contraDC_fdtd_file.close()

#%% Find the coupling coefficient

_lambda = np.linspace(1500,1600,10001)*1e-9

n_eff1 = n_eff1_fit[0] + n_eff1_fit[1]*_lambda;
n_eff2 = n_eff2_fit[0] + n_eff2_fit[1]*_lambda;
n_g1 = n_g1_fit[0] + n_g1_fit[1]*_lambda;
n_g2 = n_g2_fit[0] + n_g2_fit[1]*_lambda;

def find_nearest(a, a0):
    "Element in nd array `a` closest to the scalar value `a0`"
    idx = np.abs(a - a0).argmin()
    return idx

# find _lambda index nearest lambda_0
lambda_index = find_nearest(_lambda,float(lambda_0))

kappa = math.pi*((n_g1[lambda_index] + n_g2[lambda_index])/2) *(bandwidth / (lambda_0**2))
print("Contra-directional kappa = " + str(kappa) +"\n\n")
print("SiEPIC TOOLS:		Calling MATLAB engine Python API, please wait . . . \n\n")
#%% Call matlab
if 1:
    import matlab.engine as matlab
    
    MATLABengine = matlab.start_matlab()
    
    paath = 'C:/Users/Mustafa/Google Drive/UBC Files/MiNa/Simulations/MATLAB Scripts/CDC Simu/3_Matlab'
    
    MATLABengine.cd(paath,nargout=0)
    
    MATLABengine.workspace['n_eff1_fit1'] = n_eff1_fit[0]
    MATLABengine.workspace['n_eff1_fit2'] = n_eff1_fit[1]
    MATLABengine.workspace['n_eff2_fit1'] = n_eff2_fit[0]
    MATLABengine.workspace['n_eff2_fit2'] = n_eff2_fit[1]
    MATLABengine.workspace['contraDC_kappa'] = float(kappa)
    MATLABengine.workspace['contraDC_period'] = period
    MATLABengine.workspace['contraDC_a'] = float(a)
    MATLABengine.workspace['contraDC_N'] = float(N)
    
    
    MATLABengine.run('GratingPlotter',nargout=0)
    
    time.sleep(10000)