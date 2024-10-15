package dialer

import (
	"fmt"
	"time"

	"github.com/delimitrou/DeathStarBench/tree/master/hotelReservation/tls"
	//"github.com/grpc-ecosystem/grpc-opentracing/go/otgrpc"
	consul "github.com/hashicorp/consul/api"
	"go.opentelemetry.io/contrib/instrumentation/google.golang.org/grpc/otelgrpc"
	"google.golang.org/grpc"
	"google.golang.org/grpc/keepalive"
)

// DialOption allows optional config for dialer
type DialOption func(name string) (grpc.DialOption, error)

// WithTracer traces rpc calls
func WithTracer() DialOption {
	return func(name string) (grpc.DialOption, error) {
		return grpc.WithUnaryInterceptor(otelgrpc.UnaryClientInterceptor()), nil
	}
}

// WithBalancer enables client side load balancing
func WithBalancer(registry *consul.Client) DialOption {
	return func(name string) (grpc.DialOption, error) {
		return grpc.WithDefaultServiceConfig(`{"loadBalancingConfig": [{"round_robin":{}}]}`), nil
	}
}

// Dial returns a load balanced grpc client conn with tracing interceptor
func Dial(name string, opts ...DialOption) (*grpc.ClientConn, error) {

	dialopts := []grpc.DialOption{
		grpc.WithKeepaliveParams(keepalive.ClientParameters{
			Timeout:             120 * time.Second,
			PermitWithoutStream: true,
		}),
	}
	if tlsopt := tls.GetDialOpt(); tlsopt != nil {
		dialopts = append(dialopts, tlsopt)
	} else {
		dialopts = append(dialopts, grpc.WithInsecure())
	}

	for _, fn := range opts {
		opt, err := fn(name)
		if err != nil {
			return nil, fmt.Errorf("config error: %v", err)
		}
		dialopts = append(dialopts, opt)
	}

	conn, err := grpc.Dial(name, dialopts...)
	if err != nil {
		return nil, fmt.Errorf("failed to dial %s: %v", name, err)
	}

	return conn, nil
}
