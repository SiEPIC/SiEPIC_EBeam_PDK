function wg_loss_analysis (files,polarization,filetype_wg_loss)
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

% calculate error confidence intervals?
% check if regress function is present. This is part of the statistics toolbox.
Error_Intervals = exist('regress');

dB_threshold = -50; % minimum dB, average over the data, to use data.
Loss_unit = 'dB/cm';

% filetype_wg_loss = 'LukasC_SpiralWG';

MAKE_PLOTS = 1;
FONTSIZE = 13;  % font size for the figures;

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
    printfig(FIG)
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
    printfig(FIG)
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
    printfig(FIG)
end
