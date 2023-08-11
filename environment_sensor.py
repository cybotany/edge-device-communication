import bme680
import time
from utils.helpers import celsius_to_fahrenheit 


def get_environmental_data():
    # Initialize BME680 sensor
    try:
        sensor = bme680.BME680(bme680.I2C_ADDR_PRIMARY)
    except (RuntimeError, IOError):
        sensor = bme680.BME680(bme680.I2C_ADDR_SECONDARY)

    # These oversampling settings can be tweaked to
    # change the balance between accuracy and noise in
    # the data.

    sensor.set_humidity_oversample(bme680.OS_2X)
    sensor.set_pressure_oversample(bme680.OS_4X)
    sensor.set_temperature_oversample(bme680.OS_8X)
    sensor.set_filter(bme680.FILTER_SIZE_3)
    
    sensor.set_gas_status(bme680.ENABLE_GAS_MEAS)
    sensor.set_gas_heater_temperature(320)
    sensor.set_gas_heater_duration(150)
    sensor.select_gas_heater_profile(0)

    # Up to 10 heater profiles can be configured, each
    # with their own temperature and duration.
    # sensor.set_gas_heater_profile(200, 150, nb_profile=1)
    # sensor.select_gas_heater_profile(1)

    c_temp = sensor.data.temperature
    f_temp = celsius_to_fahrenheit(c_temp)
    pressure = sensor.data.pressure
    humidity = sensor.data.humidity

    if sensor.data.heat_stable:
        gas_resistance = sensor.data.gas_resistance
    else:
        gas_resistance = 0
    
    output = '{0:.2f} F, {1:.2f} hPa, {2:.2f} %RH, {3:.2f} Ohms'.format(
        f_temp,
        pressure,
        humidity,
        gas_resistance)

    print(output)
