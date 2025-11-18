import subprocess
import sys
import os
import json


try:
    with open(os.path.join(os.path.dirname(__file__), "command_param_clients.json"), "r") as file:
        config = json.load(file)

except:
    print("Json File Not Found !")

HOST = config["gfd_host"]
PORT = config["gfd_port"]
rm_host = config["gfd_rm_host"]
rm_port = config["gfd_rm_port"]
timeout = config["gfd_time_out"]

file_path = os.path.join(os.path.dirname(__file__), "..", "src", "gfd", "gfd.py")

try:

    subprocess.run([sys.executable, file_path, "--host", HOST, "--port", str(PORT), "--rm_host", str(rm_host), "--rm_port", str(rm_port) , "--timeout", str(timeout)])

except KeyboardInterrupt:

    print("LFD Process End.")