import numpy as np
import scipy, scipy.interpolate
from . import  utils

def dasmtx(SIG : np.ndarray, x: np.ndarray, z: np.ndarray, *varargin):
    """
    %DASMTX   Delay-and-sum matrix
    %   M = DASMTX(SIG,X,Z,DELAYS,PARAM) returns the numel(X)-by-numel(SIG)
    %   delay-and-sum DAS matrix. The matrix M can be used to beamform SIG (RF
    %   or I/Q signals) at the points specified by X and Z.
    %
    %   Try it: enter "dasmtx" in the command window for an example.
    %
    %   Because the signals in SIG are NOT required (only its size is needed)
    %   to create M, the following syntax is recommended:
    %       M = DASMTX(size(SIG),X,Z,DELAYS,PARAM)
    %   !IMPORTANT! -- With this syntax, use M = DASMTX(1i*size(SIG),...) to
    %   return a complex DAS matrix for I/Q data.
    %
    %   NOTE: SIG must be a 2-D or 3-D array (the 3rd dimension is ignored).
    %         Or, size(SIG) must be a two- or three-component vector (the 3rd
    %         component is ignored). The first dimension (i.e. each column)
    %         corresponds to a single RF or I/Q signal over (fast-) time, with
    %         COLUMN #k corresponding to ELEMENT #k.
    %
    %   DASMTX returns the same results as DAS.
    %       1) using DAS:
    %           bfSIG = das(SIG,x,z,delays,param,method);
    %       2) using DASMTX:
    %           M = dasmtx(size(SIG),x,z,delays,param,method);
    %           bfSIG = M*SIG(:);
    %           bfSIG = reshape(bfSIG,size(x));
    %
    %   DELAYS are the transmit time delays (in s). The number of elements in
    %   DELAYS must be the number of elements in the array (which is equal to
    %   size(SIG,2)). If a sub-aperture was used during transmission, use
    %   DELAYS(i) = NaN if element #i of the linear array was off.
    %
    %   PARAM is a structure that contains the parameter values required for
    %   DAS beamforming (see below for details).
    %
    %   M is a large sparse matrix. Computing M can be much more cost-effective
    %   than using DAS if you need to beamform several SIG matrices, because
    %   M needs to be determined only once.
    %
    %   Let us consider that a series SIG{1}, SIG{2} ... SIG{N} of ultrasound
    %   matrices have been generated by sending similar wavefronts with the
    %   same array. These signals SIG{i} are stacked in a 3D array sig3D so
    %   that sig3D(:,:,i) = SIG{i}. To beamform these data with a delay-and-sum
    %   approach, the following can be used:
    %       M = dastmtx([size(sig3D,1) size(sig3D,2)],x,z,delays,param);
    %       % (or M = dastmtx(1i*[size(sig3D,1) size(sig3D,2)],...) for I/Q data)
    %       bfSIG3D = M*reshape(sig3D,[],size(sig3D,3));
    %       bfSIG3D = reshape(bfSIG3D,size(x,1),size(x,2),[]);
    %
    %   You can also consider saving the DAS matrix M in a MAT file and loading
    %   it when needed. The previous syntax is much faster than:
    %       for k = 1:N
    %           bfSIG{k} = das(SIG{k},x,z,delays,param);
    %       end
    %
    %   DASMTX(SIG,X,Z,PARAM) uses DELAYS = param.TXdelay.
    %
    %   DASMTX(...,METHOD) specifies the interpolation method. The available
    %   methods are decribed in NOTE #3 below.
    %
    %   [M,PARAM] = DASMTX(...) also returns the structure PARAM with the
    %   default values.
    %
    %   ---
    %   NOTE #1: X- and Z-axes
    %   The migrated signals are calculated at the points specified by (X,Z).
    %   Conventional axes are used:
    %   i) For a LINEAR array, the X-axis is PARALLEL to the transducer and
    %      points from the first (leftmost) element to the last (rightmost)
    %      element (X = 0 at the CENTER of the transducer). The Z-axis is
    %      PERPENDICULAR to the transducer and points downward (Z = 0 at the
    %      level of the transducer, Z increases as depth increases).
    %   ii) For a CONVEX array, the X-axis is parallel to the chord and Z = 0
    %       at the level of the chord.
    %   ---
    %   NOTE #2: DASMTX uses a standard delay-and-sum.
    %   ---
    %   NOTE #3: Interpolation methods
    %   By default DASMTX uses a linear interpolation to generate the DAS
    %   matrix. To specify the interpolation method, use DASMTX(...,METHOD),
    %   with METHOD being:
    %      'nearest'   - nearest neighbor interpolation
    %      'linear'    - (default) linear interpolation
    %      'quadratic' - quadratic interpolation
    %      'lanczos3'  - 3-lobe Lanczos (windowed sinc) interpolation
    %      '5points'   - 5-point least-squares parabolic interpolation
    %      'lanczos5'  - 5-lobe Lanczos (windowed sinc) interpolation
    %
    %   The linear interpolation (it is a 2-point method) returns a matrix
    %   twice denser than the nearest-neighbor interpolation. It is 3, 4, 5, 6
    %   times denser for 'quadratic', 'lanczos3', '5points', 'lanczos5',
    %   respectively (they are 3-to-6-point methods).
    %   ---
    %
    %   PARAM is a structure that contains the following fields:
    %   -------------------------------------------------------
    %   1)  PARAM.fs: sampling frequency (in Hz, REQUIRED)
    %   2)  PARAM.pitch: pitch of the transducer (in m, REQUIRED)
    %   3)  PARAM.fc: center frequency (in Hz, REQUIRED for I/Q signals)
    %   4)  PARAM.radius: radius of curvature (in m, default = Inf, linear array)
    %   5)  PARAM.TXdelay: transmission delays (in s, required if DELAYS is not given)
    %   6)  PARAM.c: longitudinal velocity (in m/s, default = 1540 m/s)
    %   7)  PARAM.t0: start time for reception (in s, default = 0 s)
    %
    %   A note on the f-number
    %   ----------------------
    %   The f-number is defined by the ratio (depth)/(aperture size). A null
    %   f-number (PARAM.fnumber = 0) means that the full aperture is used
    %   during DAS-beamforming. This might be a suboptimal strategy since the
    %   array elements have some directivity.
    %
    %   Use PARAM.fnumber = [] to obtain an "optimal" f-number, which is
    %   estimated from the element directivity (and depends on fc, bandwidth,
    %   element width):
    %
    %   8)  PARAM.fnumber: reception f-number (default = 0, i.e. full aperture)
    %   9)  PARAM.width: element width (in m, REQUIRED if PARAM.fnumber = [])
    %        or PARAM.kerf: kerf width (in m, REQUIRED if PARAM.fnumber = [])
    %        note: width = pitch-kerf
    %   10) PARAM.bandwidth: pulse-echo 6dB fractional bandwidth (in %)
    %            The default is 75% (used only if PARAM.fnumber = []).
    %
    %   Advanced option for vector Doppler (Reception angle):
    %   ---------------------------------------------------
    %   11) PARAM.RXangle: reception angles (in rad, default = 0)
    %       This option can be used for vector Doppler. Beamforming with at
    %       least two (sufficiently different) reception angles enables
    %       different Doppler directions and, in turn, vector Doppler.
    %
    %   Passive imaging
    %   ---------------
    %   12) PARAM.passive: must be true for passive imaging (i.e. no transmit).
    %       The default is false.
    %
    %
    %   REFERENCES:
    %   ----------
    %   1) If you use DAS or DASMTX, please cite:
    %      V Perrot, M Polichetti, F Varray, D Garcia. So you think you can
    %      DAS? A viewpoint on delay-and-sum beamforming. Ultrasonics 111,
    %      106309. <a
    %      href="matlab:web('https://www.biomecardio.com/publis/ultrasonics21.pdf')">PDF here</a>
    %   2) If you use PARAM.RXangle for vector Doppler, please also cite:
    %      Madiena C, Faurie J, Porée J, Garcia D. Color and vector flow
    %      imaging in parallel ultrasound with sub-Nyquist sampling. IEEE Trans
    %      Ultrason Ferroelectr Freq Control, 2018;65:795-802. <a
    %      href="matlab:web('https://www.biomecardio.com/publis/ieeeuffc18a.pdf')">PDF here</a>
    %
    %
    %   Example:
    %   -------
    %   %-- Generate RF signals using a phased-array transducer
    %   % Phased-array @ 2.7 MHz:
    %   param = getparam('P4-2v');
    %   % TX time delays (80-degree-wide diverging wave)
    %   dels = txdelay(param,0,80/180*pi);
    %   % Scatterers' position:
    %   xs = [(-1:0.5:1)*4e-2 zeros(1,5)];
    %   zs = [ones(1,5)*6e-2 (2:2:10)*1e-2];
    %   % Backscattering coefficient
    %   BSC = [ones(1,9) 0];
    %   % RF signals:
    %   param.fs = 4*param.fc; % sampling frequency
    %   RF = simus(xs,zs,BSC,dels,param);
    %   % Plot the RF signals
    %   subplot(121)
    %   plot((RF(:,1:7:64)/max(RF(:))+(1:10)*2)',...
    %      (0:size(RF,1)-1)/param.fs*1e6,'k')
    %   set(gca,'XTick',(1:10)*2,'XTickLabel',int2str((1:7:64)'))
    %   title('RF signals')
    %   xlabel('Element number'), ylabel('time (\mus)')
    %   xlim([0 22]), axis ij
    %
    %   %-- Demodulation and beamforming
    %   % Demodulation
    %   IQ = rf2iq(RF,param);
    %   % Beamforming 256x128 80-degrees wide polar grid
    %   [x,z] = impolgrid([256 128],9e-2,80/180*pi,param);
    %   % DAS matrix and beamformed IQ
    %   Mdas = dasmtx(1i*size(IQ),x,z,dels,param);
    %   IQb = reshape(Mdas*IQ(:),size(x));
    %   % Beamformed image
    %   subplot(122)
    %   pcolor(x*100,z*100,abs(IQb).^.5)
    %   colormap(gray)
    %   title('Gamma-compressed image')
    %   xlabel('[cm]'), ylabel('[cm]')
    %   shading interp, axis equal ij tight
    %
    %
    %   This function is part of <a
    %   href="matlab:web('https://www.biomecardio.com/MUST')">MUST</a> (Matlab UltraSound Toolbox).
    %   MUST (c) 2020 Damien Garcia, LGPL-3.0-or-later
    %
    %   See also DAS, DASMTX3, SIMUS, TXDELAY, RF2IQ, GETPARAM.
    %
    %   -- Damien Garcia -- 2017/10, last update 2022/05/06
    %   website: <a
    %   href="matlab:web('http://www.biomecardio.com')">www.BiomeCardio.com</a>

    %
    %   PARAM can also contain the "elements" field:
    %   -------------------------------------------
    %   13) PARAM.elements: coordinates of the transducer elements (in m)
    %       PARAM.elements must contain the x- (and optionally z-) coordinates
    %       of the transducer elements. It must be a vector (or a matrix with 2
    %       rows or 2 columns) corresponding to the x- (and optionally z-)
    %       coordinates, respectively.
    %       
    """



    #%------------------------%
    #% CHECK THE INPUT SYNTAX %
    #%------------------------%

    NArg = len(varargin) +3
    assert NArg>3,'Not enough input arguments.'
    assert NArg<7,'Too many input arguments.'
    #% assert(nargout<3,'Too many output arguments.')

    assert x.shape == z.shape,'X and Z must of same size.'
    if  np.prod(SIG.shape) in [2, 3]:
        SIG = SIG.flatten()
        nl = int(abs(SIG[0]))
        nc = int(abs(SIG[1]))
    else:
        nl,nc = SIG.shape[0], SIG.shape[1]


    #% check if we have I/Q signals
    isIQ = utils.iscomplex(SIG)

    #%-- Check input parameters
    if isinstance(varargin[-1], str):
        method = varargin[NArg - 1]
        NArg = NArg-1
    else:
        method = 'linear'
        NArg = NArg


    if NArg==4: #% DASMTX(SIG,x,z,param)
        if isinstance(varargin[0], utils.Param):
            param = varargin[0]
            param.ignoreCaseInFieldNames()
        else:
            raise ValueError('The structure PARAM is required.')

        assert utils.isfield(param,'TXdelay'), 'A TX delay vector (PARAM.TXdelay or DELAYS) is required.'
        delaysTX = param.TXdelay

    else: #% NArg=5: #DASMTX(SIG,x,z,delaysTX,param)
        delaysTX = varargin[0]
        param = varargin[1]
        assert isinstance(param, utils.Param), 'The structure PARAM is required.'
        param.ignoreCaseInFieldNames()

        if utils.isfield(param,'TXdelay'): #% DASMTX(SIG,x,z,delaysTX,param)
            assert np.allclose(delaysTX.flatten(), param.TXdelay.flatten()),'If both specified, PARAM.TXdelay and DELAYS must be equal.'



    #%-- Interpolation method
    if method.lower() not in ['nearest','linear','quadratic','lanczos3','5points','lanczos5']:
        raise ValueError('METHOD must be ''nearest'', ''linear'', ''quadratic'', ''Lanczos3'', ''5points'' or ''Lanczos5''.')


    #%-- Propagation velocity (in m/s)
    if not utils. isfield(param,'c'):
        param.c = 1540; #% longitudinal velocity in m/s


    #%-- Sampling frequency (in Hz)
    if param.get('fs', None) is None:
        raise ValueError('A sampling frequency (PARAM.fs) is required.')

    #%-- f-number
    if not utils.isfield(param,'fnumber'):
        param.fnumber = 0; #% f-number (default = full aperture)
    elif param.get('fnumber', 'None') is None:
        # do nothing:
        # The f-number will be determined automatically
        pass
    else:
        assert np.isscalar(param.fnumber) and utils.isnumeric(param.fnumber), 'If not empty, PARAM.fnumber must be a scalar.'
        assert param.fnumber>=0, 'PARAM.fnumber must be non-negative.'


    #%-- Acquisition start time (in s)
    if not utils.isfield(param,'t0'):
        param.t0 = np.zeros((1,1)) #% acquisition start time in s


    #%-- Pitch & width or kerf (in m)
    if not utils.isfield(param,'pitch'):
        raise ValueError('A pitch value (PARAM.pitch) is required.')

    if param.get('fnumber', None) is None:
        #% NOTE:
        #% An element width or a kerf width is required if the f-number is []
        if utils.isfield(param,'width') and utils.isfield(param,'kerf'):
            assert abs(param.pitch-param.width-param.kerf)<utils.eps(), 'The pitch must be equal to (kerf width + element width).'
        elif utils.isfield(param,'kerf'):
            param.width = param.pitch-param.kerf
        elif utils.isfield(param,'width'):
            param.kerf = param.pitch-param.width
        else:
            raise ValueError('An element width (PARAM.width) or kerf width (PARAM.kerf) is required if PARAM.fnumber = [].')

        ElementWidth = param.width


    #%-- -6dB bandwidth (in %)
    if not utils.isfield(param,'bandwidth'):
        param.bandwidth = 75

    if param.get('fnumber', None) is None:
        assert param.bandwidth>0 and param.bandwidth<200, 'The fractional bandwidth at -6 dB (PARAM.bandwidth, in %) must be in ]0,200['


    #%-- Radius of curvature (in m)
    #% for a convex array
    if not utils.isfield(param,'radius'):
        param.radius = np.inf #% default = linear array

    RadiusOfCurvature = param.radius
    isLINEAR = np.isinf(RadiusOfCurvature)

    #%-- Reception angle (in rad) -- [Advanced option for vector Doppler] --
    if not utils.isfield(param,'RXangle') or param.RXangle==0:
        isRXangle = False
        param.RXangle = 0
    else:
        #%- this option is not available for convex arrays
        assert np.isinf(RadiusOfCurvature), 'PARAM.RXangle must be 0 with a convex array.'
        #%-
        isRXangle = True
        cosRX = np.cos(param.RXangle)
        tanRX = np.tan(param.RXangle)
        if np.isscalar(param.RXangle):
            cosRX = cosRX*np.ones(x.shape)
            tanRX = tanRX*np.ones(x.shape)



    #%-- Passive imaging
    if not utils.isfield(param,'passive'):
        param.passive = False
    else:
        assert utils.islogical(param.passive), 'PARAM.passive must be a boolean (false or true)'


    #%-- Number of elements
    if delaysTX.shape[0] == nc and delaysTX.shape[1] != nc:
        delaysTX = delaysTX.T

    assert delaysTX.shape[1]==nc, 'DELAYS and/or PARAM.TXdelay must be vectors of length size(SIG,2).'
    #% Note: param.Nelements can be required in other functions of the
    #%       Matlab Ultrasound Toolbox
    if utils.isfield(param,'Nelements'):
        assert param.Nelements==nc, 'PARAM.TXdelay or DELAYS must be of length PARAM.Nelements.'


    #%-- Locations of the transducer elements (!if PARAM.elements is given!)
    if utils.isfield(param,'elements'):
        assert len(param.elements.shape) == 2 and (1 in param.elements.shape or 2 in param.elements.shape), \
        'PARAM.elements must be a vector, a 2-row or a 2-column matrix that contains the x- (and optionally z-)locations of the transducer elements.'
        if param.elements.shape[0] ==2:
            #% param.elements is a two-row matrix
            xe = param.elements[0, :]
            ze = param.elements[1, :]
        elif param.elements.shape[1 ]==2:
            #% param.elements is a two-column matrix
            xe = param.elements[:, 0]
            ze = param.elements[:, 1]
        else:
            #% param.elements is a vector
            xe = param.elements.reshape((1,-1))
            ze = np.zeros_like(xe)

        isPARAMelements = True
    else:
        isPARAMelements = False


    #%-- Center frequency (in Hz)
    if isIQ:
        if utils.isfield(param,'fc'):
            if utils.isfield(param,'f0'):
                assert abs(param.fc-param.f0)<utils.eps(), \
                    'A conflict exists for the center frequency: PARAM.fc and PARAM.f0 are different!'

        elif utils.isfield(param,'f0'):
            param.fc = param.f0 #% Note: param.f0 can also be used
        else:
            raise ValueError('A center frequency (PARAM.fc) is required with I/Q data.')
        
        wc = 2*np.pi*param.fc



    #%-------------------------------%
    #% end of CHECK THE INPUT SYNTAX %
    #%-------------------------------%



    #%-- Centers of the tranducer elements (x- and z-coordinates)
    xe, ze, THe, h = param.getElementPositions()

    #% note: THe = angle of the normal to element #e with respect to the z-axis


    #% some parameters
    fs = param.fs #% sampling frequency
    c = param.c   #% propagation velocity


    #% Interpolations of the TX delays for a better estimation of dTX
    idx = np.logical_not(np.isnan(delaysTX))
    assert np.sum(np.abs(np.diff(idx)))<3, 'Several simultaneous sub-apertures are not allowed.'

    if not param.passive:
        nTX = np.count_nonzero(idx)#; % number of transmitting elements
        if nTX>1:
            idxi = np.linspace(0,nTX -1,4*nTX)
            xTi = utils.interp1(xe[idx], idxi, kind = 'cubic')
            if isLINEAR:
                zTi = np.zeros_like(xTi)
            else:
                zTi = utils.interp1(ze[idx], idxi,'spline')
            delaysTXi = utils.interp1(delaysTX[idx],idxi,'spline')
        else:
            xTi = xe[idx]
            if isLINEAR:
                zTi =np.zeros_like(idx)
            else: 
                zTi = ze[idx]
            delaysTXi = delaysTX[idx]


    #%-- f-number (determined automatically if not given)
    #% The f-number is determined from the element directivity
    #% See the paper "So you think you can DAS?"
    if param.get('fnumber', None) is None:
        lambdaMIN = c/(param.fc*(1+param.bandwidth/200))
        RXa = abs(param.RXangle)
        #% Note: in Matlab, sinc(x) = sin(pi*x)/(pi*x)
        f = lambda th,width= ElementWidth,l= lambdaMIN: np.abs(np.cos(th+RXa)*np.sinc(width/l*np.sin(th+RXa))-0.71)

        x = scipy.optimize.fminbound(f,0,np.pi/2-RXa,tolx= np.pi/100)
        alpha = x.xopt
        param.fnumber = 1/2/np.tan(alpha)

    fNum = param.fnumber


    t0 = param.t0
    x = x.reshape((-1,1), order = 'F')
    z = z.reshape((-1,1), order = 'F')

    #%----
    #% Migration - diffraction summation (Delay & Sum, DAS)
    #%----

    #%-- TX distances
    #% For a given location [x(k),z(k)], one has:
    #% dTX(k) = min(delaysTXi*c + sqrt((xTi-x(k)).^2 + (zTi-z(k)).^2));
    #% In a compact matrix form, this yields:
    if not param.passive:
        dTX = np.min(delaysTXi*c + np.sqrt((xTi-x)**2 + (zTi-z)**2), 1).reshape((-1,1))
    else:
        dTX = np.zeros_like(x)


    #%-- RX distances
    #% For a given location [x(k),z(k)], one has:
    #% dRX(k) = sqrt((xT-x(k)).^2 + (zT-z(k)).^2);
    #% In a compact matrix form, this yields:
    dxT = x-xe
    dzT = z-ze
    dRX = np.sqrt(dxT**2 + dzT**2)

    #%-- Travel times
    tau = (dTX+dRX)/c

    #%-- Corresponding fast-time indices
    idxt = (tau-t0.reshape((1, -1)))*fs
    idxt = idxt.astype(np.float64) #% in case tau is in single precision

    #%-- In-range indices:
    method = method.lower()  
    if method == 'nearest':
        I = np.logical_and(idxt>=0, idxt<=nl - 1)
    elif method == 'linear':
        I = np.logical_and(idxt>=0, idxt<=nl -2 )
    elif method == 'quadratic':
        I = np.logical_and(idxt>=0, idxt<=nl -3 )
    elif method == 'lanczos3':
        I = np.logical_and(idxt>=0, idxt<=nl -3 )
    elif method == '5points':
        I = np.logical_and(idxt>=0, idxt<=nl -3 )
    elif method == 'lanczos5':
        I = np.logical_and(idxt>=0, idxt<=nl -4 )
    else:
        raise ValueError('Unknown interpolation method: %s' % method)

    #%-- Aperture (using the f-number):
    if fNum>0:
        if not isRXangle:
            if np.isfinite(RadiusOfCurvature):
                #% -- for a convex array
                Iaperture = np.abs(np.arcsin(dxT/dRX)-THe)<=np.arctan(1/2/fNum)
            else:
                #% -- for a linear array
                #% For a given location [x(k),z(k)], one has:
                #% Iaperture = abs(xT-x(k)) <= z(k)/2/fNum;
                Iaperture = np.abs(dxT)<=(z/2/fNum)
                #% Iaperture = mean(abs(dxT),1)<=(z/2/fNum);


        else: #% [Advanced option for vector Doppler: Reception angle]
            #% -- ONLY for a rectilinear array
            #% For a given location [x(k),z(k)], one has:
            #% Iaperture = abs(xT-x(k)-z(k)*tanRX(k)) <= z(k)/cosRX(k)/2/fNum;
            Iaperture = np.abs(dxT-z.tanRX.flatten())<=(z/cosRX.flatten()/2/fNum)

        I = np.logical_and(I,Iaperture)

    #I = np.asfortranarray(I)
    #% subscripts to linear indices (instead of using SUB2IND)
    idx_matrix = idxt + np.arange(nc).reshape((1, -1))*nl
    j, i = np.where(I.T) # GB: This weird inverion is to make sure that the ordering is consistent with matlab
    idx = np.take(idx_matrix, np.ravel_multi_index([i,j], I.shape)) 
    tau_I = np.take(tau, np.ravel_multi_index([i,j], I.shape))
    idxf = np.floor(idx).astype(int)
    idx = idx-idxf


    #%-- Let's fill in the sparse DAS matrix
    if method == 'nearest':
        j = np.round(idx).astype(int)
        s = np.ones_like(i)
        n_repeat = 1
            
    elif method == 'linear': #%-- Linear interpolation (2-point method)            
        #%-- DAS matrix
        j = np.concatenate([idxf, idxf+1])
        s = np.concatenate([-idx+1,  idx])
        n_repeat = 2
    elif method == 'quadratic': #%-- quadratic interpolation (3-point method)

        #%-- DAS matrix
        j = np.concatenate([idxf, idxf+1, idxf+2])
        s = np.concatenate([(idx-1)*(idx-2)/2,
            -idx*(idx-2),
            idx*(idx-1)/2])        
        n_repeat = 3
    elif method ==  'lanczos3': #%-- 3-lobe Lanczos interpolation (4-point method)
        j = np.concatenate([idxf-1, idxf, idxf+1, idxf+2])
        s = np.concatenate([np.sinc(idx+1)*np.sinc((idx+1)/2),
            np.sinc(idx)*np.sinc(idx/2),
            np.sinc(idx-1)*np.sinc((idx-1)/2),
            np.sinc(idx-2)*
            np.sinc((idx-2)/2)])
        n_repeat = 4
    elif method == '5points': #%-- 5-point least-squares parabolic interpolation  
        j =  np.concatenate([idxf-2, idxf-1, idxf, idxf+1, idxf+2])
        idx2 = idx**2
        s *= np.concatenate([1/7*idx2-1/5*idx-3/35,
            -1/14*idx2-1/10*idx+12/35,
            -1/7*idx2+17/35,
            -1/14*idx2+1/10*idx+12/35,
            1/7*idx2+1/5*idx-3/35])
        n_repeat = 5
    elif method == 'lanczos5': #%-- 5-lobe Lanczos interpolation (6-point method)
        j = np.concatenate([idxf-2, idxf-1, idxf, idxf+1, idxf+2, idxf+3])
        s = np.concatenate([np.sinc(idx+2)*np.sinc((idx+2)/2),
            np.sinc(idx+1)*np.sinc((idx+1)/2),
            np.sinc(idx)*np.sinc(idx/2),
            np.sinc(idx-1)*np.sinc((idx-1)/2),
            np.sinc(idx-2)*np.sinc((idx-2)/2),
            np.sinc(idx-3)*np.sinc((idx-3)/2)])
        n_repeat = 6

    i = np.tile(i, n_repeat)
    if isIQ:
        s = np.exp(1j*wc*np.tile(tau_I, n_repeat)) * s

    if utils.isfield(param,'TransposeDASMatrix'):
            #% -- DASMTX has been called by the function DAS --
            #%
            #% The smallest DAS matrix (in terms of memory) is returned.
            #% (Matlab stores sparse matrices in compressed sparse column format)
            if len(x)>nl*nc:
                param.TransposeDASMatrix = False
                M = scipy.sparse.coo_matrix((s,(i,j)), shape = (len(x),nl*nc))
                #% M is a [numel(x)]-by-[nl*nc] sparse matrix
            else:
                param.TransposeDASMatrix = True
                M = scipy.sparse.coo_matrix((s,(j,i)),shape = (nl*nc, len(x)))
                #% M is a [nl*nc]-by-[numel(x)] sparse matrix
    else:
        M = scipy.sparse.coo_matrix((s,(i,j)), shape= (len(x),nl*nc))
            #% M is a [numel(x)]-by-[nl*nc] sparse matrix
    return M #TODO: maybe use another type of sparse matrix will be more efficient