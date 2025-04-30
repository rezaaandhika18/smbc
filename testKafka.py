from kafka import KafkaConsumer # type: ignore
import json

# Create the Kafka consumer
consumer = KafkaConsumer(
    'customer_prefix.public.customers',  # Topic name
    bootstrap_servers='localhost:9092',  # Kafka broker address
    auto_offset_reset='earliest',        # Ensure to read from the beginning
    value_deserializer=lambda m: json.loads(m.decode('utf-8')) if m else None  # Deserialize if not None
)

# Consume and print messages
for msg in consumer:
    if msg.value:  # Only process if the value is not None
        print(json.dumps(msg.value, indent=2))  # Pretty print the JSON message
    else:
        print("DELETE operation detected: No data in 'after' field.")
