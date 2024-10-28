# Stage 1: Build the Go application
FROM golang:1.22 as builder

WORKDIR /workspace

# Copy necessary files for dependency resolution
COPY go.sum go.sum
COPY go.mod go.mod
COPY vendor/ vendor/

# Copy the source code
COPY cmd/ cmd/
COPY dialer/ dialer/
COPY registry/ registry/
COPY services/ services/
COPY tls/ tls/
COPY tracing/ tracing/
COPY tune/ tune/

COPY config.json config.json

COPY notnets_grpc/ notnets_grpc/

ENV LD_LIBRARY_PATH=/usr/local/lib:$LD_LIBRARY_PATH
ENV CGO_ENABLED=1
ENV CGO_CFLAGS="-I/workspace/notnets_grpc/notnets_shm/libnotnets/include"
ENV CGO_LDFLAGS="-L/workspace/notnets_grpc/notnets_shm/libnotnets/bin -lnotnets"

# Build the Go application
RUN GOOS=linux GO111MODULE=on go install -ldflags="-s -w" -mod=vendor ./cmd/...

# Stage 2: Create the final image
FROM ubuntu:22.04

WORKDIR /workspace

# Install libstdc++ to match GCC 11.4
RUN apt-get update && apt-get install -y --no-install-recommends \
    libstdc++6 gcc libc-dev && \
    rm -rf /var/lib/apt/lists/*

# Ensure the shared library is in a standard location
COPY libnotnets.so /usr/local/lib/libnotnets.so

# Set LD_LIBRARY_PATH to include /usr/local/lib
ENV LD_LIBRARY_PATH=/usr/local/lib:$LD_LIBRARY_PATH

# Copy the executables from the builder stage
COPY --from=builder /go/bin/* /workspace/
COPY --from=builder /workspace/config.json /workspace/config.json

# Set the library path for runtime
ENV LD_LIBRARY_PATH=/workspace/notnets_shm/libnotnets/bin:$LD_LIBRARY_PATH

