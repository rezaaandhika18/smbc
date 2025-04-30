# smbc
Data Engineer: CDC Challenge

## Step 1: Install postgree database
Edit `postgresql.conf`:
```ini
wal_level = logical
max_wal_senders = 10
max_replication_slots = 10
```
## Step 2: Connect to the database:
psql -h localhost -U postgres -d source_db

Create the `table`:
```ini
CREATE TABLE customers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

Create Replicator and publisher :
```ini
CREATE PUBLICATION mypub FOR TABLE customers;
CREATE USER replicator WITH REPLICATION PASSWORD 'replicator';
GRANT SELECT ON customers TO replicator;
ALTER TABLE customers REPLICA IDENTITY FULL;
```
Check Replication Run :
```ini
    SELECT * FROM pg_replication_slots;
```

## Step 3: Install Python and PIP
Install `Pakages PIP`:
```ini
pip install kafka-python
pip install confluent-kafka
```

## Step 4: Download Kafka and Debezium
`Kafka` :
```ini
wget https://downloads.apache.org/kafka/3.9.0/kafka_2.13-3.9.0.tgz

Extract => 
    tar -xvzf kafka_2.13-3.9.0.tgz
```
`Debezium` :
```ini
cd kafka_2.13-3.9.0
mkdir plugins
wget https://repo1.maven.org/maven2/io/debezium/debezium-connector-postgres/2.4.1.Final/debezium-connector-postgres-2.4.1.Final-plugin.tar.gz

Extract => 
    tar -xvzf plugins/debezium-connector-postgres-2.4.1.Final-plugin.tar.gz
```
    
## Step 5: Setup Kafka
- In folder kafka
```ini
cd config
```

- Edit file `connect-standalone.properties`:
```ini
plugin.path=/mnt/e/smbc/kafka_2.13-3.9.0/plugins #your path plugin
```

- Create your own connector config file (e.g. `pg-source.properties`):
```ini
name=pg-connector
connector.class=io.debezium.connector.postgresql.PostgresConnector
database.hostname=localhost
database.port=5432
database.user=replicator
database.password=replicator
database.dbname=source_db
database.server.name=pg
table.include.list=public.customers
plugin.name=pgoutput
publication.name=mypub
slot.name=customer_slot
topic.prefix=customer_prefix
```

## Step 6: Start Kafka
- Back to folder kafka (e.g. /mnt/e/smbc/kafka_2.13-3.9.0)

- Start Zookeeper (terminal 1):
```ini
bin/zookeeper-server-start.sh config/zookeeper.properties
```

- Start Kafka Broker (terminal 2)
```ini
bin/kafka-server-start.sh config/server.properties
```

- Start Kafka Client (terminal 3)
```ini
bin/connect-standalone.sh config/connect-standalone.properties config/pg-connector.properties
```

## Step 7: Check Kafka and CDC from postgree
Check list `kafka`:
```ini
bin/kafka-topics.sh --bootstrap-server localhost:9092 --list
```

Run File Python (Check kafka changes) :
```ini
python3 testKafka.py
```

## Step 8: Insert, Update, Delete Posgree
`E.g.Insert`:
```ini
INSERT INTO customers (name, email) VALUES 
('Alice', 'alice@example.com'),
('James', 'james@example.com'),
('Abert', 'abert@example.com'),
('Luna', 'luna@example.com'),
('Gerald', 'gerald@example.com'),
('Isabella', 'isabella@example.com'),
('Jacob', 'jacob@example.com'),
('Charlotte', 'charlotte@example.com'),
('Benjamin', 'benjamin@example.com'),
('Max', 'max@example.com');
```

`E.g.Update`:
```ini
UPDATE customers SET name = 'Maya', email= 'maya@example.com' WHERE id = 'f8822bff-d654-412b-9722-603738eecc9c';
```

`E.g.Delete`:
```ini
Delete customers WHERE id = 'f8822bff-d654-412b-9722-603738eecc9c';
```

Expect Result From Kafka :
```ini
{
    "before": null,
    "after": {
        "id": "00266192-e898-4e62-8198-41af58ce981e",
        "name": "Max",
        "email": "max@example.com",
        "updated_at": 1746008890163558
    },
    "source": {
        "version": "2.4.1.Final",
        "connector": "postgresql",
        "name": "customer_prefix",
        "ts_ms": 1745983690169,
        "snapshot": "false",
        "db": "source_db",
        "sequence": "[\"38763440\",\"38785928\"]",
        "schema": "public",
        "table": "customers",
        "txId": 857,
        "lsn": 38785928,
        "xmin": null
    },
    "op": "c",
    "ts_ms": 1745983690684,
    "transaction": null
}
```

## Step 9 : Export Log (JSON)
Run File :
```ini
python3 consume.py
```

Check Result :
```ini
consumer/kafka-cdc.log
```

Expected Result :
```ini
"c"	Create => A new row was inserted.
"u"	Update => An existing row was updated.
"d"	Delete => A row was deleted.
"r"	Snapshot => Row from a snapshot (initial data load).

Time|Latency|Type|idtrx|table|schema|idcustomer|JSONBefore|JSONAfter
2025-04-30 10:28:10,848|0.17s|c|857|customers|public|4bee2648-b0fa-4a61-9306-cc42e29f28c5|null|{'id': '4bee2648-b0fa-4a61-9306-cc42e29f28c5', 'name': 'Charlotte', 'email': 'charlotte@example.com', 'updated_at': 1746008890163558}
2025-04-30 10:28:10,849|0.17s|c|857|customers|public|00266192-e898-4e62-8198-41af58ce981e|null|{'id': '00266192-e898-4e62-8198-41af58ce981e', 'name': 'Max', 'email': 'max@example.com', 'updated_at': 1746008890163558}
```

## Step 10 : Monitoring
### Loki:
```ini
wget https://github.com/grafana/loki/releases/download/v2.9.4/loki-linux-amd64.zip

Extract => 
unzip loki-linux-amd64.zip
```
    
Create your own config file (e.g. `loki-config.yaml`): # same path with export loki
```ini
auth_enabled: false

server:
    http_listen_port: 3100
    grpc_listen_port: 9096
    log_level: debug
    grpc_server_max_concurrent_streams: 1000

common:
    instance_addr: 127.0.0.1
    path_prefix: /mnt/e/smbc/loki
storage:
    filesystem:
    chunks_directory: /mnt/e/smbc/loki/chunks
    rules_directory: /mnt/e/smbc/loki/rules
replication_factor: 1
ring:
    kvstore:
    store: inmemory

query_range:
    results_cache:
        cache:
        embedded_cache:
            enabled: true
            max_size_mb: 100

limits_config:
    metric_aggregation_enabled: true

schema_config:
    configs:
        - from: 2020-10-24
        store: tsdb
        object_store: filesystem
        schema: v13
        index:
            prefix: index_
            period: 24h

pattern_ingester:
    enabled: true
    metric_aggregation:
        loki_address: localhost:3100

ruler:
    alertmanager_url: http://localhost:9093

frontend:
    encoding: protobuf
```

### Promtail:
```ini
wget https://github.com/grafana/loki/releases/download/v3.2.0/promtail-linux-amd64.zip
Extract => 
    unzip loki-linux-amd64.zip
```
    
Create your own config file (e.g. `promtail-config.yaml`): # same path with export promtail
```ini
server:
    http_listen_port: 9080

    positions:
        filename: /mnt/e/smbc/positions.yaml

    clients:
        - url: http://localhost:3100/loki/api/v1/push

    scrape_configs:
        - job_name: python-logs
            static_configs:
            - targets:
                - localhost
                labels:
                job: kafka-cdc
                __path__: /mnt/e/smbc/consumer/kafka-cdc.log #path yout export JSON
```

### Grafana:
```ini    
wget https://dl.grafana.com/enterprise/release/grafana-enterprise-11.6.1.linux-amd64.tar.gz

Extract => 
    tar -xvzf grafana-enterprise-11.6.1.linux-amd64.tar.gz
```
===============================================================================
- Run Loki and promtail :
```ini
    ./promtail-linux-amd64 -config.file=promtail-config.yaml
    ./loki-linux-amd64 -config.file=loki-config.yaml
```
- Check :
```ini
http://localhost:3100/metrics #Loki
```

- Run Grafana
```ini
grafana-v11.6.1/bin/grafana-server web
```
- Go To :
```ini
http://localhost:3000
Login: admin/admin
```
    
Set up Grafana to Visualize Logs from Loki
```ini
- Add Loki as a Data Source:
- Go to Configuration -> Data Sources.
- Click Add Data Source and choose Loki.
- Set the URL to http://localhost:3100.
- Click Save & Test to verify the connection.
```
Visualize Logs in Grafana
```ini
- Create a new Dashboard in Grafana.
- Add a Panel and set the data source to Loki.
- Run a Loki query to filter and visualize the logs. You can use a simple query like:
    {job="kafka-cdc"}
```

## Handle If CDC failure
- Install `supervisor`
```ini
sudo apt install supervisor
```

- Config supervisor
Create your own config zookeeper (e.g. `zookeeper.conf`)
```ini
[program:zookeeper]
command=/mnt/e/smbc/kafka_2.13-3.9.0/bin/zookeeper-server-start.sh /mnt/e/smbc/kafka_2.13-3.9.0/config/zookeeper.properties
directory=/mnt/e/smbc/kafka_2.13-3.9.0
autostart=true
autorestart=true
stdout_logfile=/mnt/e/smbc/log/zookeeper.out.log
stderr_logfile=/mnt/e/smbc/log/zookeeper.err.log
user=apps

Create your own config kafka-broker (e.g. `kafka-broker.conf`)
```ini
[program:kafka-broker]
command=/mnt/e/smbc/kafka_2.13-3.9.0/bin/kafka-server-start.sh /mnt/e/smbc/kafka_2.13-3.9.0/config/server.properties
directory=/mnt/e/smbc/kafka_2.13-3.9.0
autostart=true
autorestart=true
stdout_logfile=/mnt/e/smbc/log/kafka-broker.out.log
stderr_logfile=/mnt/e/smbc/log/kafka-broker.err.log
user=apps
```

Create your own config kafka (e.g. `kafka-connect.conf`)
```ini
[program:kafka-connect]
command=/mnt/e/smbc/kafka_2.13-3.9.0/bin/connect-standalone.sh /mnt/e/smbc/kafka_2.13-3.9.0/config/connect-standalone.properties /mnt/e/smbc/kafka_2.13-3.9.0/config/pg-connector.properties
directory=/mnt/e/smbc/kafka_2.13-3.9.0
autostart=true
autorestart=true
stdout_logfile=/mnt/e/smbc/log/kafka-connect.out.log
stderr_logfile=/mnt/e/smbc/log/kafka-connect.err.log
user=apps
```

Create your own config consume (e.g. `consume.conf`)
```ini
[program:consume]
command=/usr/bin/python3 /mnt/e/smbc/consume.py
directory=/mnt/e/smbc
autostart=true
autorestart=true
stderr_logfile=/mnt/e/smbc/log/consume.err.log
stdout_logfile=/mnt/e/smbc/log/consume.out.log
user=apps
```

Supervisor Command
```ini
| Command                            | Description                                                     |
|------------------------------------|-----------------------------------------------------------------|
| `sudo supervisorctl reread`        | Scans for new or changed config files (does not apply them yet) |
| `sudo supervisorctl update`        | Applies changes from `reread`, starts new or updated programs   |
| `sudo supervisorctl status`        | Displays the current status of all managed processes            |
| `sudo supervisorctl start <name>`  | Starts the specified program manually                           |
| `sudo supervisorctl stop <name>`   | Stops the specified program gracefully                          |
| `sudo supervisorctl restart <name>`| Restarts the specified program (stop -> start)                  |
| `sudo supervisorctl restart all`   | Restarts all managed services                                   |
```

#### Abstract:
    Python 3.11.2
    pip 23.0.1
    Kafka_2.13-3.9.0
    Loki v2.9.4
    Promtail v3.2.0
    grafana-v11.6.1
    supervisor