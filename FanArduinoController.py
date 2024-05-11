import serial
import os
from ctypes import windll
import time
import requests
from threading import Timer
import threading

isRunning = True
last_temp = 1000         #set it very high so first iteration of get_temperature_from_ohm() will definatly change the fan speed to the appropiate dutyCycle.
ser = None
update_frequency = 5 # once every n seconds
useOHM = True
commander_message = "enter pwm of 0-255 for custom command and -1 for using automatic speed control using OHM's reading\n"
last_message = "0"
last_time_was_connected = False
ohm_start_used = False
loop_count = 0

def send_to_arduino(message):
    try:
        global ser
        global last_message
        last_message = message
        ser.write((message + '\n').encode())
        return True
    except:
        print(f"in send_to_arduino Failed to open serial")
        return False

def on_sign_out():
    global isRunning
    isRunning = False
    log("ended by FanArduinoController.pyw")
    # print("Signing out... Sending 0 to Arduino")
    send_to_arduino('0')

def get_temperature_from_ohm_and_set_arduino():
    global isRunning, last_temp, useOHM, loop_count
    while isRunning:
        try:
            if useOHM:
                #get gpu info:
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
                    if (70 < gpu_temp and last_temp <= 70) or gpu_temp == 1000:
                        new_duty_cycle = "240"
                        update_arduino = True
                    elif 60 < gpu_temp and gpu_temp <= 70 and (last_temp <= 60 or 70 < last_temp):
                        new_duty_cycle = "100"
                        update_arduino = True
                    elif 50 < gpu_temp and gpu_temp <= 60 and (last_temp <= 50 or 60 < last_temp):
                        new_duty_cycle = "23"
                        update_arduino = True
                    elif gpu_temp <= 50 and 50 < last_temp:
                        new_duty_cycle = "10"
                        update_arduino = True
                    
                    if update_arduino:
                        send_arduino_with_log_with_last_temps_duty_cycle(f"new_duty_cycle: {new_duty_cycle}, gpu_temperature: {gpu_temp_str}celsius, last_temp: {last_temp}", new_duty_cycle, gpu_temp)

                else:
                    log("GPU temperature not found.(OHM not running.)")
                
        except Exception as e:
            log(f"probably Failed to retrieve temperature so starting OHM!: {e}")
            loop_count += 1
            global ohm_start_used
            if not ohm_start_used and loop_count > 2:
                try:
                    # Path to OHM executable
                    game_path = "C:\Program Files (x86)\OpenHardwareMonitor\OpenHardwareMonitor.exe"
                    # Launch the OHM
                    os.startfile(game_path)
                    ohm_start_used = True
                except:
                    pass
        finally:
            time.sleep(update_frequency)
            loop_count = 0

def send_arduino_with_log_with_last_temps_duty_cycle(message, new_duty_cycle, gpu_temp):
    global last_temp
    log(message)
    send_to_arduino(new_duty_cycle)
    last_temp = gpu_temp

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
  
def check_for_command():
    global useOHM, commander_message, isRunning
    while isRunning:
        try:
            if os.path.getsize('command.txt') > len(commander_message):
                with open('command.txt', 'r+') as file:
                    content = file.read()
                    commandline = content.split("\n")
                    if commandline[1] == "-1":
                        useOHM = True
                        log("back at using OHM reading auto control!")
                    elif int(commandline[1]) >= 0 and int(commandline[1]) <= 255:
                        useOHM = False
                        inputPWM = commandline[1]
                        send_arduino_with_log_with_last_temps_duty_cycle(f"new_duty_cycle: {inputPWM} by the commander!", inputPWM, 1000)
                        log(f"commander now incharge!")
                    file.seek(0)
                    file.truncate()
                    file.write(commander_message)
            elif os.path.getsize('command.txt') < len(commander_message):
                file.write(commander_message)
        except:
            try:
                with open('command.txt', 'w') as file:
                    file.write(commander_message)
            except:
                log("there is a serious error in the check_for_command method!")
        finally:
            time.sleep(update_frequency)

def redo():
    global last_message
    global ser
    global last_time_was_connected
    while isRunning:
        time.sleep(30)
        if last_time_was_connected:
            time.sleep(600)
        else:
            try:
                ser = serial.Serial('COM4', 9600, timeout=1)
                time.sleep(4)
                send_to_arduino(last_message)
            except:
                # print(f"in redo Failed to open serial port")
                # log(f"in redo Failed to open serial port")
                pass


if __name__ == "__main__":
    # Ensure the script runs with administrator privileges
    if windll.shell32.IsUserAnAdmin():
        try:
            ser = serial.Serial('COM4', 9600, timeout=1)
            time.sleep(4)
        except:
            # print(f"in main Failed to open serial port")
            log(f"in main Failed to open serial port")

        # print("Sending 150 to Arduino on startup...")
        log("started")
        send_to_arduino('150')
        t = Timer(update_frequency, get_temperature_from_ohm_and_set_arduino)
        alive_check_time = time.perf_counter()
        log("starting loop")
        t.start()
        commanderrr = threading.Thread(target=check_for_command)
        commanderrr.start()
        rd = threading.Thread(target=redo)
        rd.start()


    else:
        # print("This script requires administrator privileges.")
        # Re-run the script with admin rights if possible
        log("no permission")

        # if sys.platform == "win32":
        #     os.system(f"powershell Start-Process python '{__file__}' -Verb runAs")
