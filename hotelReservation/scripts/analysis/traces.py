import argparse
import datetime
import json
import os
import random
import re

import numpy as np

import trace_inspector
import tempo_extract
import matplotlib.pyplot as plt


def graph_stacked_bar_plot(name, traces_array: np.array):
    
        # Total number of traces
        num_traces = len(traces_array)

        # Create aggregated series by percentile distribution of trace durations
        # sorted_array =  traces_array.sort(axis=0) TODO: WTF
        sorted_array = traces_array[traces_array[:, 0].argsort()]
        
        # Calculate percentiles
        # percentiles = [50, 75, 90, 95, 99, 99.9, 99.99, 99.999]
        percentiles = [50, 75, 90, 95, 99, 100]

        percentile_values = np.percentile(sorted_array[:,0], percentiles)
        
        # Group tuples based on percentiles
        groups = {}
        start_idx = 0
        for index, p_value in enumerate(percentile_values):
            end_idx = np.max(np.where(sorted_array[:, 0] <= p_value))
            groups[p_value] = (sorted_array[start_idx:end_idx])
            start_idx = end_idx
        # TODO: How many traces_array entries are left?

        # Calculate mean and standard deviation for each group
        means = []
        std_devs = []
        
        means_map = {}
        std_devs_map = {}
        
        for p_value, group in groups.items():
            if len(group) > 0:
                                
                max_value = group[:, 0].max()    
            
                server_span_mean = group[:, 1].mean()
                server_span_std = group[:, 1].std()

                gap_span_mean = group[:, 2].mean()
                gap_span_std = group[:, 2].std()
                
                internal_span_mean = group[:, 3].mean()
                internal_span_std = group[:, 3].std()
                
                root_span_mean = group[:, 4].mean()
                root_span_std = group[:, 4].std()
                
                means_map[p_value] = [server_span_mean, gap_span_mean, internal_span_mean, root_span_mean]
                means.append([server_span_mean, gap_span_mean, internal_span_mean, root_span_mean])
                std_devs_map[p_value] = [server_span_std, gap_span_std, internal_span_std, root_span_std]
                std_devs.append([server_span_std, gap_span_std, internal_span_std, root_span_std])

        # Convert to numpy arrays for easier plotting
        means = np.array(means)
        std_devs = np.array(std_devs)
        
        num_columns = len(percentiles)
        if means.shape[0] != num_columns:
            print(f"Not enough data for all percentiles...")
            num_columns = means.shape[0]
            return
                            
        if means.shape != std_devs.shape:
            print(f"Means shape: {means.shape}")
            print(f"Std Devs shape: {std_devs.shape}")
            print("Means and Std Devs shapes do not match, likely insufficient entries to calculate stddev. Skipping...")
            return
        
        weighted_means_by_series = {
            "Server Function": [means[:,0], std_devs[:,0]],
            "Client Call - Server Function Gap (Network)": [means[:,1], std_devs[:,1]],
            "Cache Call":[means[:,2], std_devs[:,2]],
            "Frontend": [means[:,3], std_devs[:,3]]
        }
        
        plt.style.use('tableau-colorblind10')
        fig, ax = plt.subplots()
        bottom = np.zeros(num_columns)
        # width = 0.6
        
        # Create Bar Names percentile + p_value
        bar_names = []
        for index, p_value in enumerate(groups):
            p_num = percentiles[index]
            bar_names.append(f"p{p_num}-{round(p_value,1)}ms") 
            
        # Create a stacked bar chart, with error bars
        for index, series in enumerate(weighted_means_by_series.keys()):
            means_and_std_dev = weighted_means_by_series[series]
            x_vals = np.arange(num_columns)

            p = ax.bar(x_vals, means_and_std_dev[0], label=series, bottom=bottom, error_kw=dict(capsize=5), color= plt.cm.tab20(index))
            
            # Add error bars
            ax.errorbar(x_vals - 1/10 + index/10, means_and_std_dev[0] + bottom, yerr= means_and_std_dev[1], linestyle='none', capsize=5, color='black')
            # above line sets the errorbar loctions, adding i/10 each time
            plt.xticks(ticks=x_vals, labels=bar_names)
            # reset the xticks to their names
            
            bottom += means_and_std_dev[0]

        # Add labels and title
        
        ax.grid(True)
        ax.set_axisbelow(True)
        fig.autofmt_xdate()

        plt.xlabel('Percentile - Max Duration Value of Percentile')
        plt.ylabel('Proportion of Overall Trace Duration')
        plt.title(f'Average Proportion of Trace Duration for End to End Trace Components - Total-Traces: {num_traces}')
        plt.legend()
        # plt.legend(weighted_means_by_series.keys(), loc='upper right')

        plt.savefig(f"trace_durations_{name}.png")
        plt.clf()
        plt.cla()
    

def graph_all_traces(name, traces_array: np.array):
    # Convert to numpy arrays for stacking
    # server_span_durations = np.array(span_durations)
    # internal_span_durations = np.array(internal_durations)
    # client_span_durations = np.array(gap_durations)
    # root_span_durations = np.array(root_durations)

    # # Create a stacked bar chart
    # plt.bar(trace_durations, server_span_durations, label='Server Span Durations')
    # plt.bar(trace_durations, internal_span_durations, bottom=server_span_durations, label='Internal Span Durations')
    # plt.bar(trace_durations, client_span_durations, bottom=server_span_durations + internal_span_durations, label='Client Span Durations')
    # plt.bar(trace_durations, root_span_durations,  bottom=server_span_durations + internal_span_durations + client_span_durations, label='Root Span Durations')

    # Add labels and title
    plt.xlabel('trace_duration (ms)')
    plt.ylabel('Percentt of trace_duration')
    plt.title('Proportion of trace_duration for server spans and server-client gaps')
    
    # Calculate percentiles
    # p50 = np.percentile(trace_durations, 50)
    # p75 = np.percentile(trace_durations, 75)
    # p90 = np.percentile(trace_durations, 90)
    # p95 = np.percentile(trace_durations, 95)
    # p99 = np.percentile(trace_durations, 99)

    # Add vertical lines at specific x-axis values
    # x_values_to_mark = {"p50": p50, "p75": p75, "p90": p90, "p95": p95, "p99": p99}
    
    # for label,x_value in x_values_to_mark.items():
    #     plt.axvline(x=x_value, color='r', linestyle='--', linewidth=1)
    #     plt.text(x_value, 1, label, verticalalignment='center')

    # plt.xscale('log')
    # Add a legend
    plt.legend()

    # Display the plot
    # plt.show()
    plt.savefig(f"trace_durations_{name}.png")
    plt.clf()
    plt.cla()
    

def graph_distribution(name, traces_array: np.array):
    
    traces_array = traces_array[traces_array[:, 0].argsort()]

    # Calculate from percentile proportions the actual values of each span type
    server_spans = traces_array[:,0] * traces_array[:,1]
    gap_spans = traces_array[:,0] * traces_array[:,2]
    cache_spans = traces_array[:,0] * traces_array[:,3]
    root_spans = traces_array[:,0] * traces_array[:,4]
    
    # Create a histogram of server span durations
    # plt.hist(traces_array[:,0], bins=100, alpha=0.2, label='Full Trace Durations')
    
    plt.hist(server_spans, bins=100, alpha=0.5, label='Server Span Durations')
    plt.hist(gap_spans, bins=100, alpha=0.5, label='Gap Span Durations')
    plt.hist(cache_spans, bins=100, alpha=0.5, label='Cache Span Durations')
    plt.hist(root_spans, bins=100, alpha=0.5, label='Root Span Durations')
    
    plt.yscale('log')

    
    # Add vertical lines at specific x-axis values
    # x_values_to_mark = {"p50": p50, "p75": p75, "p90": p90, "p95": p95, "p99": p99}
    
    # for label,x_value in x_values_to_mark.items():
    #     plt.axvline(x=x_value, color='r', linestyle='--', linewidth=1)
    #     plt.text(x_value, 1, label, verticalalignment='center')

    plt.xlabel('Duration (ms)')
    plt.ylabel('Number of spans')

    plt.title('Distribution of trace durations by category')
    plt.legend(loc='upper right') 

    plt.savefig(f"histogram_{name}.png")
    plt.clf()
    plt.cla()
    

def extract_traces(dir,start, end, window, num_buckets):
    base_url = "http://localhost:3200"
    client = tempo_extract.TempoClient(base_url)
            
    ### Extract traces
    query = {
        "limit": 20000,
        "kind": "server",
        # "status": "ok"
        "tags": ["http.status_code=200"],
    }
    # Extract traces within a window of time
    if start and end:        
        query["start"] = start
        query["end"] = end
        
    # Extract traces with different duration bounds
    for i in reversed(range(num_buckets)):
        # Max Value, capture whole tail
        if i == num_buckets - 1: # First Bucket, includes all traces north of it
            bound = window * i
            min_duration = 0 + bound
            max_duration = window + (bound * i )
            min =  str(min_duration) + "ms"
            max = str(max_duration) + "ms"
        else: # Standard Bucket
            bound = window * i
            min_duration = 0 + bound
            max_duration = window + bound
            min =  str(min_duration) + "ms"
            max = str(max_duration) + "ms"
        
        query["minDuration"] = min
        query["maxDuration"] = max

        print(f"Query: {query}")
        traces = tempo_extract.collect_traces_with_query(client, query)
        
        filen_name = f'{dir}/traces_min_{min_duration}_max_{max_duration}.json'
        with open(filen_name, 'w') as f:
            json.dump(traces, f, indent=4)
    
    
def main(extract, start, end, window, num_buckets, dir):
    
    if dir == "trace_collection":
        trace_collection_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "trace_collection")
    else:
        trace_collection_dir = dir
    
    ### Extract traces
    if extract == True:
        # Clear previous trace_collection
        # Create a directory for the trace collection
        trace_collection_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)),"trace_collection" ,datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
        os.makedirs(trace_collection_dir, exist_ok=True)

        extract_traces(trace_collection_dir,start, end, window, num_buckets)
    
    ### Process traces
    os.makedirs(trace_collection_dir, exist_ok=True)
    path = trace_collection_dir
    all_root_spans = []
    ### Get all traces from files, and process them into graphs
    trace_files = os.listdir(path)
    for trace_file in trace_files:
        tset = trace_inspector.TraceSet(os.path.join(path, trace_file))
        root_spans = tset.get_root_spans()
        print(len(root_spans))
        all_root_spans.extend(root_spans)
    
    distinct_graphs ={}
    graph_signature_counts = {}
    ### Group traces by graph signature    
    for root_span in all_root_spans:
        signature = root_span.get_graph_signature_from_root()
        if signature in distinct_graphs:
            distinct_graphs[signature].append(root_span)
            graph_signature_counts[signature] += 1
        else:
            distinct_graphs[signature] = [root_span]
            graph_signature_counts[signature] = 1
            
    ### Process by graph signature
    for signature, graphs in distinct_graphs.items():
        
        first_call_name = signature.split("|")
    
        name = re.sub(r'\W+', '', first_call_name[0])+ "_" + str(hash(signature))
        
        print(f"Graph: {name}")
        print(f"Graph: {signature}")
        print(f"Count: {graph_signature_counts[signature]}")
        print()
        
        trace_durations = []
        root_durations = []
        span_durations = []
        gap_durations = []
        internal_durations = []
        
        trace_durations.clear()
        span_durations.clear()
        gap_durations.clear()
        internal_durations.clear()
        root_durations.clear()
        
        grouped_spans = distinct_graphs[signature]
        
        for root_span in grouped_spans:
            
            ### Get total trace duration for this root_span
            trace_duration = root_span.get_span_duration(root_span)
            trace_durations.append(trace_duration/1000000) # Convert from ns to ms 
            # trace_durations.append(trace_duration) # Keep as ns

            
            
            ### Get INTERNAL and SERVER spans
            field_values = {"kind": "SPAN_KIND_INTERNAL"}
            internal_span_ids = root_span.find_spans_by_fields(field_values)
            
            field_values = {"kind": "SPAN_KIND_SERVER"}
            server_span_ids = root_span.find_spans_by_fields(field_values)        

            internal_duration = tset.aggregate_span_durations( tset.get_proporational_durations(root_span, [root_span.get_span(span_id) for span_id in internal_span_ids]))
            internal_durations.append(internal_duration)
            
            # Remove root span from server_span_ids
            # to prevent gap calculation from trying to 
            # calculate a gap between the root span and a nonexist parent
            # and to prevent double counting of the root span
            server_span_ids.remove(root_span.span_id)            

            span_duration = tset.aggregate_span_durations( tset.get_proporational_durations(root_span, [root_span.get_span(span_id) for span_id in server_span_ids]))
            span_durations.append(span_duration)

            gap_duration = tset.aggregate_gap_span_durations(tset.get_proportional_durations_of_gaps(root_span, [root_span.get_span(span_id) for span_id in server_span_ids]))
            gap_durations.append(gap_duration)
            
            root_duration = tset.get_proportional_root_span_duration_exclude_children(root_span)
            root_durations.append(root_duration)


        number_of_messages = len(trace_durations)        
        print(f"Number of Messages: {number_of_messages}")
        
        traces = list(zip(trace_durations, span_durations, gap_durations, internal_durations, root_durations))
        traces_array = np.array(traces)
        
        # TODO : Get Histogram of proportional distribution by server span, gap span, internal (cache) span, root span

        # 1. Stacked Bar Plot
        graph_stacked_bar_plot(name, traces_array)

        # 2. Histogram of trace durations
        graph_distribution(name, traces_array)
        

    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Trace parsing script")
    parser.add_argument("-e","--extract",action="store_true" ,help="Extract traces from tempo")
    parser.add_argument("-f","--dir", type=str, default="trace_collection", help="Trace dir for processing")
    parser.add_argument("--start", type=int, help="Start time for trace extraction")
    parser.add_argument("--end", type=int, help="End time for trace extraction")
    parser.add_argument("--window", type=int, default=5, help="Window size for trace extraction (ms)")
    parser.add_argument("--num-buckets", type=int, default=200, help="Number of buckets for trace extraction querying")


    args = parser.parse_args()
    main(args.extract, args.start, args.end, args.window, args.num_buckets, args.dir)
    