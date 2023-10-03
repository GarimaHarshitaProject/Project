from flask import Flask, render_template, jsonify, request
import spidev
from numpy import interp
from time import sleep
from random import random
import RPi.GPIO as GPIO
import requests

app = Flask(__name__)

# Start SPI connection
spi = spidev.SpiDev()  # Create an object
spi.open(0, 0)

# Set up GPIO
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

# Create a dictionary called pins to store the pin number, name, and pin state:
pins = {
    23: {'name': 'GPIO 23', 'state': GPIO.LOW},
    24: {'name': 'GPIO 24', 'state': GPIO.LOW}
}

# Set each pin as an output and make it low:
for pin in pins:
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, GPIO.LOW)

water_level_pin = 22

# Initialize the water level sensor pin
GPIO.setup(water_level_pin, GPIO.IN)

# Variable to track if the sensor was low in the previous reading
sensor_low_prev = False

water_level_per = 0

IFTTT_WEBHOOK_URL = 'https://maker.ifttt.com/trigger/no_water/json/with/key/ul9Zx4Y5pFU623gfLLobRhTg59wyMWjPlYGmnFJuo8'

# Read MCP3008 data
def analogInput(channel):
    spi.max_speed_hz = 1350000
    adc = spi.xfer2([1, (8 + channel) << 4, 0])
    data = ((adc[1] & 3) << 8) + adc[2]
    return data

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/data')
def get_data():
    output0 = analogInput(0)  # Reading from CH0
    output1 = analogInput(1)
    output0 = interp(output0, [0, 716], [100, 0])
    output1 = interp(output1, [0, 716], [100, 0])
    output0 = int(output0)
    output1 = int(output1)
    moisture1 = random() * 1000
    moisture2 = random() * 1000
    sleep(2)
    
    global sensor_low_prev
    global water_level_per
    water_pin = GPIO.input(water_level_pin)
    # Check if the water level is low (empty)
    if water_pin == GPIO.LOW and not sensor_low_prev:
        # Trigger IFTTT webhook if the sensor is low (empty)
        requests.post(IFTTT_WEBHOOK_URL)
        water_level_per = 5
        sensor_low_prev = True
    if water_pin == GPIO.HIGH:
        water_level_per = 100
        sensor_low_prev = False

    return jsonify({"moisture1": moisture1, "moisture2": moisture2, "water_level": water_level_per, "water_pin": water_pin})

@app.route('/pump1/<action>')
def control_pump1(action):
    changePin = 23  # GPIO pin for Pump 1
    # Get the device name for the pin being changed:
    deviceName = pins[changePin]['name']
    if action == "on":
        GPIO.output(changePin, GPIO.HIGH)
        message = "Turned " + deviceName + " on."
    elif action == "off":
        GPIO.output(changePin, GPIO.LOW)
        message = "Turned " + deviceName + " off."
    else:
        message = "Invalid action."
    
    # For each pin, read the pin state and store it in the pins dictionary:
    for pin in pins:
        pins[pin]['state'] = GPIO.input(pin)
    
    # Along with the pin dictionary, put the message into the template data dictionary:
    templateData = {
        'pins': pins
    }

    return render_template('index.html', **templateData)

@app.route('/pump2/<action>')
def control_pump2(action):
    changePin = 24  # GPIO pin for Pump 2
    # Get the device name for the pin being changed:
    deviceName = pins[changePin]['name']
    if action == "on":
        GPIO.output(changePin, GPIO.HIGH)
        message = "Turned " + deviceName + " on."
    elif action == "off":
        GPIO.output(changePin, GPIO.LOW)
        message = "Turned " + deviceName + " off."
    else:
        message = "Invalid action."

    # For each pin, read the pin state and store it in the pins dictionary:
    for pin in pins:
        pins[pin]['state'] = GPIO.input(pin)

    # Along with the pin dictionary, put the message into the template data dictionary:
    templateData = {
        'pins': pins
    }

    return render_template('index.html', **templateData)

if __name__ == "__main__":
    app.run(host='192.168.1.2', port=8080, debug=True)
