import tkinter as tk
from tkinter import ttk
import random
import time
import threading
import paho.mqtt.client as mqtt

# MQTT Broker Configuration
BROKER = "test.mosquitto.org"
PORT = 1883
TOPIC_SENSOR = "iot/sensor/soil_moisture"
TOPIC_PUMP_COMMAND = "iot/actuator/pump_command"
TOPIC_MODE = "iot/mode/set_mode"
TOPIC_PUMP_STATE = "iot/status/pump_state"

# Global Variables
sensor_value = 100  # Initial soil moisture value
actuator_state = "OFF"  # Pump state
mode = "Manual"  # Operating mode (Manual/Automatic)
update_period = 10  # Data update period in seconds
running = True  # Main loop control

# MQTT Client Setup
def on_connect(client, userdata, flags, rc):
    """Callback for when the client connects to the broker."""
    if rc == 0:
        print("Connected to MQTT Broker")
        client.subscribe(TOPIC_PUMP_COMMAND)
        client.subscribe(TOPIC_MODE)
    else:
        print(f"Failed to connect, return code {rc}")

def on_message(client, userdata, msg):
    """Callback for when a message is received."""
    global actuator_state, mode
    payload = msg.payload.decode()
    if msg.topic == TOPIC_PUMP_COMMAND:
        if payload == "ON":
            actuator_state = "ON"
            print("Pump activated via MQTT")
        elif payload == "OFF":
            actuator_state = "OFF"
            print("Pump deactivated via MQTT")
    elif msg.topic == TOPIC_MODE:
        if payload in ["Manual", "Automatic"]:
            mode = payload
            print(f"Mode set to: {mode}")

def start_mqtt(client):
    """Starts the MQTT loop."""
    client.loop_forever()

# Function to Simulate Sensor Data
def update_sensor_data(client):
    global sensor_value, actuator_state, mode
    while running:
        time.sleep(update_period)
        # Simulate sensor behavior
        if actuator_state == "ON":
            sensor_value = min(sensor_value + random.randint(10, 15), 100)
        else:
            sensor_value = max(sensor_value - random.randint(5, 10), 0)

        # Publish sensor data
        client.publish(TOPIC_SENSOR, f"{sensor_value}")
        print(f"Published sensor data: {sensor_value}%")

        # Automatic mode logic
        if mode == "Automatic":
            if sensor_value <= 30:
                actuator_state = "ON"
                client.publish(TOPIC_PUMP_STATE, "ON")
                print("Automatic: Pump activated")
            elif sensor_value > 40:
                actuator_state = "OFF"
                client.publish(TOPIC_PUMP_STATE, "OFF")
                print("Automatic: Pump deactivated")

# Graphical Interface
class IoTSimulatorApp:
    def __init__(self, root, mqtt_client):
        self.root = root
        self.client = mqtt_client
        self.root.title("IoT Device Simulator")

        # Sensor Value Display
        self.sensor_label = ttk.Label(root, text=f"Soil Moisture: {sensor_value}%", font=("Arial", 14))
        self.sensor_label.pack(pady=10)

        # Actuator State Display
        self.actuator_label = ttk.Label(root, text=f"Pump State: {actuator_state}", font=("Arial", 14))
        self.actuator_label.pack(pady=10)

        # Mode Selection
        self.mode_label = ttk.Label(root, text=f"Mode: {mode}", font=("Arial", 14))
        self.mode_label.pack(pady=10)

        # Buttons for Manual Control
        self.on_button = ttk.Button(root, text="Turn On Pump", command=self.turn_on_pump)
        self.on_button.pack(pady=5)

        self.off_button = ttk.Button(root, text="Turn Off Pump", command=self.turn_off_pump)
        self.off_button.pack(pady=5)

        # Update UI Periodically
        self.update_ui()

    def turn_on_pump(self):
        global actuator_state
        actuator_state = "ON"
        self.client.publish(TOPIC_PUMP_COMMAND, "ON")
        print("Pump manually turned ON")

    def turn_off_pump(self):
        global actuator_state
        actuator_state = "OFF"
        self.client.publish(TOPIC_PUMP_COMMAND, "OFF")
        print("Pump manually turned OFF")

    def update_ui(self):
        self.sensor_label.config(text=f"Soil Moisture: {sensor_value}%")
        self.actuator_label.config(text=f"Pump State: {actuator_state}")
        self.mode_label.config(text=f"Mode: {mode}")
        self.root.after(1000, self.update_ui)

# Main Function
def main():
    global running

    # Initialize MQTT Client
    mqtt_client = mqtt.Client()
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message

    # Connect to the MQTT Broker
    mqtt_client.connect(BROKER, PORT, 60)

    try:
        # Start MQTT in a Background Thread
        mqtt_thread = threading.Thread(target=start_mqtt, args=(mqtt_client,))
        mqtt_thread.daemon = True
        mqtt_thread.start()

        # Start Sensor Data Update in a Background Thread
        sensor_thread = threading.Thread(target=update_sensor_data, args=(mqtt_client,))
        sensor_thread.daemon = True
        sensor_thread.start()

        root = tk.Tk()
        app = IoTSimulatorApp(root, mqtt_client)
        root.mainloop()
    except KeyboardInterrupt:
        print("Shutting down...")
        running = False
        mqtt_client.disconnect()

if __name__ == "__main__":
    main()