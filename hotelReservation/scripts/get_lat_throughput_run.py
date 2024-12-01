import json
import os
import subprocess
import re
import time
import argparse

import matplotlib.pyplot as plt

def run_command(command: str, print_output: bool | None = None, print_error: bool | None = None) -> str:
    print(f"Running command: {command}")
    result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        if print_error:
                print(f"Error running command: {result.stderr}")
        print(f"Error running command.")
    else:
        if print_output:
            print(result.stdout)
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
    
        
    def set_experiment_environment(self, submodule_branch, config_file_updates,clear_shm):

        # switch and build submodule branch
        if submodule_branch:
            run_command(f"cd ../notnets_grpc/notnets_shm && git checkout {submodule_branch} && make && sudo make install && cd ../../scripts")
        
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
            run_command("cd ../notnets_grpc && sudo ./clear_all.sh root m && cd ../scripts")
                

    def  down_application(self):
        # Clear previous deployments: docker compose down
        run_command("docker-compose down")
            
   
    def deploy_application(self):
        # Docker Compose Up
        run_command("docker-compose up -d --build", print_output=False, print_error=False)
        
    
        
    def run_experiment(self, command_template, target_throughput, save_output_to_file):
        for target in target_throughput:
            command = command_template.format(target)
            output = run_command(command, print_output=False)
            if save_output_to_file:
                save_output_to_file(output, f"{self.run_name}",f"{self.run_name}/throughput_{target}.txt")            
            throughput = parse_output_by_key_value(output, 'Requests\/sec:')
            latency_p50 = parse_output_by_key_value(output, '50\.000%')
            latency_p75 = parse_output_by_key_value(output, '75\.000%')
            latency_p90 = parse_output_by_key_value(output, '90\.000%')
            latency_p99 = parse_output_by_key_value(output, '99\.000%')             
            print(f"Run Name: {self.run_name}, Throughput: {throughput}, Latency p50: {latency_p50}, Latency p75: {latency_p75}, Latency p90: {latency_p90}, Latency p99: {latency_p99}")
            self.throughput.append(throughput)
            self.latency_p50.append(latency_p50)
            self.latency_p75.append(latency_p75)
            self.latency_p90.append(latency_p90)
            self.latency_p99.append(latency_p99)
    

def load_experiment_from_directory(directory) -> ExpRun:
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


def monitor_system_call(command, key_to_monitor, target_value, monitor_num_rows_for_value: None | int = None):
    start_time = None
    end_time = None
    
    captured_row_values = {}  # Store the rows that contain the key_to_monitor

    while start_time is None or end_time is None:
        output = run_command(command, print_output=False, print_error=False)
        rows = output.splitlines()
        for row in rows:
            # matching_rows = [row for row in rows if key_to_monitor in row]
            # print(f"Number of rows matching '{key_to_monitor}': {len(matching_rows)}")
            if key_to_monitor in row:
                name = row.split()[0]
                value = row.split()[5]  # Assuming the value is the 6th column (+1 for 0-indexing). Corresponds to the 6th column in the output of `ipcs` command
                if start_time is None:
                    start_time = time.time()
                
                if monitor_num_rows_for_value:
                    captured_row_values[name] = value
                    # print(f"Captured len row values: {len(captured_row_values)}")
                    if len(captured_row_values) > monitor_num_rows_for_value:
                        if all([value == target_value for value in captured_row_values.values()]):
                            end_time = time.time()
                            break
                elif value == target_value:
                    end_time = time.time()
                    break
        time.sleep(1)  # Adjust the sleep time as needed

    if start_time and end_time:
        duration = end_time - start_time
        print(f"Time duration for {key_to_monitor} to reach {target_value}: {duration} seconds")
    return duration


# # RUN FROM SCRIPTS DIRECTORY
# def main():
#     run_command = "../../wrk2/wrk -D exp -t16 -c1000 -d30s -L -s ../wrk2/scripts/hotel-reservation/mixed-workload_type_1.lua http://127.0.0.1:5000 -R{}"
#     target_throughput = list(range(1000, 15000, 1000))  
    
#     exp_baseline =  ExpRun(f"baseline")
#     exp_baseline.set_experiment_environment(None, {"overSharedMem": "false"}, True)
#     exp_baseline.run_experiment(run_command, target_throughput, True)

#     # Example usage
#     monitor_system_call("ipcs", "root", "2", monitor_num_rows_for_value=26)

#     exp_notnets = ExpRun(f"notnets")
#     exp_notnets.set_experiment_environment("adaptive_polling", {"overSharedMem": "true"}, True)
#     exp_notnets.run_experiment(run_command, target_throughput, True)
        


    
#     graph_exp_list([load_experiment_from_directory("baseline"),  load_experiment_from_directory("notnets")], "hotel_reservation_mixed_workload_type_1", "throughput_vs_latency.png")
    
def parse_arguments():
    parser = argparse.ArgumentParser(description="Run and analyze hotel reservation experiments.")
    parser.add_argument('--run_experiment', action='store_true', help="Flag to run the experiment")
    parser.add_argument('--load_experiments', nargs='+', help="List of experiment directories to load")
    parser.add_argument('--graph', action='store_true', help="Flag to graph the results")
    parser.add_argument('--graph_title', type=str, default="Throughput vs Latency", help="Title of the graph")
    parser.add_argument('--fig_name', type=str, default="throughput_vs_latency.png", help="Filename for the graph image")
    return parser.parse_args()

def main():
    args = parse_arguments()
    run_command_template = "../../wrk2/wrk -D exp -t16 -c1000 -d30s -L -s ../wrk2/scripts/hotel-reservation/mixed-workload_type_1.lua http://127.0.0.1:5000 -R{}"
    target_throughput = list(range(1000, 15000, 1000))  
    
    experiments = []
    
    if args.run_experiment:
        # exp_baseline = ExpRun("baseline")
        # exp_baseline.down_application()
        # exp_baseline.set_experiment_environment(None, {"overSharedMem": "false"}, True)
        # exp_baseline.deploy_application()
        # exp_baseline.run_experiment(run_command_template, target_throughput, save_output_to_file)
        
        
        # exp_notnets_full_polling = ExpRun("notnets-full_polling")
        # exp_notnets_full_polling.down_application()
        # exp_notnets_full_polling.set_experiment_environment("main", {"overSharedMem": "true"}, True)
        # exp_notnets_full_polling.deploy_application()
        # # monitor connection time
        # monitor_system_call("ipcs", "root", "2", monitor_num_rows_for_value=26)
        # exp_notnets_full_polling.run_experiment(run_command_template, target_throughput, save_output_to_file)
        

        
        exp_notnets_adaptive_polling = ExpRun("notnets-adaptive_polling")
        exp_notnets_adaptive_polling.down_application()
        exp_notnets_adaptive_polling.set_experiment_environment("esiramos/adaptive_polling", {"overSharedMem": "true"}, True)
        exp_notnets_adaptive_polling.deploy_application()
        monitor_system_call("ipcs", "root", "2", monitor_num_rows_for_value=26)
        exp_notnets_adaptive_polling.run_experiment(run_command_template, target_throughput, save_output_to_file)
        


        # exp_notnets_initial_adaptive_polling = ExpRun("notnets-initial_adaptive_polling")
        # exp_notnets_initial_adaptive_polling.set_experiment_environment("esiramos/initial_adaptive_polling", {"overSharedMem": "true"}, True)
        # exp_notnets_initial_adaptive_polling.run_experiment(run_command_template, target_throughput, save_output_to_file)
        
        
        # exp_notnets_hybrid_mean_polling = ExpRun("notnets-hybrid_mean_polling")
        # exp_notnets_hybrid_mean_polling.set_experiment_environment("esiramos/hybrid_mean_polling", {"overSharedMem": "true"}, True)
        # exp_notnets_hybrid_mean_polling.run_experiment(run_command_template, target_throughput, save_output_to_file)
        
        # experiments = [exp_baseline, exp_notnets_full_polling, exp_notnets_adaptive_polling, exp_notnets_initial_adaptive_polling, exp_notnets_hybrid_mean_polling]
        experiments = [exp_baseline, exp_notnets_full_polling, exp_notnets_adaptive_polling]
    
    if args.load_experiments:
        experiments = [load_experiment_from_directory(directory) for directory in args.load_experiments]
    
    if args.graph:
            graph_exp_list(experiments, args.graph_title, args.fig_name)

if __name__ == "__main__":
    main()