"""Callback functions for quantum network demo.

This module contains callback functions for handling Bell pair delivery
and measurement in the quantum network simulation.
"""

from functools import partial
import netsquid as ns
from netsquid.components.qprogram import QuantumProgram
from netsquid.components.instructions import INSTR_MEASURE


def measurement_done(node, q_id, program):
    """Callback executed after qubit measurement completes.
    
    Parameters
    ----------
    node : Node
        Network node that performed the measurement
    q_id : int
        Qubit ID that was measured
    program : QuantumProgram
        The quantum program that executed the measurement
    """
    result = program.output["m0"][0]
    print(f"{node.name}(q_id: {q_id}): {result}")


def create_receive_callback(metrics_collector, qubit_store):
    """Create a receive callback function with access to metrics collector and qubit store.
    
    Parameters
    ----------
    metrics_collector : MetricsCollector
        The metrics collector instance for recording delivery metrics
    qubit_store : dict
        Dictionary for storing qubits before measurement (shared across nodes)
        
    Returns
    -------
    callable
        Receive callback function that can be used with node.qnp.socket()
    """
    def receive_callback(node, net, deliver_msg):
        """Callback to process received qubits and collect metrics.
        
        This callback:
        1. Stores qubit references BEFORE measurement
        2. When both node qubits are available, calculates fidelity
        3. Records metrics in the metrics collector
        4. Performs qubit measurement
        
        Parameters
        ----------
        node : Node
            Network node receiving the Bell pair
        net : Network
            The quantum network instance
        deliver_msg : DeliverMessage
            Message containing Bell pair delivery information
        """
        print(f"{node.name} received Bell Pair: "
              f"request_id={deliver_msg.request_id}, "
              f"sequence={deliver_msg.sequence}, "
              f"bell_qubit_id={deliver_msg.bell_qubit_id}, "
              f"bell_pair_state={deliver_msg.bell_pair_state}")
        
        # Store qubit reference BEFORE measurement
        # Key: (request_id, sequence) uniquely identifies each Bell pair
        key = (deliver_msg.request_id, deliver_msg.sequence)
        if key not in qubit_store:
            qubit_store[key] = {}
        
        try:
            # Get the qubit from quantum memory BEFORE it's measured
            # Try primary method (qnode.qmemory.peek) first, fallback to qpm.qubits
            try:
                qubit = node.qnode.qmemory.peek(deliver_msg.bell_qubit_id)[0]
            except:
                qubit = node.qpm.qubits[deliver_msg.bell_qubit_id]
                
            qubit_store[key][node.name] = qubit
            print(f"  → Stored qubit for {node.name}, total stored: {len(qubit_store[key])}")
            
            # When both qubits are received, calculate fidelity BEFORE measuring
            if len(qubit_store[key]) == 2:
                qubits_list = list(qubit_store[key].values())
                print(f"  → Both qubits ready, calculating fidelity for pair {deliver_msg.sequence}")
                
                # Record delivery with both qubits for fidelity calculation
                metrics_collector.record_delivery(
                    request_id=deliver_msg.request_id,
                    qubit_id=deliver_msg.bell_qubit_id,
                    qubits=qubits_list
                )
                
                print(f"  ✓ Recorded metrics for pair {deliver_msg.sequence}")
                print(f"  ✓ Active requests: {len(metrics_collector._active_requests)}, "
                      f"Completed: {len(metrics_collector.requests)}")
                      
        except Exception as e:
            import traceback
            print(f"  ✗ Error recording metrics: {e}")
            traceback.print_exc()
        
        # NOW measure the qubit (after fidelity calculation)
        # Measurement collapses the quantum state, so it must happen last
        measure = QuantumProgram()
        measure.apply(INSTR_MEASURE, [0], output_key="m0")
        
        node.qpm.execute_program(
            partial(measurement_done, node, deliver_msg.bell_qubit_id, measure),
            None,
            measure,
            qubit_mapping=[deliver_msg.bell_qubit_id],
        )
    
    return receive_callback
