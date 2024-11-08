import json
from collections import defaultdict
from datetime import datetime, timedelta

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
    
    def get_all_spans(self):
        spans = [self]
        for child in self.children:
            spans.extend(child.get_all_spans())
        return spans
    
    def get_span_duration(self, span):
        return int(span.end_time) - int(span.start_time)
    
    def get_graph_signature_from_root(self):
        signature = []
        signature.append(self.operation_name)
        for child in self.children:
            signature.append(child.get_graph_signature_from_root())
        return '-'.join(signature)
        
    def get_start_gap_duration_of_parent(self, span):
        parent_span = self.get_span(span.parent_span_id)
        if parent_span:
            return  int(span.start_time) - int(parent_span.start_time)
        return None
    
    def get_end_gap_duration_of_parent(self, span):
        parent_span = self.get_span(span.parent_span_id)
        if parent_span:
            return  int(parent_span.end_time) - int(span.end_time)
        return None
    
    def get_gap_durations_of_parent(self, span):
        return self.get_start_gap_duration_of_parent(span), self.get_end_gap_duration_of_parent(span)
    
        
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

class TraceSet:
    def __init__(self, trace_file_path):
        self.trace_file_path = trace_file_path
        self.json_traces = self.load_traces()
        self.root_spans = self.parse_traces(self.json_traces)

    def load_traces(self):
        with open(self.trace_file_path, 'r') as f:
            json_traces = json.load(f)
        return json_traces   
    
    def filter_out_traces(self, field_values) -> list[Span]:
        matching_traces = []
        for root_span in self.root_spans:
            
            spans = root_span.find_spans_by_fields(field_values)
            if len(spans) > 0:
                matching_traces.append(root_span)
        return matching_traces
    
    def parse_traces(self, traces) -> list[Span]:
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
                            # print(f"Found child span before parent span: {span_dict[parent_span_id]}")
                    else:
                        # Add Root Span    
                        root_spans.append(new_span)
        return root_spans

    def get_root_spans(self):
        return self.root_spans
    
    def get_dict_of_span_durations(self, spans: list[Span]) -> dict[Span, float]:
        durations = {}
        for span in spans:
            durations[span] = span.get_span_duration(span)
        return durations

    def _calculate_durations(self, span: Span):
        total_duration = span.get_span_duration(span)
        child_intervals = []
        duration_to_subtract = 0
        # prevent overlap of parallel children durations
        for child in span.children:
            child_intervals.append((int(child.start_time), int(child.end_time)))
        
        if len(child_intervals) == 0:
            return total_duration
        
        # sort by start time
        child_intervals.sort(key=lambda x: x[0])
        
        merged_intervals = []
        current_start, current_end = child_intervals[0]
        for start, end in child_intervals[1:]:
            if start <= current_end:
                current_end = max(current_end, end)
            else:
                merged_intervals.append((current_start, current_end))
                current_start, current_end = start, end
        merged_intervals.append((current_start, current_end))
        
        duration_to_subtract = sum([end - start for start, end in merged_intervals])
        return total_duration - duration_to_subtract
    
    def get_proporational_durations(self, root: Span, spans: list[Span]) -> dict[Span, float]:
        proportional_durations = {}
        span_durations = self.get_dict_of_span_durations(spans)            
        
        #TODO: Subtract from ancestor spans that contain another included span the duration of the included span
        # TODO: Ensure it's working right
        for span_duration in span_durations.items():
            adjusted_duration = self._calculate_durations(span_duration[0])
            span_durations[span_duration[0]] = adjusted_duration
        
        for span_duration in span_durations.items():
            proportional_durations[span_duration[0]] = span_duration[1] / root.get_span_duration(root)
      
        return proportional_durations
    
    def get_list_of_gaps_with_parent(self, root: Span, spans: list[Span]) -> dict[Span, tuple[int, int]]:
        parent_gaps = {}
        for span in spans:
            parent_gaps[span] =  root.get_gap_durations_of_parent(span)
        return parent_gaps
    
    def get_proportional_durations_of_gaps(self, root: Span, spans: list[Span]) -> dict[Span, tuple[float, float]]:
        proportional_durations = {}    
        list_of_gaps = self.get_list_of_gaps_with_parent(root, spans)
        
        for span_gaps in list_of_gaps.items():
            proportional_durations[span_gaps[0]] = span_gaps[1][0] / root.get_span_duration(root), span_gaps[1][1] / root.get_span_duration(root)
      
        return proportional_durations
    
    def aggregate_span_durations(self, durations: dict[Span, float]) -> float:
        sum = 0
        for duration in durations.items():
            sum += durations[duration[0]]
        return sum
    
    def aggregate_proportional_span_durations(self, proportional_durations: dict[Span, tuple[float,float]]) -> float:
        return sum([durations[0] + durations[1] for durations in proportional_durations.values()])
        
    def print_span_durations(self, durations: dict[Span, float]):
        for span, duration in durations.items():
            print(f"{span}: {duration}")
    
    def print_proportional_span_durations(self, proportional_durations: dict[Span, float]):
        for span, duration in proportional_durations.items():
            print(f"{span}: {duration}")
            
    def print_proportional_duration_of_gaps_with_parent(self, proportional_gaps: dict[Span, tuple[float, float]]):
        for span, gaps in proportional_gaps.items():
            print(f"{span}: {gaps}")

# Example usage
if __name__ == "__main__":
    # with open('/home/estebanramos/projects/DeathStarBench/hotelReservation/scripts/analysis/traces.json', 'r') as f:
        # traces = json.load(f)
    
    tset = TraceSet('/home/estebanramos/projects/DeathStarBench/hotelReservation/scripts/analysis/traces.json')
    root_spans = tset.get_root_spans()
    
    for root_span in root_spans:
        # print_span_tree(root_span, fields_to_print=["trace_id", "span_id", "operation_name", "kind","service"])
        print("Root Span Duration:")
        print(root_span.get_span_duration(root_span))
        # print("All Spans:")
        
        field_values = {"kind": "SPAN_KIND_CLIENT"}
        client_span_ids = root_span.find_spans_by_fields(field_values)
        # Remove root span from matching span ids
        print("Client Span IDs:", client_span_ids)
        
        field_values = {"kind": "SPAN_KIND_INTERNAL"}
        interanl_span_ids = root_span.find_spans_by_fields(field_values)
        # Remove root span from matching span ids
        print("Internal Span IDs:", interanl_span_ids)

        
        # Search for server spans
        field_values = {"kind": "SPAN_KIND_SERVER"}
        server_span_ids = root_span.find_spans_by_fields(field_values)
        
        # Remove root span from matching span ids
        server_span_ids.remove(root_span.span_id)
        print("Server Span IDs:", server_span_ids)
        
        # for span_id in server_span_ids:
        #     server_span = root_span.get_span(span_id)
        #     print("Server Span:")
        #     print_span_tree(server_span, fields_to_print=["span_id", "operation_name", "kind","service"])
        #     print("")
            
        
        # tset.print_span_durations(tset.get_dict_of_span_durations([root_span.get_span(span_id) for span_id in server_span_ids]))
        # tset.print_proportional_span_durations(tset.get_proporational_durations(root_span, [root_span.get_span(span_id) for span_id in matching_span_ids]))
        # tset.print_proportional_duration_of_gaps_with_parent(tset.get_proportional_durations_of_gaps(root_span, [root_span.get_span(span_id) for span_id in matching_span_ids]))
        print("Aggregate Server-Client Gap Span Durations:")
        print(tset.aggregate_proportional_span_durations(tset.get_proportional_durations_of_gaps(root_span, [root_span.get_span(span_id) for span_id in server_span_ids])))
        print("Aggregate Server Span Durations:")
        print(tset.aggregate_span_durations( tset.get_proporational_durations(root_span, [root_span.get_span(span_id) for span_id in server_span_ids])))
        print("Aggregate Internal Span Durations:")
        print(tset.aggregate_span_durations( tset.get_proporational_durations(root_span, [root_span.get_span(span_id) for span_id in interanl_span_ids])))
        print("Aggregate Client Span Durations:")
        print(tset.aggregate_span_durations( tset.get_proporational_durations(root_span, [root_span.get_span(span_id) for span_id in client_span_ids])))



