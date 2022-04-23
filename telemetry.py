import network
from time import sleep, ticks_ms
from azure_mqtt_client import AzureMQTT
from retry import try_or_retry_times
from json import dumps
from configuration import iot_hub_connection_string
from time_conversion import ms_ticks_per_minute

mqtt_connection_time_to_live_minutes = 45


class TelemetryClient:
    mqtt_client = None
    mqtt_client_expired_at_ticks = None
    number_of_cloud_events = 0
    connection = None
    next_cycle_max_cloud_events_ticks = None
    max_cloud_events = 0
    max_cloud_events_window_minutes = 0

    def __init__(self, max_cloud_events, max_cloud_events_window_minutes):
        self.max_cloud_events = max_cloud_events
        self.max_cloud_events_window_minutes = max_cloud_events_window_minutes

    def init(self):
        print('init telemetry client')
        try_or_retry_times(self._get_mqtt_client, 3)

    def send(self, telemetry):
        current_ticks_ms = ticks_ms()

        if self.next_cycle_max_cloud_events_ticks is None:
            self.next_cycle_max_cloud_events_ticks = ms_ticks_per_minute(
                self.max_cloud_events_window_minutes) + current_ticks_ms

        if current_ticks_ms > self.next_cycle_max_cloud_events_ticks:
            print('Reset number of allowed events to 0')
            self.number_of_cloud_events = 0
            self.next_cycle_max_cloud_events_ticks = ms_ticks_per_minute(
                self.max_cloud_events_window_minutes) + current_ticks_ms

        if self.number_of_cloud_events > self.max_cloud_events or self.mqtt_client_expired_at_ticks is None:
            print('Exceeded number of allowed events')
            return

        if current_ticks_ms > self.mqtt_client_expired_at_ticks:
            print('mqtt client expired: creating new connection')
            try_or_retry_times(self._get_mqtt_client, 3)

        self.number_of_cloud_events += 1
        self.mqtt_client.send(dumps(telemetry))

    def _get_mqtt_client(self):
        self.connection = network.Cellular()

        while not self.connection.isconnected():
            print("Waiting for network connection...")
            sleep(4)

        print("Network connected")
        print(iot_hub_connection_string)
        self.mqtt_client = AzureMQTT(iot_hub_connection_string)
        print("mqtt client set")
        try_or_retry_times(self.mqtt_client.setup, 3)
        print('setup complete')
        self.mqtt_client_expired_at_ticks = ms_ticks_per_minute(mqtt_connection_time_to_live_minutes) + ticks_ms()

        print("Azure connected")
