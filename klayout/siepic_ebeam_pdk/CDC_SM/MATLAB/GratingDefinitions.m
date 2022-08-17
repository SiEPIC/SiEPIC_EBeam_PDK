% Grating definitions
% To be called by GratingPlotter.m (needs some variables declared)
% Jonathan St-Yves 2014
% Needs ApodizedContraDC.m




segments=(contraDC_a*100+1);    %apodization segments


no=1; gratingDef(no)=ApodizedContraDC;
gratingDef(no).a=contraDC_a;
gratingDef(no).kappaMax= contraDC_kappa;
gratingDef(no).kappaMin=0;
gratingDef(no).period=contraDC_period;

% gratingDef(no).neffwg2=0.00000402547*10^6;
% gratingDef(no).neffwg1=0.0000042082*10^6;
% gratingDef(no).Dneffwg2=-0.965064*10^6;
% gratingDef(no).Dneffwg1=-1.20098*10^6;

gratingDef(no).neffwg2=n_eff2_fit1;
gratingDef(no).neffwg1=n_eff1_fit1;
gratingDef(no).Dneffwg2=n_eff2_fit2;
gratingDef(no).Dneffwg1=n_eff1_fit2;


gratingDef(no).centralWL_neff=1550*10^-9;
gratingDef(no).N_Corrugations=contraDC_N;
gratingDef(no).starting_wavelength=1500;
gratingDef(no).ending_wavelength=1700;
gratingDef(no).resolution=res;
gratingDef(no).N_seg=segments;
gratingDef(no).name=cat(2, 'RUNNING: SiEPIC-Tools Contra-directional coupler simulation module');
