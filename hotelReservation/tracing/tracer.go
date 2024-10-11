package tracing

import (
	"os"
	"strconv"
	"time"

	"github.com/grafana/dskit/spanprofiler"
	"github.com/grafana/pyroscope-go"
	opentracing "github.com/opentracing/opentracing-go"
	"github.com/rs/zerolog/log"
	"github.com/uber/jaeger-client-go/config"
)

var (
	defaultSampleRatio float64 = 1.0
)

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

	pyroscope.Start(pyroscope.Config{
		ApplicationName: serviceName,
		// replace this with the address of pyroscope server
		ServerAddress:   "http://172.17.0.1:4040",
	
		// you can disable logging by setting this to nil
		Logger:          pyroscope.StandardLogger,
		UploadRate:    1.0,
	
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
	

	// Wrap it with the tracer-profiler 
	wrappedTracer := spanprofiler.NewTracer(tracer)
	// Use the wrapped tracer in your application
	opentracing.SetGlobalTracer(wrappedTracer)

	return wrappedTracer, nil
}

