import subprocess
import sys
import os
import json


try:
    with open(os.path.join(os.path.dirname(__file__), "command_param.json"), "r") as file:
        config = json.load(file)

except:
    print("Json File Not Found !")

HOST = config["rm_host"]
PORT = config["rm_port"]

file_path = os.path.join(os.path.dirname(__file__), "..", "src", "rm", "rm.py")

try:

    subprocess.run([sys.executable, file_path, "--host", HOST, "--port", str(PORT)])

except KeyboardInterrupt:

    print("RM Process End.")