import serial
# import os
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
            except:
                return False
            time.sleep(0.5)
    return False

while True:
    try:
        ports = list_serial_ports()
        if not ports:
            break
        port = ports[looper % len(ports)]

        ser = serial.Serial(port, 9600, timeout=1)
        time.sleep(3)

        if ser is None:
            break

        ser.write((pwm + '\n').encode())

        if read_from_arduino():
            time.sleep(100)
        else:
            looper = (looper + 1) % len(ports)

    finally:
        if ser is not None and ser.is_open:
            ser.close()
        time.sleep(60)
