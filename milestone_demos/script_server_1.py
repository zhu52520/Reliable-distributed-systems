import subprocess
import sys
import os
import json



try:
    with open(os.path.join(os.path.dirname(__file__), "command_param.json"), "r") as file:
        config = json.load(file)

except:
    print("Json File Not Found !")

id = config["id_server_1"]
host = config["server1_host"]
port = config["server1_port"]
replica_id = config["server1_replica_id"]
state_file = config["server1_state_file"]
checkpoint_freq = config["server1_checkpoint_freq"]
is_primary = config["server1_isprimary"]

backup1 = {
            "name": config["server1_backup1_name"],
            "host": config["server1_backup1_host"],
            "port": config["server1_backup1_port"],
        }

backup2 = {
            "name": config["server1_backup2_name"],
            "host": config["server1_backup2_host"],
            "port": config["server1_backup2_port"],
        }


file_path = os.path.join(os.path.dirname(__file__), "..", "src", "server", "server.py")

try:
    subprocess.run([
    sys.executable, file_path,
    "--host", host,
    "--port", str(port),
    "--replica-id", replica_id,
    "--state-file", state_file,
    "--checkpoint-freq", str(checkpoint_freq),
    "--is-primary", str(is_primary),
    "--backup1-name", backup1["name"],
    "--backup1-host", backup1["host"],
    "--backup1-port", str(backup1["port"]),
    "--backup2-name", backup2["name"],
    "--backup2-host", backup2["host"],
    "--backup2-port", str(backup2["port"]),
])
    
except KeyboardInterrupt:

    print("Server Process End.")


