function BW = bandw(wav,Amp,dBs)
    %BW:  [bandwidth in m , bandwidth in Hz, central wavelenght in m]
    %wav: vector of wavelenghts
    %Amp: vector of corresponding amplitudes, in dB
    %dBs: decrease in dB to be considered out of band
    %
    %Assumes a bell-like shape
    [centerValue,centerIndex]=max(Amp);
    isInBand=Amp>centerValue-dBs;
    
    leftBound=centerIndex;
    while (isInBand(leftBound)==1)
        leftBound=leftBound-1;
    end
    rightBound=centerIndex;
    while (isInBand(rightBound)==1)
        rightBound=rightBound+1;
    end
    
    c = 299792458;  %[m/s]
    topFreq=c./wav(leftBound);
    lowFreq=c./wav(rightBound);
    BW=[wav(rightBound)-wav(leftBound) topFreq-lowFreq (wav(rightBound)+wav(leftBound))/2];
end