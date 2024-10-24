import json
import os
import random

import trace_inspector
import tempo_extract
import matplotlib.pyplot as plt

if __name__ == "__main__":
    base_url = "http://localhost:3200"
    client = tempo_extract.TempoClient(base_url)
    
    os.makedirs("trace_collection", exist_ok=True)
    # Extract traces with different duration bounds
    for i in range(80):
        bound = 5 * i
        min_duration = 1 + bound
        max_duration = 5 + bound
        
        min =  str(min_duration) + "ms"
        max = str(max_duration) + "ms"
        query = {
            "minDuration": min,
            "maxDuration": max,
            "limit": 20,
            "kind": "server",
            "tags" : {
                "service.name": "frontend"
            }
        }
        traces = tempo_extract.collect_traces_with_query(client, query)
        with open(f'trace_collection/traces_min_{min_duration}_max_{max_duration}.json', 'w') as f:
            json.dump(traces, f, indent=4)
    
    
    trace_durations = []
    span_durations = []
    gap_durations = []
    
    # Process Traces and plot
    trace_files = os.listdir("trace_collection")
    for trace_file in trace_files:
        
        tset = trace_inspector.TraceSet(os.path.join("trace_collection", trace_file))
        
        root_spans = tset.get_root_spans()
        
        for root_span in root_spans:
            # print(f"Root Span: {root_span}")
            trace_duration = root_span.get_span_duration(root_span)
            if trace_duration/1000000 > 500:
                print(f"Trace ID: {root_span.trace_id}")
                print(f"Trace Duration: {trace_duration/1000000} ms")
                continue
            trace_durations.append(trace_duration/1000000)
            # print(f"Trace Duration: {trace_duration/1000000} ms")
            
            field_values = {"kind": "SPAN_KIND_SERVER"}
            matching_span_ids = root_span.find_spans_by_fields(field_values)        
            
            # Remove root span from matching span ids
            matching_span_ids.remove(root_span.span_id)
            # print("Matching Span IDs:", matching_span_ids)
            
            # print("Aggregate Server Span Durations:")
            span_duration = tset.aggregate_span_durations( tset.get_proporational_durations(root_span, [root_span.get_span(span_id) for span_id in matching_span_ids]))
            # print(span_duration)
            span_durations.append(span_duration)
            # print("Aggregate Server-Client Gap Span Durations:")
            gap_duration = tset.aggregate_proportional_span_durations(tset.get_proportional_durations_of_gaps(root_span, [root_span.get_span(span_id) for span_id in matching_span_ids]))
            # print(gap_duration)
            gap_durations.append(gap_duration)
            # print()

        
    # Plot the first series
    plt.scatter(trace_durations, span_durations, label='server_span_durations', marker='o')

    # Plot the second series
    plt.scatter(trace_durations, gap_durations, label='gap_durations', marker='x')

    # Add labels and title
    plt.xlabel('trace_duration (ms)')
    plt.ylabel('Percentt of trace_duration')
    plt.title('Proportion of trace_duration for server spans and server-client gaps')

    # Add a legend
    plt.legend()

    # Display the plot
    plt.savefig("trace_durations.png")
    
