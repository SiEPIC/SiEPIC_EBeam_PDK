
% Process Control Module (PCM) experimental data analysis and report
% generation
% SiEPIC PDK, www.github.com/lukasc-ubc/SiEPIC_EBeam_PDK
% Copyright 2016, Lukas Chrostowski

function PCM_analysis

global FONTSIZE MAKE_PLOTS lambda0 folder_name report_filename

%%%%%%%%%%%%%%%%%%%%%
% User configuration:
%%%%%%%%%%%%%%%%%%%%%

MAKE_PLOTS = 1;
FONTSIZE =  13; % font size for the figures;

% Script will process all experimental data from the following folder, and
% write a report PDF file here.
%folder_name = uigetdir('','Select root folder for the experimental data')
folder_name = '/Users/lukasc/SiEPIC_EBeam_PDK/PCM/D2016_10_ANT';

% polarization definitions:
polarizations = {'TE', 'TM'};

% filename conventions for each PCM:
filetype_wg_loss = 'LukasC_SpiralWG';  % replace with PCM_Spiral
UncertaintyMax_wg_loss = 30;

% At what wavelength do you want to find out the Loss of the DUT
lambda0 = 1.55e-6;

%%%%%%%%%%%%%%%%%%%%%%

close all;

% write a report PDF file here:
[pathstr,name,ext] = fileparts(folder_name);
report_filename = [folder_name '/' name '_PCM_report']
system(['rm ' report_filename '*.pdf' ]);

fid = fopen([report_filename '.txt'],'w');
fprintf(fid,'%s\n\n','Report for Silicon Photonics chip, Process Control Module');
% fprintf(fid,'%s\n\n\n',['Chip ID: ' CHIPID, ', ' num2str(NUM) ' devices']);
fprintf(fid,'%s\n',  '*************************');
fclose(fid);

% find all the sub-folders
[~,list]=system(['find ' folder_name ' -type d ']);


%%%%%%%%%%%%%%%%%%%%%%
% waveguide propagation loss
Table_WG_Loss=table;
% find all the PCM files, and iterate through all the folders
[~,files]=system(['find ' folder_name ' -type f -name \*' filetype_wg_loss '\*.mat ']);
files=strsplit(files);
folders = [];
for i=1:length(files)
    f=cell2mat(files(i));
    [pathstr,name,ext] = fileparts(f);
    folders = [folders; pathstr];
end
folders = unique(folders,'rows');
count=0;
for i = 1:size(folders,1)
    folder = folders(i,:);
    for pol = 1:length(polarizations)
        polarization = char(polarizations(pol));
        [~,files] = system( ['find ' folder ' -type f -name \*' ...
            filetype_wg_loss '\*' polarization '\*.mat '] );
        files=strsplit(files); files={files{~cellfun(@isempty,files)}};
        [Loss, SlopeError95CI, Loss_unit] = wg_loss_analysis(files,polarization,filetype_wg_loss);
        if SlopeError95CI < UncertaintyMax_wg_loss
            T=table;
            T.Name = categorical({strrep(folder,folder_name,'')});
            T.Loss = Loss;
            T.err = categorical({'+/-'});
            T.Uncertainty = SlopeError95CI;
            T.Unit = categorical({Loss_unit});
            T.Polarization = categorical({polarization});
            Table_WG_Loss = [Table_WG_Loss;T];
        end
    end
end
T=Table_WG_Loss(Table_WG_Loss.Polarization=='TE',:)
if size(T)>0
    LOG('');
    LOG('Spiral waveguid propagation loss, TE:');
    LOG(regexprep(evalc('disp(T)'),'<.*?>',''));  % convert table to plain text
    LOG(['Mean TE: ' num2str(mean(T.Loss)) ' ' char(T.Unit(1))]);
    LOG('');
end
T=Table_WG_Loss(Table_WG_Loss.Polarization=='TM',:)
if size(T) >0
    LOG('');
    LOG('Spiral waveguid propagation loss, TM:');
    LOG(regexprep(evalc('disp(T)'),'<.*?>',''));  % convert table to plain text
    LOG(['Mean TM: ' num2str(mean(T.Loss)) ' ' char(T.Unit(1))  ]);
    LOG('');
end

system(['a2ps -o - ' report_filename '.txt'  '  | ps2pdf - ' report_filename '_000.pdf']);
system (['gs -q -sPAPERSIZE=letter -dNOPAUSE -dBATCH -sDEVICE=pdfwrite -sOutputFile=' report_filename '.pdf ' report_filename '_*.pdf'])
system ([ 'rm ' report_filename '_*.pdf' ] );
system ([ 'rm ' report_filename '*.txt' ] );
system(['open ' report_filename '.pdf '])

end

function LOG(text)
global report_filename
% write text to a file
fid = fopen([report_filename '.txt'],'a');
fprintf(fid,'%s\n',text);
%fprintf(fid,'%s\n\n','Report for Silicon Photonics chip, Process Control Module');
% fprintf(fid,'%s\n\n\n',['Chip ID: ' CHIPID, ', ' num2str(NUM) ' devices']);
%fprintf(fid,'%s\n',  '*************************');
%fprintf(fid,'%s\n\n','*** Figure captions: ***');
%writetable(Table_WG_Loss, '/tmp/t.txt,'Delimiter',' ')
fclose(fid);
end

function printfig (b)
% print figure to a PDF file and crop.
global PRINT_titles FONTSIZE folder_name report_filename;
%fid = fopen('AlignGC1_Ring_titles.txt','a');
%fprintf(fid,'%s\n\n',['Fig. ' num2str(gcf) ': ' get(get(gca,'title'),'String')]);
%fclose(fid);
set(get(gca,'xlabel'),'FontSize',FONTSIZE);
set(get(gca,'ylabel'),'FontSize',FONTSIZE);
set(get(gca,'title'),'FontSize',FONTSIZE-5);
set(gca,'FontSize',FONTSIZE-2);
if PRINT_titles==0
    delete(get(gca,'title'))
end
g=gcf; 

pdf = [report_filename '_' num2str(g.Number,'%03.0f') b ];
print ('-dpdf','-r300', pdf);
system([ '/Library/TeX/texbin/pdfcrop ' pdf ' ' pdf '.pdf  > /dev/null' ]);
%system(['acroread ' pdf '.pdf &']);
%system('open -n /Applications/Utilities/Terminal.app')

% need to modify MATLAB startup script:
% http://www.mathworks.com/matlabcentral/newsreader/view_thread/255609
%/Applications/ImageMagick-6.8.9/bin:/opt/local/bin:/opt/local/sbin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:/opt/X11/bin:/Library/TeX/texbin:/usr/texbin/

end

function [Loss, SlopeError95CI, Loss_unit] = wg_loss_analysis (files,polarization,filetype_wg_loss)
% This script analyzes experimental data to determine the Loss
% of a device under test (DUT), e.g., YBranch, using the cut-back method.
% The layout is several (e.g., 4) circuits each consisting of N devices in
% series, where N ranges from a small number (e.g., 0) to a large number.  The
% large number is chosen as a trade-off between the layout size and a
% value that gives an excess Loss of about 10 dB.  For example,
% if the DUT is estimated to have an Loss of 0.3 dB, we would
% choose the largest value of N to be 10 dB / 0.24 dB = 42.

% To find the Loss, we plot the measured Loss versus
% the number of DUTs in the circuit.  Then we perform a linear regression,
% and the slope tells us the Loss for one DUT.

global FONTSIZE MAKE_PLOTS lambda0

% calculate error confidence intervals?
% check if regress function is present. This is part of the statistics toolbox.
Error_Intervals = exist('regress');

dB_threshold = -50; % minimum dB, average over the data, to use data.
Loss_unit = 'dB/cm';

% filetype_wg_loss = 'LukasC_SpiralWG';

% Identify the name of the Device Under Test.
deviceName = ['Spiral waveguide (' polarization ')'];

% At what wavelength do you want to find out the Loss of the DUT
%lambda0 = 1.55e-6;

% matrix of measurement data files, and # of components in each
if ~exist(files{1},'file')
    files = { ...
        'LukasC_SpiralWG0kTM_1293.mat', ...
        'LukasC_SpiralWG5kTM_1296.mat', ...
        'LukasC_SpiralWG10kTM_1294.mat', ...
        'LukasC_SpiralWG30kTM_1295.mat' ...
        };
end

%PORT=2;  % fibre measurement configuration; detector number.

% Load data from Dropbox:
if ~exist(files{1})
    disp 'Loading files from Dropbox'
    url = { ...
        'https://www.dropbox.com/s/anlo8zmydrji1f8/LukasC_SpiralWG0kTM_1293.mat', ...
        'https://www.dropbox.com/s/yvdfgl8qoq3d0fz/LukasC_SpiralWG5kTM_1296.mat', ...
        'https://www.dropbox.com/s/rossgslht5r5cq7/LukasC_SpiralWG10kTM_1294.mat', ...
        'https://www.dropbox.com/s/vj4uf6u59h9vt60/LukasC_SpiralWG30kTM_1295.mat' ...
        };
    for i=1:length(files)
        a=websave(files{i},url{i},'dl', '1'); % get data from Dropbox
    end
else
    %    disp 'Loading files from local disk'
end

% determine which PORT is used, by finding the port with the highest power
% in all measurements
powers = [];
for i=1:length(files)
    load(files{i});                             % Load the data
    powers(end+1,:) = mean(scandata.power);
end
mean(powers); [~,i]=max(powers);
PORT=i(1);

% find data that has high-enough power measured:
m = find(powers(:,PORT) > dB_threshold);
files = {files{m}};

% extract the length of spiral from the filename
%Num = [ 0, 0.5, 1.0, 3.0 ];
Num = [];
for i = 1:length(files)
    [pathstr,name,ext] = fileparts(files{i});
    name = strrep(name,filetype_wg_loss,'');
    n = strtok(name,polarization);
    if strfind(n,'k')
        n = strtok(name,'k');
        n = [n '000'];
    end
    Num(i) = str2num(n) / 1e4;  % cm
end


% Plot all the raw data, and also curve-fit each to a polynomial
if MAKE_PLOTS; FIG=figure; end
LegendText={}; amplitude=[]; amplitude_poly=[];
for i=1:length(files)
    load(files{i});                             % Load the data
    lambda = scandata.wavelength';              % wavelength
    amplitude(:,i) = scandata.power(:,PORT);    % detector data
    if MAKE_PLOTS
        plot (lambda*1e6, amplitude(:,i)); hold all;
    end
    
    % Curve-fit data to a polynomial
    p=polyfit((lambda-mean(lambda))*1e6, amplitude(:,i), 4);
    amplitude_poly(:,i)=polyval(p,(lambda-mean(lambda))*1e6);
    
    if MAKE_PLOTS
        plot (lambda*1e6, amplitude_poly(:,i), 'LineWidth',2);
        % legend entries
        LegendText(2*i-1)=cellstr(['raw data: ' strrep(files{i},'_','\_')]);
        LegendText(2*i)=cellstr(['fit data: ' strrep(files{i},'_','\_')]);
    end
    
end
if MAKE_PLOTS
    title (['Optical spectra for the ' deviceName ' test structures']);
    xlabel ('Wavelength (nm)');
    ylabel ('Optical Power (dBm)');
    legend (LegendText,'Location','South');
    axis tight;
    set(gca,'FontSize',FONTSIZE)
    printfig('')
end

% least-squares linear regression of the Loss values vs. number
% of DUTs, at lambda0, to find the slope, A(2), and y-intercept, A(1)
% The slope, A(2), is the Loss for one DUT
[c index] = min(abs(lambda-lambda0));  % find lambda0 in lambda vector.
A = [ ones(length(Num),1) Num'] \ amplitude_poly(index,:)';
Loss = -A(2);
if MAKE_PLOTS
    FIG=figure;
    plot (Num, amplitude(index,:),'x'); hold all;
    plot (Num, amplitude_poly(index,:),'o', 'MarkerSize',7);
    plot (Num, A(1) + Num*A(2),'LineWidth',3)
    legend ('raw data at lambda0', 'polyfit of raw data', ...
        'linear regression of polyfit');
    xlabel ('Waveguide length (cm)');
    ylabel (['Loss (' Loss_unit ')']);
    title (['Cut-back method, ' deviceName ' Loss, at ' num2str(lambda0*1e9) ' nm'] )
    set(gca,'FontSize',FONTSIZE)
    printfig('')
end

% Calculate the slope error, +/- dB, with a 95% confidence interval
if Error_Intervals
    [b, bint] = regress(amplitude_poly(index,:)', [Num' ones(numel(Num),1)]);
    SlopeError95CI = diff(bint (1,:))/2;
    InterceptError95CI = diff(bint (2,:))/2;
    if MAKE_PLOTS
        a=annotation('textbox', [.2 .2 .1 .1], 'String', ...
            {['Fit results, with 90% confidence intervals: '], ...
            ['slope is = ',num2str(A(2),'%0.2g') ' +/- ' ...
            num2str(SlopeError95CI,'%.01g') ' ' Loss_unit], ...
            ['intercept is = ',num2str(A(1),'%0.3g') ' +/- ' ...
            num2str(InterceptError95CI,'%.02g') ' dB'] ...
            });
        set(a,'FontSize',FONTSIZE);
    end
    disp (['Cut-back method, ' deviceName ' Loss, at ' ...
        num2str(lambda0*1e9) ' nm is = ',num2str(Loss,'%0.2g') ' +/- ' ...
        num2str(SlopeError95CI,'%.01g') ' ' Loss_unit])
else
    disp 'Skipping fitting error estimations'
    if MAKE_PLOTS
        
        annotation('textbox', [.2 .2 .1 .1], 'String', ...
            {['Fit results: '], ...
            ['slope is = ',num2str(A(2),'%0.2g') ' ' Loss_unit], ...
            ['intercept is = ',num2str(A(1),'%0.3g') ' dB'] ...
            });
    end
    disp (['Cut-back method, ' deviceName ' Loss, at ' ...
        num2str(lambda0*1e9) ' nm is = ',num2str(Loss,'%0.2g') ' ' Loss_unit])
    SlopeError95CI=inf;
end



% wavelength dependance of the DUT Loss
% perform a linear regression at each wavelength, using the raw data
C = [ ones(length(Num),1) Num'] \ amplitude';

if MAKE_PLOTS
    
    FIG=figure;
    if Error_Intervals
        % perform a linear regression at each wavelength, using the polyfit data
        slope=[]; slope_int=[];
        lambda_downsampled = lambda(1:100:end);
        amplitude_poly_downsampled = amplitude_poly (1:100:end,:);
        for i=1:length(lambda_downsampled)
            [b, bint] = regress(amplitude_poly_downsampled(i,:)', ...
                [Num' ones(numel(Num),1)]);
            slope(i)=b(1);
            slope_int(i,:)=bint(1,:);
        end
        % Plot the 95% confidence interval as a shaded region. It is based on the
        % polyfit fit results
        X=[lambda_downsampled; flip(lambda_downsampled)]*1e6;
        Y=[slope_int(:,1); flip(slope_int(:,2))];
        fill(X,-Y,[0.7 1 1],'LineStyle','none');  hold all;
        
        % plot the linear regression results from the polyfit data
        plot(lambda_downsampled*1e6, -slope', 'b', 'LineWidth',3);
        
        % plot the linear regression results from the raw data
        plot(lambda*1e6, -[C(2,:)']); hold all;
        legend ( 'Loss, 95% Confidence Interval', ...
            'Loss, from polyfit', ...
            'Loss, from Raw data', ...
            'Location','Best' )
    else
        % perform a linear regression at each wavelength, using the polyfit data
        D = [ ones(length(Num),1) Num'] \ amplitude_poly';
        plot(lambda*1e6, -[D(2,:)' C(2,:)']); hold all;
        legend ( 'Loss, from polyfit', ...
            'Loss, from Raw data', ...
            'Location','Best' )
    end
    axis tight; yl=ylim;
    ylim ([0, yl(2)]);
    title (['Cut-back method, ' deviceName ...
        ' Loss, wavelength dependance'] )
    ylabel (['Loss (' Loss_unit ' )']);
    xlabel ('Wavelength (nm)');
    set(gca,'FontSize',FONTSIZE)
    printfig('')
end
end
