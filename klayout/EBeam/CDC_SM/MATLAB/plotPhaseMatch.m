%ob = grating;
neff_a_data=ob.neffwg1+ob.Dneffwg1.*(ob.Lambda);
neff_b_data=ob.neffwg2+ob.Dneffwg2.*(ob.Lambda);
neff_avg_data =  (neff_b_data+neff_a_data)/2;
Lambda_data_left=ob.Lambda;
Lambda_data_right=ob.Lambda;

%% Calculate phase match condition
tolerence = 0.001;

PhaseMatch = ob.Lambda/(2*ob.period);
PhaseMatchLambda = ob.Lambda(find(abs(PhaseMatch - neff_avg_data)<tolerence));
midIndex = round(size(PhaseMatchLambda)/2); midIndex = midIndex(1,2);
PhaseMatchLambda = PhaseMatchLambda(midIndex);

%% Plot
figure; hold on;
title('Phase match coniditon for the contra-DC')
xlabel('Wavelength (nm)')
ylabel('Effective Index')

plot(ob.Lambda*1e9, neff_a_data,'LineWidth',1);
plot(ob.Lambda*1e9, neff_b_data,'LineWidth',1);
plot(ob.Lambda*1e9, neff_avg_data,'LineWidth',2);
plot(ob.Lambda*1e9, PhaseMatch,'--','LineWidth',2);
line([PhaseMatchLambda*1e9, PhaseMatchLambda*1e9],[0,10],'Color','black','LineStyle','--')
xlim([ob.starting_wavelength,ob.ending_wavelength])
ylim([min(neff_avg_data)-.1,max(neff_avg_data)+.1])
legend('Waveguide 1 Effective Index', 'Waveguide 2 Effective Index', 'Average effective index', 'Phase matching coniditon','Contra-coupling wavelength')
set(gca,'FontSize',20)
set(gca,'FontName','Times New Roman')