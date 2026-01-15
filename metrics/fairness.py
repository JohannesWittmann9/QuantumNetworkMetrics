"""Fairness (J) metric for quantum networks.

Balance of resource allocation across request origins or network positions
using Jain's fairness index.
"""

import numpy as np
from typing import List


def fairness(values: List[float]) -> float:
    """Calculate Fairness (J) using Jain's fairness index.
    
    The metric is resource type independent and is defined for several 
    measures: throughput T, end-to-end fidelity Fe2e, request latency Lr, 
    unit latency Lu, or scaled latency Ls.
    
    Jain's Index: J = (Σxi)² / (n·Σxi²)
    
    Parameters
    ----------
    values : List[float]
        List of metric values across different nodes/requests
        
    Returns
    -------
    float
        Jain's fairness index J in [0,1], where 1 is perfectly fair
        
    Examples
    --------
    >>> fairness([100, 100, 100])  # Perfect fairness
    1.0
    >>> fairness([100, 50])  # Some unfairness
    0.9
    >>> fairness([100, 0])  # Maximum unfairness
    0.5
    """
    x = np.array(values, dtype=float)
    if len(x) == 0:
        return 1.0
    return float((x.sum() ** 2) / (len(x) * (x ** 2).sum()))
