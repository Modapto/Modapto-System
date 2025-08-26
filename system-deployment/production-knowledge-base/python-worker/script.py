import json
import os
import sys
import logging
from kafka import KafkaConsumer, KafkaProducer
from elasticsearch import Elasticsearch, NotFoundError
import base64


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Kafka settings
KAFKA_BROKER = os.getenv("KAFKA_URL", "kafka:9092")
ELASTIC_PASSWORD = os.getenv("ELASTIC_PASSWORD", "###")

TOPICS = [
    "modapto-module-creation",
    "modapto-module-deletion",
    "modapto-module-update",
    "smart-service-assigned",
    "smart-service-unassigned",
    "base64-input-events"
]
TARGET_TOPIC = "aegis-test"

# Elasticsearch settings
ES_HOST = os.getenv("ELASTICSEARCH_URL", "http://elasticsearch:9200")
ES_USERNAME = os.getenv("ELASTIC_USERNAME", "elastic")
ES_PASSWORD = os.getenv("ELASTIC_PASSWORD", "changeme")
ES_INDEX = "modapto-modules"

# Decoded index 
DECODED_INDEX = "decoded-events"

logger.info(f"Connecting to Elasticsearch at: {ES_HOST}")
logger.info(f"Connecting to Kafka at: {KAFKA_BROKER}")
logger.info(f"Listening to topics: {TOPICS}")

# Connect to Elasticsearch
try:
    es = Elasticsearch(
        ES_HOST,
        basic_auth=("elastic", ELASTIC_PASSWORD),
        headers={
            "Accept": "application/vnd.elasticsearch+json; compatible-with=8",
            "Content-Type": "application/vnd.elasticsearch+json; compatible-with=8"
        }
    )
    # Test connection
    es.info()
    logger.info("Elasticsearch connection successful")
except Exception as e:
    logger.error(f"Elasticsearch connection failed: {e}")
    sys.exit(1)

# Kafka consumer & producer
try:
    consumer = KafkaConsumer(
        *TOPICS,
        bootstrap_servers=KAFKA_BROKER,
        auto_offset_reset="earliest",
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        enable_auto_commit=True,
        group_id="modapto-handler"
    )
    
    producer = KafkaProducer(
        bootstrap_servers=KAFKA_BROKER,
        value_serializer=lambda m: json.dumps(m).encode("utf-8")
    )
    logger.info("Kafka connection successful")
except Exception as e:
    logger.error(f"Kafka connection failed: {e}")
    sys.exit(1)


def find_document_by_module_id(module_id, index_name=ES_INDEX):
    """Find Elasticsearch document by moduleId field"""
    try:
        search_query = {
            "query": {
                "term": {
                    "moduleId": module_id
                }
            }
        }
        
        search_response = es.search(index=index_name, body=search_query)
        hits = search_response.get("hits", {}).get("hits", [])
        
        if not hits:
            logger.warning(f"No document found with moduleId '{module_id}' in index '{index_name}'")
            return None, None
        
        if len(hits) > 1:
            logger.warning(f"Multiple documents found with moduleId '{module_id}'. Using the first one.")
        
        # Return document ID and source
        doc_hit = hits[0]
        doc_id = doc_hit["_id"]
        doc_source = doc_hit["_source"]
        
        logger.debug(f"Found document with ID '{doc_id}' for moduleId '{module_id}'")
        return doc_id, doc_source
        
    except Exception as e:
        logger.error(f"Error searching for moduleId '{module_id}': {e}")
        return None, None


def create_index_if_missing(index_name):
    """Create Elasticsearch index if it doesn't exist"""
    try:
        if not es.indices.exists(index=index_name):
            logger.info(f"Index '{index_name}' not found. Creating index...")
            es.indices.create(index=index_name)
            logger.info(f"Index '{index_name}' created successfully")
        else:
            logger.debug(f"Index '{index_name}' already exists")
    except Exception as e:
        logger.error(f"Failed to create index '{index_name}': {e}")
        raise


def update_smart_services(module_id, service_data, assign=True, event=None, msg=None):
    """Update smart services for a module by searching for moduleId field"""
    try:
        doc_id, doc_source = find_document_by_module_id(module_id)
        
        if not doc_id or not doc_source:
            logger.error(f"Cannot update smart services: module '{module_id}' not found")
            return
        
        services = doc_source.get("smartServices") or []

        if assign:
            if not any(s.get("serviceId") == service_data["serviceId"] for s in services):
                services.append(service_data)
                logger.info(f"Assigned smart service '{service_data['serviceId']}' to module '{module_id}'")
            else:
                logger.warning(f"Service '{service_data['serviceId']}' already assigned to module '{module_id}'")
        else:
            original_count = len(services)
            services = [s for s in services if s.get("serviceId") != service_data["serviceId"]]
            if len(services) < original_count:
                logger.info(f"Unassigned smart service '{service_data['serviceId']}' from module '{module_id}'")
            else:
                logger.warning(f"Service '{service_data['serviceId']}' was not assigned to module '{module_id}'")

        # Update using the actual document ID
        es.update(index=ES_INDEX, id=doc_id, body={
            "doc": {
                "timestamp_elastic": msg.timestamp,
                "timestamp_dt": event.get("timestamp"),
                "smartServices": services
            }
        })
        
    except Exception as e:
        logger.error(f"Failed to update smart services for module '{module_id}': {e}")


def decode_base64_event(event):
    """Decode base64 encoded events and store in Elasticsearch"""
    try:
        event_id = event.get("id")
        timestamp = event.get("timestamp")
        encoded_data = event.get("encoded")

        if not encoded_data:
            logger.warning("No 'encoded' field found in base64 event")
            return

        if not event_id:
            logger.warning("No 'id' field found in base64 event")
            return

        # Create index if missing
        create_index_if_missing(DECODED_INDEX)

        # Decode base64 data
        decoded_bytes = base64.b64decode(encoded_data)
        decoded_string = decoded_bytes.decode("utf-8")

        doc = {
            "id": event_id,
            "timestamp": timestamp,
            "decoded": decoded_string,
            "original_encoded": encoded_data[:100] + "..." if len(encoded_data) > 100 else encoded_data
        }

        es.index(index=DECODED_INDEX, id=event_id, document=doc)
        logger.info(f"Decoded and stored event '{event_id}' in index '{DECODED_INDEX}'")
        logger.debug(f"Decoded content preview: {decoded_string[:200]}..." if len(decoded_string) > 200 else decoded_string)

    except Exception as e:
        logger.error(f"Failed to decode base64 event: {e}")
        logger.debug(f"Event data: {json.dumps(event, indent=2)}")


def handle_module_creation(event, msg):
    """Handle module creation events"""
    logger.info("Handling module creation...")
    results = event.get("results", {})
    module_id = results.get("id")
    
    if not module_id:
        logger.error("No module ID found in creation event")
        return
    
    create_index_if_missing(ES_INDEX)
    doc = {
        "name": results.get("name"),
        "moduleId": module_id,
        "endpoint": results.get("endpoint"),
        "timestamp_elastic": msg.timestamp,
        "timestamp_dt": event.get("timestamp"),
        "smartServices": []
    }
    
    # Use a generated document ID instead of module_id
    es.index(index=ES_INDEX, document=doc)
    logger.info(f"Inserted module document with moduleId '{module_id}' into '{ES_INDEX}'")
    
    # Send to target topic
    producer.send(TARGET_TOPIC, value=doc)
    logger.debug(f"Sent module creation event to topic '{TARGET_TOPIC}'")


def handle_module_update(event, msg):
    """Handle module update events"""
    logger.info("Handling module update...")
    results = event.get("results", {})
    module_id = event.get("module")
    
    if not module_id:
        logger.error("No module ID found in update event")
        return
    
    try:
        doc_id, doc_source = find_document_by_module_id(module_id)
        
        if not doc_id:
            logger.warning(f"No document found with moduleId '{module_id}' for update. Creating new document.")
            # Create new document if not found
            doc = {
                "name": results.get("name"),
                "moduleId": module_id,
                "endpoint": results.get("endpoint"),
                "timestamp_dt": event.get("timestamp"),
                "timestamp_elastic": msg.timestamp,
                "smartServices": []
            }
            es.index(index=ES_INDEX, document=doc)
            logger.info(f"Created new module document with moduleId '{module_id}' in '{ES_INDEX}'")
            return
        
        update_doc = {
            "doc": {
                "name": results.get("name"),
                "endpoint": results.get("endpoint"),
                "timestamp_dt": event.get("timestamp"),
                "timestamp_elastic": msg.timestamp
            }
        }
        
        es.update(index=ES_INDEX, id=doc_id, body=update_doc)
        logger.info(f"Updated module document with moduleId '{module_id}' in '{ES_INDEX}'")
        
    except Exception as e:
        logger.error(f"Failed to update module '{module_id}': {e}")


def handle_module_deletion(event):
    """Handle module deletion events"""
    logger.info("Handling module deletion...")
    module_id = event.get("module")
    
    if not module_id:
        logger.error("No module ID found in deletion event")
        return
    
    try:
        # Search for all documents with matching moduleId field
        search_query = {
            "query": {
                "term": {
                    "moduleId": module_id
                }
            }
        }
        
        search_response = es.search(index=ES_INDEX, body=search_query)
        hits = search_response.get("hits", {}).get("hits", [])
        
        if not hits:
            logger.warning(f"No document found with moduleId '{module_id}' for deletion")
            return
        
        # Delete all matching documents
        deleted_count = 0
        for hit in hits:
            doc_id = hit["_id"]
            es.delete(index=ES_INDEX, id=doc_id)
            deleted_count += 1
            logger.debug(f"Deleted document with ID '{doc_id}' for moduleId '{module_id}'")
        
        logger.info(f"Deleted {deleted_count} document(s) with moduleId '{module_id}' from '{ES_INDEX}'")
        
    except Exception as e:
        logger.error(f"Failed to delete module '{module_id}': {e}")


def handle_smart_service_event(event, topic, msg):
    """Handle smart service assignment/unassignment events"""
    results = event.get("results", {})
    module_id = event.get("module")
    assign = topic == "smart-service-assigned"
    
    if not module_id:
        logger.error(f"No module ID found in {topic} event")
        return
    
    service_data = {
        "name": results.get("name"),
        "catalogueId": results.get("serviceCatalogId"),
        "serviceId": results.get("id"),
        "endpoint": results.get("endpoint")
    }
    
    logger.info(f"Handling smart service {'assignment' if assign else 'unassignment'} for module '{module_id}'")
    update_smart_services(module_id, service_data, assign=assign, event=event, msg=msg)


def main():
    """Main event processing loop"""
    logger.info("Kafka Consumer started successfully")
    logger.info("Waiting for messages...")
    
    try:
        message_count = 0
        for msg in consumer:
            message_count += 1
            topic = msg.topic
            event = msg.value
            
            logger.info(f"Received message #{message_count} from topic: '{topic}'")
            logger.debug(f"Raw event: {json.dumps(event, indent=2)}")

            try:
                # Route messages based on topic
                if topic == "modapto-module-creation":
                    handle_module_creation(event, msg)
                    
                elif topic == "modapto-module-update":
                    handle_module_update(event, msg)
                    
                elif topic == "modapto-module-deletion":
                    handle_module_deletion(event)
                    
                elif topic in ["smart-service-assigned", "smart-service-unassigned"]:
                    handle_smart_service_event(event, topic, msg)
                    
                elif topic == "base64-input-events":
                    logger.info("Handling base64 encoded input...")
                    decode_base64_event(event)
                    
                else:
                    logger.warning(f"Unknown topic received: '{topic}'")
                    
                logger.info(f"Successfully processed message from '{topic}'")
                
            except Exception as e:
                logger.error(f"Error processing message from '{topic}': {e}")
                logger.debug(f"Failed event data: {json.dumps(event, indent=2)}")
                continue

    except KeyboardInterrupt:
        logger.info("Received shutdown signal, stopping gracefully...")
    except Exception as e:
        logger.error(f"Fatal error in main loop: {e}")
        raise
    finally:
        logger.info("Closing Kafka consumer and producer...")
        try:
            consumer.close()
            producer.close()
        except Exception as e:
            logger.error(f"Error closing Kafka connections: {e}")
        logger.info("Application shutdown complete")


if __name__ == "__main__":
    main()