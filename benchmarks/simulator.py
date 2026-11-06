import math
import csv
import matplotlib.pyplot as plt

def amdahl_speedup(a, P):
    return 1.0 / (a + (1.0 - a) / P)

def gustafson_speedup(a, P):
    return P - a * (P - 1.0)

def run_simulation(a_val, max_p, output_csv, output_plot):
    P_values = [2**i for i in range(0, int(math.log2(max_p)) + 1)]
    
    results = []
    for P in P_values:
        s_amdahl = amdahl_speedup(a_val, P)
        s_gust = gustafson_speedup(a_val, P)
        results.append({"P": P, "Amdahl": s_amdahl, "Gustafson": s_gust})
        
    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["P", "Amdahl", "Gustafson"])
        writer.writeheader()
        writer.writerows(results)
        
    plt.figure(figsize=(10, 6))
    plt.plot(P_values, [r["Gustafson"] for r in results], 'o-', label=f'Gustafson (a={a_val})')
    plt.plot(P_values, [r["Amdahl"] for r in results], 's--', label=f'Amdahl (s={a_val})')
    plt.plot(P_values, P_values, 'k:', label='Ideal Linear Speedup')
    plt.xscale('log', base=2)
    plt.yscale('log', base=2)
    plt.xlabel('Processor Count (P)')
    plt.ylabel('Speedup S(P)')
    plt.title('Strong Scaling (Amdahl) vs Weak Scaling (Gustafson)')
    plt.grid(True, which="both", ls="--")
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_plot)
    plt.close()

if __name__ == "__main__":
    run_simulation(0.04, 65536, "benchmarks/scaling_simulation.csv", "plots/scaling_comparison.png")
    print("Simulation complete. Data saved to CSV and plot generated.")
