% dependencies in the same folder:  ApodizedContraDC.m
%                                   GratingDefinitions.m

%clear all;
%Speed/Accuracy
res=501;       %number of wavelengths (spectral resolution)

%Options
forceRedefine = 0;   %redefining will clear all computed data and apply 
                     %changes to the definitions in GratingDefinitions.m

%Gratings to plot
amplitudeToPlot=  [1];
phaseToPlot=[1];
apodProfileToPlot=[1]; %not functional, use grating(iii).plotKappa

printBW= amplitudeToPlot;

plotSystemGroupDelay=1;



%%
%%Definition Updater%%
global grating %The gratings are going to get accessed all over the place
if isa(grating,'double') %first initialization is a double
    grating = ApodizedContraDC;
end

    GratingDefinitions; %get all gratingDef
if (forceRedefine==1 || ~exist('grating'))
    grating=gratingDef;
else
    for iii=1:length(gratingDef)
        if (length(grating)<iii)
            grating(iii) = ApodizedContraDC;
        end
        if ~grating(iii).hasSameDef(gratingDef(iii))
            grating(iii)=gratingDef(iii);
        end
    end
end


%%
%%Calculation Updater
gratingsToCompute=amplitudeToPlot;

%Choose which gratings to calculate [TIME INTENSIVE PART]

for iii=gratingsToCompute
    if isempty(grating(iii).Lambda)
        grating(iii)=grating(iii).update;
    end
end


%%
noRef=max([max(gratingsToCompute) amplitudeToPlot]); 

wav=(grating(noRef).Lambda)*1e9;

figure1=figure;  %Figure parameters
textSizeSmall=14;
textSizeLarge=16;
axes1 = axes('Parent',figure1);
box(axes1,'on');
hold(axes1,'all');
xlabel('Wavelength [nm]','fontsize',textSizeSmall,'FontName', 'Times New Roman');
ylabel('Response [dB]','fontsize',textSizeSmall,'FontName', 'Times New Roman');


% Plot single filters
for iii=amplitudeToPlot
    %plot(wav,grating(iii).drop,'displayname', cat(2, grating(iii).name),'LineWidth',2);
    %plot(wav,grating(iii).thru,'displayname', cat(2, grating(iii).name),'LineWidth',2);
    plot(wav,grating(iii).drop,'displayname', 'Drop','LineWidth',2);
    plot(wav,grating(iii).thru,'--','displayname', 'Thru','LineWidth',2);
end


%=== Axis and Legend ===
%startWL=1500;
%endWL=1600;
%xlim([startWL endWL]);
%ylim([-40 4.5]);
legend1=legend('show');
set(legend1,'FontSize',12,'FontName','Times New Roman','box','on',...
   'Location','NorthEast');
%======================
%set(gcf,'Position',[1250,100,600,400]);
%set(gcf,'Position',[1050,50,800,600]);
hold off;



%%
%PHASE INFORMATION
for iii=phaseToPlot
    grating(iii).plotGroupDelay;
end

%%
%Apod Profile
for iii=apodProfileToPlot
    grating(iii).plotKappa;
end

%%
%BANDWIDTH INFORMATION
for ii=printBW
    disp(cat(2,'== ',grating(ii).name,' =='));
    for dBdrops=[1 20]
        BW=bandw(grating(ii).Lambda,grating(ii).drop,dBdrops); %calculates the BW
        fprintf('%1$ 3ddB: %2$ 6.2f nm / %3$ 8.2f GHz \n',dBdrops,BW(1)*1e9,BW(2)/1e9);
        bandwi2(dBdrops)=BW(2);
        if ( dBdrops==1)
            bandwi(ii)=BW(1)*1e9; %storing 1dB BW for analytics
        end
    end
    disp(cat(2,' Efficiency: ',num2str(bandwi2(1)./bandwi2(20),'% 4.3f') ));
end




