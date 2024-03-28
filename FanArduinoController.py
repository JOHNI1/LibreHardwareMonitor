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
    global isRunning, last_temp
    while isRunning:
        try:
            response = requests.get("http://localhost:8085/data.json")
            data = response.json()
            
            # Attempt to find and process GPU temperature
            gpu_temp_str = None  # Use a separate variable to hold the string value
            for hardware in data['Children']:
                if 'NVIDIA' in hardware['Text']:
                    for sensor in hardware['Children']:
                        if sensor['Text'] == 'Temperatures':
                            for temp in sensor['Children']:
                                if temp['Text'] == 'GPU Core':
                                    gpu_temp_str = temp['Value']
                                    break
                            
            if gpu_temp_str is not None:
                gpu_temp = float(gpu_temp_str)  # Convert string to float
                update_arduino = False
                if 70 < gpu_temp and last_temp <= 70:
                    send_to_arduino("240")
                    update_arduino = True
                elif 60 < gpu_temp <= 70 and (last_temp <= 60 or last_temp > 70):
                    send_to_arduino("190")
                    update_arduino = True
                elif 50 < gpu_temp <= 60 and (last_temp <= 50 or last_temp > 60):
                    send_to_arduino("120")
                    update_arduino = True
                elif gpu_temp <= 50 and last_temp > 50:
                    send_to_arduino("80")
                    update_arduino = True
                
                if update_arduino:
                    print(f"Sent fan dutyCycle to Arduino. GPU temp: {gpu_temp}°C")
                    last_temp = gpu_temp
                else:
                    print("Arduino fan speed not updated. GPU temp: {gpu_temp}°C")
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
