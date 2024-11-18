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



def run_command(command):
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

def main():
    command_template = "../wrk2/wrk -D exp -t16 -c1000 -d30s -L -s ./wrk2/scripts/hotel-reservation/mixed-workload_type_1.lua http://127.0.0.1:5000 -R{}"
    target_throughput = [500, 1000, 1500, 2000, 2500, 3000, 3500, 4000, 4500, 5000,5500,6000,6500]  # Example parameter values

    throughputs = []
    latencies_p50 = []
    latencies_p75 = []
    latencies_p90 = []
    latencies_p99 = []


    for target in target_throughput:
        command = command_template.format(target)
        output = run_command(command)
        # print(output)
        throughput, latency_p50,  latency_p75, latency_p90, latency_p99 = parse_output(output)
        print(f"Throughput: {throughput}, Latency p50: {latency_p50}, Latency p75: {latency_p75}, Latency p90: {latency_p90}, Latency p99: {latency_p99}")
        throughputs.append(throughput)
        latencies_p50.append(latency_p50)
        latencies_p75.append(latency_p75)
        latencies_p90.append(latency_p90)
        latencies_p99.append(latency_p99)


    plt.plot(throughputs, latencies_p50, marker='o')
    plt.plot(throughputs, latencies_p75, marker='>')
    plt.plot(throughputs, latencies_p90, marker='<')
    plt.plot(throughputs, latencies_p99, marker='^')
    
    plt.yscale('log')
    plt.xlabel('Throughput')
    plt.ylabel('Latency')
    plt.title('Throughput vs Latency')
    plt.grid(True)
    plt.savefig("throughput_vs_latency.png")

if __name__ == "__main__":
    main()