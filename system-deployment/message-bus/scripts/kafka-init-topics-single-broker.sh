#!/bin/bash

echo "----------------------------------------------"
echo "Starting topic creation..."
echo "----------------------------------------------"

# Create topics
topics=(
    "self-awareness-diagnosis"
    "self-awareness-detection"
    "predictive-maintenance"
    "process-drift"
    "production-schedule-update"
    "delivery-delay"
    "production-schema-registration"
    "smart-service-event"
    "modapto-module-creation"
    "modapto-module-deletion"
    "modapto-module-update"
    "smart-service-invoke"
    "smart-service-finish"
    "modapto-mqtt-topics"
)

for topic in "${topics[@]}"; do
    echo "Creating topic: {$topic}..."
    max_attempts=3
    attempt=1

    while [ $attempt -le $max_attempts ]; do
        if kafka-topics --create \
            --topic "$topic" \
            --partitions 6 \
            --replication-factor 1 \
            --if-not-exists \
            --bootstrap-server kafka:29092; then
            echo "Successfully created topic: $topic"
            echo "----------------------------------------------"
            break
        else
            echo "Attempt $attempt failed to create topic: $topic"
            if [ $attempt -eq $max_attempts ]; then
                echo "Failed to create topic after $max_attempts attempts"
                echo "----------------------------------------------"
                exit 1
            fi
            attempt=$((attempt + 1))
            sleep 5
        fi
    done
done

echo "----------------------------------------------"
echo "All topics created successfully!"
echo "----------------------------------------------"