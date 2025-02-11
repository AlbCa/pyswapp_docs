import numpy as np

# %% helper functions for inversion
def linear_LSQR(x,y,w=None):
    """estimate coefficients of a line y = k*x+phi0"""

    if w is None:
        W = np.diag(np.ones(len(x)))
    else:
        W = np.diag(w) # weighted LSQR

    A = np.vstack([-x, np.ones(len(x))]).T # design matrix

    N = np.transpose(A) @ W @ A
    beta = np.linalg.inv(N) @ np.transpose(A)@ W @ y

    k = beta[0]
    phi0 = beta[1]

    return k, phi0

def phase_response(x, k, phi0):
    """return the phase"""
    return -k * x + phi0


def compute_chi2(data, resp, error):
    """compute rms and chi^2"""
    misfit = data - resp
    error_weighted_misfit = np.abs(misfit) / error

    rms = np.sqrt(np.mean(np.abs(misfit) ** 2))
    rrms = np.sqrt(np.mean((np.abs(misfit)/np.abs(data)) ** 2))
    chi2 = np.mean(error_weighted_misfit ** 2)
    return rms, rrms, chi2


def tomo2D_phasediff(lam,f,A,dphi,w):
    """
    Tomographic like approach (Barone et al., 2019)

    Parameters
    ----------
    lam : int, regularization strength
    f : float, frequency value of the analysis
    A : np.ndarray, design matrix
    dphi : np.ndarray, phase differences
    w : np.ndarray, weight matrix

    Returns
    -------
    phi_vel: np.ndarray, phase velocities
    phi_model: np.ndarray, phase model
    """

    nm = len(A[0,:]) # corresponds to number of receivers
    G = np.zeros((nm-1,nm)) # first-order differential operator
    for i in range(nm-1):
        G[i,i] = 1
        G[i,i+1] = -1

    Ni = np.transpose(A) @ w @ A
    Mi = np.transpose(G) @  G

    m = np.linalg.inv(Ni + lam ** 2 * Mi) @ np.transpose(A) @ w @ dphi

    phi_vel = -2*np.pi*f/m
    phi_model = A@m

    return phi_vel, phi_model
