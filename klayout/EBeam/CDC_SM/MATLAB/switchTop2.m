%Function: switchTop2
%Takes a 4*4 matrix and switch the first 2 inputs with first 2 outputs, ex:
%
%   [A          [E
%    B  =   P    F
%    C           G
%    D]          H]
%
%   [E          [A
%    F  =   H    B
%    C           G
%    D]          H]

function H = switchTop2(P)
    if (~isequal(size(P),[4 4]))
        error('Matrix not 4*4');
    end
    P_FF=[P(1, 1), P(1, 2); P(2, 1), P(2, 2)];
    P_FG=[P(1, 3), P(1, 4); P(2, 3), P(2, 4)];
    P_GF=[P(3, 1), P(3, 2); P(4, 1), P(4, 2)];
    P_GG=[P(3, 3), P(3, 4); P(4, 3), P(4, 4)];
    H=[P_FF-P_FG*P_GG^-1*P_GF, P_FG*P_GG^-1; -P_GG^-1*P_GF, P_GG^-1];
end
%Reference: Wei Shi, Silicon photonic grating-assisted contra-directional
%couplers, Optics Express 3633 , 2013