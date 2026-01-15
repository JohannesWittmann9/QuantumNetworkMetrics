"""Core simulation runner for quantum network demo.

This module provides functions to run individual simulations and
configure the quantum network with different parameters.
"""

from functools import partial
import os

import netsquid as ns

from qnp.network import Network, NetworkParams
from qnp.interface import REQUEST, Address, Fidelity, RequestType
from simulations.runner import calculate_fidelity_map, load_fidelity_map
from metrics.metrics_collector import MetricsCollector

from demo_metrics.demo_callbacks import create_receive_callback


def run_single_simulation(source_node, dest_node, num_bps=2, 
                         config_file="./demo_metrics/config.yml"):
    """Run a single quantum network simulation with one request.
    
    Parameters
    ----------
    source_node : str
        Source node name (e.g., "RA", "RB")
    dest_node : str
        Destination node name (e.g., "RA", "RB")
    num_bps : int, optional
        Number of Bell pairs to request (default: 2)
    config_file : str, optional
        Path to network configuration YAML file (default: "./demo_metrics/config.yml")
        
    Returns
    -------
    dict
        Dictionary containing all calculated metrics for this simulation:
        - throughput: States per second
        - mean_request_latency: Average request completion time (ns)
        - mean_unit_latency: Average time per Bell pair (ns)
        - mean_scaled_latency: Normalized latency (ns)
        - mean_fidelity: Average fidelity of delivered states
        - fairness_throughput: Jain's index for throughput
        - fairness_latency: Jain's index for latency
        - fairness_fidelity: Jain's index for fidelity
        - per_node_metrics: Detailed metrics broken down by node
        
    Notes
    -----
    The simulation uses NetSquid's discrete event simulation engine.
    Each simulation:
    1. Resets the simulation environment
    2. Creates a quantum network from configuration
    3. Opens sockets on source and destination nodes
    4. Submits a Bell pair request
    5. Runs until completion or timeout (simulation time scales with num_bps)
    6. Collects and returns performance metrics
    
    The simulate_failure parameter controls link quality via memory cutoff (alpha):
    - Normal: alpha = [0.03, 0.1, 0.3] - more permissive, better performance
    - Degraded: alpha = [0.1, 0.3, 0.5] - stricter cutoffs, simulates link failures
    """
    # Reset for this simulation
    ns.set_qstate_formalism(ns.DM_FORMALISM)
    ns.simutil.sim_reset()
    
    # Create fresh metrics collector and qubit store for this simulation
    qubit_store = {}
    metrics_collector = MetricsCollector(fidelity_threshold=0.0)
    metrics_collector.start_simulation()
    
    # Configuration files
    netconf_file = config_file
    fidelity_file = "./demo_metrics/fidelities.json"
    
    # Calculate fidelity map if not already present
    if not os.path.exists(fidelity_file):
        calculate_fidelity_map(netconf_file, fidelity_file)
    
    alpha_values = [0.03, 0.1, 0.3]  # Baseline: normal operation
        
    # Create and start the quantum network
    net = Network(NetworkParams(
        config_path=netconf_file,
        fidelity_map=load_fidelity_map(fidelity_file),
        alpha=alpha_values,
        magic=True,  # Enable magic (improved entanglement generation)
    ))
    net.start()
    
    # Let network converge (initialize all components)
    ns.simutil.sim_run(10**3)  # 1 microsecond
    
    # Create receive callback with access to metrics collector and qubit store
    receive_callback = create_receive_callback(metrics_collector, qubit_store)
    
    # Open quantum sockets on both nodes
    socket_src = net.get_node(source_node).qnp.socket(
        rcv_cbk=partial(receive_callback, net.get_node(source_node), net),
    )
    socket_dst = net.get_node(dest_node).qnp.socket(
        rcv_cbk=partial(receive_callback, net.get_node(dest_node), net),
        identifier=32,  # Socket identifier for addressing
    )
    
    # Create and submit Bell pair request
    request = REQUEST(
        request_type=RequestType.NORMAL,
        request_id=0,
        num_bps=num_bps,
        state=None,  # No specific state requirement
        end_time=None,  # No deadline
    )
    
    # Record request in metrics collector
    metrics_collector.record_request(
        request_id=request.request_id,
        num_units=request.num_bps,
        node_id=source_node
    )
    
    # Submit request through socket
    socket_src.request(
        request,
        destination=Address(dest_node, 32),
        fidelity=Fidelity.F95,  # Request fidelity >= 0.95
    )
    
    # Run simulation - duration scales with number of Bell pairs
    # Typical time per pair: ~500-700 microseconds for 2-hop network
    sim_time = max(10, num_bps * 3) * 10**6  # nanoseconds
    ns.simutil.sim_run(sim_time)
    
    # Finalize metrics collection
    metrics_collector.end_simulation()
    
    # Return calculated metrics
    return metrics_collector.calculate_metrics()
