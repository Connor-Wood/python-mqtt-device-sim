# python-mqtt-device-sim

To explore this solution, the following guides were adapted: 

MQTT to Fabric: https://learn.microsoft.com/en-us/azure/event-grid/mqtt-events-fabric 

Device Code set up: https://github.com/Azure-Samples/MqttApplicationSamples/blob/main/Setup.md 

Device Code Telemetry: https://github.com/Azure-Samples/MqttApplicationSamples/blob/main/scenarios/telemetry/README.md 

# set up

Follow this link to install the step cli: https://smallstep.com/docs/step-cli/installation/

To create the root and intermediate CA certificates run:
```bash
step ca init \
    --deployment-type standalone \
    --name MqttAppSamplesCA \
    --dns localhost \
    --address 127.0.0.1:443 \
    --provisioner MqttAppSamplesCAProvisioner
```

update password.txt with password provided

Modify az.env

```bash
source az.env

az account set -s $sub_id
az resource create --id $res_id --is-full-object --properties '{
  "properties": {
    "isZoneRedundant": true,
    "topicsConfiguration": {
      "inputSchema": "CloudEventSchemaV1_0"
    },
    "topicSpacesConfiguration": {
      "state": "Enabled"
    }
  },
  "location": "westus2"
}'
```

Register the certificate to authenticate client certificates (usually the intermediate)

```bash
source az.env

capem=`cat ~/.step/certs/intermediate_ca.crt | tr -d "\n"`

az resource create \
  --id "$res_id/caCertificates/Intermediate01" \
  --properties "{\"encodedCertificate\" : \"$capem\"}"
```

bash onboard-device.sh {id}