import serial
import os
import time
ser = serial.Serial('/dev/ttyUSB0', 9600, timeout=1)
last_message = "0"
def send_to_arduino(message):
    try:
        global ser
        global last_message
        last_message = message
        ser.write((message + '\n').encode())
        return True
    except:
        # log(f"in send_to_arduino Failed to open serial")
        return False
# Define maximum log size (in bytes)
MAX_LOG_SIZE = 1024 * 50  # 50 kilobytes (adjust as needed)
file_size = None
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
while True:
    try:
        send_to_arduino("90")
    finally:
        time.sleep(60)
