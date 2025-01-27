# Stage 1: Build the Go application
FROM golang:1.22 AS builder

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
COPY bin/ bin/

COPY config.json config.json

# Build the Go application
ENV GOBIN=/workspace
RUN CGO_ENABLED=0 GOOS=linux GO111MODULE=on go install -ldflags="-s -w" -mod=vendor ./cmd/...

# Stage 2: Create the final image
FROM alpine:latest

WORKDIR /workspace

# Copy the executables from the builder stage
COPY --from=builder /workspace/ /workspace/
