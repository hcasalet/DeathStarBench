#!/bin/bash -x




# Capture the start timestamp
start_time=$(echo $EPOCHSECONDS)

# ../../../wrk2/wrk -D exp -t20 -c1000 -d60s -L -s ./wrk2/scripts/hotel-reservation/mixed-workload_type_1.lua http://127.0.0.1:5000 -R1000


# Capture the output of the wrk command
output=$(../../../wrk2/wrk -D exp -t20 -c1000 -d45s -L -s ../../wrk2/scripts/hotel-reservation/mixed-workload_type_1.lua http://127.0.0.1:5000 -R1000)

# p50="50.000%"
# p50_value=$(echo "$output" | grep "$p50" | awk '{print $2}')

# p75="75.000%"
# p75_value=$(echo "$output" | grep "$p75" | awk '{print $2}')

# p90="90.000%"
# p90_value=$(echo "$output" | grep "$p90" | awk '{print $2}')

# p99="99.000%"
# p99_value=$(echo "$output" | grep "$p99" | awk '{print $2}')

# Capture the end timestamp
end_time=$(echo $EPOCHSECONDS)

# Save the ouput to file
echo $output > output.txt

# python3.11 traces.py --extract --start=$start_time --end=$end_time --window=2