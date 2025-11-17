import subprocess
import sys
import os
import json



try:
    with open(os.path.join(os.path.dirname(__file__), "command_param.json"), "r") as file:
        config = json.load(file)

except:
    print("Json File Not Found !")

id2 = config["id_server_2"]
host2 = config["server2_host"]
port2 = config["server2_port"]
replica_id2 = config["server2_replica_id"]
state_file2 = config["server2_state_file"]
checkpoint_freq2 = config["server2_checkpoint_freq"]
is_primary2 = config["server2_isprimary"]

backup1_2 = {
    "name": config["server2_backup1_name"],
    "host": config["server2_backup1_host"],
    "port": config["server2_backup1_port"],
}

backup2_2 = {
    "name": config["server2_backup2_name"],
    "host": config["server2_backup2_host"],
    "port": config["server2_backup2_port"],
}

file_path = os.path.join(os.path.dirname(__file__), "..", "src", "server", "server.py")

try:
    
    subprocess.run([
        sys.executable, file_path,
        "--host", host2,
        "--port", str(port2),
        "--replica-id", replica_id2,
        "--state-file", state_file2,
        "--checkpoint-freq", str(checkpoint_freq2),
        "--is-primary", str(is_primary2),
        "--backup1-name", backup1_2["name"],
        "--backup1-host", backup1_2["host"],
        "--backup1-port", str(backup1_2["port"]),
        "--backup2-name", backup2_2["name"],
        "--backup2-host", backup2_2["host"],
        "--backup2-port", str(backup2_2["port"]),
    ])

except KeyboardInterrupt:

    print("Server Process End.")


