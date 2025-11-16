#!/usr/bin/env python3
import argparse
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import time
import os
import requests

# -------------------- Config & State --------------------

####### start #######
rm_host = None
rm_port = None
#######  end  #######

# lfd_id -> { "server_id": str, "status": str, "last_update": float }
lfd_status_table = {}

# Only these statuses are considered healthy (strict)
ALIVE_STATUSES = {"alive"}

# Heartbeat timeout (seconds): if exceeded, treat that LFD as failed
TIMEOUT = 10.0

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
    """Print and append to log file."""
    print(text)
    with open(log_file, "a") as f:
        f.write(text + "\n")

def _timestamp() -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S")

def _is_lfd_alive(info: dict, now: float) -> bool:
    """
    An LFD is considered 'alive for membership purposes' iff:
      - its reported status is strictly in ALIVE_STATUSES (e.g., 'alive'), and
      - it has not timed out.
    """
    timed_out = (now - info["last_update"] > TIMEOUT)
    return (info["status"] in ALIVE_STATUSES) and (not timed_out)

####### start #######
def report_membership_rm(timeout=5):

    rm_membership_url = f"http://{rm_host}:{rm_port}/membership"
    #print(f"will send membership: {membership}")
    payload = {
        "membership": membership,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    try:
        requests.post(rm_membership_url, json=payload, timeout=timeout)
    except requests.exceptions.RequestException as e:
        log(f"\033[33m[{time.strftime('%Y-%m-%d %H:%M:%S')}] WARN: Failed to report status to GFD: {e}\033[0m")
####### end #######

# -------------------- Membership maintenance --------------------

def recompute_membership_for(server_id: str):
    """
    Keep membership[] consistent with the aggregate of all LFDs
    reporting for this server_id.
      - If ANY LFD is alive (strictly in ALIVE_STATUSES and not timed out) -> ensure present.
      - If NONE are alive -> ensure removed.
    """
    global member_count

    now = time.time()
    any_alive = False
    for info in lfd_status_table.values():
        if info["server_id"] != server_id:
            continue
        if _is_lfd_alive(info, now):
            any_alive = True
            break

    in_membership = (server_id in membership)

    if any_alive and not in_membership:
        membership.append(server_id)
        member_count += 1
        log(f"\033[35m[{_timestamp()}] GFD: Adding server {server_id}...\033[0m")
        log(f"\033[32m[{_timestamp()}] GFD: {member_count} members: {' '.join(membership)}\033[0m")
        ####### start #######
        report_membership_rm()
        ####### end #######

    elif (not any_alive) and in_membership:
        membership.remove(server_id)
        member_count -= 1
        log(f"\033[35m[{_timestamp()}] GFD: Deleting server {server_id}...\033[0m")
        log(f"\033[32m[{_timestamp()}] GFD: {member_count} members: {' '.join(membership)}\033[0m")
        ####### start #######
        report_membership_rm()
        ####### end #######

def check_timeouts():
    """
    Mark timed-out LFDs as failed (if they weren't already) and
    recompute membership for their server.
    """
    now = time.time()
    # Iterate over a list of items to avoid dict-size-change pitfalls
    for lfd_id, info in list(lfd_status_table.items()):
        # If it's already 'failed', no need to flip; we still recompute below
        if (now - info["last_update"] > TIMEOUT) and info["status"] != "failed":
            info["status"] = "failed"
            # Optional: log status change on timeout
            log(f"[{_timestamp()}] Timeout: LFD={lfd_id} (server={info['server_id']}) -> failed")
        # Recompute for each server that had any chance of state change by timeout
        recompute_membership_for(info["server_id"])

# -------------------- HTTP Handler --------------------

class GFDHandler(BaseHTTPRequestHandler):
    def _set_headers(self, code=200):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        try:
            data = json.loads(body)
        except Exception:
            self._set_headers(400)
            self.wfile.write(json.dumps({"error": "invalid json"}).encode())
            return

        path = self.path

        if path == "/register":
            lfd_id = data.get("lfd_id")
            server_id = data.get("server_id")
            if not lfd_id or not server_id:
                self._set_headers(400)
                self.wfile.write(json.dumps({"error": "missing lfd_id/server_id"}).encode())
                return

            # Register as 'registered' (NOT healthy). This will NOT add to membership.
            lfd_status_table[lfd_id] = {
                "server_id": server_id,
                "status": "registered",
                "last_update": time.time()
            }

            # Safe to call; 'registered' isn't counted as alive
            recompute_membership_for(server_id)

            self._set_headers(200)
            self.wfile.write(json.dumps({"msg": "registered"}).encode())
            return

        elif path == "/status":
            lfd_id = data.get("lfd_id")
            server_id = data.get("server_id")
            status = data.get("status")  # expected: 'alive' | 'warn' | 'failed' (or others)
            if not lfd_id or not server_id or status is None:
                self._set_headers(400)
                self.wfile.write(json.dumps({"error": "missing lfd_id/server_id/status"}).encode())
                return

            timestamp = _timestamp()
            prev_status = lfd_status_table.get(lfd_id, {}).get("status")

            lfd_status_table[lfd_id] = {
                "server_id": server_id,
                "status": status,
                "last_update": time.time()
            }

            if prev_status != status:
                log(f"\033[31m[{timestamp}] Status change: LFD={lfd_id} -> {status}...\033[0m")

            # IMPORTANT: keep membership in sync on every status report
            recompute_membership_for(server_id)

            self._set_headers(200)
            self.wfile.write(json.dumps({"msg": "status received"}).encode())
            return

        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({"error": "unknown path"}).encode())
            return

    def log_message(self, fmt, *args):
        # Silence BaseHTTPRequestHandler's default access logs
        return

# -------------------- Main --------------------

def main():
    parser = argparse.ArgumentParser(description="GFD Server for LFDs")
    parser.add_argument("--host", default="0.0.0.0", help="GFD host (default 0.0.0.0)")
    parser.add_argument("--port", type=int, default=6000, help="GFD port (default 6000)")

    ####### start #######
    parser.add_argument("--rm_host", default="0.0.0.0", help="RM host to notify (default 127.0.0.1)")
    parser.add_argument("--rm_port", type=int, default=8090,help="RM port to notify (default 8090)")
    #######  end  #######

    parser.add_argument("--timeout", type=float, default=10.0, help="LFD heartbeat timeout seconds (default 10.0)")
    args = parser.parse_args()

    global TIMEOUT
    TIMEOUT = args.timeout

    ####### start #######
    global rm_host, rm_port
    rm_host = args.rm_host
    rm_port = args.rm_port
    #######  end  #######

    log(f"[{_timestamp()}] Starting GFD at {args.host}:{args.port} with timeout={TIMEOUT}s")
    log(f"\033[32m[{_timestamp()}] GFD: {member_count} members\033[0m")
    ####### start #######
    report_membership_rm()
    ####### end #######

    server = HTTPServer((args.host, args.port), GFDHandler)
    server.timeout = 1  # process a request or timeout every 1s

    try:
        while True:
            check_timeouts()
            server.handle_request()
    except KeyboardInterrupt:
        log(f"\n[{_timestamp()}] GFD shutting down...")
        server.server_close()

if __name__ == "__main__":
    main()
