import serial
import time
import glob

pwm = '90'
ser = None
timeout = 10
looper = 0

def list_serial_ports():
    ports = glob.glob('/dev/ttyUSB*')
    return ports

def read_from_arduino():
    global ser
    end_time = time.time() + timeout
    while time.time() < end_time:
        if ser.in_waiting > 0:
            try:
                line = ser.readline().decode('utf-8').strip()
                if 'b' in line:
                    return True
            except Exception as e:
                return False
            time.sleep(0.5)
    return False

while True:
    try:
        ports = list_serial_ports()
        if not ports:
            continue
        port = ports[looper % len(ports)]

        ser = serial.Serial(port, 9600, timeout=1)
        time.sleep(3)

        if ser is None:
            continue

        ser.write((pwm + '\n').encode())

        if read_from_arduino():
            time.sleep(100)
        else:
            looper = (looper + 1) % len(ports)

    finally:
        if ser is not None and ser.is_open:
            ser.close()
        time.sleep(60)














# import serial
# import time
# import glob

# pwm = '90'
# ser = None
# timeout = 10
# looper = 0

# def list_serial_ports():
#     ports = glob.glob('/dev/ttyUSB*')
#     # print(f"Available serial ports: {ports}")
#     return ports

# def read_from_arduino():
#     global ser
#     end_time = time.time() + timeout
#     while time.time() < end_time:
#         if ser.in_waiting > 0:
#             try:
#                 line = ser.readline().decode('utf-8').strip()
#                 # print(f"Read line: {line}")
#                 if 'b' in line:
#                     # print("Received 'b' in line")
#                     return True
#             except Exception as e:
#                 # print(f"Error reading line: {e}")
#                 return False
#             time.sleep(0.5)
#     return False

# while True:
#     try:
#         ports = list_serial_ports()
#         if not ports:
#             # print("No serial ports found, exiting loop.")
#             continue
#         port = ports[looper % len(ports)]
#         # print(f"Using port: {port}")

#         ser = serial.Serial(port, 9600, timeout=1)
#         time.sleep(3)

#         if ser is None:
#             # print("Failed to open serial port.")
#             continue

#         ser.write((pwm + '\n').encode())
#         # print(f"Sent PWM: {pwm} to {port}")

#         if read_from_arduino():
#             # print("Sleeping for 100 seconds")
#             time.sleep(100)
#         else:
#             looper = (looper + 1) % len(ports)
#             # print(f"Moving to next port, looper: {looper}")

#     finally:
#         if ser is not None and ser.is_open:
#             ser.close()
#             # print(f"Closed serial port: {port}")
#         # print("Sleeping for 60 seconds")
#         time.sleep(60)
