import serial
import os
import atexit
from ctypes import windll
import time
import requests
from threading import Timer

isRunning = True
last_temp = 100         #set it very high so first iteration of get_temperature_from_ohm() will definatly change the fan speed to the appropiate dutyCycle.


def send_to_arduino(message):
    ser.write((message + '\n').encode())
    #get response from arduino
    response = ser.readline().decode('utf-8').rstrip()
    # print("Received from Arduino:", response)

def on_sign_out():
    global isRunning
    isRunning = False
    log("ended")
    # print("Signing out... Sending 0 to Arduino")
    send_to_arduino('0')


def get_temperature_from_ohm_and_set_arduino():
    global isRunning, last_temp
    while isRunning:
        try:
            response = requests.get("http://localhost:8085/data.json")
            data = response.json()

            gpu_temp_str = None

            def traverse(node):
                nonlocal gpu_temp_str
                if isinstance(node, dict):
                    if "Text" in node and node["Text"] == "Temperatures":
                        for child in node.get("Children", []):
                            if "Text" in child and child["Text"] == "GPU Core":
                                gpu_temp_str = child.get("Value")
                                break
                    else:
                        for child in node.get("Children", []):
                            traverse(child)

            # Attempt to find and process GPU temperature
            traverse(data)
            

            if gpu_temp_str is not None:
                gpu_temp_str = gpu_temp_str.replace(' °C', '')  # Remove ' °C' from the string
                gpu_temp = float(gpu_temp_str)
                update_arduino = False
                new_duty_cycle = None
                if 70 < gpu_temp and last_temp <= 70:
                    new_duty_cycle = "240"
                    update_arduino = True
                elif 60 < gpu_temp and gpu_temp <= 70 and (last_temp <= 60 or 70 < last_temp):
                    new_duty_cycle = "190"
                    update_arduino = True
                elif 50 < gpu_temp and gpu_temp <= 60 and (last_temp <= 50 or 60 < last_temp):
                    new_duty_cycle = "120"
                    update_arduino = True
                elif gpu_temp <= 50 and 50 < last_temp:
                    new_duty_cycle = "90"
                    update_arduino = True
                
                if update_arduino:
                    # print(f"Sending new fan dutyCycle({new_duty_cycle}) to Arduino. GPU temp: {gpu_temp}celsius")
                    log(f"new_duty_cycle: {new_duty_cycle}, gpu_temperature: {gpu_temp_str}celsius, last_temp: {last_temp}")
                    send_to_arduino(new_duty_cycle)
                    last_temp = gpu_temp
                else:
                    # print(f"Arduino fan speed not updated. GPU temp: {gpu_temp}celsius")
                    pass
            else:
                # print("GPU temperature not found.")
                pass
                
        except Exception as e:
            # print(f"Failed to retrieve temperature: {e}")
            pass
        finally:
            time.sleep(5)

def log(message):
  """Logs a message with a timestamp to a limited-size file."""
  import time

  # Define maximum log size (in bytes)
  MAX_LOG_SIZE = 1024 * 10  # 10 kilobytes (adjust as needed)

  current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
  formatted_message = f"{current_time}: {message}\n"

  try:
    # Open the log file in append mode
    with open('log.txt', 'a') as file:
      # Get current file size
      file_size = os.path.getsize('log.txt')

      # Truncate if exceeding maximum size
      if file_size > MAX_LOG_SIZE:
        file.truncate(0)  # Clear the file content

      # Write the formatted message
      file.write(formatted_message)
  except OSError:
    # Handle potential file access errors
    pass


if __name__ == "__main__":
    # Ensure the script runs with administrator privileges
    if windll.shell32.IsUserAnAdmin():
        # Register the sign-out function to be called on exit
        atexit.register(on_sign_out)

        # Setup the serial connection (adjust 'COM4' as needed for your setup)
        ser = serial.Serial('COM4', 9600, timeout=1)
        time.sleep(3)
        
        # print("Sending 150 to Arduino on startup...")
        send_to_arduino('150')
        log("started")
        t = Timer(20, get_temperature_from_ohm_and_set_arduino)
        t.start()
    else:
        # print("This script requires administrator privileges.")
        # Re-run the script with admin rights if possible
        log("no permission")

        # if sys.platform == "win32":
        #     os.system(f"powershell Start-Process python '{__file__}' -Verb runAs")

