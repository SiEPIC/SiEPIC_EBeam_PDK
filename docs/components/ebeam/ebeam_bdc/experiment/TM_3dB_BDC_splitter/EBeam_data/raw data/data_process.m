clear;

%%
filtername = 'zqluBDCMZI_A9B2_9C1_7Width500Test*.mat';
all_files = glob(filtername);
size_files = size(all_files,1);

for ii=1:1:size_files
    file_string=char(all_files(ii,1));
    [pathstr,name,ext] = fileparts(all_files{ii});


load(file_string);
Device_P1 = rot90(scandata.power(:,2));
wavelength = scandata.wavelength(1,:)*1e9;


D_P1 = Device_P1;


[pks_min,locs] = findpeaks(-D_P1,'minpeakdistance',15);
wavelength_valley = wavelength(locs);
pks_min=-pks_min;

sizevalley_min = size(locs(1,:));
sizevalley_min = sizevalley_min(1,2);

[pks_max,locs] = findpeaks(D_P1,'minpeakdistance',15);
wavelength_peak = wavelength(locs);
sizepeak_min = size(locs(1,:));
sizepeak_min = sizepeak_min(1,2);

N = min(sizevalley_min,sizepeak_min);
pks_min = pks_min(1,1:N);
pks_max = pks_max(1,1:N);
wavelength_peak = wavelength_peak(1,1:N);
wavelength_valley = wavelength_valley(1,1:N);

fit_max = interp1(wavelength_peak,pks_max,wavelength,'spline');
fit_min = interp1(wavelength_valley,pks_min,wavelength,'spline');


ER = fit_max - fit_min;
ER_linear = 10.^(ER/10);

  Kappa2 = 0.5*(1-1./sqrt(ER_linear));
  t2 = 1 - Kappa2;
  Kappa2_DB = 10*log10(Kappa2);
  t2_DB = 10*log10(t2);
  IM = abs(t2_DB - Kappa2_DB);
  

%
lambda = 1.5:0.001:1.6;
temp=-3*ones(1,101);

%%  %%%%%%%

figure
hold on
plot(wavelength, D_P1,'linewidth',1.5);
plot(wavelength, fit_max,'--k','linewidth',1);
plot(wavelength, fit_min,'-.k','linewidth',1);
box on
axis([1500 1600 -45 0.5]);
%plot(wavelength_peak,pks_max,'*');
%plot(wavelength_valley,pks_min,'o');
xlabel('Wavelength (nm)','FontSize',24,'FontWeight','bold');
ylabel('Transmission (dB)','FontSize',24,'FontWeight','bold');
hd1=legend('Spectrum','Maxima envelope','Minima envelope','Location','Best');
set(hd1, 'FontSize', 22);
set(gca, 'FontName', 'Arial');
set(gca, 'FontSize', 22);
fig = gcf;
fig.PaperPositionMode = 'auto';
fig_pos = fig.PaperPosition;
fig.PaperSize = [fig_pos(3) fig_pos(4)]; 
%saveas(gcf,'BDC_MZI_spectrum.pdf'); 


figure
box on
hold on
axis([1500 1600 0 100]);
plot(wavelength,Kappa2*100,'r','linewidth',1.5);
plot(wavelength,t2*100,'--','linewidth',1.5);
hd1 = legend('Cross','Through','Location','Best');
xlabel('Wavelength (\mum)','FontSize',24,'FontWeight','bold');
ylabel('Coupling ratios (%)','FontSize',24,'FontWeight','bold');
hd1 = legend('Cross-coupling (extracted)','Through-coupling (extracted)','Location','SouthEast');
set(hd1, 'FontSize', 22);
set(gca, 'FontName', 'Arial');
set(gca, 'FontSize', 22);
set(gca, 'XTick', [1500:20:1600]);
set(gca, 'YTick', [0:10:100]);
fig = gcf;
fig.PaperPositionMode = 'auto';
fig_pos = fig.PaperPosition;
fig.PaperSize = [fig_pos(3) fig_pos(4)]; 
saveas(gcf,[name,'_extracted.pdf']); 


%close all;

end