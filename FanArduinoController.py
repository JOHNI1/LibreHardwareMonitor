import serial
import os
import sys
import atexit
from ctypes import windll
import time
import requests
from threading import Timer

isRunning = True
last_temp = 100         #set it very high so first iteration of get_temperature_from_ohm() will definatly change the fan speed to the appropiate dutyCycle.

def send_to_arduino(message):
    with serial.Serial('COM4', 9600, timeout=1) as ser:
        ser.write(message.encode())

def on_sign_out():
    global isRunning
    isRunning = False
    print("Signing out... Sending 0 to Arduino")
    send_to_arduino('0')

def get_temperature_from_ohm():
    global isRunning
    while isRunning:
        try:
            response = requests.get("http://localhost:8085/data.json")  # Default OHM web server URL
            data = response.json()
            # Parse the JSON data for your specific sensor information
            # The structure of the JSON needs to be navigated to find the correct temperature reading
            # Placeholder for actual parsing logic
        except Exception as e:
            print(f"Failed to retrieve temperature: {e}")
        finally:
            time.sleep(30)

def get_temperature_from_ohm():
    global isRunning
    global last_temp
    while isRunning:
        try:
            response = requests.get("http://localhost:8085/data.json")  # Default OHM web server URL
            data = response.json()
            
            # Initialize variable to store GPU temperature
            gpu_temp = None
            
            # Search for the GPU temperature in the JSON data
            for hardware in data['Children']:
                if 'NVIDIA' in hardware['Text']:  # This might need adjustment depending on the actual GPU name
                    for sensor in hardware['Children']:
                        if sensor['Text'] == 'Temperatures':
                            for temp in sensor['Children']:
                                if temp['Text'] == 'GPU Core':
                                    gpu_temp = temp['Value']
                                    break
                            
            # Check if GPU temperature was found and send it to Arduino
            if gpu_temp is not None:
                update_arduino = True
                if 70 < gpu_temp and last_temp < 70:
                    send_to_arduino("220")
                elif 60 < gpu_temp < 70 and (last_temp < 60 or 70 < last_temp):
                    send_to_arduino("150")
                elif 50 < gpu_temp < 60 and (last_temp < 50 or 60 < last_temp):
                    send_to_arduino("120")
                elif gpu_temp < 50 and 50 < last_temp:
                    send_to_arduino("100")
                else:
                    update_arduino = False
                    print("arduino fan speed not updated!")
                if update_arduino:
                    print(f"sent fan dutyCycle to Arduino. the gpu temp is: {gpu_temp}°C")
                    last_temp = gpu_temp
            else:
                print("GPU temperature not found.")
                
        except Exception as e:
            print(f"Failed to retrieve temperature: {e}")
        finally:
            time.sleep(30)



if __name__ == "__main__":
    # Ensure the script runs with administrator privileges
    if windll.shell32.IsUserAnAdmin():
        # Register the sign-out function to be called on exit
        atexit.register(on_sign_out)
        
        print("Sending 100 to Arduino on startup...")
        send_to_arduino('150')
        t = Timer(20, get_temperature_from_ohm)
        t.start()
    else:
        print("This script requires administrator privileges.")
        # Re-run the script with admin rights if possible
        if sys.platform == "win32":
            os.system(f"powershell Start-Process python '{__file__}' -Verb runAs")
