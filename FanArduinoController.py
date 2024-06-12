import serial
import os
from ctypes import windll
import time
import threading

from HardwareMonitor.Hardware import *  # equivalent to 'using LibreHardwareMonitor.Hardware;'

import psutil



class UpdateVisitor(IVisitor):
    __namespace__ = "TestHardwareMonitor"  # must be unique among implementations of the IVisitor interface
    def VisitComputer(self, computer: IComputer):
        computer.Traverse(self)

    def VisitHardware(self, hardware: IHardware):
        hardware.Update()
        for subHardware in hardware.SubHardware:
            subHardware.Update()

    def VisitParameter(self, parameter: IParameter): pass

    def VisitSensor(self, sensor: ISensor): pass
    
    
def is_on_battery_power():
    """
    Checks if the laptop is currently on battery power.

    Returns:
        True if on battery power, False if connected to power.
    """
    battery = psutil.sensors_battery()
    return not battery.power_plugged






# namespace LibreHardwareMonitor.Hardware.Storage;
computer = Computer()  # settings can not be passed as constructor argument (following below)
computer.IsMotherboardEnabled = False
computer.IsControllerEnabled = False
computer.IsCpuEnabled = True
computer.IsGpuEnabled = True
computer.IsBatteryEnabled = False
computer.IsMemoryEnabled = False
computer.IsNetworkEnabled = False
computer.IsStorageEnabled = False
computer.Open()

def get_temp() -> list[int]:    #[cpu_max_tmp, cpu_average_tmp, gpu_max_temp, gpu_average_temp]
    computer.Accept(UpdateVisitor())

    time.sleep(1)
    #                           for cpu:↓          ↓for max cpu temp <-sensor
    cpu_max_tmp = int(computer.Hardware[0].Sensors[83].Value)
    #                               for cpu:↓          ↓for average cpu temp <-sensor
    cpu_average_tmp = int(computer.Hardware[0].Sensors[84].Value)
    #                            for gpu:↓          ↓for max gpu temp <-sensor
    gpu_max_temp = int(computer.Hardware[1].Sensors[19].Value)
    #                        for gpu:↓          ↓for gpu temp <-sensor
    gpu_average_temp = int(computer.Hardware[1].Sensors[0].Value)

    returnList = [cpu_max_tmp, cpu_average_tmp, gpu_max_temp, gpu_average_temp]

    return returnList


isRunning = True
last_temp = 1000         #set it very high so first iteration of get_temperature_from_ohm() will definatly change the fan speed to the appropiate dutyCycle.
ser = None
update_frequency = 20 # once every n seconds
useLHM = True
commander_message = "enter pwm of 0-255 for custom command and -1 for using automatic speed control using OHM's reading\n"
last_message = "0"
last_battery_used = True


def send_to_arduino(message):
    try:
        global ser
        global last_message
        last_message = message
        ser.write((message + '\n').encode())
        return True
    except:
        log(f"in send_to_arduino Failed to open serial")
        return False
    



def on_sign_out():
    global isRunning
    isRunning = False 
    log("ended by FanArduinoController.pyw")
    # print("Signing out... Sending 0 to Arduino")
    send_to_arduino('0')




average_temp = None
weights = [1.2, 0.8, 1.2, 0.8]   # <=[cpu_max_tmp, cpu_average_tmp, gpu_max_temp, gpu_average_temp]
temps = None
update_arduino = False
new_duty_cycle = None

def get_temperature_from_lhm_and_set_arduino():
    global isRunning, last_temp, useLHM, loop_count
    while isRunning:
        try:
            if useLHM:
                #get processros temp:
                
                try:
                    temps = get_temp()     #[cpu_max_tmp, cpu_average_tmp, gpu_max_temp, gpu_average_temp]
                    average_temp = int((temps[0]*weights[0]+temps[1]*weights[1]+temps[2]*weights[2]+temps[3]*weights[3])/4)
                except:
                    log("some fucked up shit happened. check the code!")
                update_arduino = False
                if (70 < average_temp and last_temp <= 70) or average_temp == 1000:
                    new_duty_cycle = "240"
                    update_arduino = True
                elif 60 < average_temp and average_temp <= 70 and (last_temp <= 60 or 70 < last_temp):
                    new_duty_cycle = "100"
                    update_arduino = True
                elif 50 < average_temp and average_temp <= 60 and (last_temp <= 50 or 60 < last_temp):
                    new_duty_cycle = "23"
                    update_arduino = True
                elif average_temp <= 50 and 50 < last_temp:
                    new_duty_cycle = "10"
                    update_arduino = True
                
                if update_arduino:
                    send_arduino_with_log_with_last_temps_duty_cycle(f"new_duty_cycle: {new_duty_cycle},      average_temp: {average_temp}C,      cpu_max: {temps[0]}C,      gpu_max: {temps[2]}C,      last_temp: {last_temp}C", new_duty_cycle, average_temp)

        except Exception as e:
            log("some fucked up shit happened. check the code!")
        time.sleep(update_frequency)

def send_arduino_with_log_with_last_temps_duty_cycle(message, new_duty_cycle, average_temp):
    global last_temp
    log(message)
    send_to_arduino(new_duty_cycle)
    last_temp = average_temp

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
    global useLHM, commander_message, isRunning
    while isRunning:
        try:
            if os.path.getsize('command.txt') > len(commander_message):
                with open('command.txt', 'r+') as file:
                    content = file.read()
                    commandline = content.split("\n")
                    if commandline[1] == "-1":
                        useLHM = True
                        log("back at using OHM reading auto control!")
                    elif int(commandline[1]) >= 0 and int(commandline[1]) <= 255:
                        useLHM = False
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
    global last_message, last_battery_used, ser
    while isRunning:
        time.sleep(5)
        if last_battery_used == True and not is_on_battery_power():
            try:
                log("computer connected to docking station! starting the serial connection and commanding pwm!")
                ser = serial.Serial('COM4', 9600, timeout=1)
                time.sleep(3)
                ser.write((last_message + '\n').encode())
            except:
                try:
                    time.sleep(3)
                    ser.write((last_message + '\n').encode())
                except:
                    last_battery_used == True
                    continue
            log("finished redoing!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        last_battery_used = is_on_battery_power()


    


if __name__ == "__main__":
    # Ensure the script runs with administrator privileges
    if windll.shell32.IsUserAnAdmin():

        try:
            ser = serial.Serial('COM4', 9600, timeout=1)
            time.sleep(4)
        except:
            log(f"in main Failed to open serial port")


        log("started")
        send_to_arduino('150')


        t = threading.Thread(target=get_temperature_from_lhm_and_set_arduino)
        log("starting loop")
        t.start()


        commanderrr = threading.Thread(target=check_for_command)
        commanderrr.start()


        rd = threading.Thread(target=redo)
        rd.start()

    else:
        log("no permission code exiting")

