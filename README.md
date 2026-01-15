# Quantum Network Performance Metrics

This project implements 7 key performance metrics for quantum networks, integrated with the NetSquid simulator from the paper "Designing a Quantum Network Protocol".

## Project Structure

```
QuantumNetworkMetrics/
├── README.md                          # This file
├── main.py                            # Entry point (configures paths and runs demo)
├── metrics/                           # Metric calculation modules
│   ├── metrics_collector.py          # Runtime metrics collection
│   ├── aggregate_metrics.py          # Combined metrics calculation
│   ├── throughput.py                 # Throughput metric
│   ├── e2e_fidelity.py               # Fidelity metric
│   ├── latency.py                    # Latency metrics (Lr, Lu, Ls)
│   ├── fairness.py                   # Jain's fairness index
│   ├── robustness.py                 # Robustness metric
│   └── metrics.py                    # Additional metrics utilities
└── demo_metrics/                      # Demonstration experiments
    ├── demo_main.py                  # Main orchestration
    ├── demo_simulation.py            # Simulation runner
    ├── demo_callbacks.py             # Callback functions for qubit handling
    ├── demo_with_metrics.py          # Original monolithic demo (legacy)
    ├── config.yml                    # Network configuration
    ├── config_degraded.yml           # Degraded network configuration
    ├── fidelities.json               # Pre-calculated fidelity map
    └── results/                      # Output JSON files
        ├── results.json              # Latest simulation results
        └── results_magic.json        # Results with magic mode enabled
```

## Overview

This demonstration runs multiple simulations on a three-node quantum network to measure and analyze **seven key performance metrics** for quantum networks, including robustness testing under link degradation scenarios.

## Network Topology

```
RA ←→ R0 ←→ RB
```

- **3 nodes**: RA (Alice), R0 (Repeater), RB (Bob)
- **2 quantum links**: RA-R0 and R0-RB (heralded entanglement generation)
- **Classical control**: Fiber connections for classical communication
- **Hardware**: NV-center based quantum devices with configurable noise parameters

## Metrics Measured

### 1. **T (Throughput)**
- **Definition**: Rate of successfully generated entangled states
- **Unit**: states/second
- **Calculation**: Total delivered Bell pairs / active request time

### 2. **Fe2e (End-to-End Fidelity)**
- **Definition**: Quality of entangled states against ideal Bell states
- **Unit**: Unitless, range [0,1] where 1 is perfect
- **Calculation**: Average fidelity using NetSquid's qapi.fidelity()
- **Method**: Checks against all 4 Bell states (Φ+, Φ-, Ψ+, Ψ-)

### 3-5. **Latency Metrics (Lr, Lu, Ls)**
- **Lr (Request Latency)**: Time from request submission to completion
- **Lu (Unit Latency)**: Average time per Bell pair
- **Ls (Scaled Latency)**: Request latency normalized by number of units
- **Unit**: Nanoseconds (displayed in milliseconds)

### 6. **J (Fairness - Jain's Index)**
- **Definition**: Balance of resource allocation across nodes
- **Unit**: Range [0,1] where 1 is perfectly fair
- **Formula**: J = (Σxi)² / (n·Σxi²)
- **Calculation**: Computed across throughput, latency, and fidelity for all nodes

### 7. **RM (Robustness)**
- **Definition**: Performance resilience under network degradation
- **Method**: Compare baseline vs degraded scenarios
- **Degradation Model**: Stricter memory cutoffs (alpha values) simulating link failures
  - Baseline: α = [0.03, 0.1, 0.3]
  - Degraded: α = [0.1, 0.3, 0.5]
- **Calculation**: RM = degraded/baseline (for throughput/fidelity), baseline/degraded (for latency)

## Experiment Design

### Experiment 1 - Magic Entanglement

In this experiment we use magic to create entanglement.

#### Baseline Simulations (Normal Operation)
- **5 simulations**: RA → RB (2 Bell pairs each)
- **5 simulations**: RB → RA (2 Bell pairs each)
- **Total**: 10 requests across 2 nodes
- **Purpose**: Establish performance benchmarks and measure fairness

#### Degraded Simulations (Link Degradation)
- **5 simulations**: RA → RB with stricter alpha
- **5 simulations**: RB → RA with stricter alpha
- **Total**: 10 degraded requests
- **Purpose**: Measure robustness to link failures/degradation

### Experiment 2 - Heralded Entanglement

In this experiment we use heralded entanglement generation.

#### Baseline Simulations (Normal Operation)
- **5 simulations**: RA → RB (2 Bell pairs each)
- **5 simulations**: RB → RA (2 Bell pairs each)
- **Total**: 10 requests across 2 nodes
- **Purpose**: Establish performance benchmarks and measure fairness

#### Degraded Simulations (Link Degradation)
- **5 simulations**: RA → RB with stricter alpha
- **5 simulations**: RB → RA with stricter alpha
- **Total**: 10 degraded requests
- **Purpose**: Measure robustness to link failures/degradation

## File Structure

```
demo/
├── README.md                    # This file
├── config.yml                   # Network configuration (baseline)
├── fidelities.json             # Pre-calculated fidelity map
├── demo_callbacks.py           # Qubit reception and measurement callbacks
├── demo_simulation.py          # Core simulation runner functions
├── demo_main.py                # Main entry point and orchestration
└── results/
    └── demo_with_metrics.json  # Output metrics (auto-generated)
```

## Running the Demo

### Prerequisites
- Python 3.7
- NetSquid 0.5.2+
- Required packages: see `../requirements.txt`
- Repo of "Designing a Quantum Network Protocol" at root level , available at https://dataverse.nl/dataset.xhtml?persistentId=doi:10.34894/2P1P91

### Execution

```bash
# From the NL directory
cd QuantumNetworkMetrics
python main.py
```

### Results

Results saved to `demo_metrics/results/`:

```json
{
    "scenario": "multiple_simulations_with_metrics",
    "num_requests_per_node": 5,
    "num_bps_per_request": 2,
    "baseline": {
        "ra_simulations": [...],
        "rb_simulations": [...],
        "ra_averages": {
            "throughput": 1542.23,
            "latency": 1298765.4,
            "fidelity": 0.969850
        },
        "combined_fairness": {
            "J_throughput": 0.999845,
            "J_latency": 0.999845,
            "J_fidelity": 0.999999997
        }
    },
    "degraded": {...},
    "robustness": {
        "RM_throughput": 0.659301,
        "RM_latency": 0.656566,
        "RM_fidelity": 0.998312,
        ...
    }
}
```

## References

1. **QNP Paper**: "Designing a Quantum Network Protocol" (ACM CoNEXT 2020)
2. **NetSquid**: https://netsquid.org

## License

This demo is part of the QNP repository. See main repository LICENSE for details.
