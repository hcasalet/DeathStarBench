package tracing

import (
	"context"
	"runtime"

	otelpyroscope "github.com/grafana/otel-profiling-go"
	"github.com/grafana/pyroscope-go"

	"go.opentelemetry.io/otel"
	"go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracehttp"
	"go.opentelemetry.io/otel/sdk/resource"
	"go.opentelemetry.io/otel/sdk/trace"
	semconv "go.opentelemetry.io/otel/semconv/v1.26.0"

	"go.opentelemetry.io/otel/propagation"
)

var (
	defaultSampleRatio float64 = 1.0
)

// func InitTracer(serviceName string) func() {
// 	exporter, err := stdouttrace.New(stdouttrace.WithPrettyPrint())
// 	if err != nil {
// 		log.Fatal(err)
// 	}

// 	tp := trace.NewTracerProvider(
// 		trace.WithBatcher(exporter),
// 		trace.WithResource(resource.NewWithAttributes(
// 			semconv.SchemaURL,
// 			semconv.ServiceNameKey.String(serviceName),
// 		)),
// 	)

// 	otel.SetTracerProvider(tp)

// 	return func() {
// 		_ = tp.Shutdown(context.Background())
// 	}
// }


// Init returns a newly configured tracer
func Init(serviceName string) ( error) {

	runtime.SetCPUProfileRate(2000)

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
	tp := trace.NewTracerProvider(trace.WithResource(res), trace.WithSpanProcessor(bsp), trace.WithSampler(trace.AlwaysSample()))

	// Create the OTLP trace provider with the exporter
	// and wrap it with the pyroscope tracer provider
	otelTracerProvider := otelpyroscope.NewTracerProvider(tp)
	// otelTracer := otelTracerProvider.Tracer(serviceName)

	// Use the bridgeTracer as your OpenTracing tracer.
	// openTracingBridgeTracer, wrapperTracerProvider := otelBridge.NewTracerPair(otelTracer)
	// Use the wrapped tracer in your application
	// opentracing.SetGlobalTracer(openTracingBridgeTracer)
	otel.SetTracerProvider(otelTracerProvider)
	otel.SetTextMapPropagator(propagation.TraceContext{})


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
		// ProfileTypes: []pyroscope.ProfileType{
		//   pyroscope.ProfileCPU,
		//   pyroscope.ProfileAllocObjects,
		//   pyroscope.ProfileAllocSpace,
		//   pyroscope.ProfileInuseObjects,
		//   pyroscope.ProfileInuseSpace,
		// },
	  })



	return err
}

