// Package grpchan provides an abstraction for a gRPC transport, called a
// Channel. The channel is more general than the concrete *grpc.ClientConn
// and *grpc.Server types provided by gRPC. It allows gRPC over alternate
// substrates and includes sub-packages that provide two such alternatives:
// in-process and HTTP 1.1.
//
// The key type in this package is an alternate implementation of
// grpc.ServiceRegistrar interface that allows you to accumulate service
// registrations, for use with an implementation other than *grpc.Server.
//
// Protoc Plugin
//
// This repo also includes a deprecated protoc plugin. This is no longer
// needed now that the standard protoc-gen-go-grpc plugin generates code that
// uses interfaces: grpc.ClientConnInterface and grpc.ServiceRegistrar. In
// older versions, the generated code only supported concrete types
// (*grpc.ClientConn and *grpc.Server) so this repo's protoc plugin would
// generate alternate code that used interfaces (and thus supported other
// concrete implementations).
//
// Continued use of the plugin is only to continue supporting code that
// uses the functions generated by it.
//
// To use the protoc plugin, you need to first build it and make sure its
// location is in your PATH.
//
//   go install github.com/fullstorydev/grpchan/cmd/protoc-gen-grpchan
//   # If necessary, make sure its location is on your path like so:
//   #   export PATH=$PATH:$GOPATH/bin
//
// When you invoke protoc, include a --grpchan_out parameter that indicates
// the same output directory as used for your --go_out parameter. Alongside
// the *.pb.go files generated, the grpchan plugin will also create
// *.pb.grpchan.go files.
//
// In older versions of the Go plugin (when emitting gRPC code), a server
// registration function for each RPC service defined in the proto source files
// was generated that looked like so:
//
//    // A function with this signature is generated, for registering
//    // server handlers with the given server.
//    func Register<ServiceName>Server(s *grpc.Server, srv <ServiceName>Server) {
//        s.RegisterService(&_<ServiceName>_serviceDesc, srv)
//    }
//
// The grpchan plugin produces a similarly named method that accepts the
// ServiceRegistry interface:
//
//    func RegisterHandler<ServiceName>(sr grpchan.ServiceRegistry, srv <ServiceName>Server) {
//        s.RegisterService(&_<ServiceName>_serviceDesc, srv)
//    }
//
// A new transport can then be implemented by just implementing two interfaces:
// grpc.ClientConnInterface for the client side and grpchan.ServiceRegistry for
// the server side.
//
// The alternate method also works just fine with *grpc.Server as it implements
// the ServiceRegistry interface.
//
// NOTE: If your have code relying on New<ServiceName>ChannelClient methods that
// earlier versions of this package produced, they can still be generated by passing
// a "legacy_stubs" option to the plugin. Example:
//
//    protoc foo.proto --grpchan_out=legacy_stubs:./output/dir
//
// Client-Side Channels
//
// The client-side implementation of a transport is done with just the two
// methods in grpc.ClientConnInterface: one for unary RPCs and the other for
// streaming RPCs.
//
// Note that when a unary interceptor is invoked for an RPC on a channel that
// is *not* a *grpc.ClientConn, the parameter of that type will be nil.
//
// Not all client call options will make sense for all transports. This repo
// chooses to ignore call options that do not apply (as opposed to failing
// the RPC or panicking). However, several call options are likely important
// to support: those for accessing header and trailer metadata. The peer,
// per-RPC credentials, and message size limits are other options that are
// reasonably straight-forward to apply to other transports. But the other
// options (dealing with on-the-wire encoding, compression, etc) may not be
// applicable.
//
// Server-Side Service Registries
//
// The server-side implementation of a transport must be able to invoke
// method and stream handlers for a given service implementation. This is done
// by implementing the grpc.ServiceRegistrar interface. When a service is
// registered, a service description is provided that includes access to method
// and stream handlers. When the transport receives requests for RPC operations,
// it in turn invokes these handlers. For streaming operations, it must also
// supply a grpc.ServerStream implementation, for exchanging messages on the
// stream.
//
// Note that the server stream's context will need a custom implementation of
// the grpc.ServerTransportStream in it, too. Sadly, this interface is just
// different enough from grpc.ServerStream that they cannot be implemented by
// the same type. This is particularly necessary for unary calls since this is
// how a unary handler indicates what headers and trailers to send back to the
// client.
package grpchan