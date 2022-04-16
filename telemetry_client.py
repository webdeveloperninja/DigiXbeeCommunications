import network
from time import sleep, ticks_ms
from azure_mqtt_client import AzureMQTT
from retry import try_or_retry_times
from json import dumps
from configuration import iot_hub_connection_string

mqtt_connection_time_to_live_minutes = 45
max_cloud_events = 200
minutes_in_a_day = 1440


class TelemetryClient:
    mqtt_client = None
    mqtt_client_expired_at_ticks = None
    number_of_cloud_events = 0
    connection = None
    next_day_ticks = None

    def init(self):
        print('init telemetry client')
        try_or_retry_times(self._get_mqtt_client, 3)

    def send_telemetry(self, telemetry):
        current_ticks_ms = ticks_ms()

        if self.next_day_ticks is None:
            self.next_day_ticks = ticks_per_minute(minutes_in_a_day) + current_ticks_ms

        if current_ticks_ms > self.next_day_ticks:
            self.number_of_cloud_events = 0
            self.next_day_ticks = ticks_per_minute(minutes_in_a_day) + current_ticks_ms

        if self.number_of_cloud_events > max_cloud_events or self.mqtt_client_expired_at_ticks is None:
            return

        if current_ticks_ms > self.mqtt_client_expired_at_ticks:
            print('mqtt client expired: creating new connection')
            try_or_retry_times(self._get_mqtt_client, 3)

        def send_telemetry():
            if self.connection.isconnected():
                self.number_of_cloud_events += 1
                self.mqtt_client.send(dumps(telemetry))
                print('Telemetry Sent')
                return

            self.connection = network.Cellular()
            while not self.connection.isconnected():
                print("Waiting for network connection...")
                sleep(4)

        try_or_retry_times(send_telemetry, 3)

    def _get_mqtt_client(self):
        self.connection = network.Cellular()

        while not self.connection.isconnected():
            print("Waiting for network connection...")
            sleep(4)

        print("Network connected")
        print(iot_hub_connection_string)
        self.mqtt_client = AzureMQTT(iot_hub_connection_string)
        print("mqtt client set")
        self.mqtt_client.setup()
        print('setup complete')
        self.mqtt_client_expired_at_ticks = ticks_per_minute(mqtt_connection_time_to_live_minutes) + ticks_ms()

        print("Azure connected")


def ticks_per_minute(minutes):
    return minutes * 60000
