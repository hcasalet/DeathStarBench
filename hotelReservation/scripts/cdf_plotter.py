import matplotlib.pyplot as plt
import re
import os

def parse_detailed_percentiles(data):
    """
    Parses the 'Detailed Percentile spectrum' from raw benchmark data.
    Returns lists of latencies and percentiles.
    """
    percentiles = []
    latencies = []

    in_spectrum = False
    for line in data.splitlines():
        if "Detailed Percentile spectrum" in line:
            in_spectrum = True
            continue
        if in_spectrum:
            if line.strip() == "":
                continue
            match = re.match(r"\s*([\d\.]+)\s+([\d\.]+)\s+\d+", line)
            if match:
                latency = float(match.group(1))
                percentile = float(match.group(2)) * 100  # Convert to %
                latencies.append(latency)
                percentiles.append(percentile)
            elif line.strip().startswith("#"):
                break  # End of section
    return latencies, percentiles

def extract_throughput(filename):
    """
    Extracts the numeric throughput from a filename like 'throughput_1000.txt'.
    """
    match = re.search(r"(\d+)", filename)
    return int(match.group(1)) if match else float('inf')

def load_and_sort_samples(directory):
    """
    Loads .txt files and sorts them by extracted throughput value.
    """
    samples = []
    for filename in os.listdir(directory):
        if filename.endswith(".txt"):
            throughput = extract_throughput(filename)
            path = os.path.join(directory, filename)
            with open(path, "r") as file:
                data = file.read()
            samples.append((throughput, filename, data))

    # Sort by throughput
    samples.sort(key=lambda x: x[0])
    return samples

def plot_ordered_cdfs(directory):
    """
    Plots CDFs of latency for each sample file, ordered by throughput.
    """
    samples = load_and_sort_samples(directory)

    if not samples:
        print("No .txt files found in directory.")
        return

    plt.figure(figsize=(10, 6))
    for throughput, filename, data in samples:
        latencies, percentiles = parse_detailed_percentiles(data)
        label = f"{throughput} RPS"
        plt.plot(latencies, percentiles, label=label)

    # plt.xscale("linear")
    # plt.xscale("log")

    plt.xlabel("Latency (ms)")
    plt.ylabel("Cumulative Percentile (%)")
    plt.title("CDF of Request Latencies Ordered by Throughput")
    plt.grid(True)
    plt.legend(title="Target Load")
    plt.tight_layout()
    plt.savefig("latency_cdf_ordered.png")

# Example usage
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python cdf_plotter.py <directory_path>")
    else:
        plot_ordered_cdfs(sys.argv[1])
