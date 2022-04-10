from machine import ADC, Pin
import xbee

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

connection_status_output = Pin.board.D10
connection_status_output.mode(Pin.OUT)

device_status_output = Pin.board.D11
device_status_output.mode(Pin.OUT)


def get_sensor_values():
    left_load_cell_value = left_load_cell_input.read()
    right_load_cell_value = right_load_cell_input.read()
    speed_sensor_value = speed_sensor_input.read()

    print("- left load cell voltage [V]:", left_load_cell_value * reference / 4095)
    print("- right load cell voltage [V]:", right_load_cell_value * reference / 4095)
    print("- speed sensor voltage [V]:", speed_sensor_value * reference / 4095)
    print("=================================================")


def connection_led_on():
    connection_status_output.on()


def connection_led_off():
    connection_status_output.off()


def device_status_led_on():
    device_status_output.on()


def device_status_led_off():
    device_status_output.off()
