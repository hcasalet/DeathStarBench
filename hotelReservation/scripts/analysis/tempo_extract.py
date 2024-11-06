from concurrent.futures import ProcessPoolExecutor
import urllib.request

import requests
import json
import urllib

class TempoClient:
    def __init__(self, base_url):
        self.base_url = base_url
        
    def get_tags(self) -> list:
        url = f"{self.base_url}/api/search/tags"
        response = requests.get(url)
        response.raise_for_status()
        resp = response.json()
        tag_list = resp.get('tagNames')
        return tag_list

    def get_services(self):
        url = f"{self.base_url}/api/search/tag/service.name/values"
        response = requests.get(url)
        response.raise_for_status()
        resp = response.json()
        service_names = resp.get('tagValues')
        return service_names

    def query_traces(self, query):
        url = f"{self.base_url}/api/search"
        
        
        # print(requests.get(url, params=query).request.path_url)
        response = requests.get(url, params=query)
        response.raise_for_status()
        return response.json()

    def get_trace(self, trace_id):
        url = f"{self.base_url}/api/traces/{trace_id}"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()

def collect_traces_with_query(client, query):
    traces = []
    search_results = client.query_traces(query)
    trace_ids = []

    print(f"Num Traces: {len(search_results.get('traces', []))}") 
    for trace in search_results.get('traces', []):
        trace_id = trace.get('traceID')
        if trace_id:
            trace_ids.append(trace_id)

            #trace_data = client.get_trace(trace_id)
            #traces.append(trace_data)
    
    with ProcessPoolExecutor(max_workers=8) as executor:
        for trace_data in executor.map(client.get_trace, trace_ids):
            if trace_data:
                traces.append(trace_data)

    return traces

def main():
    base_url = "http://localhost:3200"
    client = TempoClient(base_url)

    # print(f" Tags: { client.get_tags()}")
    
    
    query = {
        "limit": 2,
        "kind": "server",
        "tags": ["http.status_code=200", "http.target=\hotels"],
        # "tags=http.target": "\hotels"
        # "tags" : {
        #     "http.status_code": "200"
        # }
    }

    traces = collect_traces_with_query(client, query)

    with open('traces.json', 'w') as f:
        json.dump(traces, f, indent=4)

if __name__ == "__main__":
    main()
