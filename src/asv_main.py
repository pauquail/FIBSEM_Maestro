import os
import sys
import socket
import time
from fibsem_maestro.serial_control import SerialControl

#  remove line 22: serial_control.imaging(1) # !!!
#  plots
#  bordel v beam (az bude milling)
#  mask for acb
#  mask online training
#  refactor

# test: multiple masking, spiral af, email


settings_path = 'settings.yaml'

# set the listening socket
sock = socket.socket()
sock.bind(("localhost", 6287))

print('The microscope control FIBSEM Maestro now')

serial_control = SerialControl(settings_path)

print('The microscope successfully initalized')

serial_control.imaging(1) # !!!

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


