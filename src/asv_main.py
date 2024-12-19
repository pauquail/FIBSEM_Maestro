import os
import sys
import socket
import time
import version
from fibsem_maestro.serial_control import SerialControl

#  !!! remove serial_control.imaging(1) # !!!
#  !!! remove AS forced to be virtual

#  ACB on reduced area
#  email if problem, stop on error, new image timeout - settings
#  virtual mode
#  sweeping max limits to autoscript_control.py
#  z score for template matching

#  test: email, reduced scanning, template matching, milling
#  add ACB check to criterion !
#  comments from template_settings.yaml as hints

#  v1.1
#  mask for acb
#  spiral af
#  test: multiple masking, mask online training,

settings_path = 'settings.yaml'

# set the listening socket
sock = socket.socket()
sock.bind(("localhost", 6287))

print(f'The microscope is under control FIBSEM_Maestro v {version.VERSION}!')

serial_control = SerialControl(settings_path)

print('Initialization finished!')

serial_control.cycle(2)  # !!!
serial_control.cycle(3)  # !!!

# run FIBSEM control


def run(slice_number):
    serial_control.cycle(slice_number)


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
