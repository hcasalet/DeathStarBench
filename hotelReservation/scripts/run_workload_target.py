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
        self.run_dir = ""
        self.raw_data_dir = ""
        self.csv_dir = "" 

    
        
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
        