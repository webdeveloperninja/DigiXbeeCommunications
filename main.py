from machine import ADC, Pin
import xbee
import network
from time import sleep, ticks_ms
from connection import AzureMQTT
from json import dumps
from retry import try_or_retry_times

SAMPLE_RATE_MINUTES = 10

ADC_RIGHT_LOAD_CELL_ID = "D0"
ADC_LEFT_LOAD_CELL_ID = "D1"
ADC_SPEED_SENSOR_ID = "D3"

AV_VALUES = {0: 1.25, 1: 2.5, 2: 3.3, None: 2.5}

try:
    av = xbee.atcmd("AV")
except KeyError:
    av = None
reference = AV_VALUES[av]

device_id = 'ad4a0701-f7f8-4991-a3c3-d1443c097c19'
iot_hub_host_name = 'iottesting.azure-devices.net'
shared_access_key = '-----'
iot_hub_connection_string = f"HostName={iot_hub_host_name};DeviceId={device_id};SharedAccessKey={shared_access_key}"


left_load_cell_input = ADC(ADC_LEFT_LOAD_CELL_ID)
right_load_cell_input = ADC(ADC_RIGHT_LOAD_CELL_ID)
speed_sensor_input = ADC(ADC_SPEED_SENSOR_ID)

connection_status_output = Pin.board.D10
connection_status_output.mode(Pin.OUT)

device_status_output = Pin.board.D11
device_status_output.mode(Pin.OUT)


def get_mqtt_client():
    conn = network.Cellular()

    while not conn.isconnected():
        print("Waiting for network connection...")
        sleep(4)

    print("Network connected")

    mqtt_client = AzureMQTT(iot_hub_connection_string)
    mqtt_client.setup()

    print("Azure connected")

    return mqtt_client


def create_my_device_spot_payload(left_load_cell_value, right_load_cell_value, speed_sensor_value):
    return {
        "deviceId": device_id,
        "key": "belt_scale",
        "hasLocation": False,
        "body": {
            "leftLoadCell": left_load_cell_value,
            "rightLoadCell": right_load_cell_value,
            "speedSensor": speed_sensor_value
        }
    }


def get_voltage(pin_value):
    return pin_value * reference / 4095


def get_sensor_values():
    left_load_cell_value = left_load_cell_input.read()
    right_load_cell_value = right_load_cell_input.read()
    speed_sensor_value = speed_sensor_input.read()

    print("- left load cell voltage [V]:", left_load_cell_value * reference / 4095)
    print("- right load cell voltage [V]:", right_load_cell_value * reference / 4095)
    print("- speed sensor voltage [V]:", speed_sensor_value * reference / 4095)
    print("=================================================")

    return {
        "leftLoadCell": get_voltage(left_load_cell_value),
        "rightLoadCell": get_voltage(right_load_cell_value),
        "speedSensor": get_voltage(speed_sensor_value)
    }


def ticks_per_minute(minutes):
    return minutes * 60000


def main():
    print('startup')
    number_of_cloud_events = 0
    max_cloud_events = 200
    mqtt_connection_time_to_live_minutes = 15

    mqtt_client = get_mqtt_client()
    mqtt_client_expired_at_ticks = ticks_per_minute(mqtt_connection_time_to_live_minutes) + ticks_ms()

    def refresh_mqtt_client():
        print('refresh connection')
        nonlocal mqtt_client
        nonlocal mqtt_client_expired_at_ticks

        mqtt_client = get_mqtt_client()
        mqtt_client_expired_at_ticks = ticks_per_minute(mqtt_connection_time_to_live_minutes) + ticks_ms()

    while True:
        if number_of_cloud_events > max_cloud_events:
            return

        if ticks_ms() > mqtt_client_expired_at_ticks:
            print('connection expired: creating new connection')
            try_or_retry_times(refresh_mqtt_client, 3)

        number_of_cloud_events += 1
        sensor_values = get_sensor_values()

        my_device_spot_payload = create_my_device_spot_payload(
            sensor_values["leftLoadCell"],
            sensor_values["rightLoadCell"],
            sensor_values["speedSensor"]
        )

        def send_telemetry():
            mqtt_client.send(dumps(my_device_spot_payload))

        try_or_retry_times(send_telemetry, 3)

        print('sent telemetry')
        sleep(SAMPLE_RATE_MINUTES * 60)


try_or_retry_times(main, 3)
