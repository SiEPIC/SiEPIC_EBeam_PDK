
% Process Control Module (PCM) experimental data analysis and report
% generation
% SiEPIC PDK, www.github.com/lukasc-ubc/SiEPIC_EBeam_PDK
% Copyright 2016, Lukas Chrostowski

function PCM_analysis

global FONTSIZE MAKE_PLOTS lambda0 folder_name folder_name_linux report_filename report_filename_linux

%%%%%%%%%%%%%%%%%%%%%
% User configuration:
%%%%%%%%%%%%%%%%%%%%%

MAKE_PLOTS = 1;
FONTSIZE =  13; % font size for the figures;

% Script will process all experimental data from the following folder, and
% write a report PDF file here.
%folder_name = uigetdir('','Select root folder for the experimental data')

%folder_name = '/Users/lukasc/Dropbox (SiEPIC)/EBeam_PCM/D2015_10';
%folder_name = '/Users/lukasc/Dropbox (SiEPIC)/EBeam_PCM/D2016_02_UW';
%folder_name = '/Users/lukasc/Dropbox (SiEPIC)/EBeam_PCM/test';
%folder_name = '/Users/lukasc/Dropbox (SiEPIC)/EBeam_PCM/D2016_05';
%folder_name = '/Users/lukasc/Dropbox (SiEPIC)/EBeam_PCM/D2016_07';
%folder_name = '/Users/lukasc/Dropbox (SiEPIC)/EBeam_PCM/D2016_08_ANT';
%folder_name = '/Users/lukasc/Dropbox (SiEPIC)/EBeam_PCM/D2016_10_ANT';
folder_name = '/Users/lukasc/Dropbox (SiEPIC)/EBeam_PCM/D2017_01_02_ANT';
folder_name = '/Users/lukasc/Dropbox (SiEPIC)/EBeam_PCM/D2017_01_02_UW';

folder_name_linux = regexprep (folder_name,'\s|)|(', '\\$0');
%system(['ls ' folder_name_linux  ]);


% polarization definitions:
polarizations = {'TE', 'TM'};

% filename conventions for each PCM:
filetype_wg_loss = 'LukasC_SpiralWG';
filetype_wg_loss = 'PCM_PCM_SpiralWG';
filetype_wg_lossN = {'PCM_PCM_SpiralWG', 'PCM_PCM_StraightWGloss'};
filetype_wg_loss_descriptions = {'Spiral waveguide propagation loss', 'Straight waveguide propagation loss'};
UncertaintyMax_wg_loss = 50;

% At what wavelength do you want to find out the Loss of the DUT
lambda0 = 1.55e-6;

%%%%%%%%%%%%%%%%%%%%%%


close all;

% write a report PDF file here:
[pathstr,name,ext] = fileparts(folder_name);
report_filename = [folder_name '/' name '_PCM_report'];
report_filename_linux = regexprep (report_filename,'\s|)|(', '\\$0');
system(['rm ' report_filename_linux '*.pdf' ]);
fid = fopen([report_filename '.txt'],'w');
fprintf(fid,'%s\n\n','Report for Silicon Photonics chip, Process Control Module');
% fprintf(fid,'%s\n\n\n',['Chip ID: ' CHIPID, ', ' num2str(NUM) ' devices']);
fprintf(fid,'%s\n',  '*************************');
fclose(fid);

for ll = 1:length(filetype_wg_lossN)
    filetype_wg_loss = filetype_wg_lossN{ll};
    filetype_wg_loss_description = filetype_wg_loss_descriptions{ll};
    
    % find all the sub-folders
    [~,list]=system(['find ' folder_name_linux ' -type d ']);
    
    
    %%%%%%%%%%%%%%%%%%%%%%
    % waveguide propagation loss
    Table_WG_Loss=table;
    % find all the PCM files, and iterate through all the folders
    [~,files]=system(['find ' folder_name_linux ' -type f -name \*' filetype_wg_loss '\*.mat ']);
    files=regexp(files, '[\f\n\r]', 'split');
    %files=strsplit(files)
    %return;
    folders = {};
    for i=1:length(files)
        f=cell2mat(files(i));
        [pathstr,name,ext] = fileparts(f);
        folders{end+1} = pathstr;
    end
    folders = unique(folders);
    count=0;
    for i = 1:length(folders)
        folder = folders{i};
        if length(folder) > 0
            folder_linux = regexprep (folder,'\s|)|(', '\\$0');
            disp (['Folder: ' folder ]);
            for pol = 1:length(polarizations)
                polarization = char(polarizations(pol));
                [~,files] = system( ['find ' folder_linux ' -type f -name \*' ...
                    filetype_wg_loss '\*' polarization '\*.mat '] );
                files=regexp(files, '[\f\n\r]', 'split'); files={files{~cellfun(@isempty,files)}};
                if length(files) > 0
                    [Loss, SlopeError95CI, Loss_unit] = wg_loss_analysis(files,polarization,filetype_wg_loss,filetype_wg_loss_description);
                    if SlopeError95CI < UncertaintyMax_wg_loss
                        T=table;
                        T.Name = categorical({strrep(folder,folder_name,'')});
                        T.Loss = Loss;
                        T.err = categorical({'+/-'});
                        T.CI95 = SlopeError95CI;
                        T.Unit = categorical({Loss_unit});
                        T.Pol = categorical({polarization});
                        Table_WG_Loss = [Table_WG_Loss;T];
                    end
                end
            end
        end
    end
    T=Table_WG_Loss(Table_WG_Loss.Pol=='TE',:)
    if size(T)>0
        LOG('');
        LOG([filetype_wg_loss_description ', TE:']);
        LOG(regexprep(evalc('disp(T)'),'<.*?>',''));  % convert table to plain text
        LOG(['Mean TE: ' num2str(mean(T.Loss)) ' ' char(T.Unit(1))]);
        LOG('');
    end
    T=Table_WG_Loss(Table_WG_Loss.Pol=='TM',:)
    if size(T) >0
        LOG('');
        LOG([filetype_wg_loss_description ', TM:']);
        LOG(regexprep(evalc('disp(T)'),'<.*?>',''));  % convert table to plain text
        LOG(['Mean TM: ' num2str(mean(T.Loss)) ' ' char(T.Unit(1))  ]);
        LOG('');
    end
end
system(['a2ps -o - ' report_filename_linux '.txt'  '  | ps2pdf - ' report_filename_linux '_000.pdf']);
system (['gs -q -sPAPERSIZE=letter -dNOPAUSE -dBATCH -sDEVICE=pdfwrite -sOutputFile=' report_filename_linux '.pdf ' report_filename_linux '_*.pdf']);
system ([ 'rm ' report_filename_linux '_*.pdf' ] );
system ([ 'rm ' report_filename_linux '*.txt' ] );
system(['open ' report_filename_linux '.pdf ']);

end

function LOG(text)
global report_filename
% write text to a file
fid = fopen([regexprep(report_filename,'\','') '.txt'],'a');
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
global PRINT_titles FONTSIZE folder_name report_filename report_filename_linux;
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
pdf_linux = [report_filename_linux '_' num2str(g.Number,'%03.0f') b ];
system([ '/Library/TeX/texbin/pdfcrop ' pdf_linux ' ' pdf_linux '.pdf  > /dev/null' ]);
%system(['acroread ' pdf '.pdf &']);
%system('open -n /Applications/Utilities/Terminal.app')

% need to modify MATLAB startup script:
% http://www.mathworks.com/matlabcentral/newsreader/view_thread/255609
%/Applications/ImageMagick-6.8.9/bin:/opt/local/bin:/opt/local/sbin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:/opt/X11/bin:/Library/TeX/texbin:/usr/texbin/

end

function [Loss, SlopeError95CI, Loss_unit] = wg_loss_analysis (files,polarization,filetype_wg_loss, filetype_wg_loss_description)
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

dB_threshold = -60; % minimum dB, average over the data, to use data.
dB_threshold_diff =-20;  % consider only data that is dB_threshold_diff below the peaks
Loss_unit = 'dB/cm';

% filetype_wg_loss = 'LukasC_SpiralWG';

% Identify the name of the Device Under Test.
deviceName = [filetype_wg_loss_description ' (' polarization ')'];

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
    disp 'Loading files from local disk'
end

% determine which PORT is used, by finding the port with the highest power
% in all measurements
powers_av = [];
for i=1:length(files)
    load(files{i});                             % Load the data
    powers_av(end+1,:) = mean(scandata.power);
    %    size(mean(scandata.power))
    %    size(scandata.power)
    %    size(max(smooth(scandata.power,101),2))
    %    powers(end+1,:) = max(smooth(scandata.power,101));
end
[~,i]=max(sum(powers_av,1));
PORT=i(1);

% find data that has high-enough power measured, smoothed max:
powers_max = [];
for i=1:length(files)
    load(files{i});                             % Load the data
    powers_max(i) = max(smooth(scandata.power(100:end-100,PORT),101));
    %figure;plot(smooth(scandata.power(:,PORT),101))
end
m = find(powers_max > dB_threshold);
files = {files{m}};

if length(files) > 0
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
    
    
    % load data, Plot all the raw data
    % find a zoomed in wavelength range, based on data above the noise
    min_lambda_index=0; max_lambda_index=inf;
    amplitude=[]; LegendText={};
    if MAKE_PLOTS; FIG=figure; end
    for i=1:length(files)
        load(files{i});                             % Load the data
        lambda = scandata.wavelength';              % wavelength
        amplitude(:,i) = scandata.power(:,PORT);    % detector data
        if MAKE_PLOTS
            plot (lambda*1e6, amplitude(:,i)); hold all;
            ax=gca;
            % legend entries
            LegendText(i)=cellstr(['Length: ' num2str(Num(i)) ' cm']);
            %            LegendText(i)=cellstr(['raw data: ' strrep(files{i},'_','\_')]);
        end
        ind=find(amplitude(:,i)> max(dB_threshold, max(amplitude(:,i))+dB_threshold_diff) );
        if min(ind) > min_lambda_index
            min_lambda_index = min(ind);
        end
        if max(ind) < max_lambda_index
            max_lambda_index = max(ind);
        end
    end
    ind = min_lambda_index:max_lambda_index;
    lambda_good = lambda(ind);  % wavelength range for which we will curve fit
    
    % curve-fit each to a polynomial
    amplitude_good=[]; amplitude_poly=[]; amplitude_poly_good=[];
    for i=1:length(files)
        %        load(files{i});                             % Load the data
        %       lambda = scandata.wavelength';              % wavelength
        %       amplitude(:,i) = scandata.power(:,PORT);    % detector data
        %        ind=find(amplitude(:,i)> max(dB_threshold, max(amplitude(:,i))+dB_threshold_diff) );
        %        ind=find(amplitude(:,i)> dB_threshold);
        amplitude_good(:,i) = amplitude(ind,i);
        %        lambda_good = lambda(ind);
        
        % Curve-fit data to a polynomial
        %        p=polyfit((lambda-mean(lambda))*1e6, amplitude(:,i), 4);
        p=polyfit((lambda_good-mean(lambda_good))*1e6, amplitude_good(:,i), 4);
        %        amplitude_poly(:,i)=polyval(p,(lambda-mean(lambda))*1e6);
        amplitude_poly_good(:,i)=polyval(p,(lambda_good-mean(lambda_good))*1e6);
        
        if MAKE_PLOTS
            %            plot (lambda*1e6, amplitude_poly(:,i), 'LineWidth',2);
            ax.ColorOrderIndex = i;
            plot (lambda_good*1e6, amplitude_poly_good(:,i), 'k--','LineWidth',4);
            % legend entries
            %            LegendText(2*i-1)=cellstr(['raw data: ' strrep(files{i},'_','\_')]);
            %            LegendText(2*i)=cellstr(['fit data: ' strrep(files{i},'_','\_')]);
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
    [c index_good] = min(abs(lambda_good-lambda0));  % find lambda0 in lambda vector.
    %    A = [ ones(length(Num),1) Num'] \ amplitude_poly(index,:)';
    A = [ ones(length(Num),1) Num'] \ amplitude_poly_good(index_good,:)';
    Loss = -A(2);
    if MAKE_PLOTS
        figure;
        plot (Num, amplitude(index,:),'x'); hold all;
        plot (Num, amplitude_poly_good(index_good,:),'o', 'MarkerSize',7);
        plot (Num, A(1) + Num*A(2),'LineWidth',3)
        legend ('raw data, at lambda0', 'polyfit of raw data, at lambda0', ...
            'linear regression of polyfit');
        xlabel ('Waveguide length (cm)');
        ylabel (['Loss (' Loss_unit ')']);
        title (['Cut-back method, ' deviceName ' Loss, at ' num2str(lambda0*1e9) ' nm'] )
        set(gca,'FontSize',FONTSIZE)
    end
    
    % Calculate the slope error, +/- dB, with a 95% confidence interval
    if Error_Intervals
        %[b, bint] = regress(amplitude_poly(index,:)', [Num' ones(numel(Num),1)]);
        [b, bint] = regress(amplitude_poly_good(index_good,:)', [Num' ones(numel(Num),1)]);
        SlopeError95CI = diff(bint (1,:))/2;
        InterceptError95CI = diff(bint (2,:))/2;
        if MAKE_PLOTS
            a=annotation('textbox', [.2 .2 .1 .1], 'String', ...
                {['Fit results, with 95% confidence intervals: '], ...
                ['slope is = ',num2str(A(2),'%3.3g') ' +/- ' ...
                num2str(SlopeError95CI,'%3.3g') ' ' Loss_unit], ...
                ['intercept is = ',num2str(A(1),'%0.3g') ' +/- ' ...
                num2str(InterceptError95CI,'%.3g') ' dB'] ...
                });
            set(a,'FontSize',FONTSIZE);
            printfig('')
        end
        disp (['Cut-back method, ' deviceName ' Loss, at ' ...
            num2str(lambda0*1e9) ' nm is = ',num2str(Loss,'%0.3g') ' +/- ' ...
            num2str(SlopeError95CI,'%.3g') ' ' Loss_unit])
    else
        disp 'Skipping fitting error estimations'
        if MAKE_PLOTS
            
            a=annotation('textbox', [.2 .2 .1 .1], 'String', ...
                {['Fit results: '], ...
                ['slope is = ',num2str(A(2),'%0.2g') ' ' Loss_unit], ...
                ['intercept is = ',num2str(A(1),'%0.3g') ' dB'] ...
                });
            set(a,'FontSize',FONTSIZE);
            printfig('')
        end
        disp (['Cut-back method, ' deviceName ' Loss, at ' ...
            num2str(lambda0*1e9) ' nm is = ',num2str(Loss,'%0.2g') ' ' Loss_unit])
        SlopeError95CI=inf;
    end
    
    
    
    % wavelength dependance of the DUT Loss
    % perform a linear regression at each wavelength, using the raw data
    C = [ ones(length(Num),1) Num'] \ amplitude_good';
    
    if MAKE_PLOTS
        
        FIG=figure;
        downsample_ratio=10;
        if Error_Intervals
            % perform a linear regression at each wavelength, using the polyfit data
            slope=[]; slope_int=[];
            lambda_downsampled = lambda_good(1:downsample_ratio:end);
            amplitude_poly_downsampled = amplitude_poly_good (1:downsample_ratio:end,:);
            %            lambda_downsampled = lambda(1:100:end);
            %            amplitude_poly_downsampled = amplitude_poly (1:100:end,:);
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
            plot(lambda_good*1e6, -[C(2,:)']); hold all;
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
else
    Loss=NaN;
    SlopeError95CI=NaN;
end

end
