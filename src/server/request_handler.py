from http.server import BaseHTTPRequestHandler
import json
import time
from urllib.parse import urlparse, parse_qs
import re
import os
from enum import Enum

class Role(Enum):
    PRIMARY = "primary"
    BACKUP = "backup"

class Configuration(Enum):
    ACTIVE = 0
    PASSIVE = 1

# The server injects a StateManager instance via a class attribute.
class CounterRequestHandler(BaseHTTPRequestHandler):
    state_manager = None
    replica_id = "S1"
    configuration = Configuration.ACTIVE
    role = Role.PRIMARY
    server_start_time = time.strftime("%Y%m%d_%H:%M:%S")
    # log_file = f"logs/server_{replica_id}_log_{server_start_time}.txt"
    log_file = os.path.join(os.path.dirname(__file__), "..",'..', "logs", f"server_{replica_id}_log_{server_start_time.replace(':','_')}.txt")


    # block the default log of BaseHTTPRequestHandler
    # e.g. 127.0.0.1 - "GET /get HTTP/1.1" 200
    def log_request(self, code='-', size='-'):
        pass

    def log_message(self, fmt, *args, color="\033[0;96m"):
        # Add timestamp as suggested in the guide
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        text = f"{color}[{ts}] {self.address_string()} - {fmt % args}\033[0m"
        print(text)
        # write in log
        with open(self.log_file, "a") as f:
            f.write(f"[{ts}] {self.address_string()} - {fmt % args}\n")
        return text
    
    def log_message_before_after(self, fmt, *args, color="\033[0;35m"):
        # Prepend timestamp as suggested in the guide
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        text = f"{color}[{ts}] {self.address_string()} - {fmt % args}\033[0;35m"
        print(text)
        # write in log
        with open(self.log_file, "a") as f:
            f.write(f"[{ts}] {self.address_string()} - {fmt % args}\n")
        return text

    def _send_json(self, code: int, payload: dict):
        data = json.dumps(payload).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def check_legal(self):
        if self.configuration == Configuration.ACTIVE or self.role == Role.PRIMARY:
            return True
        return False

    # Handle GET
    def do_GET(self):
        parsed_url = urlparse(self.path)
        query = parse_qs(parsed_url.query)
        path = parsed_url.path
        client_id = query.get("client_id", ["Not get client id"])[0]
        lfd_id = query.get("lfd_id", ["Not get lfd id"])[0]
        request_num = int(query.get("request_num", [0])[0])

        if path == "/get":
            if not self.check_legal():
                return
            
            value = self.state_manager.get()
            # self.log_message('Sending <reply> for /get with counter=%d', value)
            text = self.log_message('Received <%s, %s, request id: %d, get>', client_id, self.replica_id, request_num)
            text_only_request = re.search(r'<.*?>', text).group(0)
            self.log_message_before_after('state_%s = %d before processing %s', self.replica_id, value, text_only_request)

            self._send_json(200, {"counter": value, "replica_id": self.replica_id, "primary": self.role==Role.PRIMARY})

            self.log_message_before_after('state_%s = %d after processing %s', self.replica_id, value, text_only_request)

            self.log_message('Sending <%s, %s, request id: %d, primary: %s, reply>', client_id, self.replica_id, request_num, self.role==Role.PRIMARY)

        elif path == "/heartbeat":
            self.log_message("%s receives heartbeat from %s", self.replica_id, lfd_id, color="\033[1;92m")
            self._send_json(200, {"ok": True, "replica_id": self.replica_id})
            self.log_message("%s sends heartbeat to %s", self.replica_id, lfd_id, color="\033[1;92m")

        else:
            self._send_json(404, {"error": "not found"})

    # Handle POST
    def do_POST(self):
        client_id = ""
        request_num = 0
        length = int(self.headers.get("Content-Length", 0))
        if length > 0:
            body = self.rfile.read(length)
            try:
                message_data = json.loads(body)
                client_id = message_data.get("client_id")
                request_num = message_data.get("request_num")
            except Exception:
                print("Cannot get the body")

        if self.path == "/increase":
            if not self.check_legal():
                return
            
            text = self.log_message('Received <%s, %s, request id: %d, increase>', client_id, self.replica_id, request_num)
            text_only_request = re.search(r'<.*?>', text).group(0)
            self.log_message_before_after('state_%s = %d before processing %s', self.replica_id, self.state_manager.get(), text_only_request)
            value = self.state_manager.increase()
            self.log_message_before_after('state_%s = %d after processing %s', self.replica_id, self.state_manager.get(), text_only_request)

            self._send_json(200, {"counter": value, "replica_id": self.replica_id, "primary": self.role==Role.PRIMARY})
            text = self.log_message('Sending <%s, %s, request id: %d, primary: %s, reply>', client_id, self.replica_id, request_num, self.role==Role.PRIMARY)
        
        elif self.path == "/decrease":
            if not self.check_legal():
                return
            
            text = self.log_message('Received <%s, %s, request id: %d, decrease>', client_id, self.replica_id, request_num)
            text_only_request = re.search(r'<.*?>', text).group(0)
            self.log_message_before_after('state_%s = %d before processing %s', self.replica_id, self.state_manager.get(), text_only_request)
            value = self.state_manager.decrease()
            self.log_message_before_after('state_%s = %d after processing %s', self.replica_id, self.state_manager.get(), text_only_request)

            self._send_json(200, {"counter": value, "replica_id": self.replica_id, "primary": self.role==Role.PRIMARY})
            text = self.log_message('Sending <%s, %s, request id: %d, primary: %s, reply>', client_id, self.replica_id, request_num, self.role==Role.PRIMARY)
        
        elif self.path == "/send_checkpoint":
            # Primary replica sending checkpoint request to backups
            self.state_manager.set(message_data.get("state", 0))
            value = self.state_manager.get()
            checkpoint_count = message_data.get("checkpoint_count", 0)
            self.log_message('%s received checkpoint request: my state value is %d, new checkpoint count is: %d', self.replica_id, value, checkpoint_count, color="\033[0;36m")
            self._send_json(200, {"ok": True, "replica_id": self.replica_id})

        elif self.path == "/select_primary":
            CounterRequestHandler.role = Role.PRIMARY
            self.log_message('%s set to PRIMARY by select_primary request', self.replica_id, color="\033[0;36m")
            self._send_json(200, {"ok": True, "replica_id": self.replica_id, "role": self.role.value})

        elif self.path == "/select_backup":
            CounterRequestHandler.role = Role.BACKUP
            self.log_message('%s set to BACKUP by select_backup request', self.replica_id, color="\033[0;36m")
            self._send_json(200, {"ok": True, "replica_id": self.replica_id, "role": self.role.value})
        
        else:
            self._send_json(404, {"error": "not found"})
    
    # Handle do HEAD
    def do_HEAD(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
