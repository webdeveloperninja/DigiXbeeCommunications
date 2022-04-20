from machine import ADC, WDT, SOFT_RESET
import xbee
from time import sleep
from telemetry_client import TelemetryClient
from configuration import device_id

SAMPLE_RATE_MINUTES = 10
WATCH_DOG_FAILURE_MINUTES = 3

MAX_CLOUD_EVENTS = 12
MAX_CLOUD_EVENTS_TIME_WINDOW_MINUTES = 60

ADC_RIGHT_LOAD_CELL_ID = "D0"
ADC_LEFT_LOAD_CELL_ID = "D1"
ADC_SPEED_SENSOR_ID = "D3"

AV_VALUES = {0: 1.25, 1: 2.5, 2: 3.3, None: 2.5}

try:
    av = xbee.atcmd("AV")
except KeyError:
    av = None
reference = AV_VALUES[av]

left_load_cell_input = ADC(ADC_LEFT_LOAD_CELL_ID)
right_load_cell_input = ADC(ADC_RIGHT_LOAD_CELL_ID)
speed_sensor_input = ADC(ADC_SPEED_SENSOR_ID)


def ms_ticks_per_minute(minutes):
    return minutes * 60000


def start():
    print('startup')
    iot_client = TelemetryClient(MAX_CLOUD_EVENTS, MAX_CLOUD_EVENTS_TIME_WINDOW_MINUTES)
    dog = WDT(timeout=ms_ticks_per_minute(SAMPLE_RATE_MINUTES + WATCH_DOG_FAILURE_MINUTES), response=SOFT_RESET)

    while True:
        dog.feed()

        ## Sleeping the device shuts down open socket connections
        ## ensure socket is open after sleep
        iot_client.init()
        sensor_values = get_sensor_values()

        my_device_spot_payload = create_my_device_spot_payload(
            sensor_values["leftLoadCell"],
            sensor_values["rightLoadCell"],
            sensor_values["speedSensor"]
        )

        iot_client.send_telemetry(my_device_spot_payload)
        sleep(SAMPLE_RATE_MINUTES * 60)


def get_sensor_values():
    left_load_cell_voltage = get_voltage(left_load_cell_input.read())
    right_load_cell_voltage = get_voltage(right_load_cell_input.read())
    speed_sensor_voltage = get_voltage(speed_sensor_input.read())

    print("- left load cell voltage [V]:", left_load_cell_voltage)
    print("- right load cell voltage [V]:", right_load_cell_voltage)
    print("- speed sensor voltage [V]:", speed_sensor_voltage)
    print("=================================================")

    return {
        "leftLoadCell": left_load_cell_voltage,
        "rightLoadCell": right_load_cell_voltage,
        "speedSensor": speed_sensor_voltage
    }


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
