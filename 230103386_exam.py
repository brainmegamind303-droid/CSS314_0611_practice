# ==============================================================================
# MIDTERM PRACTICAL EXAMINATION: PARALLEL COMPUTING
# Topic: Karp–Flatt Metric & Empirical Overhead Profiling
# Total Marks: 50
# Instructor: Sufyan bin Uzayr
#
# SUBMISSION INSTRUCTIONS:
# 1. Enter your integer Student ID in PART 0.
# 2. Complete the required implementations in PART 1 and PART 2.
# 3. Execute this file on your local machine to collect empirical benchmarking data.
# 4. Fill in your diagnostic answers directly in the multiline strings in PART 4.
# 5. Submit ONLY this completed .py file to Moodle: <YourStudentID>_exam.py
# ==============================================================================

"""
HONOR CODE & ANTI-PLAGIARISM NOTICE:
This examination is governed by hardware-telemetry verification. 
Your benchmark timings, cache saturation boundaries, and Karp-Flatt curves 
must originate from physical execution on your local machine.

AI-generated synthetic timings lack realistic OS scheduling jitter, process 
spawn latency, and microarchitectural memory bus saturation. Any submission 
containing fabricated benchmark data will receive 0/50 for academic dishonesty.
"""

import os
import sys
import time
import platform
import multiprocessing as mp
import numpy as np


# ==============================================================================
# PART 0: STUDENT IDENTITY & DETERMINISTIC SEED INITIALIZATION (Pass/Fail Gate)
# ==============================================================================
# Enter your student ID as a pure integer (e.g., 2493129439, 210103042, etc.)
STUDENT_ID = 230103386  # TODO: Replace with your actual Student ID

def compute_seeds(student_id: int):
    """
    Computes deterministic seeds using direct integer modulo arithmetic.
    Do NOT modify these formulas.
    """
    if student_id <= 0:
        raise ValueError("Please set STUDENT_ID to your valid student ID number.")
    
    k1 = (student_id % 7) + 3                     # Range: [3, 9]
    k2 = ((student_id // 10) % 5) + 2             # Range: [2, 6]
    n0 = 1_500_000 + (student_id % 20) * 75_000   # Range: [1,500,000 - 2,925,000]
    return k1, k2, n0


# ==============================================================================
# PART 1: KERNEL IMPLEMENTATION (15 Marks)
# ==============================================================================
# Kernel: Stochastic Potential Field Reduction
# For slice index range [start_idx, start_idx + count):
# Compute: sum( sqrt(K1 * x^2 + 1.0) * cos(x / K2) ) * dx
# where dx = 1.0 / total_elements, x = i * dx

def worker_kernel(start_idx: int, count: int, total_elements: int, k1: int, k2: int) -> float:
    """
    TODO: Implement the numeric worker kernel. (15 Marks)
    
    Mathematical Kernel Specification:
        sum( sqrt(k1 * x^2 + 1.0) * cos(x / k2) ) * dx
    where:
        dx = 1.0 / total_elements
        x = i * dx, for index i in range [start_idx, start_idx + count)

    Requirements:
    1. Compute step size dx = 1.0 / total_elements.
    2. Generate coordinate array x for indices in range [start_idx, start_idx + count)
       using np.float64 precision.
    3. Compute element-wise transformed potential values:
       values = np.sqrt(k1 * (x ** 2) + 1.0) * np.cos(x / k2)
    4. Return the aggregate sum multiplied by dx as a standard Python float.
    """
    # --- YOUR CODE STARTS HERE (approx. 4-6 lines) ---
    dx = 1.0 / total_elements
    indices = np.arange(start_idx, start_idx + count, dtype=np.float64)
    x = indices * dx
    values = np.sqrt(k1 * (x ** 2) + 1.0) * np.cos(x / k2)
    return float(np.sum(values) * dx)
    # --- YOUR CODE ENDS HERE ---


# ==============================================================================
# PART 2: PARALLEL HARNESS & KARP-FLATT ENGINE (15 Marks Total)
# ==============================================================================
# The Karp-Flatt Metric evaluates experimentally observed parallel overhead:
#
#     e = ( (1 / S) - (1 / p) ) / ( 1 - (1 / p) )
#
# where:
#     p = number of concurrent worker processes (p >= 2)
#     S = speedup = T_serial / T_parallel(p)
#
# Under strong scaling (fixed total work N0), if e remains constant as p grows,
# parallel efficiency loss is strictly caused by the serial portion of the code.
# If e increases as p grows, efficiency loss is driven by parallel overheads
# (process contention, IPC, cache thrashing, memory bus saturation).

def calculate_karp_flatt(speedup: float, p: int) -> float:
    """
    TODO: Implement Karp-Flatt metric calculation. (5 Marks)
    
    Formula:
        e = ((1.0 / S) - (1.0 / p)) / (1.0 - (1.0 / p))
    
    Requirements:
    1. For p <= 1, return 0.0 (by definition, baseline has no parallel overhead).
    2. For p >= 2, evaluate and return the Karp-Flatt overhead metric e.
    """
    # --- YOUR CODE STARTS HERE ---
    if p <= 1:
        return 0.0
    if speedup <= 0.0:
        return 1.0
    return ((1.0 / speedup) - (1.0 / p)) / (1.0 - (1.0 / p))
    # --- YOUR CODE ENDS HERE ---


def parallel_reduction(p: int, total_elements: int, k1: int, k2: int) -> float:
    """
    TODO: Implement parallel workload partitioning and multiprocessing dispatch. (10 Marks)
    
    Requirements:
    1. Partition total_elements across p processes into contiguous (start_idx, count) slices.
       Ensure all total_elements are accounted for exactly once without overlap or gaps.
    2. Prepare argument tuples for worker_kernel.
    3. Use multiprocessing.Pool(processes=p) to execute tasks concurrently across worker processes.
    4. Gather and sum partial results from all workers, and return the aggregate integral as a float.
    """
    # --- YOUR CODE STARTS HERE (approx. 8-12 lines) ---
    base_size = total_elements // p
    remainder = total_elements % p
    
    tasks = []
    current_idx = 0
    for i in range(p):
        count = base_size + (1 if i < remainder else 0)
        if count > 0:
            tasks.append((current_idx, count, total_elements, k1, k2))
        current_idx += count

    with mp.Pool(processes=p) as pool:
        partial_results = pool.starmap(worker_kernel, tasks)
        
    return float(np.sum(partial_results))
    # --- YOUR CODE ENDS HERE ---


def run_benchmark():
    """
    Runs the empirical benchmark across core allocations and computes metrics.
    Executes Part 1 and Part 2 implementations against the student's hardware.
    """
    k1, k2, n0 = compute_seeds(STUDENT_ID)
    
    # Target thread counts: 1, 2, 4, physical cores, and logical cores
    logical_cores = os.cpu_count() or 4
    phys_cores = max(1, logical_cores // 2)
    
    p_candidates = sorted(list(set([1, 2, 4, phys_cores, logical_cores])))
    p_levels = [p for p in p_candidates if p <= 16]
    
    print(f"==================================================================")
    print(f"Executing Karp-Flatt Benchmark | Student ID: {STUDENT_ID}")
    print(f"Seeds: K1={k1}, K2={k2}, Fixed Workload N0={n0:,}")
    print(f"Host Hardware: {platform.processor()} | Logical Cores: {logical_cores}")
    print(f"==================================================================")
    
    # 1. Establish Baseline Serial Execution Time (P=1)
    print("[*] Timing single-process baseline T(1)...")
    t0 = time.perf_counter()
    res_base = worker_kernel(0, n0, n0, k1, k2)
    t1 = time.perf_counter() - t0
    print(f"    T(1) baseline = {t1:.4f} seconds | Integral check = {res_base:.6f}\n")
    
    results = []
    
    for p in p_levels:
        # Benchmark Parallel Execution Time T(p) using student's parallel_reduction
        t_start = time.perf_counter()
        total_sum = parallel_reduction(p, n0, k1, k2)
        t_p = time.perf_counter() - t_start
        
        # Verify numeric consistency with serial baseline
        diff = abs(total_sum - res_base)
        if diff > 1e-4:
            print(f"[!] Warning: Result mismatch at P={p}: got {total_sum:.6f}, expected {res_base:.6f} (diff={diff:.2e})")
        
        speedup = t1 / t_p
        e_metric = calculate_karp_flatt(speedup, p)
        
        results.append({
            "p": p,
            "t_p_sec": round(t_p, 4),
            "speedup": round(speedup, 4),
            "karp_flatt_e": round(e_metric, 4)
        })
        
        print(f"P = {p:2d} | T(P) = {t_p:7.4f}s | Speedup = {speedup:6.3f}x | Karp-Flatt e = {e_metric:8.4f}")
        
    return results


# ==============================================================================
# PART 3: HARDWARE DIAGNOSTICS & SYSTEM TELEMETRY (Pass/Fail Gate)
# ==============================================================================
def collect_telemetry():
    """Captures execution environment metadata to cross-verify physical runs."""
    return {
        "student_id": STUDENT_ID,
        "platform": platform.platform(),
        "processor": platform.processor(),
        "python_version": sys.version.split()[0],
        "cpu_count_logical": os.cpu_count(),
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
    }


# ==============================================================================
# PART 4: TECHNICAL DIAGNOSTICS & ANALYSIS (20 Marks: 4 x 5 Marks)
# ==============================================================================
# Read your printed benchmark results table and answer the following 4 questions.
# Write your analysis directly inside the multiline strings below.
# Be concrete and refer to your measured numbers (P, T(P), Speedup, and e).

ANALYSIS_Q1 = """
[Problem 4.1: Karp-Flatt Trend & Overhead Classification - 5 Marks]
Look at your measured Karp-Flatt metric e as P increases from 2 to your maximum core count:
- Does e remain constant, or does it steadily increase with P?
- Based on the theoretical definition of the Karp-Flatt metric, what does this behavior 
  reveal about your workload? Is performance primarily limited by an immutable serial 
  algorithmic fraction, or are parallel overheads (process contention, IPC synchronization, 
  memory contention) dominating? Cite your exact e values.

YOUR ANSWER:
The measured Karp-Flatt metric e does not remain constant; it stays high and increases 
significantly up to e = 14.1971 at P = 12 (starting from e = 11.8117 at P = 2 and 
e = 9.3954 at P = 4). In Karp-Flatt theory, a rising e value as P increases proves that 
performance degradation is not caused by an immutable serial portion of the algorithm. 
Instead, it indicates that parallel management overheads—specifically multiprocessing pool 
creation, IPC serialization via pickle, and CPU cache/memory bandwidth contention—are 
severely dominating the execution time.
"""

ANALYSIS_Q2 = """
[Problem 4.2: Microarchitectural SMT / Hyperthreading Boundary - 5 Marks]
Compare the Karp-Flatt metric e at P = physical_cores versus P = logical_cores:
- What happens to the rate of increase of e when P crosses from physical cores to SMT virtual cores?
- From a microarchitectural perspective, explain why Simultaneous Multithreading (SMT) fails to 
  deliver linear speedup for floating-point vectorized array kernels (such as numpy arithmetic). 
  What shared execution units on the core become the primary execution bottleneck?

YOUR ANSWER:
When scaling from physical cores (P = 6, e = 9.3654, T(6) = 0.3208s) to logical SMT 
threads (P = 12, e = 14.1971, T(12) = 0.5270s), the execution time almost doubles and e 
rises sharply. On Intel Alder/Raptor Lake architectures (Intel64 Model 186), NumPy float64 
vector operations heavily saturate the core's SIMD/AVX execution units and floating-point 
ALUs. Because SMT logical threads on the same physical core share the same FPU execution 
ports and L1 data cache, assigning concurrent vector-heavy processes to paired SMT threads 
causes severe port starvation, cache thrashing, and context-switch latency rather than speedup.
"""

ANALYSIS_Q3 = """
[Problem 4.3: Memory Footprint & Cache Hierarchy Contention - 5 Marks]
Calculate the working memory footprint for your workload:
- Footprint per process = (count * 8 bytes * 2) / (1024^2) MB (for indices and values arrays).
- How does this footprint compare to your CPU's L2 and L3 cache per core?
- When multiple processes simultaneously stream float64 arrays through the memory controller,
  explain how DRAM memory bus saturation affects both T(P) and the apparent Karp-Flatt metric e.

YOUR ANSWER:
For N0 = 1,950,000 elements, each process allocates:
Footprint = (1,950,000 * 8 * 2) / (1024^2) ≈ 29.75 MB.
This 29.75 MB array allocation easily exceeds the per-core L2 cache (~1.25MB-2MB) and 
substantially consumes shared L3 cache space. When P = 12 processes run in parallel, 
the total memory footprint reaches ~357 MB, causing immediate cache line evictions and 
forcing memory requests directly into system DRAM. This heavy memory bus saturation 
creates memory controller bottlenecks, driving T(P) up from 0.0402s (serial compute) 
to 0.5270s, which artificially inflates the Karp-Flatt metric e.
"""

ANALYSIS_Q4 = """
[Problem 4.4: Superlinear Anomalies vs Real System Stalling - 5 Marks]
- Did your Karp-Flatt metric ever drop below zero (e < 0) at any process count? 
  Under what theoretical hardware condition can e become negative?
- Identify two concrete Python-specific runtime overheads present in `multiprocessing.Pool` 
  (e.g., pickle serialization, OS fork latency) that artificially inflate e at small workloads.

YOUR ANSWER:
No, the Karp-Flatt metric never dropped below zero (e > 0 across all P). Theoretically, 
e becomes negative (e < 0) during superlinear speedup (S > P), which only occurs when a 
partitioned workload suddenly fits completely within aggregate high-speed L2/L3 caches. 
In our Python execution, two specific overheads artificially inflated e:
1. Process Pool Initialization & OS Process Creation Latency: Setting up 12 worker processes 
   takes ~0.23s, which dwarfs the fast 0.0402s raw NumPy computation time.
2. Object Pickling & IPC Pipe Bottlenecks: Serializing worker task arguments and 
   deserializing float return values across POSIX/Windows pipes adds substantial IPC delay.
"""


# ==============================================================================
# SELF-VALIDATION & SUBMISSION BUNDLE
# ==============================================================================
def run_all():
    if STUDENT_ID == 0:
        print("[!] ERROR: Set your STUDENT_ID in Part 0 before running.")
        return
        
    # Check that student answered the questions
    questions = [("Q1", ANALYSIS_Q1), ("Q2", ANALYSIS_Q2), ("Q3", ANALYSIS_Q3), ("Q4", ANALYSIS_Q4)]
    unanswered = [q_name for q_name, text in questions if len(text.strip().splitlines()) <= 8]
    
    telemetry = collect_telemetry()
    benchmark_data = run_benchmark()
    
    print("\n==================================================================")
    print("SUBMISSION STATUS CHECK:")
    print(f"Student ID       : {STUDENT_ID}")
    print(f"Telemetry Status : Captured successfully.")
    print(f"Benchmark Status : {len(benchmark_data)} data points collected.")
    if unanswered:
        print(f"Diagnostic Status: [WARNING] The following sections appear uncompleted: {unanswered}")
    else:
        print(f"Diagnostic Status: All 4 diagnostic sections populated.")
    print("==================================================================")
    print("[+] When finished, save this file and submit directly to Moodle.")

if __name__ == "__main__":
    run_all()