#!/usr/bin/bash

export CGO_ENABLED=0
export GOOS=linux
export GO111MODULE=on

# Specify the directory path
BIN_DIR="./bin"

# Check if the directory exists
if [ -d "$BIN_DIR" ]; then
    echo "Directory exists. Clearing its contents..."
    rm -rf "$BIN_DIR"/*
else
    echo "Directory does not exist. Creating it..."
    mkdir -p "$BIN_DIR"
fi

export GOBIN=$(pwd)/$BIN_DIR
go install -ldflags="-s -w" -mod=vendor ./cmd/...