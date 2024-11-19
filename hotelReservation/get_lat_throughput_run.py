import os
import subprocess
import re

import matplotlib.pyplot as plt

class ExpRun:
    def __init__(self, run_name):
        self.run_name = run_name
        self.throughput = []
        self.latency_p50 = []
        self.latency_p75 = []
        self.latency_p90 = []
        self.latency_p99 = []

def run_command( command):
    result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return result.stdout

def parse_output(output):
    # Assuming the output contains lines like "Throughput: X, Latency: Y"
    throughput = float(re.search(r'Requests\/sec: *(\d+\.?\d*)', output).group(1))
    latency_p50 = float(re.search(r'50.000% *(\d+\.?\d*)', output).group(1))
    latency_p75 = float(re.search(r'75.000% *(\d+\.?\d*)', output).group(1))
    latency_p90 = float(re.search(r'90.000% *(\d+\.?\d*)', output).group(1))
    latency_p99 = float(re.search(r'99.000% *(\d+\.?\d*)', output).group(1))

    return throughput, latency_p50, latency_p75, latency_p90, latency_p99


def parse_output_key_value(output: str, key: str):
    # Assuming the output contains lines like "key: value"
    return float(re.search(rf'{key}: *(\d+\.?\d*)', output).group(1))

def save_output_to_file(output, filename):
    with open(filename, 'w') as f:
        f.write(output)
        
        
def load_experiment_data(directory):
    exp = ExpRun(directory)
    
    for file in os.listdir(directory):
        if file.startswith("throughput_"):
            target = int(file.split("_")[1].split(".")[0])
            
            with open(file, 'r') as f:
                output = f.read()
                throughput, latency_p50,  latency_p75, latency_p90, latency_p99 = parse_output(output)
                exp.throughput.append(throughput)
                exp.latency_p50.append(latency_p50)
                exp.latency_p75.append(latency_p75)
                exp.latency_p90.append(latency_p90)
                exp.latency_p99.append(latency_p99)
    return exp

def main():
    command_template = "../wrk2/wrk -D exp -t16 -c1000 -d30s -L -s ./wrk2/scripts/hotel-reservation/mixed-workload_type_1.lua http://127.0.0.1:5000 -R{}"
    target_throughput = [500, 1000, 1500, 2000, 2500, 3000, 3500, 4000, 4500, 5000,5500,6000,6500]  # Example parameter values

    exp_notnets = ExpRun(f"target_notnets")

    for target in target_throughput:
        command = command_template.format(target)
        output = run_command(command)
        save_output_to_file(output, f"{exp_notnets.run_name}/throughput_{target}.txt")
        
        throughput, latency_p50,  latency_p75, latency_p90, latency_p99 = parse_output(output)
        print(f"Throughput: {throughput}, Latency p50: {latency_p50}, Latency p75: {latency_p75}, Latency p90: {latency_p90}, Latency p99: {latency_p99}")
        exp_notnets.throughput.append(target)
        exp_notnets.latency_p50.append(latency_p50)
        exp_notnets.latency_p75.append(latency_p75)
        exp_notnets.latency_p90.append(latency_p90)
        exp_notnets.latency_p99.append(latency_p99)
        
        
    baseline = load_experiment_data(exp_notnets.run_name)

    plt.plot(exp_notnets.throughput, exp_notnets.latency_p50, marker='o', label='notnets_p50')
    plt.plot(exp_notnets.throughput, exp_notnets.latency_p99, marker='^', label='notnets_p99')
    
    plt.plot(baseline.throughput, baseline.latency_p50, marker='o', label='baseline_p50')
    plt.plot(baseline.throughput, baseline.latency_p99, marker='^', label='baseline_p99')
    
    plt.yscale('log')
    plt.xlabel('Throughput')
    plt.ylabel('Latency')
    plt.title('Throughput vs Latency')
    plt.grid(True)
    plt.savefig("throughput_vs_latency.png")

if __name__ == "__main__":
    main()