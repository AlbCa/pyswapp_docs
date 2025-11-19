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
    chi2 = np.sum(error_weighted_misfit**2)
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

    nm = A.shape[1]

    # first-order finite difference operator
    G = np.zeros((nm - 1, nm))
    for i in range(nm - 1):
        G[i, i] = 1
        G[i, i + 1] = -1

    # weighted least squares matrices
    ATW = A.T @ w
    Ni = ATW @ A  # data term
    Mi = G.T @ G  # smoothness term

    # solve (Ni + λ² Mi) m = Aᵀ W dφ
    rhs = ATW @ dphi

    Mreg = Ni + (lam ** 2) * Mi
    m = np.linalg.solve(Mreg, rhs)

    # m is dφ/dx = (ω/c)
    omega = 2 * np.pi * f

    # avoid division by zero
    eps = 1e-12
    m = np.where(np.abs(m) < eps, eps, m)

    phi_vel = -omega / m  # (nrec - 1)
    phi_model = A @ m  # predicted phase differences

    return phi_vel, phi_model
