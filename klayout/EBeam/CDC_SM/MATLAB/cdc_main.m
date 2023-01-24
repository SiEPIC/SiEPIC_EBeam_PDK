% Mustafa Hammood	Mustafa@ece.ubc.ca
% SiEPIC TOOLS Contra-directional coupler simulator module
% to-be called from kLayout SiEPIC Tools package
% August 2018

%% Hard code contra-DC parameters for debugging
if(0)
    contraDC_kappa = 33000;
    contraDC_period = 304e-9;
    contraDC_a =10;
    contraDC_N = 1000;

    n_eff2_fit1 = 4.23027;
    n_eff1_fit1 = 4.02561;
    n_eff2_fit2 = -1.2208e6;
    n_eff1_fit2 = -965224;
end

%% Run script
GratingPlotter;