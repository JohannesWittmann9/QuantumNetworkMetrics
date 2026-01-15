from typing import List, Dict, Optional, Callable
import numpy as np


def throughput(num_entangled_states: int, total_time: float) -> float:
    """Calculate Entanglement Generation Rate / Throughput (T).
    
    The average rate at which usable entanglement resources are delivered 
    to the application layer, measured in entangled states per unit time.
    
    Parameters
    ----------
    num_entangled_states : int
        Total number of entangled states delivered
    total_time : float
        Total time period over which states were delivered
        
    Returns
    -------
    float
        Throughput in entangled states per unit time
    """
    if total_time <= 0:
        return 0.0
    return num_entangled_states / total_time


def end_to_end_fidelity(delivered_state: np.ndarray, ideal_state: np.ndarray) -> float:
    """Calculate End-to-End Fidelity (Fe2e).
    
    Fidelity of the delivered entangled state as observed by the application,
    independent of the generation mechanism. Calculated as F = <ψ|ρ|ψ> where
    |ψ> is the ideal state and ρ is the delivered density matrix.
    
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


def request_latency(completion_time: float, request_time: float) -> float:
    """Calculate Request Latency (Lr) / Waiting Time.
    
    Time from service request initiation to the completion of the service
    at the requesting node. This metric includes all delays, including 
    queuing, entanglement generation attempts, or classical signaling.
    
    Parameters
    ----------
    completion_time : float
        Time when the request was completed
    request_time : float
        Time when the request was initiated
        
    Returns
    -------
    float
        Request latency in time units
    """
    return completion_time - request_time


def unit_latency(total_time: float, num_units: int) -> float:
    """Calculate Unit Latency (Lu).
    
    Mean time for the generation of a single entanglement unit (e.g. a 
    Bell-pair or multipartite state) required by a service request.
    
    Parameters
    ----------
    total_time : float
        Total time spent generating entanglement units
    num_units : int
        Number of entanglement units generated
        
    Returns
    -------
    float
        Unit latency in time units per entanglement unit
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
        Total request latency (Lr)
    num_units : int
        Number of entanglement units requested
        
    Returns
    -------
    float
        Scaled latency in time units per entanglement unit
    """
    if num_units <= 0:
        return float('inf')
    return request_latency / num_units


def fairness(values: List[float]) -> float:
    """Calculate Fairness (J) using Jain's fairness index.
    
    Balance of resource allocation across request origins or network 
    positions. The metric is resource type independent and is defined 
    for several measures: throughput T, end-to-end fidelity Fe2e, 
    request latency Lr, unit latency Lu, or scaled latency Ls.
    
    Parameters
    ----------
    values : List[float]
        List of metric values across different nodes/requests
        
    Returns
    -------
    float
        Jain's fairness index J in [0,1], where 1 is perfectly fair
    """
    x = np.array(values, dtype=float)
    if len(x) == 0:
        return 1.0
    return float((x.sum() ** 2) / (len(x) * (x ** 2).sum()))


def robustness(
    metric_baseline: float,
    metric_degraded: float,
    metric_type: str = 'throughput'
) -> float:
    """Calculate Robustness (RM) for a performance metric.
    
    The sensitivity of a performance metric M to network failures. Robustness 
    is evaluated by measuring the degradation of M under a specified failure 
    model. This can be applied to metrics such as throughput T, end-to-end 
    fidelity Fe2e, request latency Lr, unit latency Lu, scaled latency Ls, 
    or fairness J.
    
    Parameters
    ----------
    metric_baseline : float
        Metric value under normal operation (no failures)
    metric_degraded : float
        Metric value under failure conditions
    metric_type : str, optional
        Type of metric being measured. Options: 'throughput', 'fidelity', 
        'fairness' (higher is better) or 'latency' (lower is better).
        Default is 'throughput'.
        
    Returns
    -------
    float
        Robustness ratio. For throughput/fidelity/fairness: ratio of degraded 
        to baseline (closer to 1 is more robust). For latency: ratio of 
        baseline to degraded (closer to 1 is more robust).
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


def aggregate_metrics(
    requests: List[Dict],
    simulation_time: float,
    fidelity_values: Optional[List[float]] = None,
    rejected_states: int = 0
) -> Dict[str, float]:
    """Aggregate multiple metrics from a list of completed requests.
    
    This is a convenience function to calculate all metrics at once from
    simulation results.
    
    Parameters
    ----------
    requests : List[Dict]
        List of request dictionaries, each containing:
        - 'request_time': time when request was initiated
        - 'completion_time': time when request was completed
        - 'num_units': number of entanglement units requested
        - 'delivered_state': (optional) delivered quantum state
    simulation_time : float
        Total simulation time
    ideal_state : np.ndarray, optional
        Ideal target state for fidelity calculation
    fidelity_values : List[float], optional
        Pre-calculated fidelity values (from qapi.fidelity)
    rejected_states : int
        Number of states rejected due to fidelity threshold
        
    Returns
    -------
    Dict[str, float]
        Dictionary containing calculated metrics:
        - 'throughput': overall throughput
        - 'mean_request_latency': average request latency
        - 'mean_unit_latency': average unit latency
        - 'mean_scaled_latency': average scaled latency
        - 'fairness_throughput': fairness of throughput distribution
        - 'fairness_latency': fairness of latency distribution
        - 'mean_fidelity': (if ideal_state provided) average fidelity
    """
    if not requests:
        return {
            'throughput': 0.0,
            'mean_request_latency': 0.0,
            'mean_unit_latency': 0.0,
            'mean_scaled_latency': 0.0,
            'fairness_throughput': 1.0,
            'fairness_latency': 1.0,
        }
    
    # Calculate per-request and per-node metrics
    latencies = []
    unit_latencies = []
    scaled_latencies = []
    per_node_data = {}  # Store all metrics per node
    fidelities = []
    
    total_units = 0
    fid_idx = 0  # Index for accessing fidelity_values list
    
    for req in requests:
        req_latency = request_latency(req['completion_time'], req['request_time'])
        latencies.append(req_latency)
        
        num_units = req.get('num_units', 1)
        total_units += num_units
        
        unit_lat = unit_latency(req_latency, num_units)
        unit_latencies.append(unit_lat)
        
        scaled_lat = scaled_latency(req_latency, num_units)
        scaled_latencies.append(scaled_lat)
        
        # Track metrics per node
        node_id = req.get('node_id', 'default')
        if node_id not in per_node_data:
            per_node_data[node_id] = {
                'units': 0,
                'latencies': [],
                'fidelities': [],
                'first_request_time': float('inf'),
                'last_completion_time': 0
            }
        per_node_data[node_id]['units'] += num_units
        per_node_data[node_id]['latencies'].append(req_latency)
        
        # Track time window for this node
        per_node_data[node_id]['first_request_time'] = min(
            per_node_data[node_id]['first_request_time'], 
            req['request_time']
        )
        per_node_data[node_id]['last_completion_time'] = max(
            per_node_data[node_id]['last_completion_time'], 
            req['completion_time']
        )
        
        # Use pre-calculated fidelity values from qapi.fidelity()
        # (calculated during simulation when qubits are available)
        if fidelity_values and 'delivered_state' in req:
            num_states = len(req.get('delivered_state', []))
            for i in range(num_states):
                if fid_idx < len(fidelity_values):
                    fid = fidelity_values[fid_idx]
                    fidelities.append(fid)
                    per_node_data[node_id]['fidelities'].append(fid)
                    fid_idx += 1
    
    # Calculate per-node aggregated metrics
    per_node_throughputs = []
    per_node_latencies = []
    per_node_fidelities = []
    per_node_metrics = {}
    
    for node_id, data in per_node_data.items():
        # Calculate throughput based on node's active time window
        node_active_time = data['last_completion_time'] - data['first_request_time']
        if node_active_time > 0:
            node_throughput = data['units'] / node_active_time * 1e9  # states per second
        else:
            node_throughput = 0.0
            
        node_avg_latency = np.mean(data['latencies'])
        per_node_throughputs.append(node_throughput)
        per_node_latencies.append(node_avg_latency)
        
        per_node_metrics[node_id] = {
            'throughput': node_throughput,
            'avg_latency': node_avg_latency,
            'total_units': data['units'],
            'active_time': node_active_time
        }
        
        if data['fidelities']:
            node_avg_fidelity = np.mean(data['fidelities'])
            per_node_fidelities.append(node_avg_fidelity)
            per_node_metrics[node_id]['avg_fidelity'] = node_avg_fidelity
    
    # Aggregate metrics with per-node fairness
    metrics = {
        'throughput': throughput(total_units, simulation_time),
        'mean_request_latency': np.mean(latencies),
        'mean_unit_latency': np.mean(unit_latencies),
        'mean_scaled_latency': np.mean(scaled_latencies),
        'fairness_throughput': fairness(per_node_throughputs),  # Fairness across nodes
        'fairness_latency': fairness(per_node_latencies),  # Fairness across nodes
        'per_node_metrics': per_node_metrics,
        'rejected_states': rejected_states
    }
    
    if fidelities:
        metrics['mean_fidelity'] = np.mean(fidelities)
        if per_node_fidelities:
            metrics['fairness_fidelity'] = fairness(per_node_fidelities)  # Fairness across nodes
    
    return metrics
