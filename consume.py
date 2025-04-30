from kafka import KafkaConsumer  # type: ignore
import json
import time
import logging
from logging.handlers import TimedRotatingFileHandler

# Configure log rotation
logger = logging.getLogger("kafka_logger")
logger.setLevel(logging.INFO)

log_handler = TimedRotatingFileHandler(
    '/mnt/e/smbc/consumer/kafka-cdc.log',
    when='midnight',
    interval=1,
    backupCount=7
)
log_handler.setFormatter(logging.Formatter('%(asctime)s|%(message)s'))
logger.addHandler(log_handler)

# Kafka consumer setup
consumer = KafkaConsumer(
    'customer_prefix.public.customers',
    bootstrap_servers='localhost:9092',
    auto_offset_reset='latest', #earliest
    enable_auto_commit=True,
    value_deserializer=lambda m: json.loads(m.decode('utf-8')) if m else None
)

# Main consume loop
def consume():
    for msg in consumer:
        try:
            payload = msg.value
            if payload and 'op' in payload:
                # CDC operation type
                type_cdc = payload['op']

                # Calculate latency
                ts_ms = payload.get('ts_ms', time.time() * 1000)
                latency = time.time() - (ts_ms / 1000.0)

                # Extract relevant info
                source = payload.get('source', {})
                after = payload.get('after') or {}
                before = payload.get('before') or {}
                id_cust = after.get('id') or before.get('id')

                # Log line data
                log_data = {
                    'idtrx': source.get('txId'),
                    'cdc': type_cdc,
                    'latency': f"{latency:.2f}s",
                    'table': source.get('table'),
                    'dbname': source.get('schema'),
                    'idcust': id_cust,
                    'after': after if after else "null",
                    'before': before if before else "null"
                }

                print(json.dumps(log_data))
                logger.info(
                    f"{latency:.2f}s|{type_cdc}|{log_data['idtrx']}|{log_data['table']}|"
                    f"{log_data['dbname']}|{log_data['idcust']}|{log_data['before']}|{log_data['after']}"
                )

        except Exception as e:
            logger.exception(f"Error processing Kafka message: {e}")

if __name__ == '__main__':
    print("Kafka CDC logger started")
    consume()