import json
import os
import subprocess
import re

import matplotlib.pyplot as plt


def run_command(command):
    result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return result.stdout


# Unit Choice: ms
def parse_output_by_key_value(output: str, key: str):
    result = re.search(rf'({key})\s*(\d+\.?\d*)(\w*)', output)
    value = float(result.group(2))
    if len(result.groups()) == 3:
        unit = (result.group(3))
        if unit == 'ms':
            return value
        elif unit == 'us':
            return value / 1000
        elif unit == 's':
            return value * 1000
        else:
            return value
    return value

def save_output_to_file(output, dirname,filename):
    os.makedirs(dirname, exist_ok=True)

    with open(filename, 'w+') as f:
        f.write(output)
        
class ExpRun:
    def __init__(self, run_name):
        self.run_name = run_name
        self.throughput = []
        self.latency_p50 = []
        self.latency_p75 = []
        self.latency_p90 = []
        self.latency_p99 = []
    
        
    def set_experiment_environment(self, submodule_branch, config_file_updates, clear_shm):
        
        # switch submodule branch
        run_command(f"cd notnets_grpc && git checkout {submodule_branch} && cd ..")
        
        # Update config file
        if config_file_updates:
            with open("../config.json", "r") as f:
                data = json.load(f)
                
            for key, value in config_file_updates.items():
                data[key] = value
                
            with open("../config.json", "w") as f:
                json.dump(data, f, indent=4)
                
        # Clear shared memory
        if clear_shm:
            run_command("cd notnets_grpc && sudo ./clear_all.sh root m && cd ..")
            
        
    def run_experiment(self, command, target_throughput):
        for target in target_throughput:
            command = command.format(target)
            output = run_command(command)
            save_output_to_file(output, f"{self.run_name}",f"{self.run_name}/throughput_{target}.txt")
            self.throughput = parse_output_by_key_value(output, 'Requests\/sec:')
            self.latency_p50 = parse_output_by_key_value(output, '50\.000%')
            self.latency_p75 = parse_output_by_key_value(output, '75\.000%')
            self.latency_p90 = parse_output_by_key_value(output, '90\.000%')
            self.latency_p99 = parse_output_by_key_value(output, '99\.000%')             
            print(f"Run Name: {self.run_name}, Throughput: {self.throughput}, Latency p50: {self.latency_p50}, Latency p75: {self.latency_p75}, Latency p90: {self.latency_p90}, Latency p99: {self.latency_p99}")
    


def load_experiment_from_directory(directory):
    exp = ExpRun(directory)
    files = os.listdir(directory)
    files = sorted(files, key=lambda x: int(x.split("_")[1].split(".")[0]))  # Sort files by the value in the name

    for file in files:
        if file.startswith("throughput_"):
            with open(os.path.join(directory, file), 'r') as f:
                output = f.read()
                throughput = parse_output_by_key_value(output, 'Requests\/sec:')
                latency_p50 = parse_output_by_key_value(output, '50\.000%')
                latency_p75 = parse_output_by_key_value(output, '75\.000%')
                latency_p90 = parse_output_by_key_value(output, '90\.000%')
                latency_p99 = parse_output_by_key_value(output, '99\.000%')                
                # throughput, latency_p50, latency_p75, latency_p90, latency_p99 = parse_output(output)
                exp.throughput.append(throughput)
                exp.latency_p50.append(latency_p50)
                exp.latency_p75.append(latency_p75)
                exp.latency_p90.append(latency_p90)
                exp.latency_p99.append(latency_p99)
    return exp


def graph_exp_list(experiments, graph_title ,fig_name):
    for exp in experiments:
        plt.plot(exp.throughput, exp.latency_p50, marker='o', label=f'{exp.run_name}_p50')
        plt.plot(exp.throughput, exp.latency_p99, marker='^', label=f'{exp.run_name}_p99')
        
    plt.yscale('log')
    plt.xlabel('Throughput(reqs/sec)')
    plt.ylabel('Latency(ms)')
    plt.title(graph_title)
    plt.grid(True)
    plt.legend() 
    plt.savefig(fig_name)

def main():
    run_command = "../wrk2/wrk -D exp -t16 -c1000 -d30s -L -s ./wrk2/scripts/hotel-reservation/mixed-workload_type_1.lua http://127.0.0.1:5000 -R{}"
    target_throughput = list(range(1000, 15000, 1000))  
    
    # exp_notnets = ExpRun(f"target_notnets")
    # exp_notnets.set_experiment_environment("adaptive_poll", {"overSharedMem": "true"}, True)
    # exp_notnets.run_experiment(run_command, target_throughput)
        
    baseline = load_experiment_from_directory("taget_baseline_adaptive_poll")
    exp_notnets = load_experiment_from_directory("taget_notnets_adaptive_poll")
    
    # baseline = load_experiment_from_directory("taget_baseline_fixed_poll")
    exp_notnets1 = load_experiment_from_directory("taget_notnets_fixed_poll")
    
    baseline1 = load_experiment_from_directory("taget_baseline_hybrid_poll")
    exp_notnets2 = load_experiment_from_directory("taget_notnets_hybrid_poll")
    
    graph_exp_list([exp_notnets, baseline, baseline1, exp_notnets1, exp_notnets2], "hotel_reservation_mixed_workload_type_1", "throughput_vs_latency.png")
    
if __name__ == "__main__":
    main()