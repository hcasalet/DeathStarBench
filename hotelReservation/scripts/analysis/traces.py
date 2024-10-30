import json
import os
import random

import numpy as np

import trace_inspector
import tempo_extract
import matplotlib.pyplot as plt

if __name__ == "__main__":
    
    extract = False
    
    if extract == True:
        base_url = "http://localhost:3200"
        client = tempo_extract.TempoClient(base_url)
        
        os.makedirs("trace_collection", exist_ok=True)
        # Extract traces with different duration bounds
        for i in range(40):
            bound = 25 * i
            min_duration = 0 + bound
            max_duration = 25 + bound
            
            min =  str(min_duration) + "ms"
            max = str(max_duration) + "ms"
            query = {
                "minDuration": min,
                "maxDuration": max,
                "limit": 20000,
                "http.status_code": "200",
                "name": "/hotels",
                "kind": "server",
                "tags" : {
                    "service.name": "frontend"
                }
            }
            traces = tempo_extract.collect_traces_with_query(client, query)
            with open(f'trace_collection/traces_min_{min_duration}_max_{max_duration}.json', 'w') as f:
                json.dump(traces, f, indent=4)
    
    
    # trace_durations = []
    # span_durations = []
    # gap_durations = []
    # internal_durations = []
    
    distinct_graphs ={}
    graph_signature_counts = {}
    
    # Process Traces and plot
    trace_files = os.listdir("trace_collection")
    for trace_file in trace_files:
        
        tset = trace_inspector.TraceSet(os.path.join("trace_collection", trace_file))
        
        root_spans = tset.get_root_spans()
        print(len(root_spans))
        
        # internal_labels = {"kind": "SPAN_KIND_INTERNAL"}
        # internal_spans = tset.filter_out_traces(internal_labels)
        # root_spans = [ span for span in root_spans if span not in internal_spans ]  
        
        for root_span in root_spans:
            
            signature = root_span.get_graph_signature_from_root()
            
            if signature in distinct_graphs:
                distinct_graphs[signature].append(root_span)
                graph_signature_counts[signature] += 1
            else:
                distinct_graphs[signature] = [root_span]
                graph_signature_counts[signature] = 1
                
        for signature, graphs in distinct_graphs.items():
            name = random.randint(0, 100000)
            print(f"Graph: {name}")
            print(f"Graph: {signature}")
            print(f"Count: {graph_signature_counts[signature]}")
            print()
            
            trace_durations = []
            span_durations = []
            gap_durations = []
            internal_durations = []
            
            trace_durations.clear()
            span_durations.clear()
            gap_durations.clear()
            internal_durations.clear()

            
            grouped_spans = distinct_graphs[signature]
            for root_span in grouped_spans:
                
                # print(f"Root Span: {root_span}")
                trace_duration = root_span.get_span_duration(root_span)

                trace_durations.append(trace_duration/1000000)
                # print(f"Trace Duration: {trace_duration/1000000} ms")
                
                field_values = {"kind": "SPAN_KIND_INTERNAL"}
                interanl_span_ids = root_span.find_spans_by_fields(field_values)
                
                field_values = {"kind": "SPAN_KIND_SERVER"}
                matching_span_ids = root_span.find_spans_by_fields(field_values)        
                
                # Remove root span from matching span ids
                matching_span_ids.remove(root_span.span_id)
                # print("Matching Span IDs:", matching_span_ids)
                internal_duration = tset.aggregate_span_durations( tset.get_proporational_durations(root_span, [root_span.get_span(span_id) for span_id in interanl_span_ids]))
                internal_durations.append(internal_duration)
                
                # print("Aggregate Server Span Durations:")
                span_duration = tset.aggregate_span_durations( tset.get_proporational_durations(root_span, [root_span.get_span(span_id) for span_id in matching_span_ids]))
                # print(span_duration)
                span_durations.append(span_duration)
                # print("Aggregate Server-Client Gap Span Durations:")
                gap_duration = tset.aggregate_proportional_span_durations(tset.get_proportional_durations_of_gaps(root_span, [root_span.get_span(span_id) for span_id in matching_span_ids]))
                # print(gap_duration)
                gap_durations.append(gap_duration)
                # print()


            number_of_messages = len(trace_durations)        
            print(f"Number of Messages: {number_of_messages}")
                
            # Plot the first series
            # plt.scatter(trace_durations, span_durations, label='server_span_durations', marker='o')
            # # Plot the second series
            # plt.scatter(trace_durations, gap_durations, label='gap_durations', marker='x')
            #     # Plot the second series
            # plt.scatter(trace_durations, internal_durations , label='internal(cache/db)_durations', marker='*')
            
            
            # Convert to numpy arrays for stacking
            server_span_durations = np.array(span_durations)
            internal_span_durations = np.array(internal_durations)
            client_span_durations = np.array(gap_durations)
            
            # # Create a stacked bar chart
            plt.bar(trace_durations, server_span_durations, label='Server Span Durations')
            plt.bar(trace_durations, internal_span_durations, bottom=server_span_durations, label='Internal Span Durations')
            plt.bar(trace_durations, client_span_durations, bottom=server_span_durations + internal_span_durations, label='Client Span Durations')

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
            x_values_to_mark = [p50, p75, p90, p95, p99]  # Example x-axis values
            for x_value in x_values_to_mark:
                plt.axvline(x=x_value, color='r', linestyle='--', linewidth=1)

            # plt.xscale('log')
            # Add a legend
            plt.legend()


            # Display the plot
            # plt.show()
            plt.savefig(f"trace_durations_{name}.png")
            plt.clf()
            plt.cla()
        
