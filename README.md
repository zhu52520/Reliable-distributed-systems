# reliable-distributed-systems
Implementation of fault-tolerant distributed counter with active/passive replication, heartbeat failure detection, and automatic recovery. 

## Usage
### GFD
`python3 src/gfd/gfd.py`

- `--host`: GFD host (default 0.0.0.0)
- `--port`: GFD port (default 6000)
- `--timeout`: LFD heartbeat timeout in seconds (default 10.0)
- `--replica-file`: Path to replica file (default ../server/replica.json)

### RM

`python3 src/rm/rm.py`

- `--host`: RM host (default 0.0.0.0)
- `--port`: RM port (default 8090)

### LFD
`python3 src/lfd/heartbeat_client.py`

- `--host`: Local server host (default: 0.0.0.0)
- `--port`: Local server port (default: 8080)
- `--gfd_host`: GFD host (default: 0.0.0.0)
- `--gfd_port`: GFD port (default: 6000)
- `--freq`: Heartbeat frequency in seconds (default: 5.0)
- `--timeout`: Heartbeat timeout in seconds (default: 10.0)
- `--lfd_id`: LFD ID (default: LFD1)
- `--server_id`: Server ID


### Server
`python3 src/server/server.py`
- `--host`: Server Host (default: 0.0.0.0)
- `--port`: Server Port (default: 8080)
- `--replica-id`: Replica ID (default: S1)
- `--state-file`: Optional JSON file for persistence (default: None)
- `--checkpoint-freq`: Send periodic checkpoints (default: 5)
- `--configuration`: 0: Active  1: Passive (default: 1)
- `--is-primary`: Whether this server is primary replica (1.primary/0.backup)
- `--backup1-name`: Backup Replica 1 Name (default: S1)
- `--backup1-host`: Backup Replica 1 Host (default: 0.0.0.0)
- `--backup1-port`: Backup Replica 1 Port (default: 8080)
- `--backup2-name`: Backup Replica 2 Name (default: S1)
- `--backup2-host`: Backup Replica 2 Host (default: 0.0.0.0)
- `--backup2-port`: Backup Replica 2 Port (default: 8080)

Endpoints: POST /increase, POST /decrease, GET /get, GET /heartbeat, POST /select_primary

### Client
`python3 src/client/client.py`
- Stdin
