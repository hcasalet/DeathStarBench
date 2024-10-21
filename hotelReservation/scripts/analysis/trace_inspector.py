import json
from collections import defaultdict
from datetime import datetime, timedelta


# class TraceSet:
#     def __init__(self, trace_file):
#         self.trace_file = trace_file
#         self.traces = self.load_traces()



class Trace:
    def __init__(self, trace_id, root_span):
        self.trace_id = trace_id
        self.root_span: Span = root_span

    def rank_span_durations(self):
        # span_durations = {}
        
        
        # for child in self.root_span.children:
        #     span_durations[child.span_id] = child.get_span_duration(child)

        
        pass
    
    def rank_client_server_duration_gap(self):
        pass
    

# def convert_unix_nano_to_datetime(unix_nano_str):
#     # Convert the string to an integer
#     unix_nano = int(unix_nano_str)
    
#     # Calculate the seconds and remaining nanoseconds
#     seconds = unix_nano // 1_000_000_000
#     nanoseconds = unix_nano % 1_000_000_000
    
#     # Create a datetime object for the Unix epoch
#     epoch = datetime(1970, 1, 1)
    
#     # Add the seconds and nanoseconds to the epoch
#     result_datetime = epoch + timedelta(seconds=seconds, microseconds=nanoseconds / 1000)
    
#     return result_datetime

class Span:
    def __init__(self, trace_id,span_id, parent_span_id, service, operation_name,kind, start_time, end_time):
        self.trace_id = trace_id
        self.span_id = span_id
        self.parent_span_id = parent_span_id # If null, root trace
        self.service = service
        self.operation_name = operation_name
        self.kind = kind
        self.start_time = start_time
        self.end_time = end_time
        self.children = []

    def add_child(self, child_span):
        self.children.append(child_span)
    
    def get_span(self, span_id):
        if self.span_id == span_id:
            return self
        for child in self.children:
            found_span = child.get_span(span_id)
            if found_span:
                return found_span
        return None
    
    
    def get_span_duration(self, span):
        return int(span.end_time) - int(span.start_time)
    
    def get_span_proportional_duration_of_root(self, span_id):
        span = self.get_span(span_id)
        if span:
            return self.get_span_duration(span) / self.get_span_duration(self)
        return None
    
    def rank_longest_leaf_spans(self):
        leaf_spans = self._find_leaf_spans()
        leaf_spans.sort(key=lambda span: self.get_span_duration(span), reverse=True)
        return leaf_spans
    
    def _find_leaf_spans(self):
        if not self.children:
            return [self]
        leaf_spans = []
        for child in self.children:
            leaf_spans.extend(child._find_leaf_spans())
        return leaf_spans    
    
    
    def find_spans_by_fields(self, field_values):
        matches = []
        if all(getattr(self, field, None) == value for field, value in field_values.items()):
            matches.append(self.span_id)
        for child in self.children:
            matches.extend(child.find_spans_by_fields(field_values))
        return matches        
    
    def __repr__(self):
        return f"Span(trace_id={self.trace_id}, span_id={self.span_id}, operation_name={self.operation_name})"
    

def print_span_tree(span: Span, indent=0, fields_to_print=None):
        if fields_to_print is None:
            fields_to_print = ["trace_id", "span_id", "operation_name"]

        indent_str = " " * (indent * 4)
        span_info = ", ".join(f"{field}: {getattr(span, field)}" for field in fields_to_print)
        print(f"{indent_str}{span_info}")

        for child in span.children:
            print_span_tree(child, indent + 1, fields_to_print)

def parse_traces(traces) -> list[Span]:
    span_dict = {}
    root_spans = []

    for batches in traces:
        # Iterate through each batch of spans
        for scope in batches['batches']:
            # Identify resource for scope
            resource = scope['resource']['attributes'][0]['value']['stringValue']
            for span in scope["scopeSpans"][0]["spans"]:
                trace_id = span["traceId"]
                span_id = span["spanId"]
                parent_span_id = span.get("parentSpanId", None)
                service = resource
                operation_name = span["name"]
                kind = span["kind"]
                start_time = span["startTimeUnixNano"]
                end_time = span["endTimeUnixNano"]
                
                new_span = Span(trace_id, span_id, parent_span_id, service, operation_name, kind, start_time, end_time)
                
                # Get Child Spans previously found
                if span_id in span_dict:
                    new_span.children = span_dict[span_id].children                
                span_dict[span_id] = new_span
                
                # If parent_span_id is not None, add the new span as a child of an empty parent span
                if parent_span_id:
                    if parent_span_id in span_dict:
                        span_dict[parent_span_id].add_child(new_span)
                    else: # Handle finding child span before parent span
                        span_dict[parent_span_id] = Span(trace_id, parent_span_id, None, None, None, None, None, None)
                        span_dict[parent_span_id].add_child(new_span)
                        print(f"Found child span before parent span: {span_dict[parent_span_id]}")
                else:
                    # Add Root Span    
                    root_spans.append(new_span)
                    
    
    return root_spans

# Example usage
if __name__ == "__main__":
    with open('/home/estebanramos/projects/DeathStarBench/hotelReservation/scripts/analysis/traces.json', 'r') as f:
        traces = json.load(f)
    root_spans = parse_traces(traces)
    
    for root_span in root_spans:
        print_span_tree(root_span, fields_to_print=["trace_id", "span_id", "operation_name", "kind","service"])

        field_values = {"operation_name": "search.Search/Nearby"}
        matching_span_ids = root_span.find_spans_by_fields(field_values)
        print("Matching Span IDs:", matching_span_ids)
        
        
        leaf_spans = root_span.rank_longest_leaf_spans()
        for leaf_span in leaf_spans:
            print("Leaf Span:")
            print_span_tree(leaf_span, fields_to_print=["span_id", "operation_name", "kind","service"])
            print( leaf_span.get_span_duration(leaf_span))
            print("")
        
        for span_id in matching_span_ids:
            matching_span = root_span.get_span(span_id)
            print("Matching Span:")
            print_span_tree(matching_span, fields_to_print=["span_id", "operation_name", "kind","service"])
            print("")
            print("Matching Span proportional duration:")
            duration = root_span.get_span_proportional_duration_of_root(span_id)
            print(duration)