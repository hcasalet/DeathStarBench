#!/bin/bash

wget https://dl.google.com/go/go1.22.4.linux-amd64.tar.gz
sudo tar -xvf go1.22.4.linux-amd64.tar.gz -C /usr/local
echo "export PATH=\$PATH:/usr/local/go/bin" >> ~/.bashrc
source ~/.bashrc
go version

cd DeathStarBench/hotelReservation
docker-compose up -d --build
