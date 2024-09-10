#!/bin/bash

cd ../../wrk2
git submodule update --init --recursive
sudo apt-get update
sudo apt-get install -y luarocks
sudo luarocks install luasocket
make

#run the workload
#./wrk -D exp -P -t20 -c1000 -d300s -L -s ../hotelReservation/wrk2/scripts/hotel-reservation/mixed-workload_type_1.lua http://127.0.0.1:5000 -R1000
