
%MZI*oneside2*

% Read data files from experiments, extract ng
% variables in MKS units.
function main()

clf; close all; format long; format compact;
global  PORT PRINT_titles FONTSIZE dL lambda0 n1 CHIPID

system('mkdir -p out; rm out/*.pdf');

DATA_SET = 1;

switch DATA_SET
  case 1
    datafolder ='DataSet1/';
    MAPfile = 'EB486A_URChip3Coords1.txt';
    PORT=1;  % Which Fibre array port is the output connected to?
		% Use this measurement to de-embed the response of the system and grating couplers
		FILE_LOOPBACK = 'ZiheGao_MZI1_272_Scan1.mat';
    CHIPID='EB486A';
%    PLOT_spectrum_list=6;  % optional: selective data analysis
end

PLOT_Loopback=1;
PLOT_Sims=0;
FONTSIZE=20;

% Map file listing all devices to read. Format:
% %<X-coord>,<Y-coord>,<Polarization>,<wavelength>,<type>,<deviceID>,<comment=waveguide length difference>
fid = fopen([datafolder MAPfile]);
MAPfile_data = textscan(fid, '%f%f%s%u%s%s%s','Delimiter',',','CommentStyle','%')
fclose(fid);
NUM=0; files={};
for i=1:length(MAPfile_data{1})
  file=cell2mat(MAPfile_data{6}(i));
  file=dir ([datafolder file '_*.mat']);
  if length(file)>0
    NUM=NUM+1;
    files{NUM}=file(1).name;
    files_label{NUM}=strrep(files{NUM},'_',' ');
    deltaL{NUM}=str2num(cell2mat(MAPfile_data{7}(i)));  % MZI waveguide length difference
  end
end

% Load calibration file, curve fit with a polynomial.  Use polynomial as calibration.
load ([datafolder FILE_LOOPBACK])
lambda=scanResults(1,PORT).Data(:,1)/1e9;
amplitude=scanResults(1,PORT).Data(:,2);
p=polyfit(lambda, amplitude, 5);
amplitude_LOOPBACK=polyval(p,lambda);
figure;
plot (lambda, [amplitude, amplitude_LOOPBACK]);
title ('Calibration loopback'); hold all;

% find wavelength range with usable data, in the loopback
loopback_IL = max(amplitude);
new_lambda_i=find(amplitude>loopback_IL-10);
lambda=lambda(new_lambda_i);
lambda_min = min(lambda);
lambda_max = max(lambda);
amplitude=amplitude(new_lambda_i);
% refit the loopback
LOOPBACK=polyfit(lambda, amplitude, 4);
amplitude_LOOPBACK=polyval(LOOPBACK,lambda);
plot (lambda, [amplitude_LOOPBACK],'r-','Linewidth',3);

FIG_ng=figure; FIG_ng.Position(1)=1; 
xlabel ('Wavelength [\mum]','FontSize',FONTSIZE)
ylabel ('Group Index','FontSize',FONTSIZE)
set (gca, 'FontSize',FONTSIZE)
xlim([min(lambda), max(lambda)]*1e6);

if ~exist('PLOT_spectrum_list')
  PLOT_spectrum_list=1:NUM;
end

ng_exp=[];  % store extracted experimental group index

for i=PLOT_spectrum_list
	% load data:
  load ([datafolder files{i}]);
  disp (files{i})
  lambda1=scanResults(1,PORT).Data(:,1)/1e9;
  amplitude=scanResults(1,PORT).Data(:,2);
  dL=deltaL{i}*1e-6;

  % check if there is no data on "PORT", try another port.
  if max(amplitude)<-40
    amplitude=scanResults(1,2).Data(:,2);
  end
  
  % data only within the bandwidth of interest.
	lambda=lambda_min:min(diff(lambda1)):lambda_max;
  amplitude=interp1(lambda1, amplitude, lambda,'linear');
  amplitude(find(amplitude==-inf))=-50;
  
  % calibrate data
  amplitude=amplitude-polyval(LOOPBACK,lambda);
  
  % plot spectrum
  FIG_spec=figure; FIG_spec.Position(3)=FIG_spec.Position(3)*2;
  FIG_spec.Position(1)=FIG_ng.Position(1)+FIG_ng.Position(3);
  plot (lambda*1e6, amplitude,'-','LineWidth',2); hold all
  drawnow;
  
  % save calibrated data:
  save (['out/' files{i}], 'amplitude', 'lambda');

  % FIND PEAKS, plot spectrum with peaks
  amplitude_smooth=smooth(amplitude, 0.001,'moving');
 	[pks,x_values,w,p]=findpeaks(-amplitude_smooth, lambda, 'minPeakProminence',4,'Annotate','extents');
  figure(FIG_spec);
  plot (x_values*1e6, interp1(lambda, amplitude, x_values,'cubic'), 'ro','MarkerSize',10)
  drawnow;
  
  % Calculate and plot ng data points from FSR
  lambda_ng = (x_values(1:end-1)+x_values(2:end))/2;
  FSR=(x_values(2:end)-x_values(1:end-1));
  ng = abs(lambda_ng.^2/1/dL./FSR);
  % find average ng from all reasonable ng values:
  ng_i = find (ng > 4); ng_i = find(ng(ng_i)<4.4); 
  ng_av = mean(ng(ng_i))

  figure(FIG_ng);
  plot (lambda_ng*1e6, ng, '-o','LineWidth',1,'MarkerSize',7 ); hold on;
  set(gca,'ColorOrderIndex',get(gca,'ColorOrderIndex')-1); % plot next line using the same color

	% find starting point for curve fitting, using the ng value
	lambda0 = x_values(floor(length(x_values)/2))
	n1_initial=2.4;
	modeNumber = n1_initial * dL / lambda0 - 0.5
	n1 = (2*floor(modeNumber)+1)*lambda0/2/dL
	n2 = (n1-ng_av)/lambda0/1e6
  figure(FIG_spec);
	plot (lambda0*1e6, -40,'s','MarkerSize',20);
	plot(lambda*1e6, T_MZI ( [ n2, 0, 1000, 0], lambda ), '--' );
	drawnow;
	
	% Curve fit:  
  x0 = [n2     0     1e2 0  ];
	lb = [n2-0.2 -1e2  1e0 -10];
	ub = [n2+0.2 1e2   1e6 30 ];
  options=optimset('Display','iter','TolFun',1e-14,'TolX',1e-12);
  [xfit,resnorm] = lsqcurvefit(@T_MZI,x0,lambda,amplitude,lb,ub,options);
	resnorm
	xfit

	% plot ng curve
  figure(FIG_ng);
	neff=n1 + xfit(1).*(lambda-lambda0)*1e6 + xfit(2).*(lambda-lambda0).^2*1e12;
  dndlambda=diff(neff)./diff(lambda); dndlambda=[dndlambda, dndlambda(end)];
	ng=(neff - lambda .* dndlambda);
	plot(lambda*1e6, ng, 'LineWidth',3);

	% waveguide parameters at lambda0
	ng0 = n1 - lambda0*xfit(1)*1e6; 	ng_exp(end+1)=ng0;
	c=299792458;	
	Dispersion0 = -lambda0 / c * 2*xfit(2)*1e12;  % [s/m^2]
	% [ps/nm/km]: 
	Dispersion0 = Dispersion0 * 1e12 /1e9 /1e-3   
  alpha_dBcm = xfit(4) * 10 * log10(exp(1))/100
	
  figure(FIG_spec);
  MZI_fit=T_MZI(xfit, lambda);
  plot(lambda*1e6, MZI_fit,'r'); drawnow;
  xlabel ('Wavelength [\mum]','FontSize',FONTSIZE)
  ylabel ('Transmission [dB]','FontSize',FONTSIZE)
  set (gca, 'FontSize',FONTSIZE);   axis tight
  title ({files_label{i}; 
	  ['Waveguide length difference [\mum]: ' num2str(dL*1e6) ]; 
	  ['Group index: ' num2str(ng0) ]; 
	  ['Disersion [ps/nm/km]: ' num2str(Dispersion0) ]; 
	  ['Waveguide Loss [dB/cm]: ' num2str(alpha_dBcm) ]; 
	  ['Excess loss [dB]: ' num2str(xfit(4)) ]; 
	  });
  printfig('');
    
end
figure(FIG_ng);
printfig('');

save t.mat

% Summary box plot:
figure;
G={}; % boxplot group labels
% load simulation data:
simfolder ='SimCorners/20_20/';
filebase_sim='wg_2D_neff_sweep_wavelength_';
file_sim=dir ([simfolder filebase_sim '*.mat']);
ng_sim=[];
for i=1:length(file_sim)
	load ([simfolder file_sim(i).name])
	ng_sim(end+1)=mean(ng);
	G{end+1}='Sim 20 nm'; 
end
simfolder ='SimCorners/10_10/';
file_sim=dir ([simfolder filebase_sim '*.mat']);
for i=1:length(file_sim)
	load ([simfolder file_sim(i).name])
	ng_sim(end+1)=mean(ng);
	G{end+1}='Sim 10 nm'; 
end
simfolder ='SimCorners/5_5/';
file_sim=dir ([simfolder filebase_sim '*.mat']);
for i=1:length(file_sim)
	load ([simfolder file_sim(i).name])
	ng_sim(end+1)=mean(ng);
	G{end+1}='Sim 5 nm'; 
end

box_data = [ng_sim ng_exp];
box_groups = [];
for j=1:length(ng_exp); 	G{end+1}='Exp.'; end;
boxplot(box_data, G);
xlabel ('Data set','FontSize',FONTSIZE)
ylabel ('Group Index','FontSize',FONTSIZE)
set (gca, 'FontSize',FONTSIZE-4)
printfig ('_boxplot')

end % function


% Transfer function for the MZI
% T_MZI ( n2, n3, alpha, excessLoss (/m)], lambda );
function F=T_MZI(x, lambda)
global dL lambda0 n1
L1=0;
L2=dL;
neff=n1 + x(1).*(lambda-lambda0)*1e6 + x(2).*(lambda-lambda0).^2*1e12;
dndlambda=diff(neff)./diff(lambda); dndlambda=[dndlambda, dndlambda(end)];
ng=(mean(neff - lambda .* dndlambda));
alpha=ones(1,length(lambda))*x(3);
beta = 2*pi*neff./lambda;
F = 0.25 * abs(exp(-1i.*beta*L1-alpha/2*L1)+exp(-1i.*beta*L2-alpha/2*L2) ).^2;
F = 10*log10(F)+x(4);
end


function printfig (b)
global FONTSIZE CHIPID;
set(get(gca,'xlabel'),'FontSize',FONTSIZE);
set(get(gca,'ylabel'),'FontSize',FONTSIZE);
set(get(gca,'title'),'FontSize',FONTSIZE-5);
set(gca,'FontSize',FONTSIZE-2);
f=gcf;
pdf = ['out/' CHIPID '_plot_'  num2str(f.Number,'%03.0f') b ];
print ('-dpdf','-r300', pdf);
system([ 'pdfcrop ' pdf ' ' pdf '.pdf &' ]);
end


