module github.com/delimitrou/DeathStarBench/tree/master/hotelReservation

go 1.22

toolchain go1.23.2

replace github.com/EIRNf/notnets_grpc => ./notnets_grpc

require (
	github.com/EIRNf/notnets_grpc v0.0.0-20241025031340-9b21afb7cec6
	github.com/bradfitz/gomemcache v0.0.0-20230905024940-24af94b03874
	github.com/google/uuid v1.6.0
	github.com/grafana/otel-profiling-go v0.5.1
	github.com/grafana/pyroscope-go v1.2.0
	github.com/hailocab/go-geoindex v0.0.0-20160127134810-64631bfe9711
	github.com/hashicorp/consul/api v1.26.1
	github.com/mbobakov/grpc-consul-resolver v1.5.3
	github.com/opentracing-contrib/go-stdlib v1.0.0
	github.com/opentracing/opentracing-go v1.2.0
	github.com/rs/zerolog v1.33.0
	go.mongodb.org/mongo-driver v1.12.2
	go.opentelemetry.io/contrib/instrumentation/net/http/otelhttp v0.55.0
	go.opentelemetry.io/otel v1.31.0
	go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracehttp v1.29.0
	go.opentelemetry.io/otel/sdk v1.31.0
	golang.org/x/net v0.30.0
	google.golang.org/grpc v1.65.1
	google.golang.org/protobuf v1.35.1
)

require (
	github.com/cenkalti/backoff/v4 v4.3.0 // indirect
	github.com/felixge/httpsnoop v1.0.4 // indirect
	github.com/go-logr/logr v1.4.2 // indirect
	github.com/go-logr/stdr v1.2.2 // indirect
	github.com/grafana/pyroscope-go/godeltaprof v0.1.8 // indirect
	github.com/grpc-ecosystem/grpc-gateway/v2 v2.22.0 // indirect
	github.com/miekg/dns v1.1.50 // indirect
	go.opentelemetry.io/contrib/instrumentation/google.golang.org/grpc/otelgrpc v0.54.0
	go.opentelemetry.io/otel/exporters/otlp/otlptrace v1.31.0 // indirect
	go.opentelemetry.io/otel/metric v1.31.0 // indirect
	go.opentelemetry.io/otel/trace v1.31.0 // indirect
	go.opentelemetry.io/proto/otlp v1.3.1 // indirect
)

require (
	github.com/armon/go-metrics v0.4.1 // indirect
	github.com/bufbuild/protocompile v0.14.1 // indirect
	github.com/fatih/color v1.15.0 // indirect
	github.com/fullstorydev/grpchan v1.1.1 // indirect
	github.com/go-playground/form v3.1.4+incompatible // indirect
	github.com/golang/snappy v0.0.4 // indirect
	github.com/hashicorp/errwrap v1.1.0 // indirect
	github.com/hashicorp/go-cleanhttp v0.5.2 // indirect
	github.com/hashicorp/go-hclog v1.5.0 // indirect
	github.com/hashicorp/go-immutable-radix v1.3.1 // indirect
	github.com/hashicorp/go-multierror v1.1.1 // indirect
	github.com/hashicorp/go-rootcerts v1.0.2 // indirect
	github.com/hashicorp/golang-lru v0.5.4 // indirect
	github.com/hashicorp/serf v0.10.1 // indirect
	github.com/jpillora/backoff v1.0.0 // indirect
	github.com/klauspost/compress v1.17.8 // indirect
	github.com/mattn/go-colorable v0.1.13 // indirect
	github.com/mattn/go-isatty v0.0.20 // indirect
	github.com/mitchellh/go-homedir v1.1.0 // indirect
	github.com/mitchellh/mapstructure v1.5.0 // indirect
	github.com/montanaflynn/stats v0.0.0-20171201202039-1bf9dbcd8cbe // indirect
	github.com/pkg/errors v0.9.1 // indirect
	github.com/xdg-go/pbkdf2 v1.0.0 // indirect
	github.com/xdg-go/scram v1.1.2 // indirect
	github.com/xdg-go/stringprep v1.0.4 // indirect
	github.com/youmark/pkcs8 v0.0.0-20181117223130-1be2e3e5546d // indirect
	golang.org/x/crypto v0.28.0 // indirect
	golang.org/x/exp v0.0.0-20230817173708-d852ddb80c63 // indirect
	golang.org/x/sync v0.8.0 // indirect
	golang.org/x/sys v0.26.0 // indirect
	golang.org/x/text v0.19.0 // indirect
	google.golang.org/genproto/googleapis/api v0.0.0-20240822170219-fc7c04adadcd // indirect
	google.golang.org/genproto/googleapis/rpc v0.0.0-20241021214115-324edc3d5d38 // indirect
	modernc.org/libc v1.61.0 // indirect
)

replace github.com/hashicorp/consul => github.com/hashicorp/consul v1.15.7
