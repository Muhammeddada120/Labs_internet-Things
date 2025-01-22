import time
import threading
import paho.mqtt.client as mqtt
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# MQTT Configuration
MQTT_BROKER = "test.mosquitto.org"
TELEMETRY_TOPIC = "iot/sensor/soil_moisture"
ACTUATOR_TOPIC = "iot/actuator/pump_command"

# Global Variables
sensor_data = "No data yet"
pump_status = "OFF"

# MQTT Callbacks
def on_connect(client, userdata, flags, rc):
    print("Connected to MQTT broker with result code " + str(rc))
    client.subscribe(TELEMETRY_TOPIC)

def on_message(client, userdata, msg):
    global sensor_data
    sensor_data = msg.payload.decode()
    print(f"Received sensor data: {sensor_data}")

# MQTT Client Setup
mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
mqtt_client.connect(MQTT_BROKER, 1883, 60)

def mqtt_loop():
    mqtt_client.loop_forever()

# Telegram Bot Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Welcome to the IoT Bot!\n"
        "Use the following commands:\n"
        "/status - Get sensor data and pump status\n"
        "/start_pump - Turn ON the pump\n"
        "/stop_pump - Turn OFF the pump"
    )

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"Current Sensor Data: {sensor_data}\nPump Status: {pump_status}"
    )

async def start_pump(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global pump_status
    pump_status = "ON"
    mqtt_client.publish(ACTUATOR_TOPIC, "ON")
    await update.message.reply_text("Pump turned ON.")

async def stop_pump(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global pump_status
    pump_status = "OFF"
    mqtt_client.publish(ACTUATOR_TOPIC, "OFF")
    await update.message.reply_text("Pump turned OFF.")

# Telegram Bot Setup
def telegram_bot():
    # Replace 'YOUR_TELEGRAM_BOT_TOKEN' with your actual bot token
    application = Application.builder().token("YOUR_TELEGRAM_BOT_TOKEN").build()

    # Registering handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("status", status))
    application.add_handler(CommandHandler("start_pump", start_pump))
    application.add_handler(CommandHandler("stop_pump", stop_pump))

    # Run the bot
    application.run_polling()

# Main Execution
if __name__ == "__main__":
    # Start MQTT loop in a separate thread
    mqtt_thread = threading.Thread(target=mqtt_loop)
    mqtt_thread.daemon = True
    mqtt_thread.start()

    # Start Telegram bot
    telegram_bot()