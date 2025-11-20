import subprocess
import sys
import os
import json


try:
    with open(os.path.join(os.path.dirname(__file__), "command_param_clients.json"), "r") as file:
        config = json.load(file)

except:
    print("Json File Not Found !")

HOST = config["rm_host"]
PORT = config["rm_port"]
rm_configuration = config["rm_configuration"]
rm_s1_host = config["rm_s1_host"]
rm_s1_port = config["rm_s1_port"]
rm_s2_host = config["rm_s2_host"]
rm_s2_port = config["rm_s2_port"]
rm_s3_host = config["rm_s3_host"]
rm_s3_port = config["rm_s3_port"]


file_path = os.path.join(os.path.dirname(__file__), "..", "src", "rm", "rm.py")

try:

    subprocess.run([
        sys.executable,
        file_path,
        "--host", HOST,
        "--port", str(PORT),
        "--configuration", str(rm_configuration),
        "--s1_host", rm_s1_host,
        "--s1_port", str(rm_s1_port),
        "--s2_host", rm_s2_host,
        "--s2_port", str(rm_s2_port),
        "--s3_host", rm_s3_host,
        "--s3_port", str(rm_s3_port)
    ])

except KeyboardInterrupt:

    print("RM Process End.")