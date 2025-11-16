import argparse
from http.server import HTTPServer
from request_handler import CounterRequestHandler, Role, Configuration
from state_manager import StateManager
from checkpoint_handler import CheckpointHandler
import time
import json

class SingleThreadedHTTPServer(HTTPServer):
    allow_reuse_address = True

def clear_json(f):
    with open(f, "w", encoding="utf-8") as f:
        json.dump({}, f)

def main():
    # Parse args
    parser = argparse.ArgumentParser(description="Counter Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8080, help="Port (default: 8080)")
    parser.add_argument("--replica-id", default="S1", help="Replica (default: S1)")
    parser.add_argument("--state-file", default=None, help="Optional JSON file for persistence (default: None)")
    parser.add_argument("--checkpoint-freq", type=int, default=5, help="Send periodic checkpoints (default: 5)")
    parser.add_argument("--configuration", type=int, default=1, help="0: Passive 1: Active")
    parser.add_argument("--is-primary", type=int, default=1, help="Whether this server is primary replica (1.primary/0.backup)")
    parser.add_argument("--backup1-name", default="S1", help="Backup Replica 1 Name")
    parser.add_argument("--backup2-name", default="S1", help="Backup Replica 2 Name")
    parser.add_argument("--backup1-host", default="0.0.0.0", help="Backup Replica 1 Host")
    parser.add_argument("--backup1-port", default="8080", help="Backup Replica 1 Port")
    parser.add_argument("--backup2-host", default="0.0.0.0", help="Backup Replica 2 Host")
    parser.add_argument("--backup2-port", default="8080", help="Backup Replica 2 Port")
    args = parser.parse_args()

    state = StateManager(state_file=args.state_file, replica_id=args.replica_id, replica_host=args.host, replica_port=args.port)
    checkpoint_handler = CheckpointHandler(time.time(), args.checkpoint_freq, state, curr_replica_id=args.replica_id)

    CounterRequestHandler.state_manager = state
    CounterRequestHandler.replica_id = args.replica_id

    if args.configuration == 1:
        CounterRequestHandler.configuration = Configuration.ACTIVE
    else:
        CounterRequestHandler.configuration = Configuration.PASSIVE

    if args.is_primary == 1:
        role = Role.PRIMARY
        i_am_ready = 1
    else:
        role = Role.BACKUP
        i_am_ready = 0

    CounterRequestHandler.role = role
    CounterRequestHandler.i_am_ready = i_am_ready

    print("\033[94m%s i_am_ready -> %d\033[0m" % (CounterRequestHandler.replica_id, CounterRequestHandler.i_am_ready))

    # Start listening
    server = SingleThreadedHTTPServer((args.host, args.port), CounterRequestHandler)
    server.timeout = 0.1
    print(f"\033[94m[{time.strftime('%Y-%m-%d %H:%M:%S')}] Listening on http://{args.host}:{args.port} as {args.replica_id}\033[0m")
    print(f"\033[94m[{time.strftime('%Y-%m-%d %H:%M:%S')}] Endpoints: POST /increase, POST /decrease, GET /get, GET /heartbeat\033[0m")

    # Use the handler's role attribute so role changes can happen at runtime
    if CounterRequestHandler.role == Role.BACKUP:
        print(f"\033[94m[{time.strftime('%Y-%m-%d %H:%M:%S')}] This replica now is a backup server \033[0m")
    else:
        print(f"\033[94m[{time.strftime('%Y-%m-%d %H:%M:%S')}] This replica now is a primary server \033[0m")

    try:
        # Writeup said that the checkpoint_count is 1 at first.
        while True: 
            if CounterRequestHandler.role == Role.PRIMARY:
                checkpoint_handler.send_request([[args.backup1_name, args.backup1_host, args.backup1_port], [args.backup2_name, args.backup2_host, args.backup2_port]])
            server.handle_request()
    except KeyboardInterrupt:
        # clear_json(args.replica_file)
        print(f"\n\033[91m[{time.strftime('%Y-%m-%d %H:%M:%S')}] server has died...\033[0m")
    finally:
        # clear_json(args.replica_file)
        server.server_close()

if __name__ == "__main__":
    main()
