import subprocess
import sys
import os
import json

with open(os.path.join(os.path.dirname(__file__), "command_param_clients.json"), "r") as file:
        config = json.load(file)

file_path = os.path.join(os.path.dirname(__file__), "..", "src", "client", "client.py")

client_id = "C1"

s1_ip  = config["servers"]["S1"]["ip"]
s1_port = config["servers"]["S1"]["port"]

s2_ip  = config["servers"]["S2"]["ip"]
s2_port = config["servers"]["S2"]["port"]

s3_ip  = config["servers"]["S3"]["ip"]
s3_port = config["servers"]["S3"]["port"]


inputs = "\n".join([
    client_id,
    s1_ip, s1_port,
    s2_ip, s2_port,
    s3_ip, s3_port,
]) + "\n"


try:

    subprocess.run([sys.executable, file_path], input=inputs, text=True,)

except KeyboardInterrupt:

    print("Client Process End.")