import argparse
import json
import os
import random

import numpy as np

import trace_inspector
import tempo_extract
import matplotlib.pyplot as plt
    
def main(extract, start, end, window, num_buckets):
    
    base_url = "http://localhost:3200"
    client = tempo_extract.TempoClient(base_url)
        
    os.makedirs("trace_collection", exist_ok=True)
        
    ### Extract traces
    if extract == True:
        query = {
            "limit": 10000,
            "kind": "server",
            "tags": ["http.status_code=200"],
        }
        # Extract traces within a window of time
        if start and end:        
            query["start"] = start
            query["end"] = end
        
        # Extract traces with different duration bounds
        for i in reversed(range(num_buckets)):
            # Max Value, capture whole tail
            if i == num_buckets - 1:
                bound = window * i
                min_duration = 0 + bound
                max_duration = window + (bound * i )
                min =  str(min_duration) + "ms"
                max = str(max_duration) + "ms"
            else:
                bound = window * i
                min_duration = 0 + bound
                max_duration = window + bound
                min =  str(min_duration) + "ms"
                max = str(max_duration) + "ms"
            
            query["minDuration"] = min
            query["maxDuration"] = max

            traces = tempo_extract.collect_traces_with_query(client, query)
            with open(f'trace_collection/traces_min_{min_duration}_max_{max_duration}.json', 'w') as f:
                json.dump(traces, f, indent=4)
    
    
    ### Process traces
    distinct_graphs ={}
    graph_signature_counts = {}
    all_root_spans = []
    
    
    path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "trace_collection")
    ### Get all traces from files, and process them into graphs
    trace_files = os.listdir(path)
    for trace_file in trace_files:
        tset = trace_inspector.TraceSet(os.path.join(path, trace_file))
        root_spans = tset.get_root_spans()
        print(len(root_spans))
        all_root_spans.extend(root_spans)
    
    
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
        name = random.randint(0, 100)
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
            trace_durations.append(trace_duration/1000000)
            
            
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
                # traces_array = np.array(traces, dtype=[('trace_duration', float), ('span_duration', float), ('gap_duration', float), ('internal_duration', float), ('root_duration', float)])


        # Create aggregated series by percentile distribution of trace durations
        traces_array.sort(axis=0)
        
        # Calculate percentiles
        percentiles = [50, 75, 90, 95, 99]
        percentile_values = np.percentile(traces_array[:,0], percentiles)
        

        # Group tuples based on percentiles
        groups = []
        start_idx = 0
        for p_value in percentile_values:
            # end_idx = np.where(traces_array[:,0] <= p_value)
            end_idx = np.max(np.where(traces_array[:, 0] <= p_value))
            # end_idx = np.searchsorted(traces_array[:, 0], p_value)
            groups.append(traces_array[start_idx:end_idx])
            start_idx = end_idx
        groups.append(traces_array[start_idx:])  # Add the remaining tuples

        # Calculate mean and standard deviation for each group
        means = []
        std_devs = []
        
        for group in groups:
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
                
                means.append([max_value, server_span_mean, gap_span_mean, internal_span_mean, root_span_mean])
                std_devs.append([max_value, server_span_std, gap_span_std, internal_span_std, root_span_std])

        # Convert to numpy arrays for easier plotting
        means = np.array(means)
        std_devs = np.array(std_devs)
        
        # Plot the results
        # x_values = percentiles
        # y_values = means[:, 1:]  # Assuming you want to plot all other axes
        y_errors = std_devs[:, 1:]
        CB_color_cycle = [
                  '#f781bf', '#a65628', '#984ea3',
                  '#999999', '#e41a1c', '#dede00']
        width = 0.6
        
        for i in range(0 , len(percentiles)):
            bottom = means[i, 1]
            plt.bar(f'p{percentiles[i]}', means[i, 1], yerr=y_errors[i,1], label=f'function_span', width=width, bottom=bottom,color=CB_color_cycle[0])
            bottom = means[i, 1] + means[i,2] 
            plt.bar(f'p{percentiles[i]}', means[i, 2], yerr=y_errors[i,2], label=f'gap_span', width=width, bottom=bottom,color=CB_color_cycle[1])
            bottom = means[i, 1] + means[i,2] + means[i,3]
            plt.bar(f'p{percentiles[i]}', means[i, 3], yerr=y_errors[i,3], label=f'cache_span', width=width, bottom=bottom,color=CB_color_cycle[2])


        # Add labels and title
        plt.xlabel('X-axis (percentile)')
        plt.ylabel('Mean values with std dev')
        plt.title('Mean and Standard Deviation of Groups by Percentile')
        plt.legend()
        plt.savefig(f"trace_durations_{name}.png")

        
        
        # Convert to numpy arrays for stacking
        # server_span_durations = np.array(span_durations)
        # internal_span_durations = np.array(internal_durations)
        # client_span_durations = np.array(gap_durations)
        # root_span_durations = np.array(root_durations)
    
        # # # Create a stacked bar chart
        # plt.bar(trace_durations, server_span_durations, label='Server Span Durations')
        # plt.bar(trace_durations, internal_span_durations, bottom=server_span_durations, label='Internal Span Durations')
        # plt.bar(trace_durations, client_span_durations, bottom=server_span_durations + internal_span_durations, label='Client Span Durations')
        # plt.bar(trace_durations, root_span_durations,  bottom=server_span_durations + internal_span_durations + client_span_durations, label='Root Span Durations')

        # # Add labels and title
        # plt.xlabel('trace_duration (ms)')
        # plt.ylabel('Percentt of trace_duration')
        # plt.title('Proportion of trace_duration for server spans and server-client gaps')
        
        # # Calculate percentiles
        # p50 = np.percentile(trace_durations, 50)
        # p75 = np.percentile(trace_durations, 75)
        # p90 = np.percentile(trace_durations, 90)
        # p95 = np.percentile(trace_durations, 95)
        # p99 = np.percentile(trace_durations, 99)

        # # Add vertical lines at specific x-axis values
        # x_values_to_mark = {"p50": p50, "p75": p75, "p90": p90, "p95": p95, "p99": p99}
        
        # for label,x_value in x_values_to_mark.items():
        #     plt.axvline(x=x_value, color='r', linestyle='--', linewidth=1)
        #     plt.text(x_value, 1, label, verticalalignment='center')

        # # plt.xscale('log')
        # # Add a legend
        # plt.legend()

        # # Display the plot
        # # plt.show()
        # plt.savefig(f"trace_durations_{name}.png")
        # plt.clf()
        # plt.cla()
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Trace parsing script")
    parser.add_argument("-e","--extract",action="store_true" ,help="Extract traces from tempo")
    parser.add_argument("--start", type=int, help="Start time for trace extraction")
    parser.add_argument("--end", type=int, help="End time for trace extraction")
    parser.add_argument("--window", type=int, default=10, help="Window size for trace extraction")
    parser.add_argument("--num-buckets", type=int, default=250, help="Number of buckets for trace extraction querying")


    args = parser.parse_args()
    main(args.extract, args.start, args.end, args.window, args.num_buckets)
    