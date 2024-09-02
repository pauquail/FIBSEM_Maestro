import os
import sys
import json

print('ASV script started')



# change work directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# open json for slice number (filename is passed as argument)
if len(sys.argv) > 1:
    with open(sys.argv[1]) as json_file:
        data = json.load(json_file)
        json_file.close()
    slice_number = data["sliceNumber"]
    print(f"Json file loaded. Slice no. {slice_number}")
else:
    slice_number = None

