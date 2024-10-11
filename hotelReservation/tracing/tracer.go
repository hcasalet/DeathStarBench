package tracing

import (
	"os"
	"strconv"
	"time"

	opentracing "github.com/opentracing/opentracing-go"
	"github.com/uber/jaeger-client-go/config"

	"github.com/rs/zerolog/log"

	otelpyroscope "github.com/grafana/otel-profiling-go"
	"github.com/grafana/pyroscope-go"

	"go.opentelemetry.io/otel"
	"go.opentelemetry.io/otel/sdk/trace"

	"go.opentelemetry.io/contrib/instrumentation/google.golang.org/grpc/otelgrpc"

	"github.com/grafana/dskit/spanprofiler"
)

var (
	defaultSampleRatio float64 = 0.01
)


func InitTracer(serviceName, host string) (*trace.TracerProvider,error){


		// Configure OTLP gRPC Exporter
		// ctx := context.Background()
		tp := trace.NewTracerProvider(
			trace.WithSampler(trace.AlwaysSample()),
		)
   
	   	// Wrap it with otelpyroscope tracer provider.
		otel.SetTracerProvider( otelpyroscope.NewTracerProvider(tp))

		// If you're using Pyroscope Go SDK, initialize pyroscope profiler.
		_, err := pyroscope.Start(pyroscope.Config{
			ApplicationName: serviceName,
			ServerAddress:   "http://172.17.0.1:4040",
			Logger:          pyroscope.StandardLogger,
			SampleRate:      101,

			ProfileTypes: []pyroscope.ProfileType{
				// these profile types are enabled by default:
				pyroscope.ProfileCPU,
				pyroscope.ProfileAllocObjects,
				pyroscope.ProfileAllocSpace,
				pyroscope.ProfileInuseObjects,
				pyroscope.ProfileInuseSpace,
		  
				// these profile types are optional:
				pyroscope.ProfileGoroutines,
				pyroscope.ProfileMutexCount,
				pyroscope.ProfileMutexDuration,
				pyroscope.ProfileBlockCount,
				pyroscope.ProfileBlockDuration,
			  },
		})
		if err != nil {
			log.Error().AnErr("error starting pyroscope profiler: %v", err)
		}
   
		otelgrpc.NewClientHandler(otelgrpc.WithTracerProvider(tp))
	   // Set the global TracerProvider
	//    otel.SetTracerProvider(tp)
   
	   return tp, nil
}

// // Instrumenting the gRPC client
// conn, _ := grpc.DialContext(
//     context.Background(),
//     "localhost:50051",
//     grpc.WithInsecure(),
//     grpc.WithUnaryInterceptor(otelgrpc.UnaryClientInterceptor()),
//     grpc.WithStreamInterceptor(otelgrpc.StreamClientInterceptor()),
// )

// // Instrumenting the gRPC server
// grpcServer := grpc.NewServer(
//     grpc.UnaryInterceptor(otelgrpc.UnaryServerInterceptor()),
//     grpc.StreamInterceptor(otelgrpc.StreamServerInterceptor()),
// )

// Init returns a newly configured tracer
func Init(serviceName, host string) (opentracing.Tracer, error) {
	ratio := defaultSampleRatio
	if val, ok := os.LookupEnv("JAEGER_SAMPLE_RATIO"); ok {
		ratio, _ = strconv.ParseFloat(val, 64)
		if ratio > 1 {
			ratio = 1.0
		}
	}

	log.Info().Msgf("Jaeger client: adjusted sample ratio %f", ratio)
	tempCfg := &config.Configuration{
		ServiceName: serviceName,
		Sampler: &config.SamplerConfig{
			Type:  "probabilistic",
			Param: ratio,
		},
		Reporter: &config.ReporterConfig{
			LogSpans:            false,
			BufferFlushInterval: 1 * time.Second,
			LocalAgentHostPort:  host,
		},
	}

	log.Info().Msg("Overriding Jaeger config with env variables")
	cfg, err := tempCfg.FromEnv()
	if err != nil {
		return nil, err
	}

	tracer, _, err := cfg.NewTracer()
	if err != nil {
		return nil, err
	}

	wrappedTracer := spanprofiler.NewTracer(tracer)
	opentracing.SetGlobalTracer(wrappedTracer)



	return tracer, nil
}
