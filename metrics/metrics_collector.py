"""Metrics collection for quantum network simulations."""

import netsquid as ns
import numpy as np
from typing import Dict, List, Optional

# Import individual metric modules
from .throughput import throughput
from .e2e_fidelity import end_to_end_fidelity
from .latency import request_latency, unit_latency, scaled_latency
from .fairness import fairness
from .robustness import robustness
from .aggregate_metrics import aggregate_metrics

# Use NetSquid's built-in fidelity calculation instead of manual dm extraction
# This properly handles the quantum state
from netsquid.qubits import qubitapi as qapi
from netsquid.qubits import ketstates


class MetricsCollector:
    """Collect and calculate metrics during simulation.
    
    This class tracks all requests and their outcomes during a simulation,
    then calculates performance metrics at the end.
    
    Parameters
    ----------
    fidelity_threshold : float, optional
        The ideal target state for fidelity calculations (e.g., Bell state)
    
    Attributes
    ----------
    requests : List[Dict]
        List of completed request records
    start_time : float
        Simulation start time
    end_time : float
        Simulation end time
    """
    
    def __init__(self, fidelity_threshold: float = 0.0):
        self.requests = []
        self.start_time = 0.0
        self.end_time = 0.0
        self.fidelity_threshold = fidelity_threshold
        self._active_requests = {}  # Track requests by create_id
        self.rejected_states = 0  # Track rejected low-fidelity states
        self.fidelity_values = []  # Store actual fidelity values from qapi.fidelity
        
    def start_simulation(self):
        """Mark the start of the simulation."""
        self.start_time = ns.sim_time()
        
    def end_simulation(self):
        """Mark the end of the simulation."""
        self.end_time = ns.sim_time()
        
    def record_request(self, request_id: int, num_units: int, node_id: str = 'default'):
        """Record a new request.
        
        Parameters
        ----------
        request_id : int
            Unique identifier for the request
        num_units : int
            Number of entanglement units requested
        node_id : str
            Identifier of the requesting node
        """
        self._active_requests[request_id] = {
            'request_id': request_id,
            'num_units': num_units,
            'node_id': node_id,
            'request_time': ns.sim_time(),
            'completion_time': None,
            'delivered_states': [],
            'completed_units': 0,
        }
        
    def record_delivery(self, request_id: int, qubit_id: int, 
                       qubits: Optional[List] = None):
        """Record a successful delivery of an entanglement unit.
        
        Parameters
        ----------
        request_id : int
            Unique identifier for the request
        qubit_id : int
            Logical qubit identifier
        qubits : List, optional
            The entangled qubits (for fidelity calculation)
        """
        if request_id not in self._active_requests:
            return
            
        req = self._active_requests[request_id]
        req['completed_units'] += 1
        
        # Store quantum state if provided
        if qubits is not None and len(qubits) > 0:
            try:
                # Calculate fidelity to all 4 Bell states and use the maximum
                # b00 = |Φ+⟩, b01 = |Ψ+⟩, b10 = |Φ-⟩, b11 = |Ψ-⟩
                fid_phi_plus = qapi.fidelity(qubits, ketstates.b00, squared=True)
                fid_psi_plus = qapi.fidelity(qubits, ketstates.b01, squared=True)
                fid_phi_minus = qapi.fidelity(qubits, ketstates.b10, squared=True)
                fid_psi_minus = qapi.fidelity(qubits, ketstates.b11, squared=True)
                
                # Use the maximum fidelity (closest to any Bell state)
                max_fid = max(fid_phi_plus, fid_psi_plus, fid_phi_minus, fid_psi_minus)
                
                # Check fidelity threshold
                if self.fidelity_threshold > 0 and max_fid < self.fidelity_threshold:
                    self.rejected_states += 1
                    # Don't count this as a completed unit - decrement
                    req['completed_units'] -= 1
                    return  # Reject this state
                
                # Store the actual fidelity value for reporting
                self.fidelity_values.append(max_fid)
                
                # Store the density matrix for other potential uses
                dm = qubits[0].qstate.dm
                req['delivered_states'].append(dm)
            except Exception as e:
                print(f"Warning: Could not get quantum state: {e}")
                pass  # Skip if we can't get the state
        
        # Check if request is complete
        if req['completed_units'] >= req['num_units']:
            req['completion_time'] = ns.sim_time()
            self._finalize_request(request_id)
            
    def _finalize_request(self, request_id: int):
        """Move a completed request to the completed list.
        
        Parameters
        ----------
        request_id : int
            Unique identifier for the request
        """
        if request_id not in self._active_requests:
            return
            
        req = self._active_requests[request_id]
        
        # Calculate average delivered state if multiple units
        if req['delivered_states']:
            req['delivered_state'] = np.mean(req['delivered_states'], axis=0)
        
        # Remove temporary data
        del req['delivered_states']
        
        # Move to completed
        self.requests.append(req)
        del self._active_requests[request_id]
        
    def calculate_metrics(self) -> Dict[str, float]:
        """Calculate all metrics from collected data.
        
        Returns
        -------
        Dict[str, float]
            Dictionary containing all calculated metrics
        """
        if self.end_time == 0:
            self.end_simulation()
            
        simulation_time = self.end_time - self.start_time
        
        # Use aggregate function for most metrics, passing actual fidelity values
        metrics = aggregate_metrics(
            self.requests, 
            simulation_time,
            fidelity_values=self.fidelity_values,
            rejected_states=self.rejected_states
        )
        
        # Add timing info
        metrics['simulation_time'] = simulation_time
        metrics['start_time'] = self.start_time
        metrics['end_time'] = self.end_time
        metrics['total_requests'] = len(self.requests)
        
        return metrics
        
    def calculate_robustness(self, baseline_metrics: Dict[str, float]) -> Dict[str, float]:
        """Calculate robustness metrics compared to baseline.
        
        Parameters
        ----------
        baseline_metrics : Dict[str, float]
            Metrics from a baseline (non-degraded) simulation
            
        Returns
        -------
        Dict[str, float]
            Robustness values for each metric
        """
        current_metrics = self.calculate_metrics()
        robustness_metrics = {}
        
        # Throughput robustness
        if 'throughput' in baseline_metrics and 'throughput' in current_metrics:
            robustness_metrics['robustness_throughput'] = robustness(
                baseline_metrics['throughput'],
                current_metrics['throughput'],
                'throughput'
            )
            
        # Fidelity robustness
        if 'mean_fidelity' in baseline_metrics and 'mean_fidelity' in current_metrics:
            robustness_metrics['robustness_fidelity'] = robustness(
                baseline_metrics['mean_fidelity'],
                current_metrics['mean_fidelity'],
                'fidelity'
            )
            
        # Latency robustness
        for lat_type in ['mean_request_latency', 'mean_unit_latency', 'mean_scaled_latency']:
            if lat_type in baseline_metrics and lat_type in current_metrics:
                robustness_metrics[f'robustness_{lat_type}'] = robustness(
                    baseline_metrics[lat_type],
                    current_metrics[lat_type],
                    'latency'
                )
                
        # Fairness robustness
        for fair_type in ['fairness_throughput', 'fairness_latency', 'fairness_fidelity']:
            if fair_type in baseline_metrics and fair_type in current_metrics:
                robustness_metrics[f'robustness_{fair_type}'] = robustness(
                    baseline_metrics[fair_type],
                    current_metrics[fair_type],
                    'fairness'
                )
                
        return robustness_metrics
        
    def print_metrics(self):
        """Print all calculated metrics in a formatted way."""
        metrics = self.calculate_metrics()
        
        print("\n" + "="*60)
        print("QUANTUM NETWORK PERFORMANCE METRICS")
        print("="*60)
        
        print(f"\nSimulation Info:")
        print(f"  Total requests: {metrics.get('total_requests', 0)}")
        print(f"  Simulation time: {metrics.get('simulation_time', 0)/1e6:.2f} ms ({metrics.get('simulation_time', 0)/1e9:.6f} s)")
        if self.fidelity_threshold > 0:
            print(f"  Fidelity threshold: {self.fidelity_threshold:.2f}")
            print(f"  Rejected low-fidelity states: {self.rejected_states}")
        
        print(f"\nThroughput (T):")
        throughput_val = metrics.get('throughput', 0)
        # Throughput is already in states/second from aggregate_metrics
        print(f"  {throughput_val:.6f} entangled states/second")
        
        if 'mean_fidelity' in metrics:
            print(f"\nEnd-to-End Fidelity (Fe2e):")
            print(f"  Mean: {metrics.get('mean_fidelity', 0):.6f} (unitless, range [0,1])")
        
        print(f"\nLatency:")
        print(f"  Lr (request latency): {metrics.get('mean_request_latency', 0)/1e6:.2f} ms")
        print(f"  Lu (unit latency): {metrics.get('mean_unit_latency', 0)/1e6:.2f} ms")
        print(f"  Ls (scaled latency): {metrics.get('mean_scaled_latency', 0)/1e6:.2f} ms")
        
        print(f"\nFairness (Jain's Index, range [0,1], 1=perfectly fair):")
        print(f"  J_throughput (per-node): {metrics.get('fairness_throughput', 0):.6f}")
        print(f"  J_latency (per-node): {metrics.get('fairness_latency', 0):.6f}")
        if 'fairness_fidelity' in metrics:
            print(f"  J_fidelity (per-node): {metrics.get('fairness_fidelity', 0):.6f}")
        
        # Show per-node breakdown
        if 'per_node_metrics' in metrics:
            print(f"\nPer-Node Breakdown:")
            for node_id, node_metrics in metrics['per_node_metrics'].items():
                print(f"  {node_id}:")
                print(f"    Throughput: {node_metrics['throughput']:.6f} states/s")
                print(f"    Avg Latency: {node_metrics['avg_latency']/1e6:.2f} ms")
                if 'avg_fidelity' in node_metrics:
                    print(f"    Avg Fidelity: {node_metrics['avg_fidelity']:.6f}")
        
        print("\n" + "="*60 + "\n")
        
        return metrics
