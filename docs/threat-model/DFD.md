flowchart LR
Client[Client / Browser / Mobile] -->|F1: HTTPS GET /media| GW[API Gateway / Reverse Proxy]
Client -->|F2: HTTPS POST/PUT /media| GW


subgraph Edge [Trust Boundary: Edge untrusted]
GW -->|F3: Forward request HTTP| SVC[Media Service FastAPI sync]
end


subgraph Core [Trust Boundary: Core trusted]
SVC -->|F4: SQL read/write| DB[(Database - sqlite/postgres)]
SVC -->|F5: Write logs / send events| LOGS[Logging / Aggregator optional]
SVC -->|F6: Call to backup/export job| STORAGE[Backup Storage]
end


subgraph DevSec [Trust Boundary: DevSec Tools]
CI[CI pipeline SCA, tests] -->|F7: Push/scan code / report| SVC
end


GW -->|F8: Rate limit / block 429| Client


style GW stroke-width:2px,stroke:royalblue
style SVC stroke-width:2px,stroke:darkgreen
style DB stroke-width:2px,stroke:gray
