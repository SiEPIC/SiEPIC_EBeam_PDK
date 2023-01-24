classdef ApodizedContraDC
%{
    CLASS ContraDC             Jonathan St-Yves
                               jonhwoods@gmail.com
                               2016
    
    Object representing a contra directionnal coupler
    in silicon. 
    
    Dependancy in the same folder: switchTop2.m
%} 
    properties
        name='undefName'
        
        NormalTemp=300;             %[K] Temperature of the mesured chip
        DeviceTemp=300;             %[K] Temperature of the device (for dNeff)
        
        starting_wavelength=1520;   %nanometers
        ending_wavelength=1580;
        resolution=500;             %number of wavelengths to compute
        
        N_Corrugations=1000         %Number of corrugations along the grating
        period=0.28e-6;             %[m] corrugation period
        
        centralWL_neff=1550*10^-9;
        neffwg1=2.5;                %neff vs wav in both waveguides (lin fit)
        Dneffwg1=-1*10^6;
        neffwg2=2.3;
        Dneffwg2=-1.2*10^6;
        alpha=10*100;                %Loss of the medium, in dB/m (10dB/cm*100cm/m)
        
        kappaMax=9000;              %contra-directional coupling
        kappaMin=0;
        a=0;                        %for gaussian function, set to 0 for custom
        ApoFunc=exp(-linspace(0,1,1000).^2);     %Function used for apodization (window function)
        mirror=false;                %makes the apodization function symetrical
        N_seg=20;                   %Number of flat steps in the coupling profile
        antiRefCoeff=.5;          %k11 and k22 relative to k12 (bragg, same-waveguide reflection)
        
        rch=0; %random chirping, maximal fraction of index randomly changing each segment
        lch=0 ; % linear chirp across the length of the device
        kch=0 ; %coupling dependant chirp, normalized to the max coupling

        
        
    end
    
    properties (Dependent=true) %these are calculated when asked to
        frequency   %[/s]
        omega       %[radians/s] Angular Frequency
        
        dT          %[K]    difference of Temperatures
        length      %[m]    Length of the grating
        
        thru        %[dB]   Thru port response
        thruPhase   %[radians] Phase at the drop port
        thruGroupDelay  %[s]
        drop        %[dB]   Drop port response
        dropPhase   %[radians] Phase at the drop port
        dropGroupDelay  %[s]
    end
    
    properties  %These properties are calculated 
                                     %with update() and read only
        Lambda      %[m] array of wavelengths used
        E_Thru      %[V] electrical field at the thru port (calculated)
        E_Drop      %[V] electrical field at the drop port (calculated)
        

        LeftRightTransferMatrix %Normal-LeftHS: A0+,B0+,A0-,B0- (Left)
                                       %RightHS:Az+,Bz+,Az-,Bz- (Right)

        TopDownTransferMatrix       %LeftHS:  A0+,Az+,A0-,Az- (bottom)
                                    %RightHS: A0+,A0-,Az+,Az- (top)
                                    
        InOutTransferMatrix         %LeftHS:  A+z,B+z,A0-,B0- (out)
                                    %RightHS: A0+,B0+,Az-,Bz- (in)
        
        kappa_apod  %coupling coefficient along the grating
        kappa_apodG %destitute, same as kappa_apod, only if Gaussian
        
        couplingChirpFrac
        lengthChirpFrac
        chirpDev
        
        betaL
        betaR
        L_seg
        beta12Wav   %[m]    Central wavelength of reflexion
        beta1Wav    %[m]    Secondary wavelength of reflexion (bragg)
        beta2Wav    %[m]    Secondary wavelength of reflexion (bragg)
        zaxis       %[m]    Values of distance along the propagation axis
    end
    
    properties (Constant = true)
        c = 299792458;  %[m/s]
        dneffdT = 1.87E-04;%[/K] assuming dneff/dn=1 (very confined)
    end
    
    
    methods
        
        %Dependent variables
        function dt = get.dT(ob)
            dt=ob.DeviceTemp-ob.NormalTemp;
        end
        function tru=get.thru(ob)
            tru=10*log10(abs(ob.E_Thru).^2);
        end
        function drp=get.drop(ob)
            drp=10*log10(abs(ob.E_Drop).^2);
        end
        function len=get.length(ob)
            len=ob.N_Corrugations*ob.period;
        end
        function thruPhase = get.thruPhase(ob)
            %thruPhase= unwrapphase((ob.E_Thru));
            thruPhase= (ob.E_Thru);
        end
        function dropPhase = get.dropPhase(ob)
            dropPhase= angle(ob.E_Drop);
        end
        function frequency = get.frequency(ob)
            frequency= ob.c./ob.Lambda;
        end
        function omega = get.omega(ob)
            omega= ob.frequency*2*pi;
        end
        function dropGroupDelay = get.dropGroupDelay(ob)
            dropGroupDelay = -diff(ob.dropPhase)./diff(ob.omega);
            dropGroupDelay(end+1)=0;
            signal = ob.drop>-80; %identifies the places without signal
            %dropGroupDelay = dropGroupDelay.*signal;  %make the delay not go to crazy number and just to 0
        end
        function thruGroupDelay = get.thruGroupDelay(ob)
            thruGroupDelay = -diff(ob.thruPhase)./diff(ob.omega);
            thruGroupDelay(end+1)=0;
            signal = ob.thru>-90;
            %thruGroupDelay = thruGroupDelay.*signal;
        end
        
        
        %Plotting
        function plotKappa(ob,mode)
            if nargin < 2
                mode = 'stairs';
            end
            
            figure;
            if strcmp(mode,'stairs')
                stairs(ob.zaxis*1e6,ob.kappa_apod/1000);
            else
                plot(ob.zaxis*1e6,ob.kappa_apod/1000);
            end
            xlim([0 (ob.length)*1e6]);
            ylim([0, max(ob.kappa_apod/1000)+2])
            xlabel('Position along the propagation axis [\mum]','fontsize',14,'FontName', 'Times New Roman');
            ylabel('\kappa_1_2 [/mm]','fontsize',14,'FontName', 'Times New Roman');
            %title( cat(2,'Apodization profile of ',ob.name),...
            %    'fontsize',20,'FontName', 'Times New Roman');
        end
        
        function plotPhase(ob)
            figure2=figure;
            axes1 = axes('Parent',figure2,'FontSize',12,'FontName','Times New Roman',...
                 'YMinorTick','on');
            set(axes1,'ColorOrder',[0 0 0;0.8 0 0;0 0.8 0;0 0 0.8],...
                  'LineStyleOrder','-|--|:');
            box(axes1,'on');
            hold(axes1,'all');
            xlabel('Frequency [THz]','fontsize',14,'FontName', 'Times New Roman');
            ylabel('Phase [cycles]','fontsize',14,'FontName', 'Times New Roman');

            plot(ob.frequency./10^12,ob.dropPhase./(2*pi),'LineWidth',2,'displayname', ob.name);
        end
        
        function plotGroupDelay(ob)
            figure2=figure;
            axes1 = axes('Parent',figure2,'FontSize',12,'FontName','Times New Roman',...
                 'YMinorTick','on');
            set(axes1,'ColorOrder',[0 0 0;0.8 0 0;0 0.8 0;0 0 0.8],...
                  'LineStyleOrder','-|--|:');
            box(axes1,'on');
            hold(axes1,'all');
            xlabel('Wavelength [nm]','fontsize',14,'FontName', 'Times New Roman');
            ylabel('Group Delay [ps]','fontsize',14,'FontName', 'Times New Roman');
            %title(ob.name);
            
            xlim([ob.starting_wavelength ob.ending_wavelength]);
            ylim([-14 14]);

            plot(ob.Lambda.*10^9,ob.dropGroupDelay.*10^12,'LineWidth',2,'displayname', cat(2,'Drop'));
            plot(ob.Lambda.*10^9,ob.thruGroupDelay.*10^12,'--','LineWidth',2,'displayname', cat(2,'Thru'));
            legend1=legend('show');
            set(legend1,'FontSize',14,'FontName','Times New Roman','box','on',...
            'Location','NorthEast');
        end
        
        function plotChirp(ob)
            figure2=figure;
            axes1 = axes('Parent',figure2,'FontSize',12,'FontName','Times New Roman',...
                 'YMinorTick','on');
            set(axes1,'ColorOrder',[0 0 0;0.8 0 0;0 0.8 0;0 0 0.8],...
                  'LineStyleOrder','-|--|:');
            box(axes1,'on');
            hold(axes1,'all');
            xlabel('Position [\mum]','fontsize',14,'FontName', 'Times New Roman');
            ylabel('Refractive Index Variation [%]','fontsize',14,'FontName', 'Times New Roman');
            %title(ob.name);

            
            randomChirpFrac=(rand(1,ob.N_seg)-0.5)*ob.rch;
            plot(ob.zaxis*1e6,(randomChirpFrac)*100,'--','LineWidth',2,'displayname', cat(2,'Random Chirp'));
            plot(ob.zaxis*1e6,(ob.couplingChirpFrac)*100,'--','LineWidth',2,'displayname', cat(2,'Coupling Chirp'));
            plot(ob.zaxis*1e6,(ob.lengthChirpFrac)*100,'--','LineWidth',2,'displayname', cat(2,'Linear Chirp'));
            plot(ob.zaxis*1e6,(ob.chirpDev+randomChirpFrac-1)*100,'LineWidth',3,'displayname', cat(2,'Full Chirp'));
            xlim([0 (ob.length)*1e6]);
            
            legend1=legend('show');
            set(legend1,'FontSize',14,'FontName','Times New Roman','box','on',...
            'Location','SouthEast');
           
        end
        
        function bol=hasSameDef(ob,other)
            bol=(  isequal(ob.name,other.name) && ...        
            ob.NormalTemp==other.NormalTemp && ...
            ob.DeviceTemp==other.DeviceTemp && ...
            ob.starting_wavelength==other.starting_wavelength && ...
            ob.ending_wavelength==other.ending_wavelength && ...
            ob.resolution==other.resolution && ...
            ob.N_Corrugations==other.N_Corrugations && ...
            ob.period==other.period && ...
            ob.centralWL_neff==other.centralWL_neff && ...
            ob.neffwg1==other.neffwg1 && ...   
            ob.Dneffwg1==other.Dneffwg1 && ...    
            ob.neffwg2==other.neffwg2 && ...     
            ob.Dneffwg2==other.Dneffwg2 && ...    
            ob.alpha==other.alpha && ...
            ob.a==other.a && ...   
            ob.N_seg==other.N_seg && ...    
            isequal(ob.ApoFunc,other.ApoFunc) && ...    
            ob.kappaMax==other.kappaMax && ...    
            ob.kappaMin==other.kappaMin && ...  
            ob.mirror==other.mirror && ...      
            ob.rch==other.rch && ...    
            ob.lch==other.lch && ...      
            ob.kch==other.kch             );
        end
        
        
        %Calculations
        function ob=update(ob)
            ob.Lambda=linspace(ob.starting_wavelength,ob.ending_wavelength,ob.resolution)*1e-9;
            alpha_e=ob.alpha/10*log(10);
            neff_detuning_factor=1; %to switch to parameters
            neffThermal = ob.dT*ob.dneffdT;
           
            %Neff from Dispersion Model 
            if (ob.neffwg1*ob.Dneffwg1*ob.neffwg2*ob.Dneffwg2~=0)
%                 neff_a_data=ob.neffwg1+ob.Dneffwg1.*(ob.Lambda-ob.centralWL_neff);
%                 neff_b_data=ob.neffwg2+ob.Dneffwg2.*(ob.Lambda-ob.centralWL_neff);
%                 Lambda_data_left=ob.Lambda;
%                 Lambda_data_right=ob.Lambda;
                plotPhaseMatch;
                Lambda_data_left=ob.Lambda;
                Lambda_data_right=ob.Lambda;

%                 
            else %Neff from MODE file
                load 280_400noslab_neffF_mode1;
                Lambda_data_left=ob.c./f;    neff_a_data=real(neff);
                load 280_400noslab_neffF_mode2;
                Lambda_data_right=ob.c./f;   neff_b_data=real(neff);
            end
            neff_a_data=neff_a_data*neff_detuning_factor+neffThermal;
            neff_b_data=neff_b_data*neff_detuning_factor+neffThermal;
            
            beta_data_left=2*pi./Lambda_data_left.*neff_a_data;
            beta_data_right=2*pi./Lambda_data_right.*neff_b_data;
            
            beta_left=interp1(Lambda_data_left, beta_data_left, ob.Lambda);
            beta_right=interp1(Lambda_data_right, beta_data_right, ob.Lambda);
            
            ob.betaL=beta_left;
            ob.betaR=beta_right;
            %%----end of beta
            
            %Calculating reflection wavelenghts
            f= 2*pi./(beta_left+beta_right); %=grating period at phase match
            [void, idx] = min(abs(f-ob.period)); %index of closest value
            ob.beta12Wav = ob.Lambda(idx); %closest value
            f= 2*pi./(2*beta_left);
            [void, idx] = min(abs(f-ob.period));
            ob.beta1Wav = ob.Lambda(idx);
            f= 2*pi./(2*beta_right);
            [void, idx] = min(abs(f-ob.period));
            ob.beta2Wav = ob.Lambda(idx);
            
            T=      zeros(1, length(ob.Lambda));
            R=      zeros(1, length(ob.Lambda));
            T_co=   zeros(1, length(ob.Lambda));
            R_co=   zeros(1, length(ob.Lambda));
            
            mode_kappa_a1=1;  
            mode_kappa_a2=0;%no initial cross coupling
            mode_kappa_b2=1;
            mode_kappa_b1=0;
            ob.LeftRightTransferMatrix = zeros(4,4,length(ob.Lambda));
            ob.TopDownTransferMatrix = zeros(4,4,length(ob.Lambda));
            ob.InOutTransferMatrix = zeros(4,4,length(ob.Lambda));
            
            %Apodization & segmenting
            l_seg=ob.N_Corrugations*ob.period/ob.N_seg;
            ob.L_seg=l_seg;
            n_apodization=(1:ob.N_seg)-0.5;
            ob.zaxis= ((1:ob.N_seg)-1)*l_seg;
            if ob.a~=0
                ob.kappa_apodG=exp(-ob.a*(n_apodization-0.5*ob.N_seg).^2/ob.N_seg^2);
                ob.ApoFunc=ob.kappa_apodG;              
            end
            profile= (ob.ApoFunc-min(ob.ApoFunc))/(max(ob.ApoFunc)-(min(ob.ApoFunc))); %normalizes the profile
            if ob.mirror==true
                profile=cat(2,fliplr(profile(2:end)),profile); %mirrors the profile (keeping only 1 center)
            end
            n_profile=linspace(0,ob.N_seg,length(profile));
            profile=interp1(n_profile, profile, n_apodization,'spline');

            ob.kappa_apod=ob.kappaMin+(ob.kappaMax-ob.kappaMin).*profile;
            
           
            lenghtLambda=length(ob.Lambda);
            
            %Phase noise and chirp
            kappa_12max=max(ob.kappa_apod);
            ob.couplingChirpFrac = zeros(1,ob.N_seg);
            n=1:ob.N_seg;
            ob.lengthChirpFrac= zeros(1,ob.N_seg); %center is neutral
            
            ob.chirpDev=1 + ob.couplingChirpFrac + ob.lengthChirpFrac;
            
            h = waitbar(0,'Please wait...');
            steps = 20;
            step=0;
            
            for ii= 1:lenghtLambda

                P=1;
                randomChirp= zeros(1,ob.N_seg);
                chirpWL=ob.chirpDev+randomChirp;
                for n=1:ob.N_seg
                    L0=(n-1)*l_seg;
                    
                    kappa_12=ob.kappa_apod(n);
                    %kappa_21=conj(kappa_12); %unused
                    kappa_11=ob.antiRefCoeff*ob.kappa_apod(n);
                    kappa_22=ob.antiRefCoeff*ob.kappa_apod(n);
                    
                    beta_del_1=beta_left*chirpWL(n)-pi/ob.period-1i*alpha_e/2;
                    beta_del_2=beta_right*chirpWL(n)-pi/ob.period-1i*alpha_e/2;
                    

                    %S1 = Matrix of propagation in each guide & direction
                    S1=[1i*beta_del_1(ii), 0, 0, 0;  ...
                        0, 1i*beta_del_2(ii), 0, 0;  ...
                        0, 0, -1i*beta_del_1(ii), 0; ...
                        0, 0, 0, -1i*beta_del_2(ii)];
                    %S2 = transfert matrix
                    S2=[-1i*beta_del_1(ii)  0  -1i*kappa_11*exp(1i*2*beta_del_1(ii)*L0)  -1i*kappa_12*exp(1i*(beta_del_1(ii)+beta_del_2(ii))*L0);...
                        0  -1i*beta_del_2(ii)  -1i*kappa_12*exp(1i*(beta_del_1(ii)+beta_del_2(ii))*L0)  -1i*kappa_22*exp(1i*2*beta_del_2(ii)*L0);...
                        1i*conj(kappa_11)*exp(-1i*2*beta_del_1(ii)*L0)  1i*conj(kappa_12)*exp(-1i*(beta_del_1(ii)+beta_del_2(ii))*L0)  1i*beta_del_1(ii)  0;...
                        1i*conj(kappa_12)*exp(-1i*(beta_del_1(ii)+beta_del_2(ii))*L0)  1i*conj(kappa_22)*exp(-1i*2*beta_del_2(ii)*L0)  0  1i*beta_del_2(ii)];
                    P=expm(S1*l_seg)*expm(S2*l_seg)*P;
                end
                if getappdata(h,'canceling')
                    break
                end
                if (ii/lenghtLambda)> (step/steps)
                    step = step+1;
                    waitbar(step / steps);
                end
                
                ob.LeftRightTransferMatrix(:,:,ii)=P;

                %Calculating In Out Matrix
                %Matrix Switch, flip inputs 1&2 with outputs 1&2
                H=switchTop2(P);
                ob.InOutTransferMatrix(:,:,ii)=H;
                
                %Calculate Top Down Matrix
                P2=P;
                %switch the order of i/o
  
                P2=[P2(4,:); P2(2,:); P2(3,:); P2(1,:)]; %switch rows
                P2=[P2(:,1)  P2(:,3)  P2(:,2)  P2(:,4)];%switch columns
                %Matrix Switch, flip inputs 1&2 with outputs 1&2
                P_FF=[P2(1, 1), P2(1, 2); P2(2, 1), P2(2, 2)];
                P_FG=[P2(1, 3), P2(1, 4); P2(2, 3), P2(2, 4)];
                P_GF=[P2(3, 1), P2(3, 2); P2(4, 1), P2(4, 2)];
                P_GG=[P2(3, 3), P2(3, 4); P2(4, 3), P2(4, 4)];
                P3=[P_FF-P_FG*P_GG^-1*P_GF, P_FG*P_GG^-1; -P_GG^-1*P_GF, P_GG^-1];
 
                P3=[P3(4,:); P3(1,:); P3(3,:); P3(2,:)]; %switch rows
                P3=[P3(:,1)  P3(:,4)  P3(:,2)  P3(:,3)];%switch columns
                ob.TopDownTransferMatrix(:,:,ii)=P3;
                
                T(ii)=H(1, 1)*mode_kappa_a1+H(1, 2)*mode_kappa_a2;
                R(ii)=H(4, 1)*mode_kappa_a1+H(4, 2)*mode_kappa_a2;
                
                T_co(ii)=H(2, 1)*mode_kappa_a1+H(2, 1)*mode_kappa_a2;
                R_co(ii)=H(3, 1)*mode_kappa_a1+H(3, 2)*mode_kappa_a2;

                % output coupling
                
                ob.E_Thru(ii)=mode_kappa_a1*T(ii)+mode_kappa_a2*T_co(ii);
                ob.E_Drop(ii)=mode_kappa_b1*R_co(ii)+mode_kappa_b2*R(ii);

            end
            delete(h);
        end
    end
    
end %class ContraDC