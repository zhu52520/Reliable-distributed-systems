import argparse
import json
import os
import socket
import time
from http.server import BaseHTTPRequestHandler, HTTPServer


# -------------------- Config & State --------------------

# Membership (current healthy servers) & count
membership = []   # list[str]
member_count = 0  # int

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

            print_membership_info(True)

            self._set_headers(200)
            self.wfile.write(json.dumps({"ack_msg": "membership updated"}).encode())
            return
            
        else:

            self._set_headers(404)
            self.wfile.write(json.dumps({"error": "unknown path"}).encode())
            return


        
def main():
    parser = argparse.ArgumentParser(description="Replication Manager server (RM)")
    parser.add_argument("--host", default="0.0.0.0", help="RM host IP (default 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8090, help="RM port number (default 8090)")
    args = parser.parse_args()

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