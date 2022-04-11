from machine import ADC, Pin
import xbee
import network
from time import sleep, ticks_ms
from connection import AzureMQTT
from json import dumps

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

DEVICE_ID = ''
iot_hub_connection_string = ""


left_load_cell_input = ADC(ADC_LEFT_LOAD_CELL_ID)
right_load_cell_input = ADC(ADC_RIGHT_LOAD_CELL_ID)
speed_sensor_input = ADC(ADC_SPEED_SENSOR_ID)

connection_status_output = Pin.board.D10
connection_status_output.mode(Pin.OUT)

device_status_output = Pin.board.D11
device_status_output.mode(Pin.OUT)


def get_connection():
    conn = network.Cellular()

    while not conn.isconnected():
        print("Waiting for network connection...")
        sleep(4)

    print("Network connected")
    connection = AzureMQTT(iot_hub_connection_string)
    print("Connecting to Azure...")
    connection.setup()
    print("Azure connected")

    return connection


def create_my_device_spot_payload(left_load_cell_value, right_load_cell_value, speed_sensor_value):
    return {
        "deviceId": DEVICE_ID,
        "key": "belt_scale",
        "hasLocation": False,
        "body": {
            "leftLoadCell": left_load_cell_value,
            "rightLoadCell": right_load_cell_value,
            "speedSensor": speed_sensor_value
        }
    }


def get_sensor_values():
    left_load_cell_value = left_load_cell_input.read()
    right_load_cell_value = right_load_cell_input.read()
    speed_sensor_value = speed_sensor_input.read()

    print("- left load cell voltage [V]:", left_load_cell_value * reference / 4095)
    print("- right load cell voltage [V]:", right_load_cell_value * reference / 4095)
    print("- speed sensor voltage [V]:", speed_sensor_value * reference / 4095)
    print("=================================================")

    return {
        "leftLoadCell": left_load_cell_value,
        "rightLoadCell": right_load_cell_value,
        "speedSensor": speed_sensor_value
    }


def connection_led_on():
    connection_status_output.on()


def connection_led_off():
    connection_status_output.off()


def device_status_led_on():
    device_status_output.on()


def device_status_led_off():
    device_status_output.off()


def ticks_per_minute(minutes):
    return minutes * 60000


def main():
    number_of_cloud_events = 0
    max_cloud_events = 10
    connection_time_to_live_minutes = 15

    connection = get_connection()
    connection_expired_at_ticks = ticks_per_minute(connection_time_to_live_minutes) + ticks_ms()

    while True:
        if number_of_cloud_events > max_cloud_events:
            return

        if ticks_ms() > connection_expired_at_ticks:
            print('connection expired: creating new connection')
            connection = get_connection()
            connection_expired_at_ticks = ticks_per_minute(connection_time_to_live_minutes) + ticks_ms()

        number_of_cloud_events += 1
        sensor_values = get_sensor_values()

        my_device_spot_payload = create_my_device_spot_payload(
            sensor_values["leftLoadCell"],
            sensor_values["rightLoadCell"],
            sensor_values["speedSensor"]
        )

        connection.send(dumps(my_device_spot_payload))
        print('send')
        sleep(SAMPLE_RATE_MINUTES * 60)


main()
