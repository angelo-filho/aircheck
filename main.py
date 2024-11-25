from fastapi import FastAPI
import serial
import asyncio
import json
import time
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware

# Serial port configuration
porta_esp32 = 'COM7'
velocidade = 9600

# Initialize serial connection
esp = serial.Serial(porta_esp32, velocidade)
time.sleep(2)  # Allow ESP32 to reset

# Shared data storage
data = {"humidade": 0, "temperatura": 0, "fumaca": 0}

@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(read_serial())

    yield

    esp.setDTR(False)  # Reset ESP32
    time.sleep(0.1)
    esp.setDTR(True)
    esp.close()
    print("Serial port closed.")

# Create FastAPI app
app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)


async def read_serial():
    """
    Background task to continuously read data from the ESP32 over serial.
    """
    global data
    while True:
        if esp.in_waiting > 0:
            try:
                # Read and decode serial data
                raw_data = esp.readline().decode("utf-8").strip()
                # Parse JSON if valid
                data = json.loads(raw_data)

                data["fumaca"] = data["fumaca"] / 10
            except json.JSONDecodeError:
                print(f"Invalid JSON: {raw_data}")
            except Exception as e:
                print(f"Error: {e}")
        # Prevent busy-waiting
        await asyncio.sleep(0.01)


@app.get("/")
async def root():
    """
    Root endpoint for basic API check.
    """
    return {"message": "ESP32 FastAPI server is running!"}


@app.get("/iot")
async def get_iot_data():
    """
    Endpoint to retrieve the latest data from the ESP32.
    """
    return data
