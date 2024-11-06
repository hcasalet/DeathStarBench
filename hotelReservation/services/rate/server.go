package rate

import (
	"context"
	"encoding/json"
	"fmt"
	"net"
	"sort"
	"strings"
	"sync"
	"time"

	"github.com/EIRNf/notnets_grpc"
	"github.com/bradfitz/gomemcache/memcache"
	"github.com/delimitrou/DeathStarBench/tree/master/hotelReservation/registry"
	pb "github.com/delimitrou/DeathStarBench/tree/master/hotelReservation/services/rate/proto"
	"github.com/delimitrou/DeathStarBench/tree/master/hotelReservation/tls"
	"github.com/google/uuid"
	"github.com/rs/zerolog/log"
	"go.mongodb.org/mongo-driver/bson"
	"go.mongodb.org/mongo-driver/mongo"
	"google.golang.org/grpc"
	"google.golang.org/grpc/keepalive"

	"go.opentelemetry.io/contrib/instrumentation/google.golang.org/grpc/otelgrpc"
	"go.opentelemetry.io/otel"
	"go.opentelemetry.io/otel/attribute"
)

const name = "srv-rate"
const LARGE_MESSAGE_SIZE = 4194304 //1MB


// Server implements the rate service
type Server struct {
	pb.UnimplementedRateServer

	uuid string

	Port        int
	IpAddr      string
	MongoClient *mongo.Client
	Registry    *registry.Client
	MemcClient  *memcache.Client
}

// Run starts the server
func (s *Server) Run(_overShm bool) error {

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
		//grpc.UnaryInterceptor(
		//	otgrpc.OpenTracingServerInterceptor(s.Tracer),
		//),
		grpc.UnaryInterceptor(unaryInterceptor),
	}

	if tlsopt := tls.GetServerOpt(); tlsopt != nil {
		opts = append(opts, tlsopt)
	}

	if _overShm {
		srv := notnets_grpc.NewNotnetsServer(notnets_grpc.SetMessageSize(LARGE_MESSAGE_SIZE))
		pb.RegisterRateServer(srv, s)

		// listener
		lis := notnets_grpc.Listen("srv-rate")

		return srv.Serve(lis)
	} else {
		srv := grpc.NewServer(opts...)

		pb.RegisterRateServer(srv, s)

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
}

// Shutdown cleans up any processes
func (s *Server) Shutdown() {
	s.Registry.Deregister(s.uuid)
}

// GetRates gets rates for hotels for specific date range.
func (s *Server) GetRates(ctx context.Context, req *pb.Request) (*pb.Result, error) {
	res := new(pb.Result)

	ratePlans := make(RatePlans, 0)

	hotelIds := []string{}
	rateMap := make(map[string]struct{})
	for _, hotelID := range req.HotelIds {
		hotelIds = append(hotelIds, hotelID)
		rateMap[hotelID] = struct{}{}
	}
	// first check memcached(get-multi)
	tracer := otel.GetTracerProvider().Tracer(uuid.NewString())

	_, memSpan := tracer.Start(ctx, "memcached_get_multi_rate")
	memSpan.SetAttributes(attribute.String("span.kind", "client"))

	resMap, err := s.MemcClient.GetMulti(hotelIds)
	memSpan.End()

	var wg sync.WaitGroup
	var mutex sync.Mutex
	if err != nil && err != memcache.ErrCacheMiss {
		log.Panic().Msgf("Memmcached error while trying to get hotel [id: %v]= %s", hotelIds, err)
	} else {
		for hotelId, item := range resMap {
			rateStrs := strings.Split(string(item.Value), "\n")
			log.Trace().Msgf("memc hit, hotelId = %s,rate strings: %v", hotelId, rateStrs)

			for _, rateStr := range rateStrs {
				if len(rateStr) != 0 {
					rateP := new(pb.RatePlan)
					json.Unmarshal([]byte(rateStr), rateP)
					ratePlans = append(ratePlans, rateP)
				}
			}

			delete(rateMap, hotelId)
		}

		wg.Add(len(rateMap))
		for hotelId := range rateMap {
			go func(id string) {
				log.Trace().Msgf("memc miss, hotelId = %s", id)
				log.Trace().Msg("memcached miss, set up mongo connection")

				_, mongoSpan := tracer.Start(ctx, "mongo_rate")
				mongoSpan.SetAttributes(attribute.String("span.kind", "client"))

				// memcached miss, set up mongo connection
				collection := s.MongoClient.Database("rate-db").Collection("inventory")
				curr, err := collection.Find(context.TODO(), bson.D{})
				if err != nil {
					log.Error().Msgf("Failed get rate data: ", err)
				}

				tmpRatePlans := make(RatePlans, 0)
				curr.All(context.TODO(), &tmpRatePlans)
				if err != nil {
					log.Error().Msgf("Failed get rate data: ", err)
				}

				mongoSpan.End()

				memcStr := ""
				if err != nil {
					log.Panic().Msgf("Tried to find hotelId [%v], but got error", id, err.Error())
				} else {
					for _, r := range tmpRatePlans {
						mutex.Lock()
						ratePlans = append(ratePlans, r)
						mutex.Unlock()
						rateJson, err := json.Marshal(r)
						if err != nil {
							log.Error().Msgf("Failed to marshal plan [Code: %v] with error: %s", r.Code, err)
						}
						memcStr = memcStr + string(rateJson) + "\n"
					}
				}

				go func(item *memcache.Item) {
					_, memSpan := tracer.Start(ctx, "memcached_set_rate")
					memSpan.SetAttributes(attribute.String("span.kind", "client"))
					s.MemcClient.Set(item)
					memSpan.End()

				}(&memcache.Item{Key: id, Value: []byte(memcStr)})

				defer wg.Done()
			}(hotelId)
		}
	}
	wg.Wait()

	sort.Sort(ratePlans)
	res.RatePlans = ratePlans

	return res, nil
}

type RatePlans []*pb.RatePlan

func (r RatePlans) Len() int {
	return len(r)
}

func (r RatePlans) Swap(i, j int) {
	r[i], r[j] = r[j], r[i]
}

func (r RatePlans) Less(i, j int) bool {
	return r[i].RoomType.TotalRate > r[j].RoomType.TotalRate
}
