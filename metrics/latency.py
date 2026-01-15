"""Latency metrics for quantum networks.

Measures time-related performance: request latency, unit latency, and scaled latency.
"""


def request_latency(completion_time: float, request_time: float) -> float:
    """Calculate Request Latency (Lr) / Waiting Time.
    
    Time from service request initiation to the completion of the service
    at the requesting node. This metric includes all delays, including 
    queuing, entanglement generation attempts, or classical signaling.
    
    Parameters
    ----------
    completion_time : float
        Time when the request was completed (in nanoseconds)
    request_time : float
        Time when the request was initiated (in nanoseconds)
        
    Returns
    -------
    float
        Request latency in nanoseconds
        Divide by 1e6 for milliseconds
    """
    return completion_time - request_time


def unit_latency(total_time: float, num_units: int) -> float:
    """Calculate Unit Latency (Lu).
    
    Mean time for the generation of a single entanglement unit (e.g. a 
    Bell-pair or multipartite state) required by a service request.
    
    Parameters
    ----------
    total_time : float
        Total time spent generating entanglement units (in nanoseconds)
    num_units : int
        Number of entanglement units generated
        
    Returns
    -------
    float
        Unit latency in nanoseconds per entanglement unit
    """
    if num_units <= 0:
        return float('inf')
    return total_time / num_units


def scaled_latency(request_latency: float, num_units: int) -> float:
    """Calculate Scaled Latency (Ls).
    
    The request latency Lr normalized by the number of entanglement units
    requested, Ls = Lr / Nu. This metric captures the effective time spent 
    per delivered entangled unit, including the impact of scheduling and 
    congestion. In the absence of concurrent requests, Ls reduces to the 
    pair latency Lu.
    
    Parameters
    ----------
    request_latency : float
        Total request latency (Lr) in nanoseconds
    num_units : int
        Number of entanglement units requested
        
    Returns
    -------
    float
        Scaled latency in nanoseconds per entanglement unit
    """
    if num_units <= 0:
        return float('inf')
    return request_latency / num_units
