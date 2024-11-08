package benchmark

import (
	"fmt"
	"net"
	"time"

	"github.com/delimitrou/DeathStarBench/tree/master/hotelReservation/registry"
	pb "github.com/delimitrou/DeathStarBench/tree/master/hotelReservation/services/benchmark/proto"
	"github.com/delimitrou/DeathStarBench/tree/master/hotelReservation/tls"
	"github.com/google/uuid"
	"github.com/rs/zerolog/log"
	"go.opentelemetry.io/contrib/instrumentation/google.golang.org/grpc/otelgrpc"
	"go.opentelemetry.io/otel"
	"golang.org/x/net/context"
	"google.golang.org/grpc"
	"google.golang.org/grpc/keepalive"
)

const name = "srv-benchmark"
const slow_service_iter = 100000
const fast_service_iter = 1000

// Server implements the user service
type Server struct {
	pb.UnimplementedBenchmarkServer

	uuid  string

	Registry    *registry.Client
	Port        int
	IpAddr      string

}

// Run starts the server
func (s *Server) Run() error {
	if s.Port == 0 {
		return fmt.Errorf("server port must be set")
	}

	s.uuid = uuid.New().String()

	tp := otel.GetTracerProvider()
	unaryInterceptor := otelgrpc.UnaryServerInterceptor(otelgrpc.WithTracerProvider(tp))

	opts := []grpc.ServerOption{
		grpc.KeepaliveParams(keepalive.ServerParameters{
			Timeout: 120 * time.Second,
		}),
		grpc.KeepaliveEnforcementPolicy(keepalive.EnforcementPolicy{
			PermitWithoutStream: true,
		}),
		grpc.UnaryInterceptor(unaryInterceptor),
	}

	if tlsopt := tls.GetServerOpt(); tlsopt != nil {
		opts = append(opts, tlsopt)
	}

	srv := grpc.NewServer(opts...)

	pb.RegisterBenchmarkServer(srv, s)

	lis, err := net.Listen("tcp", fmt.Sprintf(":%d", s.Port))
	if err != nil {
		log.Fatal().Msgf("failed to listen: %v", err)
	}

	err = s.Registry.Register(name, s.uuid, s.IpAddr, s.Port)
	if err != nil {
		return fmt.Errorf("failed register: %v", err)
	}
	log.Info().Msg("Successfully registered in consul")

	return srv.Serve(lis)
}

// Shutdown cleans up any processes
func (s *Server) Shutdown() {
	s.Registry.Deregister(s.uuid)
}

func GetBasePayload(num_chunks int) []*pb.LoadPayload {
	payload := []*pb.LoadPayload{}
	for i := 0; i < num_chunks; i++ {
		payload = append(payload, &pb.LoadPayload{Data: "pzxpcmfmzqozppzbrmgrjoaridoqxtxbnhsbkskwtaivdnltiuuyeescbmhxsogxyxklgelwfahvhgowxqlunthogrsumhmowwgfclowwlqudiwrxgdmylinvfdipyewvhfeehfkcxwjhcayowkonrdtxfwiwyepibmzdacoqfebtqbhfawroxpzywlhqdvwhsusylnqkbfdhwpriqafbmdnusqurelxzdabxhtxkcacimtwqvbeastkmgtlbvhmxbeyeqwomroshgjoazheimxsjziktbcfjynxkkckcgdvnabgvqthkftdcvnwsrosukfsakswqvgceqwmemvvwvhrymomfooqiawlitsucrojldmtjpbquhnsusdkcumubecfyhuldvexecuiucktnxouwsatqpcyiowhriwkbubwcjekmfwavzaetqhddplrcqoxlvsdomvijvltwgzelvtdojxcolgsdvzcxssfcxxegmjxeyhuqpzxinthioqlbmwvqlgjwclkjxuprbbvxqatuikwmqdoashecroztxxxcpnuwhepcwwqsgvfosefahxeyoxpolpbnkcfcwilhltglqbrjxzlaizurznchkyhfnswahnwtpvdalahwbfsatudnuvgvqmjriqsueyvnagcuydmhmquwslyzmmzthxcctkrldbkxqicycqsszaiwocwrhapsyjkwgldxkxcrwlcacbfcjxwuvjqmeslpgijjgtyqarwtzncbpkdqntowehooyumsdylcxhxbtsjuifahpabwohknexqanslhhaekdobqngxatjpmudcoydtuipwrorkawwpjngnbtblxfvcjelsalbfeojlzrfabcjqpsyyynqnfzlzawgebejexwnfzbchlzakynfmpynlcsxregnuavwadqdnfsysgqpqrhqsvzuzednryudotwsgdofbekhowwvxhvpfcwsabxyinigubpmrrrwwzaiaevlvjhyiuspviokvdcfyssya"}) // 1KB
		
	}
	return payload
}

func (s *Server) SlowService(ctx context.Context, in *pb.Request) (*pb.Result, error) {

	payload_ret := []*pb.LoadPayload{}
	payload_set := in.GetLoad()
	if in.LargeResponse { // if large response, return the same payload
		data := payload_set
		payload_ret = data
	} else { // if small response, return length of payload
		data := string(len(payload_set))
		payload_ret = append(payload_ret, &pb.LoadPayload{Data: data})
	}

	for  i := 0; i < slow_service_iter; i++ {
		// do some computation
	}

	return &pb.Result{ Load:  payload_ret}, nil
}

func (s *Server) FastService(ctx context.Context, in *pb.Request) (*pb.Result, error) {

	payload_ret := []*pb.LoadPayload{}
	payload_set := in.GetLoad()
	if in.LargeResponse { // if large response, return the same payload
		data := payload_set
		payload_ret = data
	} else { // if small response, return length of payload
		data := string(len(payload_set))
		payload_ret = append(payload_ret, &pb.LoadPayload{Data: data})
	}

	for  i := 0; i < fast_service_iter; i++ {
		// do some computation
	}

	return &pb.Result{ Load:  payload_ret}, nil
}