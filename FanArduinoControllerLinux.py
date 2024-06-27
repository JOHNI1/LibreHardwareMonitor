import serial
import os
import time
import glob


pwm = '90'
ser = None
timeout = 10
looper = 0

def list_serial_ports():
    ports = glob.glob('/dev/ttyUSB*')
    return ports

def send_to_arduino(message, port):
    try:
        global ser
        ser.write((message + '\n').encode())
        return True
    except:
        # log(f"in send_to_arduino Failed to open serial")
        return False



def read_from_arduino():
    try:
        # global timeout
        global ser
        end_time = time.time() + timeout
        while end_time > time.time():
            if ser.in_waiting > 0:
                try:
                    line = ser.readline().decode('utf-8').strip()
                    if 'b' in line:
                        return True
                    else:
                        return False
                finally:
                    time.sleep(0.5)
    finally:
        return False


while True:
    try:
        ports = list_serial_ports()
        if not ports:
            break
        port = ports[looper%len(ports)][1]

        
        ser = serial.Serial(port, 9600, timeout=1)

        time.sleep(3)

        if ser == None:
            break


        ser.write((pwm + '\n').encode())
        

        if read_from_arduino():
            time.sleep(100)
        else:
            looper += 1
        
    finally:
        ser.close()
        time.sleep(60)























# Define maximum log size (in bytes)
# MAX_LOG_SIZE = 1024 * 50  # 50 kilobytes (adjust as needed)
# file_size = None
# def log(message):
#     global file_size
#     """Logs a message with a timestamp to a limited-size file."""
#     try:
#         # Open the log file in append mode
#         with open('log.txt', 'a') as file:
#             # Get current file size
#             file_size = os.path.getsize('log.txt')

#             # Truncate if exceeding maximum size
#             if file_size > MAX_LOG_SIZE:
#                 file.truncate(0)  # Clear the file content

#             # Write the formatted message
#             file.write(f"{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}: {message}\n")
#     except:
#         # nothing to do because printing fails meaning no way of knowing
#         pass

# input = input("enter pwm: ")
# send_to_arduino(input)