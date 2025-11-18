import subprocess
import sys
import os
import json

try:
    with open(os.path.join(os.path.dirname(__file__), "command_param.json"), "r") as file:
        config = json.load(file)

except:
    print("Json File Not Found !")

id3 = config["id_server_3"]
host3 = config["server3_host"]
port3 = config["server3_port"]
replica_id3 = config["server3_replica_id"]
state_file3 = config["server3_state_file"]
checkpoint_freq3 = config["server3_checkpoint_freq"]
is_primary3 = config["server3_isprimary"]
configuration = config["server3_configuration"]

backup1_3 = {
    "name": config["server3_backup1_name"],
    "host": config["server3_backup1_host"],
    "port": config["server3_backup1_port"],
}

backup2_3 = {
    "name": config["server3_backup2_name"],
    "host": config["server3_backup2_host"],
    "port": config["server3_backup2_port"],
}

file_path = os.path.join(os.path.dirname(__file__), "..", "src", "server", "server.py")

try:
    
    subprocess.run([
        sys.executable, file_path,
        "--host", host3,
        "--port", str(port3),
        "--replica-id", replica_id3,
        "--state-file", state_file3,
        "--checkpoint-freq", str(checkpoint_freq3),
        "--configuration", str(configuration),
        "--is-primary", str(is_primary3),
        "--backup1-name", backup1_3["name"],
        "--backup1-host", backup1_3["host"],
        "--backup1-port", str(backup1_3["port"]),
        "--backup2-name", backup2_3["name"],
        "--backup2-host", backup2_3["host"],
        "--backup2-port", str(backup2_3["port"]),
    ])


except KeyboardInterrupt:

    print("Server Process End.")


