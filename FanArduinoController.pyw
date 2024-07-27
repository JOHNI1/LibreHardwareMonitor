import serial
import os
from ctypes import windll
import time
from HardwareMonitor.Hardware import *  # equivalent to 'using LibreHardwareMonitor.Hardware;'

import psutil

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
    return not psutil.sensors_battery().power_plugged


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
update_frequency = 5 # once every n seconds
useLHM = True
commander_message = "enter pwm of 0-255 for custom command and -1 for using automatic speed control using LHM's reading\n"
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


average_temp = None
weights = [1.2, 0.8, 1.2, 0.8]   # <=[cpu_max_tmp, cpu_average_tmp, gpu_max_temp, gpu_average_temp]
temps = None
new_duty_cycle = None
sum_weights = weights[0]+weights[1]+weights[2]+weights[3]

def pwm_tuner(average_temp) -> str:
    if average_temp < 40:
        return "0"
    if average_temp > 90:
        return "255"
    return str(int(246/(1+60000*(2**(-float(average_temp)/4)))+11))


# Define maximum log size (in bytes)
MAX_LOG_SIZE = 1024 * 50  # 50 kilobytes (adjust as needed)
file_size = None
def log(message):
    global file_size
    """Logs a message with a timestamp to a limited-size file."""
    try:
        # Open the log file in append mode
        with open('log.txt', 'a') as file:
            # Get current file size
            file_size = os.path.getsize('log.txt')

            # Truncate if exceeding maximum size
            if file_size > MAX_LOG_SIZE:
                file.truncate(0)  # Clear the file content

            # Write the formatted message
            file.write(f"{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}: {message}\n")
    except:
        # nothing to do because printing fails meaning no way of knowing
        pass

command = None
COM = 'COM3'
def main():

    global isRunning, last_temp, useLHM, average_temp, temps, sum_weights
    global last_message, last_battery_used, ser
    global commander_message, command
    while isRunning:
        time.sleep(update_frequency)
        if is_on_battery_power():
            if last_battery_used == False:
                last_battery_used = True
                log("computer disconnected from docking station!")

        else:
            if last_battery_used == True:
                try:
                    log("computer connected to docking station! starting the serial connection and commanding pwm!")
                    ser = serial.Serial(COM, 9600, timeout=1)
                    time.sleep(3)
                    ser.write((last_message + '\n').encode())
                    last_battery_used = False
                except:
                    try:
                        ser.write((last_message + '\n').encode())
                        last_battery_used = False
                    except:
                        last_battery_used = True
                        continue

        #commander
        try:
            command_detected = False
            with open('command.txt', 'r') as file:
                command_raw = file.read()
                command = command_raw.split("\n")[1]
                if len(command_raw) > len(commander_message):
                    log(f"commander text message!")
                    # for i, text in enumerate(command_raw.split("\n")):
                    #     log("command" + str(i) + ": " + text)
                    if command == "-1":
                        useLHM = True
                        command_detected = True
                        log("back at using LHM reading auto control!")
                    elif int(command) >= 0 and int(command) <= 255:
                        useLHM = False
                        command_detected = True
                        log(f"new_duty_cycle: {command} by the commander!")
                        send_to_arduino(command)
                        log(f"commander now incharge!")
                if len(command_raw) < len(commander_message):
                    log(len(command_raw))
                    command_detected = True

            if command_detected:
                with open('command.txt', 'w') as file:
                    file.write(commander_message)
            
        except:
            try:
                with open('command.txt', 'w') as file:
                    file.write(commander_message)
            except:
                log("there is a serious error in the check_for_command method!")
        #LHM
        try:
            if useLHM:
                #get processros temp:
                
                try:
                    temps = get_temp()     #[cpu_max_tmp, cpu_average_tmp, gpu_max_temp, gpu_average_temp]
                    average_temp = int((temps[0]*weights[0]+temps[1]*weights[1]+temps[2]*weights[2]+temps[3]*weights[3])/sum_weights)
                    if last_temp != average_temp:
                        send_to_arduino(pwm_tuner(average_temp))
                        last_temp = average_temp

                except:
                    log("some fucked up shit happened. check the code!")
        except:
            log("some fucked up shit happened. check the code!")


if __name__ == "__main__":
    # Ensure the script runs with administrator privileges
    if windll.shell32.IsUserAnAdmin():
        try:
            ser = serial.Serial(COM, 9600, timeout=1)
            time.sleep(4)
        except:
            log(f"in main Failed to open serial port")
        last_battery_used = is_on_battery_power()
        log("started")
        send_to_arduino('150')
        log("starting loop")
        main()

    else:
        log("no permission code exiting")
