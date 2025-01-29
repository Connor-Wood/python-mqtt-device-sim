#!/bin/bash

# Loop through numbers from 001 to 1000
for i in $(seq -f "%03g" 1 1000)
do
  # Call the onboard-devices.sh script with the current number
  bash onboard-device.sh $i
done
