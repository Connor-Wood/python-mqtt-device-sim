#!/bin/bash

for i in $(seq -f "%03g" 1 10)
do
  # Call the onboard-devices.sh script with the current number
  nohup python3 telemetry_producer.py --host=iotc-fabric-migration.westus2-1.ts.eventgrid.azure.net --user="$i" > /dev/null 2>&1 &
done