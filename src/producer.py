"""
Stage 2a - Kafka Producer: send the collected records to a Kafka topic.

Input: data/raw/records.json (from src.api_client)
Each record is serialized to JSON and sent as one message (key = earthquake id).

Run from the project root (Kafka must be running: docker compose up -d):
    python -m src.producer
"""

import json

from confluent_kafka import KafkaException, Producer
from confluent_kafka.admin import AdminClient, NewTopic

from src.api_client import load_records

BOOTSTRAP_SERVERS = "localhost:9092"
TOPIC = "usgs_earthquakes"


def ensure_topic():
    """Check the broker connection and create the topic if it does not exist."""
    admin = AdminClient({"bootstrap.servers": BOOTSTRAP_SERVERS})
    try:
        topics = admin.list_topics(timeout=10).topics
    except KafkaException as err:
        raise RuntimeError(f"Cannot connect to Kafka at {BOOTSTRAP_SERVERS}: {err}")

    if TOPIC not in topics:
        admin.create_topics([NewTopic(TOPIC, num_partitions=1, replication_factor=1)])
        print(f"Created topic '{TOPIC}'")


def publish(records):
    ensure_topic()
    producer = Producer({"bootstrap.servers": BOOTSTRAP_SERVERS, "acks": "all"})
    result = {"published": 0, "failed": 0}

    def on_delivery(err, msg):
        # Called by Kafka for every message: confirms delivery or reports an error
        if err is None:
            result["published"] += 1
        else:
            result["failed"] += 1
            print(f"Delivery failed: {err}")

    for record in records:
        value = json.dumps(record).encode("utf-8")   # serialize: dict -> JSON bytes
        while True:
            try:
                producer.produce(TOPIC, key=record["id"], value=value, on_delivery=on_delivery)
                break
            except BufferError:          # local queue full -> let Kafka send some first
                producer.poll(0.5)
        producer.poll(0)                 # trigger delivery callbacks

    not_sent = producer.flush(timeout=60)   # wait until all messages are delivered
    result["failed"] += not_sent
    return result


def main():
    records = load_records()
    print(f"Records to publish: {len(records)}")

    result = publish(records)
    print(f"Successfully published messages: {result['published']}")
    print(f"Failed messages:                 {result['failed']}")


if __name__ == "__main__":
    main()
