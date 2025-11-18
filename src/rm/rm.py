import argparse
import json
import os
import socket
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
import requests


# -------------------- Config & State --------------------

# Membership (current healthy servers) & count
membership = []   # list[str]
member_count = 0  # int


replicas_dic = None
primary = 'S1'
configuration = 1

# Log file path
start_time_filename = time.strftime("%Y%m%d_%H:%M:%S")
log_file = os.path.join(
    os.path.dirname(__file__), "..", "..", "logs",
    f"gfd_log_{start_time_filename.replace(':','_')}.txt"
)

# -------------------- Utils --------------------

def log(text: str):
    print(text)
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    with open(log_file, "a") as f:
        f.write(text + "\n")

def _timestamp() -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S")

def print_membership_info(communicate_with_gfd):

    global membership, member_count

    member_count = len(membership) 

    if communicate_with_gfd:
       
       if member_count > 0:
           log(f"\033[32m[{_timestamp()}] Communicate with GFD: RM: {member_count} members: {' '.join(membership)}\033[0m")
       else:
           log(f"\033[32m[{_timestamp()}] Communicate with GFD: RM: {member_count} members\033[0m")
    else:
       if member_count > 0:
           log(f"\033[32m[{_timestamp()}] RM: {member_count} members: {' '.join(membership)}\033[0m")
       else:
           log(f"\033[32m[{_timestamp()}] RM: {member_count} members\033[0m")
    
def who_is_primary():

    global primary

    if primary not in membership:
        if len(membership) > 0:
            primary = membership[0]
            for replica_name, addr in replicas_dic.items():
                if replica_name == primary:
                    primary_host, primary_port = replicas_dic[replica_name]
                    primary_url = f"http://{primary_host}:{primary_port}/select_primary"
                    try:
                        requests.post(primary_url, timeout=5)
                        #print(f"set {primary_url} to primary")
                    except requests.exceptions.RequestException as e:
                        log(f"\033[33m[{time.strftime('%Y-%m-%d %H:%M:%S')}] WARN: Failed to set the primary: {primary_url}\033[0m")
                elif replica_name in membership:
                    back_host, back_port = replicas_dic[replica_name]
                    back_url = f"http://{back_host}:{back_port}/select_backup"
                    try:
                        requests.post(back_url, timeout=5)
                        #print(f"set {back_url} to backup")
                    except requests.exceptions.RequestException as e:
                        log(f"\033[33m[{time.strftime('%Y-%m-%d %H:%M:%S')}] WARN: Failed to set the back_up: {back_url}\033[0m")

            log(f"\033[32m[{_timestamp()}] New Primary: {primary} \033[0m")
    
    else:

        server_1 = 'S1'
        if server_1 in membership and server_1 != primary:
            back_host, back_port = replicas_dic[server_1]
            back_url = f"http://{back_host}:{back_port}/select_backup"
            try:
                requests.post(back_url, timeout=5)
                print(f"set {back_url} to backup")
            except requests.exceptions.RequestException as e:
                log(f"\033[33m[{time.strftime('%Y-%m-%d %H:%M:%S')}] WARN: Failed to set the back_up: {back_url}\033[0m")


        
    
class RMHandler(BaseHTTPRequestHandler):


    def _set_headers(self, code=200):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()

    def log_message(self, fmt, *args):
        return

    def do_POST(self):

        length = int(self.headers.get("Content-Length", 0))

        if length > 0:
            body = self.rfile.read(length)
            try:
                body_data = json.loads(body)
            except Exception:
                print("Cannot get the body")

        path = self.path

        if path == "/membership":

            received_membership = body_data.get("membership", [])

            if not isinstance(received_membership, list):
                self._set_headers(400)
                self.wfile.write(json.dumps({"error": "membership must be a list"}).encode())
                return
            
            global membership
            membership = received_membership

            if configuration == 0:
                who_is_primary()

            print_membership_info(True)

            self._set_headers(200)
            self.wfile.write(json.dumps({"ack_msg": "membership updated"}).encode())
            return
            
        else:

            self._set_headers(404)
            self.wfile.write(json.dumps({"error": "unknown path"}).encode())
            return


        
def main():

    global configuration, replicas_dic

    parser = argparse.ArgumentParser(description="Replication Manager server (RM)")
    parser.add_argument("--host", default="0.0.0.0", help="RM host IP (default 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8090, help="RM port number (default 8090)")
    parser.add_argument("--configuration", type=int, default=1, help="0: Passive 1: Active")
    parser.add_argument("--s1_host", default="0.0.0.0", help="RM host IP (default 0.0.0.0)")
    parser.add_argument("--s1_port", type=int, default=8080, help="RM port number (default 8090)")
    parser.add_argument("--s2_host", default="0.0.0.0", help="RM host IP (default 0.0.0.0)")
    parser.add_argument("--s2_port", type=int, default=8081, help="RM port number (default 8090)")
    parser.add_argument("--s3_host", default="0.0.0.0", help="RM host IP (default 0.0.0.0)")
    parser.add_argument("--s3_port", type=int, default=8082, help="RM port number (default 8090)")
    args = parser.parse_args()

    s1_host = args.s1_host
    s1_port = args.s1_port
    s2_host = args.s2_host
    s2_port = args.s2_port
    s3_host = args.s3_host
    s3_port = args.s3_port
    configuration = args.configuration

    replicas_dic = {'S1': (s1_host, s1_port), 'S2': (s2_host, s2_port), 'S3':(s3_host, s3_port)}


    server = HTTPServer((args.host, args.port), RMHandler)

    log(f"[{_timestamp()}] RM listening on {args.host}:{args.port}")
    print_membership_info(False)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        log(f"\n[{_timestamp()}] RM shutting down...")
        server.server_close()


if __name__ == "__main__":
    main()