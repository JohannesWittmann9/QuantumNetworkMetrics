"""Aggregate metrics calculation for quantum network simulations.

Combines all performance metrics into a comprehensive analysis.
"""

import numpy as np
from typing import List, Dict, Optional

from .throughput import throughput
from .e2e_fidelity import end_to_end_fidelity
from .latency import request_latency, unit_latency, scaled_latency
from .fairness import fairness


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
        - 'node_id': identifier of requesting node
    simulation_time : float
        Total simulation time in nanoseconds
    fidelity_values : List[float], optional
        Pre-calculated fidelity values (from qapi.fidelity)
    rejected_states : int
        Number of states rejected due to fidelity threshold
        
    Returns
    -------
    Dict[str, float]
        Dictionary containing calculated metrics:
        - 'throughput': overall throughput (states/ns, multiply by 1e9 for states/s)
        - 'mean_request_latency': average request latency (ns)
        - 'mean_unit_latency': average unit latency (ns)
        - 'mean_scaled_latency': average scaled latency (ns)
        - 'fairness_throughput': fairness of throughput distribution
        - 'fairness_latency': fairness of latency distribution
        - 'mean_fidelity': (if fidelity_values provided) average fidelity
        - 'fairness_fidelity': (if fidelity_values provided) fairness of fidelity
        - 'per_node_metrics': per-node breakdown of all metrics
        - 'rejected_states': number of rejected low-fidelity states
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
    
    node_id = None
    for node_id, data in per_node_data.items():
        node_id = node_id
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
            'total_units': data['units'],
        }
        
        if data['fidelities']:
            node_avg_fidelity = np.mean(data['fidelities'])
            per_node_fidelities.append(node_avg_fidelity)
            per_node_metrics[node_id]['avg_fidelity'] = node_avg_fidelity

    # Aggregate metrics with per-node fairness
    metrics = {
        'mean_request_latency': np.mean(latencies),
        'mean_unit_latency': np.mean(unit_latencies),
        'mean_scaled_latency': np.mean(scaled_latencies),
        'rejected_states': rejected_states,
        **per_node_metrics[node_id],
    }
    
    if fidelities:
        metrics['mean_fidelity'] = np.mean(fidelities)
    return metrics
