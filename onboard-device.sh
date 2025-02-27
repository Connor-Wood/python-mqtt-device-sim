#!/bin/bash

# Check if a parameter is passed
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <replacement_string>"
    exit 1
fi

# Replacement string
replacement=$1

source az.env
host_name=$(az resource show --ids $res_id --query "properties.topicSpacesConfiguration.hostname" -o tsv)

mkdir -p keys

# Replace "03" with the provided string in the commands
step certificate create \
    "$replacement" keys/"$replacement".pem keys/"$replacement".key \
    --ca ~/.step/certs/intermediate_ca.crt \
    --ca-key ~/.step/secrets/intermediate_ca_key \
    --no-password --insecure \
    --ca-password-file=password.txt \
    --not-after 2400h

az resource create --id "$res_id/clients/$replacement" --properties "{
    \"authenticationName\": \"$replacement\",
    \"state\": \"Enabled\",
    \"clientCertificateAuthentication\": {
        \"validationScheme\": \"SubjectMatchesAuthenticationName\"
    },
    \"attributes\": {
        \"type\": \"vehicle\"
    },
    \"description\": \"This is a test publisher client\"
}"

nohup python3 telemetry_producer.py --host=iotc-fabric-migration.westus2-1.ts.eventgrid.azure.net --user="$replacement" > /dev/null 2>&1 &