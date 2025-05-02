import os
import subprocess
import time

import matplotlib.pyplot as plt

# Paths and configurations
wrk2_command = "../../../wrk2/wrk"
wrk2_script = "../../wrk2/scripts/hotel-reservation/mixed-workload_type_1.lua"
base_url = "http://128.110.219.52:5000"
output_dir = "./wrk2_output"
base_load_rate = 20000
burst_load_rate = 40000
base_duration = "30s"
burst_duration = "10s"
threads = 20
connections = 1000

# Ensure output directory exists
os.makedirs(output_dir, exist_ok=True)

def run_wrk2(rate, duration, output_prefix):
    """Run wrk2 with the specified rate and duration."""
    command = [
        wrk2_command,
        "-D", "exp",
        "-t", str(threads),
        "-c", str(connections),
        "-d", duration,
        "-L",
        "-s", wrk2_script,
        base_url,
        "-R", str(rate),
        "-P"
    ]
    print(f"Running: {' '.join(command)}")
    subprocess.run(command, cwd=output_dir)

def parse_latency_files():
    """Parse latency files and return a list of all latencies."""
    latencies = []
    for file in os.listdir(output_dir):
        if file.startswith("thread") and file.endswith(".latency"):
            with open(os.path.join(output_dir, file), "r") as f:
                for line in f:
                    try:
                        latencies.append(float(line.strip()))
                    except ValueError:
                        continue
    return latencies

def plot_latencies(latencies):
    """Plot latencies in the order they occurred."""
    plt.figure(figsize=(10, 6))
    plt.plot(latencies, marker='o', linestyle='-', markersize=2, label="Request Latencies")
    plt.xlabel("Request Order")
    plt.ylabel("Latency (ms)")
    plt.title("Request Latencies Over Time")
    plt.legend()
    plt.grid(True)
    plt.show()

def main():
    # Run base load
    print("Starting base load...")
    run_wrk2(base_load_rate, base_duration, "base")

    # Wait for a short period before burst
    time.sleep(5)

    # Run burst load
    print("Starting burst load...")
    run_wrk2(burst_load_rate, burst_duration, "burst")

    # Parse and plot latencies
    print("Parsing latency files...")
    latencies = parse_latency_files()
    # latencies.sort()  # Sort latencies by request order
    print(f"Total requests: {len(latencies)}")

    print("Plotting latencies...")
    plot_latencies(latencies)

if __name__ == "__main__":
    main()