"""Robustness (RM) metric for quantum networks.

The sensitivity of performance metrics to network failures.
"""


def robustness(
    metric_baseline: float,
    metric_degraded: float,
    metric_type: str = 'throughput'
) -> float:
    """Calculate Robustness (RM) for a performance metric.
    
    Robustness is evaluated by measuring the degradation of a metric M 
    under a specified failure model. This can be applied to metrics such 
    as throughput T, end-to-end fidelity Fe2e, request latency Lr, 
    unit latency Lu, scaled latency Ls, or fairness J.
    
    Parameters
    ----------
    metric_baseline : float
        Metric value under normal operation (no failures)
    metric_degraded : float
        Metric value under failure conditions
    metric_type : str, optional
        Type of metric being measured. Options:
        - 'throughput', 'fidelity', 'fairness' (higher is better)
        - 'latency' (lower is better)
        Default is 'throughput'.
        
    Returns
    -------
    float
        Robustness ratio:
        - For throughput/fidelity/fairness: degraded / baseline 
          (closer to 1 is more robust)
        - For latency: baseline / degraded 
          (closer to 1 is more robust)
          
    Examples
    --------
    >>> robustness(100, 80, 'throughput')  # 20% degradation
    0.8
    >>> robustness(0.9, 0.85, 'fidelity')  # Small fidelity drop
    0.944
    >>> robustness(10, 15, 'latency')  # 50% latency increase
    0.667
    """
    if metric_type in ['throughput', 'fidelity', 'fairness']:
        # Higher is better: robustness = degraded / baseline
        if metric_baseline <= 0:
            return 0.0
        return metric_degraded / metric_baseline
    elif metric_type == 'latency':
        # Lower is better: robustness = baseline / degraded
        if metric_degraded <= 0:
            return float('inf')
        return metric_baseline / metric_degraded
    else:
        raise ValueError(f"Unknown metric_type: {metric_type}. "
                        f"Must be 'throughput', 'fidelity', 'fairness', or 'latency'")
