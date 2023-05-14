from sense_hat import SenseHat

sense = SenseHat()

temp = sense.get_temperature()
print("Temperature: %s C" % temp)

humidity = sense.get_humidity()
print("Humidity: %s %%rH" % humidity)

pressure = sense.get_pressure()
print("Pressure: %s Millibars" % pressure)

sense.show_message("Hello world!")
