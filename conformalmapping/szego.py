import numpy as np
from numpy.linalg import norm
from .closedcurve import *
from .helpers import *

class SzegoKernel(object):
    def __init__(self, curve, a, opts):
        N = opts.numCollPts

        dt = 1.0 / float(N)
        t = np.arange(0.0, 1.0, dt)
        z = curve.position(t)
        zt = curve.tangent(t)
        zT = zt / np.abs(zt)

        IpA = np.ones((N, N), dtype=np.complex)
        for i in xrange(1, N):
            cols = np.arange(i)
            zc_zj = z[cols] - z[i]

            tmp1 = np.conjugate(zT[i]/zc_zj)
            tmp2 = zT[cols]/zc_zj
            tmp3 = np.sqrt(np.abs(np.dot(zt[i], zt[cols])))
            tmp4 = (dt/(2.0j*np.pi))

            IpA[i, cols] = (tmp1 - tmp2) * tmp3 * tmp4
            IpA[cols, i] = -np.conjugate(IpA[i, cols])

        y = 1j * np.sqrt(np.abs(zt))/(2*np.pi) * np.conjugate(zT/(z -a))

        assert(opts.kernSolMethod in ['auto','bs'])
        assert( N < 2048 )

        x = np.linalg.solve(IpA, y)

        relresid = norm(y - np.dot(IpA, x)) / norm(y)
        if relresid > 100.0 * np.spacing(1):
            raise Exception('out of tolerance')

        # set output
        self.phiColl = x
        self.dtColl = dt
        self.zPts = z
        self.zTan = zt
        self.zUnitTan = zT


class SzegoOpts(object):
    def __init__(self):
        self.confCenter = 0.0 + 0.0j
        self.numCollPts  = 512
        self.kernSolMethod = 'auto'
        self.newtonTol = 10.0 * np.spacing(2.0*np.pi)
        self.trace = False
        self.numFourierPts = 256


class Szego(object):
    def __init__(self, curve = None, confCenter = 0.0 + 0.0j, 
                 opts = None, *args, **kwargs):

        if not isinstance( curve, ClosedCurve):
            raise Exception('Expected a closed curve object')

        self.curve = curve
        self.confCenter = confCenter

        if opts is None:
            opts = SzegoOpts()

        self.numCollPts = opts.numCollPts 

        kernel = SzegoKernel(curve, confCenter, SzegoOpts())
        self.phiColl = kernel.phiColl
        self.dtColl = kernel.dtColl
        self.zPts = kernel.zPts
        self.zTan = kernel.zTan
        self.zUnitTan = kernel.zUnitTan

        self.theta0 = np.angle(-1.0j * self.phi(0.0)**2 * self.curve.tangent(0))

    @suppress_warnings
    def kerz_stein(self, ts):
        t = np.asarray(ts).reshape(1, -1)[0, :]
        w = self.curve.position(t)
        wt = self.curve.tangent(t)
        wT = wt / np.abs(wt)

        z = self.zPts
        zt = self.zTan
        zT = self.zUnitTan
        
        separation = 10 * np.spacing(np.max(np.abs(z)))

        def KS_by_idx(wi, zi):
            """Array with k elements
            """
            z_w = z[zi] - w[wi]
            assert( z_w.shape == (self.numCollPts,) )
            tmp1 = wt[wi]*zt[zi]
            assert( not np.any(np.isnan(tmp1)) )
            assert( tmp1.shape == (self.numCollPts,) )
            tmp2 = np.abs(tmp1)
            assert( not np.any(np.isnan(tmp2)) )
            assert( tmp2.dtype == np.float )
            tmp3 = np.sqrt(tmp2)
            assert( not np.any(np.isnan(tmp3)) )
            tmp4 = (2j * np.pi)

            tmp5 = np.conjugate(wT[wi]/z_w)
            assert( not np.any(np.isnan(tmp5)) )
            tmp6 = zT[zi]/z_w
            assert( not np.any(np.isnan(tmp6)) )
            tmp7 = tmp5 - tmp6
            out = tmp3 / tmp4 * tmp7
            out[np.abs(z_w) < separation] = 0.0
            return out

        wis = np.arange(len(w))
        zis = np.arange(self.numCollPts)
        A = [ KS_by_idx(wi, zis) for wi in wis ]
        A = np.vstack(A)
        return A

    def phi(self, ts):
        ts = np.asarray(ts).reshape(1, -1)[0, :]
        v = self.psi(ts) - np.dot(self.kerz_stein(ts), self.phiColl) * self .dtColl
        return v

    def psi(self, ts):
        ts = np.asarray(ts).reshape(1, -1)[0, :]
        wt = self.curve.tangent(ts)
        xs = self.curve.point(ts) - self.confCenter
        y = 1.0j / (2*np.pi) / np.sqrt(np.abs(wt)) * np.conjugate(wt / xs)
        return y

    def theta(self):
        pass

    def invtheta(self):
        pass

    def thetap(self):
        pass

    def __str__(self):
        return 'Szego kernel object:\n\n'

        
