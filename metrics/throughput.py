"""Throughput (T) metric for quantum networks.

The average rate at which usable entanglement resources are delivered 
to the application layer.
"""


def throughput(num_entangled_states: int, total_time: float) -> float:
    """Calculate Entanglement Generation Rate / Throughput (T).
    
    Parameters
    ----------
    num_entangled_states : int
        Total number of entangled states delivered
    total_time : float
        Total time period over which states were delivered (in nanoseconds)
        
    Returns
    -------
    float
        Throughput in entangled states per nanosecond
        Multiply by 1e9 to get states/second
    """
    if total_time <= 0:
        return 0.0
    return num_entangled_states / total_time
