import argparse
import json
import os
import random

import numpy as np

import trace_inspector
import tempo_extract
import matplotlib.pyplot as plt
    
def main(extract, start, end, window):
    
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
        for i in reversed(range(250)):
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
    
    ### Get all traces from files, and process them into graphs
    trace_files = os.listdir("trace_collection")
    for trace_file in trace_files:
        tset = trace_inspector.TraceSet(os.path.join("trace_collection", trace_file))
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
        name = random.randint(0, 100000)
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
            
        # Convert to numpy arrays for stacking
        server_span_durations = np.array(span_durations)
        internal_span_durations = np.array(internal_durations)
        client_span_durations = np.array(gap_durations)
        root_span_durations = np.array(root_durations)
        
        # # Create a stacked bar chart

        plt.bar(trace_durations, server_span_durations, label='Server Span Durations')
        plt.bar(trace_durations, internal_span_durations, bottom=server_span_durations, label='Internal Span Durations')
        plt.bar(trace_durations, client_span_durations, bottom=server_span_durations + internal_span_durations, label='Client Span Durations')
        plt.bar(trace_durations, root_span_durations,  bottom=server_span_durations + internal_span_durations + client_span_durations, label='Root Span Durations')

        # Add labels and title
        plt.xlabel('trace_duration (ms)')
        plt.ylabel('Percentt of trace_duration')
        plt.title('Proportion of trace_duration for server spans and server-client gaps')
        
        
        # Calculate percentiles
        p50 = np.percentile(trace_durations, 50)
        p75 = np.percentile(trace_durations, 75)
        p90 = np.percentile(trace_durations, 90)
        p95 = np.percentile(trace_durations, 95)
        p99 = np.percentile(trace_durations, 99)

        # Add vertical lines at specific x-axis values
        x_values_to_mark = {"p50": p50, "p75": p75, "p90": p90, "p95": p95, "p99": p99}
        
        for label,x_value in x_values_to_mark.items():
            plt.axvline(x=x_value, color='r', linestyle='--', linewidth=1)
            plt.text(x_value, 1, label, verticalalignment='center')

        # plt.xscale('log')
        # Add a legend
        plt.legend()


        # Display the plot
        # plt.show()
        plt.savefig(f"trace_durations_{name}.png")
        plt.clf()
        plt.cla()
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Trace parsing script")
    parser.add_argument("-e","--extract",action="store_true" ,help="Extract traces from tempo")
    parser.add_argument("--start", type=int, help="Start time for trace extraction")
    parser.add_argument("--end", type=int, help="End time for trace extraction")
    parser.add_argument("--window", type=int, default=10, help="Window size for trace extraction")


    args = parser.parse_args()
    main(args.extract, args.start, args.end, args.window)
    