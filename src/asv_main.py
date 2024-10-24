import os
import sys
import socket
import time
import version
from fibsem_maestro.serial_control import SerialControl

#  !!! remove line 33: serial_control.imaging(1) # !!!
#  email if problem (freq)
#  virtual mode
#  mask for acb
#  sweeping max limits to autoscript_control.py
#  z score for template matching
# stop on error
# new image timeout -> email
# default_settings.yaml + settings.yaml
# test: multiple masking, spiral af, email, mask online training, reduced scanning, template matching



settings_path = 'settings.yaml'

# set the listening socket
sock = socket.socket()
sock.bind(("localhost", 6287))

print(f'The microscope is under control FIBSEM_Maestro v {version.VERSION}!')

serial_control = SerialControl(settings_path)

print('Initialization finished!')

serial_control.imaging(2) # !!!
serial_control.imaging(3) # !!!

# run FIBSEM control


def run(slice_number):
    serial_control.imaging(slice_number)


print('Waiting for imaging call...')
while True:
    sock.listen(1)
    conn, addr = sock.accept()
    data = conn.recv(1024)
    received_data = int(data.decode())
    if not data:
        break
    print("Running the imaging routine of slice: " + str(received_data))
    run(received_data)
    conn.sendall(b'close')

conn.close()
