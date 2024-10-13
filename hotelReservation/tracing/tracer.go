package tracing

import (
	"context"

	otelpyroscope "github.com/grafana/otel-profiling-go"
	"github.com/grafana/pyroscope-go"

	opentracing "github.com/opentracing/opentracing-go"

	"go.opentelemetry.io/otel"
	otelBridge "go.opentelemetry.io/otel/bridge/opentracing"
	"go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracehttp"
	"go.opentelemetry.io/otel/sdk/resource"
	"go.opentelemetry.io/otel/sdk/trace"
	semconv "go.opentelemetry.io/otel/semconv/v1.26.0"
)

var (
	defaultSampleRatio float64 = 1.0
)

// Init returns a newly configured tracer
func Init(serviceName, host string) (opentracing.Tracer, error) {


	ctx := context.Background()

	// Create the OTLP trace exporter
	exp, err := otlptracehttp.New(ctx, otlptracehttp.WithEndpointURL("http://172.17.0.1:4318"))
	if err != nil {
		panic(err)
	}

	res, err := resource.New(ctx,
		resource.WithAttributes(
			semconv.ServiceNameKey.String(serviceName),
		),)

	bsp := trace.NewBatchSpanProcessor(exp)
	tp := trace.NewTracerProvider(trace.WithResource(res), trace.WithSpanProcessor(bsp))

	// Create the OTLP trace provider with the exporter
	// and wrap it with the pyroscope tracer provider
	otelTracerProvider := otelpyroscope.NewTracerProvider(tp)
	otelTracer := otelTracerProvider.Tracer(serviceName)

	// Use the bridgeTracer as your OpenTracing tracer.
	openTracingBridgeTracer, wrapperTracerProvider := otelBridge.NewTracerPair(otelTracer)
	// Use the wrapped tracer in your application
	opentracing.SetGlobalTracer(openTracingBridgeTracer)
	otel.SetTracerProvider(wrapperTracerProvider)

	// Set the wrapperTracerProvider as the global OpenTelemetry
	// TracerProvider so instrumentation will use it by default.
	// Wrap it with the tracer-profiler 
	// wrappedTracer := spanprofiler.NewTracer(openTracingBridgeTracer)

	pyroscope.Start(pyroscope.Config{
		ApplicationName: serviceName,
		// replace this with the address of pyroscope server
		ServerAddress:   "http://172.17.0.1:4040",
	
		// you can disable logging by setting this to nil
		// Logger:          pyroscope.StandardLogger,
	
		// by default all profilers are enabled,
		// but you can select the ones you want to use:
		ProfileTypes: []pyroscope.ProfileType{
		  pyroscope.ProfileCPU,
		  pyroscope.ProfileAllocObjects,
		  pyroscope.ProfileAllocSpace,
		  pyroscope.ProfileInuseObjects,
		  pyroscope.ProfileInuseSpace,
		},
	  })
	

	return openTracingBridgeTracer, nil
}

