import sys
import socket
import json

# socket connection
sock = socket.socket()
sock.connect(("localhost", 6287))

print('ASV adapter started')
print(sys.argv[1])
# load slice number from json
if len(sys.argv) > 1:
    try:
        with open(sys.argv[1]) as json_file:
            data = json.load(json_file)

        slice_number = data["sliceNumber"]
        print(f"Json file loaded. Slice no. {slice_number}")
    except Exception as e:
        print('Json file not loaded. Setting slice number to 1. '+repr(e))
        slice_number = 1
else:
    print('Argument for json file localization not passed!')
    slice_number = 1

# send slice_number to app
string_to_send = str(slice_number)
sock.sendall(string_to_send.encode(encoding="utf-8"))
print('Slice number sent by socket.')

# waiting for close
print('Waiting for close')
data = sock.recv(1024)
read_string = data.decode()
print('Received from server: ', read_string)
sock.close()
