# Python 2.7 script
# by Lukas Chrostowski in Matlab
# by Huixu (Chandler) Deng in Python, 2017

#==============================================================================
# This script analyzes experimental data to determine the insertion loss
# of a device under test (DUT), e.g., YBranch, using the cut-back method.
# The layout is several (e.g., 4) circuits each consisting of N devices in
# series, where N ranges from a small number (e.g., 0) to a large number.  The
# large number is chosen as a trade-off between the layout size and a
# value that gives an excess insertion loss of about 10 dB.  For example,
# if the DUT is estimated to have an insertion loss of 0.3 dB, we would
# choose the largest value of N to be 10 dB / 0.24 dB = 42.
# 
# To find the insertion loss, we plot the measured insertion loss versus
# the number of DUTs in the circuit.  Then we perform a linear regression,
# and the slope tells us the insertion loss for one DUT.
# 
# For the case of the YBranch, the circuit consists of two YBranches facing
# each other. This creates an interferometer.  Assuming the waveguides are
# perfectly matched, the interferometer insertion loss will be only due to
# the excess loss of the YBranch.
# 
# The following layout implements test structures for the YBranch described
# in paper http://dx.doi.org/10.1364/OE.21.001310
# EBeam_LukasChrostowski_TM_YBranches.gds
# https://www.dropbox.com/s/vs0hvrggbn5f9ip/EBeam_LukasChrostowski_TM_YBranches.gds?dl=1
#==============================================================================

from __future__ import print_function # make 'print' compatible in Python 2X and 3X
from scipy.io import loadmat        # used to load MATLAB data files
import matplotlib.pyplot as plt     # used to plot data
import os                           # used to process filenames
import urllib                       # used to download files from Dropbox.com
import numpy as np
import statsmodels.api as sm

# calculate error confidence intervals?
# check if regress function is present. This is part of the statistics toolbox.
#if 'regress' in globals():
#    Error_Intervals = True

FONTSIZE = 13   # font size for the figures;

# Identify the name of the Device Under Test.
deviceName = 'Spiral cutback (TE)'
# At what wavelength do you want to find out the insertion loss of the DUT
lam0 = 1.55e-6

# matrix of measurement data files, and # of components in each
files = ['../D2020_02_UW/PCM_PCM_SpiralWG1213TE_gap2000_1698.mat',
         '../D2020_02_UW/PCM_PCM_SpiralWG11204TE_gap2000_1695.mat',
         '../D2020_02_UW/PCM_PCM_SpiralWG32237TE_gap2000_1711.mat',
         '../D2020_02_UW/PCM_PCM_SpiralWG53018TE_gap2000_1712.mat',
         '../D2020_02_UW/PCM_PCM_SpiralWG102530TE_gap2000_1699.mat']
# number of DUTs in each circuit:
Num = np.array([1213, 11204, 32237, 53018, 102530])*1e-4
PORT=2   # fibre measurement configuration; detector number.

# Download the file from Dropbox.  Dropbox requires that you have a ?dl=1 at the end of the file
# Store the file in the local directory
# Enter the Dropbox URL here.  Make sure it has a =1 at the end:
url = [ 'https://www.dropbox.com/s/louspt78v28x1dw/lukasc_YBranch3_1262.mat?dl=1',
        'https://www.dropbox.com/s/cqyc233aqm8b2rc/lukasc_YBranch9_1261.mat?dl=1',
        'https://www.dropbox.com/s/xrvtv54hmvjpfh4/lukasc_YBranch15_1260.mat?dl=1',
        'https://www.dropbox.com/s/eiypug7qkx1p1ry/lukasc_YBranch21_1263.mat?dl=1']

wavelength = []
power = []

for i in np.arange(len(files)):
    FileName = files[i]
#    FileName = os.path.split(os.path.splitext(url[i])[0]+'.mat')[1]
#    print FileName
#    urllib.urlretrieve(url[i], FileName) # used in Python 2.x
#    urllib.request.urlretrieve(url[i], FileName) # used in Python 3.x
    # Load the file, from the MATLAB format.
    matData = loadmat(FileName)
    # Read the experimental data from the MATLAB file
    wavelength.append(matData['scandata'][0][0][0][0])
    power.append(matData['scandata'][0][0][1].T[PORT-1])

# Plot all the raw data, and also curve-fit each to a polynomial
plt.figure()
LegendText = []
p = []
amplitude = []
amplitude_poly = []
for i in np.arange(len(files)):
    lam = wavelength[i] # wavelength
    amplitude.append(power[i]) # detector data
    plt.plot(lam*1e6, amplitude[i])
    
    # Curve-fit data to a polynomial
    p.append(np.polyfit((lam-np.mean(lam))*1e6, amplitude[i], 4))
    amplitude_poly.append(np.polyval(p[i],(lam-np.mean(lam))*1e6))
    plt.plot(lam*1e6, amplitude_poly[i], linewidth=2)
    
    # legend entries
    LegendText.append('raw data:' + files[i])
    LegendText.append('fit data:' + files[i])

plt.title('Optical spectra for the test structures', fontsize = FONTSIZE)
plt.xlabel('Wavelength, $\mu$m', fontsize = FONTSIZE)
plt.ylabel('Insertion Loss, dB', fontsize = FONTSIZE)
#plt.legend(LegendText,loc = 3, fontsize = FONTSIZE)
plt.autoscale(enable=True, axis='x', tight=True)
plt.autoscale(enable=True, axis='y', tight=True)
plt.show()

#==============================================================================
# least-squares linear regression of the insertion loss values vs. number
# of DUTs, at lam0, to find the slope, A(2), and y-intercept, A(1)
# The slope, A(2), is the insertion loss for one DUT
#==============================================================================
c = np.min(np.abs(lam-lam0))  
index = int(np.argmin(np.abs(lam-lam0)))# find lam0 in lam vector.
A_a = np.hstack((np.ones(len(Num))[:,np.newaxis], Num[:,np.newaxis]))
A_b = np.array([amplitude_poly[i][index] for i in np.arange(len(Num))])[:,np.newaxis]
A =np.linalg.lstsq(A_a, A_b)[0]

plt.figure()
plt.plot(Num, np.array([amplitude[i][index] for i in np.arange(len(Num))]),'x', label = 'raw data at lam0')
plt.plot(Num, np.array([amplitude_poly[i][index] for i in np.arange(len(Num))]),'o', label = 'polyfit of raw data')
plt.plot(Num, A[0] + Num*A[1], linewidth = 3, label = 'linear regression of polyfit')
plt.xlabel('Length (cm)', fontsize = FONTSIZE)
plt.ylabel('Loss (dB/cm)', fontsize = FONTSIZE)
plt.title('Cut-back method, loss, at 1550 nm', fontsize = FONTSIZE)
plt.legend()


# Calculate the slope error, +/- dB, with a 95% confidence interval
# using the StatsModels' Regression Results
y_index = np.array([amplitude_poly[i][index] for i in np.arange(len(Num))])
x_index = np.hstack((Num[:,np.newaxis], np.ones(len(Num))[:,np.newaxis]))
mod = sm.OLS(y_index, x_index)
res = mod.fit()
b = res.params
bint =  res.conf_int(0.05)

SlopeError95CI = np.diff(bint[0,:])/2
InterceptError95CI = np.diff(bint [1,:])/2
plt.annotate('Fit results, with 95% confidence intervals:', xy=(1, -45))
plt.annotate('slope is ='+'%.3f' %A[1] + ' +/- ' + '%.3f' %SlopeError95CI + ' dB/cm', xy=(1, -50))
plt.annotate('intercept is = '+'%.3f' %A[0] + ' +/- ' + '%.3f' %InterceptError95CI + 'dB', xy=(1, -55))
plt.show()
print ('Cut-back method, insertion loss, at', lam0*1e9, 'nm is =', -A[1], 'dB/YBranch')

#==============================================================================
# wavelength dependance of the DUT insertion loss
# perform a linear regression at each wavelength, using the raw data
#==============================================================================
C_a = np.hstack((np.ones(len(Num))[:,np.newaxis], Num[:,np.newaxis]))
C_b = np.array([amplitude[i][:] for i in np.arange(len(Num))])
C = np.linalg.lstsq(C_a, C_b)[0]

# perform a linear regression at each wavelength, using the polyfit data
slope=[]
slope_int=[]
lam_downsampled = lam[np.arange(0, np.size(lam), 100)]
amplitude_poly_downsampled = np.array([amplitude_poly[i][np.arange(0, np.size(lam), 100)] for i in np.arange(len(Num))])
for i in np.arange(len(lam_downsampled)):
    y_lam_index = amplitude_poly_downsampled[:,i]
    x_lam_index = np.hstack((Num[:,np.newaxis], np.ones(len(Num))[:,np.newaxis]))
    mod_lam = sm.OLS(y_lam_index, x_lam_index)
    res_lam = mod_lam.fit()
    b_lam = res_lam.params
    bint_lam =  res_lam.conf_int(0.05)
    slope.append(b_lam[0])
    slope_int.append(bint_lam[0,:])

# Plot the 95% confidence interval as a shaded region. It is based on the
# polyfit fit results
X = lam_downsampled*1e6
Y0 = -np.array([slope_int[i][0] for i in np.arange(len(slope_int))])
Y1 = -np.array([slope_int[i][1] for i in np.arange(len(slope_int))])

plt.figure()
plt.fill_between(X, Y0, Y1, facecolor='cyan', label = 'Insertion loss, 95% Confidence Interval')
# plot the linear regression results from the polyfit data
plt.plot(lam_downsampled*1e6, -np.array(slope), 'b', linewidth = 3, label = 'Insertion loss, from polyfit')
# plot the linear regression results from the raw data
plt.plot(lam*1e6, -C[1,:], 'y', label = 'Insertion loss, from Raw data')
plt.xlim([np.min(lam*1e6), np.max(lam*1e6)])
plt.legend(loc = 2)
plt.title('Cut-back method, loss, wavelength dependance')
plt.ylabel ('Loss (dB/cm)')
plt.xlabel ('Wavelength, $\mu$m')
plt.show()


# perform a linear regression at each wavelength, using the polyfit data
D_a = np.hstack((np.ones(len(Num))[:,np.newaxis], Num[:,np.newaxis]))
D_b = np.array([amplitude_poly[i][:] for i in np.arange(len(Num))])
D = np.linalg.lstsq(D_a, D_b)[0]

plt.figure()
plt.plot(lam*1e6, -D[1,:], label = 'Insertion loss, from polyfit')
plt.plot(lam*1e6, -C[1,:], label = 'Insertion loss, from Raw data')
plt.legend(loc = 2)
plt.autoscale(enable=True, axis='x', tight=True)
plt.autoscale(enable=True, axis='y', tight=True)
plt.ylim([0, np.max(-C[1,:])])
plt.title('Cut-back method, insertion loss, wavelength dependance')
plt.ylabel ('Loss (dB/cm)')
plt.xlabel ('Wavelength, $\mu$m')
plt.show()
