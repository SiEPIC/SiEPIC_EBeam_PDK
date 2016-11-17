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

FONTSIZE = 13;  % font size for the figures;

% Identify the name of the Device Under Test.
deviceName = 'Spiral waveguide (TM)';
% At what wavelength do you want to find out the Loss of the DUT
lambda0 = 1.55e-6;

% matrix of measurement data files, and # of components in each
files = { ...
    'LukasC_SpiralWG0kTM_1293.mat', ...
    'LukasC_SpiralWG5kTM_1296.mat', ...
    'LukasC_SpiralWG10kTM_1294.mat', ...
    'LukasC_SpiralWG30kTM_1295.mat' ...
    };
% number of DUTs in each circuit:
Num = [ 0, 0.5, 1.0, 3.0 ];
PORT=2;  % fibre measurement configuration; detector number.

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

% Plot all the raw data, and also curve-fit each to a polynomial
figure;
LegendText={};
for i=1:length(files)
    load(files{i});                             % Load the data
    lambda = scandata.wavelength';              % wavelength
    amplitude(:,i) = scandata.power(:,PORT);    % detector data
    plot (lambda*1e6, amplitude(:,i)); hold all;
    
    % Curve-fit data to a polynomial
    p=polyfit((lambda-mean(lambda))*1e6, amplitude(:,i), 4);
    amplitude_poly(:,i)=polyval(p,(lambda-mean(lambda))*1e6);
    plot (lambda*1e6, amplitude_poly(:,i), 'LineWidth',2);
    
    % legend entries
    LegendText(2*i-1)=cellstr(['raw data: ' strrep(files{i},'_','\_')]);
    LegendText(2*i)=cellstr(['fit data: ' strrep(files{i},'_','\_')]);
end
title (['Optical spectra for the ' deviceName ' test structures']);
xlabel ('Wavelength (nm)');
ylabel ('Optical Power (dBm)');
legend (LegendText,'Location','South');
axis tight;
set(gca,'FontSize',FONTSIZE)

% least-squares linear regression of the Loss values vs. number
% of DUTs, at lambda0, to find the slope, A(2), and y-intercept, A(1)
% The slope, A(2), is the Loss for one DUT
[c index] = min(abs(lambda-lambda0));  % find lambda0 in lambda vector.
A = [ ones(length(Num),1) Num'] \ amplitude_poly(index,:)';
figure;
plot (Num, amplitude(index,:),'x'); hold all;
plot (Num, amplitude_poly(index,:),'o', 'MarkerSize',7);
plot (Num, A(1) + Num*A(2),'LineWidth',3)
legend ('raw data at lambda0', 'polyfit of raw data', ...
    'linear regression of polyfit');
xlabel ('Waveguide length (cm)');
ylabel ('Loss (dB/cm)');
title (['Cut-back method, ' deviceName ' Loss, at ' num2str(lambda0*1e9) ' nm'] )
set(gca,'FontSize',FONTSIZE)

% Calculate the slope error, +/- dB, with a 95% confidence interval
if Error_Intervals
    [b, bint] = regress(amplitude_poly(index,:)', [Num' ones(numel(Num),1)]);
    SlopeError95CI = diff(bint (1,:))/2;
    InterceptError95CI = diff(bint (2,:))/2;
    a=annotation('textbox', [.2 .2 .1 .1], 'String', ...
        {['Fit results, with 90% confidence intervals: '], ...
        ['slope is = ',num2str(A(2),'%0.2g') ' +/- ' ...
        num2str(SlopeError95CI,'%.01g') ' dB/cm'], ...
        ['intercept is = ',num2str(A(1),'%0.3g') ' +/- ' ...
        num2str(InterceptError95CI,'%.02g') ' dB'] ...
        });
    set(a,'FontSize',FONTSIZE);
    disp (['Cut-back method, ' deviceName ' Loss, at ' ...
        num2str(lambda0*1e9) ' nm is = ',num2str(-A(2),'%0.2g') ' +/- ' ...
        num2str(SlopeError95CI,'%.01g') ' dB/cm'])
else
    disp 'Skipping fitting error estimations'
    annotation('textbox', [.2 .2 .1 .1], 'String', ...
        {['Fit results: '], ...
        ['slope is = ',num2str(A(2),'%0.2g') ' dB/cm'], ...
        ['intercept is = ',num2str(A(1),'%0.3g') ' dB'] ...
        });
    disp (['Cut-back method, ' deviceName ' Loss, at ' ...
        num2str(lambda0*1e9) ' nm is = ',num2str(-A(2),'%0.2g') ' dB/cm'])
end



% wavelength dependance of the DUT Loss
% perform a linear regression at each wavelength, using the raw data
C = [ ones(length(Num),1) Num'] \ amplitude';

figure
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
ylabel ('Loss (dB/cm)');
xlabel ('Wavelength (nm)');
set(gca,'FontSize',FONTSIZE)
     
      