import os
import pandas as pd
import matplotlib.pyplot as plt
import re
from collections import defaultdict

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
def parse_throughput_file(filepath):
    with open(filepath, 'r') as f:
        output = f.read()
        throughput = parse_output_by_key_value(output, 'Requests\/sec:')
    return throughput
        



def parse_latency_file(filepath):
    percentiles = {}
    with open(filepath, 'r') as f:
        for line in f:
            # Extract only lines between Latency Distribution line and Detailed Percentile spectrum line
            if "Latency Distribution" in line:
                continue
            if "Detailed Percentile spectrum:" in line:
                break  # Stop reading when we reach the Detailed Percentile spectrum section
            # support for matching us, ms, and s
            match = re.match(r"\s*(\d+\.\d+)%\s+([\d.]+)(\w*)", line)
            if match:
                percentile = float(match.group(1))

                # Convert latency to milliseconds if necessary
                if match.group(3) == 'ms':
                    latency = float(match.group(2))
                elif match.group(3) == 'us':
                    latency = float(match.group(2)) / 1000
                elif match.group(3) == 's':
                    latency = float(match.group(2)) * 1000
                percentiles[percentile] = latency            
    return percentiles

def aggregate_data(parent_dir):
    latency_data = defaultdict(list)
    throughput_data = defaultdict(list)

    for run_dir in sorted(os.listdir(parent_dir)):
        run_path = os.path.join(parent_dir, run_dir)
        if not os.path.isdir(run_path) or not run_dir.startswith("run_"):
            continue

        for file in sorted(os.listdir(run_path)):
            if not file.startswith("throughput_"):
                continue

            throughput_string = file.split("_")[1]
            # remove the ".txt" extension
            throughput_target = int(throughput_string[:-4])
            throughput = int(parse_throughput_file(os.path.join(run_path, file)))
            throughput_data[throughput_target].append(throughput)

            file_path = os.path.join(run_path, file)
            parsed = parse_latency_file(file_path)

            for percentile, latency in parsed.items():
                latency_data[(throughput_target, percentile)].append(latency)

    # Aggregate to a DataFrame
    records = []

    for (throughput, percentile), latencies in latency_data.items():
        avg_throughput = sum(throughput_data[throughput]) / len(throughput_data[throughput])
        avg_latency = sum(latencies) / len(latencies)
        records.append({"throughput_target": throughput, "avg_throughput": avg_throughput,"percentile": percentile, "avg_latency": avg_latency})

    df = pd.DataFrame(records)
    df = df.sort_values(by=["throughput_target", "percentile"])
    return df

def plot_aggregated(df):
    plt.figure(figsize=(10, 6))
    for perc in sorted(df["percentile"].unique()):
        subset = df[df["percentile"] == perc]
        plt.plot(subset["avg_throughput"], subset["avg_latency"], label=f"{perc}%", marker='o')

    plt.xlabel("Throughput")
    plt.ylabel("Average Latency (ms)")
    plt.title("Latency Percentiles vs Throughput")
    plt.legend(title="Percentile")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig("grpah_throughput.png")

def plot_aggregated_multiple(dfs, labels, percentiles=None, output_file="graph_throughput_multi.png"):

    plt.style.use('tableau-colorblind10')

    plt.figure(figsize=(10, 6))
    for df, label in zip(dfs, labels):
        if percentiles is not None:
            df = df[df["percentile"].isin(percentiles)]
        for perc in sorted(df["percentile"].unique()):
            subset = df[df["percentile"] == perc]
            plt.plot(
                subset["avg_throughput"],
                subset["avg_latency"],
                marker='o',
                label=f"{label} - {perc}%"
            )

    plt.yscale("log")  # Use logarithmic scale for throughput
    plt.xlabel("Throughput")
    plt.ylabel("Average Latency (ms)")
    plt.title("Latency Percentiles vs Throughput (Multiple Runs)")
    plt.legend(title="Legend")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(output_file)
    
# Usage
baseline_directory = "/users/eirn/DeathStarBench/hotelReservation/scripts/baseline"
df_baseline = aggregate_data(baseline_directory)
full_polling_directory = "/users/eirn/DeathStarBench/hotelReservation/scripts/notnets-full_polling"
df_full_polling = aggregate_data(full_polling_directory)

adaptive_polling_directory = "/users/eirn/DeathStarBench/hotelReservation/scripts/notnets-adaptive_polling"
df_adaptive_polling = aggregate_data(adaptive_polling_directory)
# Plot the aggregated data
# plot_aggregated(df_full_polling)
# plot_aggregated(df_baseline)
plot_aggregated_multiple([df_baseline, df_full_polling, df_adaptive_polling], ["Baseline", "Full Polling", "Adaptive Polling"], percentiles=[50, 99], output_file="graph_throughput_multi.png")
