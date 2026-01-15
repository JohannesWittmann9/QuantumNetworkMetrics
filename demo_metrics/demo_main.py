"""Main entry point for quantum network metrics demonstration.

This demo runs baseline and degraded simulations to measure all 7 quantum
network performance metrics: Throughput (T), End-to-End Fidelity (Fe2e),
Request Latency (Lr), Unit Latency (Lu), Scaled Latency (Ls), Fairness (J),
and Robustness (RM).
"""

import json
import os

from metrics.fairness import fairness
from metrics.robustness import robustness
from demo_metrics.demo_simulation import run_single_simulation


def run_baseline_simulations(num_requests=5, num_bps=2):
    """Run baseline simulations with normal network operation.
    
    Parameters
    ----------
    num_requests : int
        Number of simulations to run per node
    num_bps : int
        Number of Bell pairs per request
        
    Returns
    -------
    tuple
        (all_metrics_ra, all_metrics_rb) - Lists of metrics dictionaries
    """
    all_metrics_ra = []
    all_metrics_rb = []
    
    print("="*60)
    print("BASELINE SIMULATIONS (Normal Operation)")
    print("="*60)
    
    # Run simulations for RA → RB
    print(f"\nRunning {num_requests} simulations: RA → RB ({num_bps} Bell pairs each)")
    for i in range(num_requests):
        print(f"[{i+1}/{num_requests}] RA → RB")
        metrics = run_single_simulation("RA", "RB", num_bps=num_bps, config_file="./demo_metrics/config.yml")
        all_metrics_ra.append(metrics)
    
    # Run simulations for RB → RA
    print(f"\nRunning {num_requests} simulations: RB → RA ({num_bps} Bell pairs each)")
    for i in range(num_requests):
        print(f"[{i+1}/{num_requests}] RB → RA")
        metrics = run_single_simulation("RB", "RA", num_bps=num_bps, config_file="./demo_metrics/config.yml")
        all_metrics_rb.append(metrics)
    
    return all_metrics_ra, all_metrics_rb


def run_degraded_simulations(num_degraded=5, num_bps=2):
    """Run degraded simulations with link degradation.
    
    Parameters
    ----------
    num_degraded : int
        Number of degraded simulations to run per node
    num_bps : int
        Number of Bell pairs per request
        
    Returns
    -------
    tuple
        (all_metrics_ra_degraded, all_metrics_rb_degraded) - Lists of metrics dictionaries
    """
    all_metrics_ra_degraded = []
    all_metrics_rb_degraded = []
    
    print("\n\n" + "="*60)
    print("DEGRADED SIMULATIONS (Link Degradation)")
    print("="*60)
    print("Testing robustness with:")
    print("  - Stricter memory cutoffs (alpha = [0.1, 0.3, 0.5])")
    print("  - This reduces available entanglement paths")
    print("  - Simulates link degradation/partial failures")
    
    # Run degraded simulations for RA → RB
    print(f"\nRunning {num_degraded} degraded simulations: RA → RB")
    for i in range(num_degraded):
        print(f"[{i+1}/{num_degraded}] RA → RB (degraded)")
        metrics = run_single_simulation("RA", "RB", num_bps=num_bps, config_file="./demo_metrics/config_degraded.yml")
        all_metrics_ra_degraded.append(metrics)
    
    # Run degraded simulations for RB → RA
    print(f"\nRunning {num_degraded} degraded simulations: RB → RA")
    for i in range(num_degraded):
        print(f"[{i+1}/{num_degraded}] RB → RA (degraded)")
        metrics = run_single_simulation("RB", "RA", num_bps=num_bps, config_file="./demo_metrics/config_degraded.yml")
        all_metrics_rb_degraded.append(metrics)
    
    return all_metrics_ra_degraded, all_metrics_rb_degraded


def calculate_combined_metrics(all_metrics_ra, all_metrics_rb):
    """Calculate combined metrics across all simulations.
    
    Parameters
    ----------
    all_metrics_ra : list
        List of metrics dictionaries from RA simulations
    all_metrics_rb : list
        List of metrics dictionaries from RB simulations
        
    Returns
    -------
    dict
        Dictionary containing:
        - node_throughputs, node_latencies, node_fidelities (lists)
        - fairness metrics (J_throughput, J_latency, J_fidelity)
        - per-node averages (ra_throughputs, ra_latencies, etc.)
    """
    # Extract per-node data from all simulations
    ra_node_throughputs = []
    ra_node_latencies = []
    ra_node_unit_latencies = []
    ra_node_scaled_latencies = []
    ra_node_fidelities = []

    rb_node_throughputs = []
    rb_node_latencies = []
    rb_node_unit_latencies = []
    rb_node_scaled_latencies = []
    rb_node_fidelities = []
    
    # Extract from RA simulations
    for metrics in all_metrics_ra:
        ra_node_throughputs.append(metrics['throughput'])
        ra_node_latencies.append(metrics['mean_request_latency'])
        ra_node_unit_latencies.append(metrics['mean_unit_latency'])
        ra_node_scaled_latencies.append(metrics['mean_scaled_latency'])
        ra_node_fidelities.append(metrics['mean_fidelity'])
            
    # Extract from RB simulations
    for metrics in all_metrics_rb:
        rb_node_throughputs.append(metrics['throughput'])
        rb_node_latencies.append(metrics['mean_request_latency'])
        rb_node_unit_latencies.append(metrics['mean_unit_latency'])
        rb_node_scaled_latencies.append(metrics['mean_scaled_latency'])
        rb_node_fidelities.append(metrics['mean_fidelity'])
    
    node_throughputs = ra_node_throughputs + rb_node_throughputs
    node_latencies = ra_node_latencies + rb_node_latencies
    node_fidelities = ra_node_fidelities + rb_node_fidelities

    # Calculate fairness metrics across all runs
    J_throughput = fairness(node_throughputs) if len(node_throughputs) > 1 else 1.0
    J_latency = fairness(node_latencies) if len(node_latencies) > 1 else 1.0
    J_fidelity = fairness(node_fidelities) if len(node_fidelities) > 1 else 1.0
    
    
    return {
        'node_throughputs': node_throughputs,
        'node_latencies': node_latencies,
        'node_fidelities': node_fidelities,
        'J_throughput': J_throughput,
        'J_latency': J_latency,
        'J_fidelity': J_fidelity,
        'ra_throughputs': ra_node_throughputs,
        'ra_latencies': ra_node_latencies,
        'ra_unit_latencies': ra_node_unit_latencies,
        'ra_scaled_latencies': ra_node_scaled_latencies,
        'ra_fidelities': ra_node_fidelities,
        'rb_throughputs': rb_node_throughputs,
        'rb_latencies': rb_node_latencies,
        'rb_unit_latencies': rb_node_unit_latencies,
        'rb_scaled_latencies': rb_node_scaled_latencies,
        'rb_fidelities': rb_node_fidelities,
    }


def print_results(num_requests, combined_baseline, combined_degraded=None):
    """Print formatted results to console.
    
    Parameters
    ----------
    num_requests : int
        Number of requests per node
    combined_baseline : dict
        Combined metrics from baseline simulations
    combined_degraded : dict, optional
        Combined metrics from degraded simulations (for robustness calculation)
    """
    print("\n\n" + "="*60)
    print("COMBINED METRICS FROM ALL SIMULATIONS")
    print("="*60)
    
    # Print per-node statistics
    ra_throughputs = combined_baseline['ra_throughputs']
    ra_latencies = combined_baseline['ra_latencies']
    ra_unit_latencies = combined_baseline['ra_unit_latencies']
    ra_scaled_latencies = combined_baseline['ra_scaled_latencies']
    ra_fidelities = combined_baseline['ra_fidelities']
    
    rb_throughputs = combined_baseline['rb_throughputs']
    rb_latencies = combined_baseline['rb_latencies']
    rb_unit_latencies = combined_baseline['rb_unit_latencies']
    rb_scaled_latencies = combined_baseline['rb_scaled_latencies']
    rb_fidelities = combined_baseline['rb_fidelities']
    
    print(f"\nRA Statistics ({num_requests} requests):")
    print(f"  Avg Throughput: {sum(ra_throughputs)/len(ra_throughputs):.2f} states/s "
          f"(min: {min(ra_throughputs):.2f}, max: {max(ra_throughputs):.2f})")
    print(f"  Avg Latency: {sum(ra_latencies)/len(ra_latencies)/1e6:.2f} ms "
          f"(min: {min(ra_latencies)/1e6:.2f}, max: {max(ra_latencies)/1e6:.2f})")
    print(f"  Avg Fidelity: {sum(ra_fidelities)/len(ra_fidelities):.6f} "
          f"(min: {min(ra_fidelities):.6f}, max: {max(ra_fidelities):.6f})")
    print(f"  Avg Unit Latency: {sum(ra_unit_latencies)/len(ra_unit_latencies)/1e6:.2f} ms "
          f"(min: {min(ra_unit_latencies)/1e6:.2f}, max: {max(ra_unit_latencies)/1e6:.2f})")
    print(f"  Avg Scaled Latency: {sum(ra_scaled_latencies)/len(ra_scaled_latencies)/1e6:.2f} ms "
          f"(min: {min(ra_scaled_latencies)/1e6:.2f}, max: {max(ra_scaled_latencies)/1e6:.2f})")
    print(f"\nRB Statistics ({num_requests} requests):")
    print(f"  Avg Throughput: {sum(rb_throughputs)/len(rb_throughputs):.2f} states/s "
          f"(min: {min(rb_throughputs):.2f}, max: {max(rb_throughputs):.2f})")
    print(f"  Avg Latency: {sum(rb_latencies)/len(rb_latencies)/1e6:.2f} ms "
          f"(min: {min(rb_latencies)/1e6:.2f}, max: {max(rb_latencies)/1e6:.2f})")
    print(f"  Avg Fidelity: {sum(rb_fidelities)/len(rb_fidelities):.6f} "
          f"(min: {min(rb_fidelities):.6f}, max: {max(rb_fidelities):.6f})")
    print(f"  Avg Unit Latency: {sum(rb_unit_latencies)/len(rb_unit_latencies)/1e6:.2f} ms "
          f"(min: {min(rb_unit_latencies)/1e6:.2f}, max: {max(rb_unit_latencies)/1e6:.2f})")
    print(f"  Avg Scaled Latency: {sum(rb_scaled_latencies)/len(rb_scaled_latencies)/1e6:.2f} ms "
          f"(min: {min(rb_scaled_latencies)/1e6:.2f}, max: {max(rb_scaled_latencies)/1e6:.2f})")
    print(f"\nFairness Metrics (Jain's Index, comparing all {num_requests} RA vs {num_requests} RB requests):")
    print(f"  J_throughput: {combined_baseline['J_throughput']:.6f}")
    print(f"  J_latency: {combined_baseline['J_latency']:.6f}")
    print(f"  J_fidelity: {combined_baseline['J_fidelity']:.9f}")
    
    # Print robustness metrics if degraded results available
    if combined_degraded is not None:
        baseline_throughput = (sum(ra_throughputs) + sum(rb_throughputs)) / (len(ra_throughputs) + len(rb_throughputs))
        baseline_latency = (sum(ra_latencies) + sum(rb_latencies)) / (len(ra_latencies) + len(rb_latencies))
        baseline_fidelity = (sum(ra_fidelities) + sum(rb_fidelities)) / (len(ra_fidelities) + len(rb_fidelities))
        
        ra_throughputs_deg = combined_degraded['ra_throughputs']
        ra_latencies_deg = combined_degraded['ra_latencies']
        ra_unit_latencies_deg = combined_degraded['ra_unit_latencies']
        ra_scaled_latencies_deg = combined_degraded['ra_scaled_latencies']
        ra_fidelities_deg = combined_degraded['ra_fidelities']
        rb_throughputs_deg = combined_degraded['rb_throughputs']
        rb_latencies_deg = combined_degraded['rb_latencies']
        rb_unit_latencies_deg = combined_degraded['rb_unit_latencies']
        rb_scaled_latencies_deg = combined_degraded['rb_scaled_latencies']
        rb_fidelities_deg = combined_degraded['rb_fidelities']
        
        degraded_throughput = (sum(ra_throughputs_deg) + sum(rb_throughputs_deg)) / (len(ra_throughputs_deg) + len(rb_throughputs_deg))
        degraded_latency = (sum(ra_latencies_deg) + sum(rb_latencies_deg)) / (len(ra_latencies_deg) + len(rb_latencies_deg))
        degraded_fidelity = (sum(ra_fidelities_deg) + sum(rb_fidelities_deg)) / (len(ra_fidelities_deg) + len(rb_fidelities_deg))
        
        RM_throughput = robustness(baseline_throughput, degraded_throughput, 'throughput')
        RM_latency = robustness(baseline_latency, degraded_latency, 'latency')
        RM_fidelity = robustness(baseline_fidelity, degraded_fidelity, 'fidelity')
        
        print("\n\n" + "="*60)
        print("ROBUSTNESS METRICS (RM)")
        print("="*60)
        print("\nBaseline (Normal Operation, alpha=[0.03, 0.1, 0.3]):")
        print(f"  Throughput: {baseline_throughput:.2f} states/s")
        print(f"  Latency: {baseline_latency/1e6:.2f} ms")
        print(f"  Fidelity: {baseline_fidelity:.6f}")
        
        print("\nDegraded (Link Degradation, alpha=[0.1, 0.3, 0.5]):")
        print(f"  Throughput: {degraded_throughput:.2f} states/s")
        print(f"  Latency: {degraded_latency/1e6:.2f} ms")
        print(f"  Fidelity: {degraded_fidelity:.6f}")
        
        print("\nRobustness (RM = degraded/baseline, closer to 1.0 is more robust):")
        print(f"  RM_throughput: {RM_throughput:.6f} ({(1-RM_throughput)*100:.1f}% degradation)")
        print(f"  RM_latency: {RM_latency:.6f} ({(1-RM_latency)*100:.1f}% increase)")
        print(f"  RM_fidelity: {RM_fidelity:.6f} ({(1-RM_fidelity)*100:.1f}% degradation)")


def save_results(num_requests, num_bps, all_metrics_ra, all_metrics_rb, 
                combined_baseline, all_metrics_ra_degraded=None, 
                all_metrics_rb_degraded=None, combined_degraded=None):
    """Save results to JSON file.
    
    Parameters
    ----------
    num_requests : int
        Number of requests per node
    num_bps : int
        Number of Bell pairs per request
    all_metrics_ra : list
        RA baseline simulation metrics
    all_metrics_rb : list
        RB baseline simulation metrics
    combined_baseline : dict
        Combined baseline metrics
    all_metrics_ra_degraded : list, optional
        RA degraded simulation metrics
    all_metrics_rb_degraded : list, optional
        RB degraded simulation metrics
    combined_degraded : dict, optional
        Combined degraded metrics
    """
    results_dir = "./demo_metrics/results"
    if not os.path.exists(results_dir):
        os.makedirs(results_dir)
        
    results_file = os.path.join(results_dir, "results.json")
    
    result_data = {
        "scenario": "multiple_simulations_with_metrics",
        "num_requests_per_node": num_requests,
        "num_bps_per_request": num_bps,
        "baseline": {
            "ra_simulations": all_metrics_ra,
            "rb_simulations": all_metrics_rb,
            "ra_averages": {
                "throughput": sum(combined_baseline['ra_throughputs'])/len(combined_baseline['ra_throughputs']),
                "latency": sum(combined_baseline['ra_latencies'])/len(combined_baseline['ra_latencies']),
                "unit_latency": sum(combined_baseline['ra_unit_latencies'])/len(combined_baseline['ra_unit_latencies']),
                "scaled_latency": sum(combined_baseline['ra_scaled_latencies'])/len(combined_baseline['ra_scaled_latencies']),
                "fidelity": sum(combined_baseline['ra_fidelities'])/len(combined_baseline['ra_fidelities']),
            },
            "rb_averages": {
                "throughput": sum(combined_baseline['rb_throughputs'])/len(combined_baseline['rb_throughputs']),
                "latency": sum(combined_baseline['rb_latencies'])/len(combined_baseline['rb_latencies']),
                "unit_latency": sum(combined_baseline['rb_unit_latencies'])/len(combined_baseline['rb_unit_latencies']),
                "scaled_latency": sum(combined_baseline['rb_scaled_latencies'])/len(combined_baseline['rb_scaled_latencies']),
                "fidelity": sum(combined_baseline['rb_fidelities'])/len(combined_baseline['rb_fidelities']),
            },
            "combined_fairness": {
                "J_throughput": combined_baseline['J_throughput'],
                "J_latency": combined_baseline['J_latency'],
                "J_fidelity": combined_baseline['J_fidelity'],
            }
            
        }
    }
    
    # Add robustness data if available
    if combined_degraded is not None and all_metrics_ra_degraded is not None:
        ra_throughputs = combined_baseline['ra_throughputs']
        ra_latencies = combined_baseline['ra_latencies']
        ra_unit_latencies = combined_baseline['ra_unit_latencies']
        ra_scaled_latencies = combined_baseline['ra_scaled_latencies']
        ra_fidelities = combined_baseline['ra_fidelities']
        rb_throughputs = combined_baseline['rb_throughputs']
        rb_latencies = combined_baseline['rb_latencies']
        rb_unit_latencies = combined_baseline['rb_unit_latencies']
        rb_scaled_latencies = combined_baseline['rb_scaled_latencies']
        rb_fidelities = combined_baseline['rb_fidelities']
        
        baseline_throughput = (sum(ra_throughputs) + sum(rb_throughputs)) / (len(ra_throughputs) + len(rb_throughputs))
        baseline_latency = (sum(ra_latencies) + sum(rb_latencies)) / (len(ra_latencies) + len(rb_latencies))
        baseline_fidelity = (sum(ra_fidelities) + sum(rb_fidelities)) / (len(ra_fidelities) + len(rb_fidelities))
        
        ra_throughputs_deg = combined_degraded['ra_throughputs']
        ra_latencies_deg = combined_degraded['ra_latencies']
        ra_unit_latencies_deg = combined_degraded['ra_unit_latencies']
        ra_scaled_latencies_deg = combined_degraded['ra_scaled_latencies']
        ra_fidelities_deg = combined_degraded['ra_fidelities']
        rb_throughputs_deg = combined_degraded['rb_throughputs']
        rb_latencies_deg = combined_degraded['rb_latencies']
        rb_unit_latencies_deg = combined_degraded['rb_unit_latencies']
        rb_scaled_latencies_deg = combined_degraded['rb_scaled_latencies']
        rb_fidelities_deg = combined_degraded['rb_fidelities']
        
        degraded_throughput = (sum(ra_throughputs_deg) + sum(rb_throughputs_deg)) / (len(ra_throughputs_deg) + len(rb_throughputs_deg))
        degraded_latency = (sum(ra_latencies_deg) + sum(rb_latencies_deg)) / (len(ra_latencies_deg) + len(rb_latencies_deg))
        degraded_fidelity = (sum(ra_fidelities_deg) + sum(rb_fidelities_deg)) / (len(ra_fidelities_deg) + len(rb_fidelities_deg))
        
        result_data["degraded"] = {
            "ra_simulations": all_metrics_ra_degraded,
            "rb_simulations": all_metrics_rb_degraded,
            "ra_averages": {
                "throughput": sum(combined_degraded['ra_throughputs'])/len(combined_degraded['ra_throughputs']),
                "latency": sum(combined_degraded['ra_latencies'])/len(combined_degraded['ra_latencies']),
                "unit_latency": sum(combined_degraded['ra_unit_latencies'])/len(combined_degraded['ra_unit_latencies']),
                "scaled_latency": sum(combined_degraded['ra_scaled_latencies'])/len(combined_degraded['ra_scaled_latencies']),
                "fidelity": sum(combined_degraded['ra_fidelities'])/len(combined_degraded['ra_fidelities']),
            },
            "rb_averages": {
                "throughput": sum(combined_degraded['rb_throughputs'])/len(combined_degraded['rb_throughputs']),
                "latency": sum(combined_degraded['rb_latencies'])/len(combined_degraded['rb_latencies']),
                "unit_latency": sum(combined_degraded['rb_unit_latencies'])/len(combined_degraded['rb_unit_latencies']),
                "scaled_latency": sum(combined_degraded['rb_scaled_latencies'])/len(combined_degraded['rb_scaled_latencies']),
                "fidelity": sum(combined_degraded['rb_fidelities'])/len(combined_degraded['rb_fidelities']),
            },
            "fairness": {
                "J_throughput": combined_degraded['J_throughput'],
                "J_latency": combined_degraded['J_latency'],
                "J_fidelity": combined_degraded['J_fidelity'],
            }
        }
        result_data["robustness"] = {
            "RM_throughput": robustness(baseline_throughput, degraded_throughput, 'throughput'),
            "RM_latency": robustness(baseline_latency, degraded_latency, 'latency'),
            "RM_fidelity": robustness(baseline_fidelity, degraded_fidelity, 'fidelity'),
        }
    
    with open(results_file, "w") as f:
        json.dump(result_data, f, indent=4, default=str)
    
    print(f"\n✓ Metrics saved to: {results_file}")
    print("="*60 + "\n")


def main():
    """Main entry point for the quantum network metrics demo."""
    # Configuration
    num_requests = 5  # Number of baseline simulations per node
    num_bps = 2       # Bell pairs per request
    test_robustness = True  # Enable/disable robustness testing
    
    # Run baseline simulations
    all_metrics_ra, all_metrics_rb = run_baseline_simulations(num_requests, num_bps)
    combined_baseline = calculate_combined_metrics(all_metrics_ra, all_metrics_rb)
    
    # Run degraded simulations if robustness testing enabled
    all_metrics_ra_degraded = None
    all_metrics_rb_degraded = None
    combined_degraded = None
    
    if test_robustness:
        num_degraded = 5  # Number of degraded simulations per node
        all_metrics_ra_degraded, all_metrics_rb_degraded = run_degraded_simulations(num_degraded, num_bps)
        combined_degraded = calculate_combined_metrics(all_metrics_ra_degraded, all_metrics_rb_degraded)
    
    # Print results
    print_results(num_requests, combined_baseline, combined_degraded)
    
    # Save to JSON
    save_results(num_requests, num_bps, all_metrics_ra, all_metrics_rb, combined_baseline,
                all_metrics_ra_degraded, all_metrics_rb_degraded, combined_degraded)


if __name__ == "__main__":
    main()
