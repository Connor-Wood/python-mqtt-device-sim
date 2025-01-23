# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
import sys
from argparse import ArgumentParser
import logging
import time
import paho.mqtt.client as mqtt
import paho.mqtt.properties as props
from paho.mqtt.packettypes import PacketTypes
import ssl
import threading
import random
import json

parser = ArgumentParser()
parser.add_argument("--host", help="eventgrid hostname")
parser.add_argument("--user", help="username and clientid")
args = parser.parse_args()

logging.basicConfig(level=logging.DEBUG)

connected_cond = threading.Condition()
connected_prop = False
connection_error = None

class Point:
    def __init__(self,x_init,y_init):
        self.x = x_init
        self.y = y_init

    def __repr__(self):
        return "\"type\":\"Point\", \"coordinates\":[{x},{y}]".format(x=str(self.x), y=str(self.y))

def on_connect(client, _userdata, _flags, rc, props): 
    global connected_prop
    print("Connected to MQTT broker")
    # # In Paho CB thread.
    with connected_cond:
        if rc == mqtt.MQTT_ERR_SUCCESS:
            connected_prop = True
        else:
            connection_error = Exception(mqtt.connack_string(rc))
        connected_cond.notify_all()

def on_publish(_client, _userdata, mid):
    # # In Paho CB thread.
    print(f"Sent publish with message id {mid}")

def on_disconnect(_client, _userdata, rc, props):
    print("Received disconnect with error='{}'".format(mqtt.error_string(rc)))
    global connected_prop
    # # In Paho CB thread.
    with connected_cond:
        connected_prop = False
        connected_cond.notify_all()

def wait_for_connected(timeout: float = None) -> bool:
    with connected_cond:
        connected_cond.wait_for(lambda: connected_prop or connection_error, timeout=timeout, )
        if connection_error:
            raise connection_error
        return connected_prop

def wait_for_disconnected(timeout: float = None):
    with connected_cond:
        connected_cond.wait_for(lambda: not connected_prop, timeout=timeout, )

def create_mqtt_client(client_id, user):
    mqtt_client = mqtt.Client(
        client_id=client_id,
        protocol=mqtt.MQTTv5,
        transport="tcp",
    )

    mqtt_client.username_pw_set(username=user)

    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    context.maximum_version = ssl.TLSVersion.TLSv1_3

    context.load_cert_chain(
        certfile=f'keys/{args.user}.pem',
        keyfile=f'keys/{args.user}.key'
    )
    context.load_default_certs()

    mqtt_client.tls_set_context(context)

    return mqtt_client

def main():
    # INITIALIZE
    print("Initializing Paho MQTT client")
    mqtt_client = create_mqtt_client(args.user, args.user)

    # ATTACH HANDLERS
    mqtt_client.on_connect = on_connect
    mqtt_client.on_publish = on_publish
    mqtt_client.on_disconnect = on_disconnect
    mqtt_client.enable_logger()

    try:
        # CONNECT
        print("{}: Starting connection".format(args.user))
        mqtt_client.connect(args.host, 8883, 30)
        print("Starting network loop")
        mqtt_client.loop_start()

        # WAIT FOR CONNECT
        if not wait_for_connected(timeout=10):
            print("{}: failed to connect.  exiting sample".format(args.user))
            raise TimeoutError("Timeout out trying to connect")

        # PUBLISH
        topic = f"vehicles/{args.user}/telemetry".format(client_id=args.user)
        temp = round(random.uniform(0,90))
        while True:
            lat = round(random.uniform(-90,90),6)
            lon = round(random.uniform(-180,180),6)

            temp += random.choice([-1, 1]) * random.randint(1, 2)
            temp = max(0, min(temp, 90))

            payload = json.dumps( {
                "temperature": temp,
                "coordinates": {"lat": lat, "lon": lon},
                "padding": ''.join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789", k=1000))
            })

            publish_properties = props.Properties(PacketTypes.PUBLISH)
            publish_properties.ContentType = "application/json"
            publish_properties.PayloadFormatIndicator = 1
            publish_result = mqtt_client.publish(topic, payload, qos=1, properties=publish_properties)
            print(f"Sending publish with payload \"{payload}\" on topic \"{topic}\" with message id {publish_result.mid}")
            time.sleep(10)

    except KeyboardInterrupt:
        print("User initiated exit")
    except Exception:
        print("Unexpected exception!")
        raise
    finally:
        print("Shutting down....")
        # DISCONNECT
        print("{}: Disconnecting".format(args.user))
        mqtt_client.disconnect()
        wait_for_disconnected(5)

if __name__ == "__main__":
    main()
