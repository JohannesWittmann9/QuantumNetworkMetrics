"""End-to-End Fidelity (Fe2e) metric for quantum networks.

Fidelity of the delivered entangled state as observed by the application,
independent of the generation mechanism.
"""

import numpy as np


def end_to_end_fidelity(delivered_state: np.ndarray, ideal_state: np.ndarray) -> float:
    """Calculate End-to-End Fidelity (Fe2e).
    
    Calculated as F = <ψ|ρ|ψ> where |ψ> is the ideal state and ρ is 
    the delivered density matrix.
    
    This follows the NetSquid convention of using squared fidelity.
    
    Parameters
    ----------
    delivered_state : np.ndarray
        The density matrix of the delivered state
    ideal_state : np.ndarray
        The state vector of the ideal target state
        
    Returns
    -------
    float
        Fidelity value in [0, 1]
    """
    if ideal_state.ndim == 1:
        # Pure state fidelity: F = |<ψ|ρ|ψ>|²
        # This matches NetSquid's qapi.fidelity with squared=True
        fidelity = np.abs(ideal_state.conj() @ delivered_state @ ideal_state)
    else:
        # State fidelity between two density matrices (Uhlmann fidelity)
        sqrt_rho = np.linalg.cholesky(delivered_state)
        product = sqrt_rho @ ideal_state @ sqrt_rho.conj().T
        eigenvalues = np.linalg.eigvalsh(product)
        fidelity = (np.sqrt(np.maximum(eigenvalues, 0)).sum()) ** 2
    
    return float(np.real(fidelity))
