// Copyright (c) 2017 Uber Technologies, Inc.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
// http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

package tracing

import (
	"net/http"

	"go.opentelemetry.io/contrib/instrumentation/net/http/otelhttp"
)

// NewServeMux creates a new TracedServeMux.
func OtelNewServeMux() *OtelTracedServeMux {
	return &OtelTracedServeMux{
		mux:    http.NewServeMux(),
	}
}

// TracedServeMux is a wrapper around http.ServeMux that instruments handlers for tracing.
type OtelTracedServeMux struct {
	mux    *http.ServeMux
}

// Handle implements http.ServeMux#Handle
func (tm *OtelTracedServeMux) Handle(pattern string, handler http.Handler) {
	otel_handler := otelhttp.NewHandler(handler, pattern)
	tm.mux.Handle(pattern, otel_handler)
}

// ServeHTTP implements http.ServeMux#ServeHTTP
func (tm *OtelTracedServeMux) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	tm.mux.ServeHTTP(w, r)
}
