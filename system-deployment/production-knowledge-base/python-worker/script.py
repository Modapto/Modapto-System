import json
import os
import sys
import logging
import base64
import threading
import signal
import time
from typing import Literal, Optional
from datetime import datetime
import re
import uuid

try:
    from kafka import KafkaConsumer, KafkaProducer
except Exception:
    KafkaConsumer = None
    KafkaProducer = None

# --- Elasticsearch ---
from elasticsearch import Elasticsearch, NotFoundError

# --- HTTP API ---
from fastapi import FastAPI, HTTPException, Query, UploadFile, File, Path

from fastapi import Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, conint, confloat

from json import JSONDecodeError

# ---------------------------------
# Logging
# ---------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("modapto-worker")

# ---------------------------------
# Config / Env
# ---------------------------------
RUN_MODE = os.getenv("RUN_MODE", "both").lower()  # 'api' | 'kafka' | 'both'
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "*")

GROUPING_TOPIC = "grouping-predictive-maintenance"
GROUPING_INDEX = "sew-grouping-predictive-maintenance-results"

THRESHOLD_TOPIC = "threshold-predictive-maintenance"
THRESHOLD_INDEX = "sew-threshold-predictive-maintenance-results"

MQTT_TOPIC = "modapto-mqtt-topics"
# to key tou einai to previous topic

PROD_OPT_TOPIC = "production-schedule-optimization"
PROD_OPT_INDEX = "optimization-sew"

CRF_SA_TOPIC = "self-awareness-wear-detection"
# CRF_SA_INDEX = "kitholder-event-results-crf"
CRF_SA_INDEX ="crf-kit-holder-notifications"

SA1_KPIS_TOPIC = "self-awareness-monitor-kpis"
SA1_KPIS_INDEX = "sew-self-awareness-monitoring-kpis"

SA2_MONITORING_TOPIC = "self-awareness-real-time-monitoring"
SA2_MONITORING_INDEX = "sew-self-awareness-real-time-monitoring-results"

CRF_OPT_TOPIC = "kh-picking-sequence-optimization"
CRF_OPT_INDEX = "optimization-crf"

CRF_SIM_TOPIC = "kh-picking-sequence-simulation"
CRF_SIM_INDEX = "simulation-crf"

PROD_SIM_TOPIC = "production-schedule-simulation"
PROD_SIM_INDEX = "simulation-sew"

OPT_FFT_CONFIG_INDEX = "optimization-config-fft"

ROBOT_CONFIG_FFT_INDEX = "robot-config-fft"


TOPICS_ALLOWING_NULL_RESULTS = {"modapto-module-deletion"}


# Kafka
KAFKA_BROKER = os.getenv("KAFKA_URL", "kafka:9092")
TOPICS = [
    "modapto-module-creation",
    "modapto-module-deletion",
    "modapto-module-update",
    "smart-service-assigned",
    "smart-service-unassigned",
    "base64-input-events",
    GROUPING_TOPIC,
    THRESHOLD_TOPIC,
    PROD_OPT_TOPIC,
    PROD_SIM_TOPIC,
    CRF_SA_TOPIC,
    SA1_KPIS_TOPIC,
    SA2_MONITORING_TOPIC,
    MQTT_TOPIC,
]
TARGET_TOPIC = "aegis-test"

# MAPPINGS

TIMEWINDOW_MAPPING = {
    "properties": {
        "begin": {"type": "date"},  
        "end":   {"type": "date"},
    }
}

# Indices for P3 Opt and Sim
OPT_CONFIG_INDEX = "kitting-configs-opt"
SIM_CONFIG_INDEX = "kitting-configs-sim"

# ---------------------------------
# Mappings 
# ---------------------------------
PROCESS_DRIFT_MAPPINGS = {
    "properties": {
        "moduleId": {"type": "keyword"},  
        "module": {"type": "keyword"},    
        "component": {"type": "keyword"},


        "stage": {"type": "keyword"},
        "cell": {"type": "keyword"},
        "failureType": {"type": "keyword"},
        "failureDescription": {"type": "text"},
        "maintenanceAction": {"type": "text"},
        "componentReplacement": {"type": "keyword"},
        "workerName": {"type": "keyword"},
        "driftDone": {"type": "boolean"},


        "timestamp": {"type": "date"},               # event timestamp UI
        "timestamp_api_received": {"type": "date"},  # server-side
        "starttime": {"type": "date"},               # moment START declared
        "endtime": {"type": "date"},                 # moment DONE toggled


        "source": {"type": "keyword"}  # 'eds'
    }
}

PROD_OPT_RESULT_MAPPINGS = {
    "properties": {
        "timestamp":  {"type": "keyword"},
        "moduleId":   {"type": "keyword"},
        "data":       {"type": "object", "dynamic": True},
        "smartServiceId": {"type": "keyword"},
        "sourceRaw":  {"type": "object", "dynamic": True},
    }
}


CONFIG_MAPPINGS = {
    "properties": {
        "filename":   {"type": "keyword"},
        "uploadedAt": {"type": "date"},
        "rawText":    {"type": "text"},      # JSON string 
        "config":     {"type": "object"},    # parsed JSON 
        "case":       {"type": "keyword"},   # 'opt' or 'sim'
        "etag":       {"type": "keyword"}    # hash for idempotency 
    }
}

CRF_SA_MAPPINGS = {
    "properties": {
        "moduleId":       {"type": "keyword"},
        "eventType":      {"type": "keyword"},   
        "rfidStation":    {"type": "integer"},
        "khType":         {"type": "integer"},
        "khId":           {"type": "integer"},
        "timestamp":      {"type": "date"},      
    }
}


SA1_KPIS_MAPPINGS = {
    "properties": {
        "smartServiceId": {"type": "keyword"},
        "moduleId": {"type": "keyword"},
        "timestamp": {"type": "date"},         
        "stage": {"type": "keyword"},
        "cell": {"type": "keyword"},
        "plc": {"type": "keyword"},
        "module": {"type": "keyword"},
        "subElement": {"type": "keyword"},
        "component": {"type": "keyword"},
        "variable": {"type": "keyword"},
        "variableType": {"type": "keyword"},
        "startingDate": {"type": "keyword"},    
        "endingDate": {"type": "keyword"},     
        "dataSource": {"type": "keyword"},
        "bucket": {"type": "keyword"},
        "data": {"type": "float"}              
    }
}


SA2_MONITORING_MAPPINGS = {
    "properties": {
        "timestamp": {"type": "date"},
        "moduleId": {"type": "keyword"},
        "module": {"type": "keyword"},
        "component": {"type": "keyword"},
        "property": {"type": "keyword"},
        "value": {"type": "keyword"},             # string, όπως στο index model
        "lowThreshold": {"type": "double"},
        "highThreshold": {"type": "double"},
        "deviationPercentage": {"type": "double"},
    }
}


PROD_OPT_RESULT_MAPPINGS = {
    "properties": {
        "timestamp":  {"type": "keyword"},   # string timestamps, όπως στο schema
        "moduleId":   {"type": "keyword"},
        "data":       {"type": "object", "dynamic": True},
        "smartServiceId": {"type": "keyword"},
        "sourceRaw":  {"type": "object", "dynamic": True},
    }
}

MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10 MB

GROUPING_RESULT_MAPPINGS = {
    "properties": {
        "moduleId":       {"type": "keyword"},
        "smartServiceId": {"type": "keyword"},
        "costSavings":    {"type": "double"},
        "timeWindow":     TIMEWINDOW_MAPPING,
        "groupingMaintenance":   {"type": "object", "dynamic": True},
        "individualMaintenance": {"type": "object", "dynamic": True},
        "timestamp":      {"type": "date"},
    }
}


# --- CRF OPT / SIM mappings ---
CRF_OPT_RESULT_MAPPINGS = {
    "properties": {
        "timestamp": {"type": "keyword"},
        "message": {"type": "text"},
        "moduleId": {"type": "keyword"},
        "optimization_results": {"type": "object", "dynamic": True},
        "optimization_run": {"type": "boolean"},
        "solutionTime": {"type": "long"},
        "totalTime": {"type": "long"},
    }
}

CRF_SIM_RESULT_MAPPINGS = {
    "properties": {
        "timestamp": {"type": "keyword"},
        "message": {"type": "text"},
        "moduleId": {"type": "keyword"},
        "simulation_run": {"type": "boolean"},
        "solutionTime": {"type": "long"},
        "totalTime": {"type": "long"},
        "baseline": {"type": "object", "dynamic": True},
        "best_phase": {"type": "object", "dynamic": True},
    }
}


THRESHOLD_RESULT_MAPPINGS = {
    "properties": {
        "moduleId":       {"type": "keyword"},
        "smartServiceId": {"type": "keyword"},
        "recommendation": {"type": "text", "analyzer": "standard"},
        "details":        {"type": "text", "analyzer": "standard"},
        "timestamp":      {"type": "date"},
    }
}



# Elasticsearch
ES_HOST = os.getenv("ELASTICSEARCH_URL", "http://elasticsearch:9200")
ES_USERNAME = os.getenv("ELASTIC_USERNAME", "elastic")
ES_PASSWORD = os.getenv("ELASTIC_PASSWORD", "changeme")

# Indexes
ES_INDEX = "modapto-modules"
DECODED_INDEX = "decoded-events"
PROCESS_DRIFT_INDEX = "process_drift"  

logger.info(f"Elasticsearch: {ES_HOST}")
logger.info(f"Kafka broker: {KAFKA_BROKER}")
logger.info(f"Kafka topics: {TOPICS}")
logger.info(f"RUN_MODE={RUN_MODE}")

# ---------------------------------
# Elasticsearch client
# ---------------------------------
try:
    es = Elasticsearch(
        ES_HOST,
        basic_auth=(ES_USERNAME, ES_PASSWORD),
        headers={
            "Accept": "application/vnd.elasticsearch+json; compatible-with=8",
            "Content-Type": "application/vnd.elasticsearch+json; compatible-with=8",
        },
    )
    es.info()
    logger.info("Elasticsearch connection successful")
except Exception as e:
    logger.error(f"Elasticsearch connection failed: {e}")
    sys.exit(1)

# ---------------------------------
# Kafka init 
# ---------------------------------
consumer = None
producer = None
kafka_ready = False
stop_event = threading.Event()

def init_kafka():
    global consumer, producer, kafka_ready
    if KafkaConsumer is None or KafkaProducer is None:
        logger.error("kafka-python is not installed. Install it to use Kafka mode.")
        raise RuntimeError("Kafka not available")

    try:
        consumer = KafkaConsumer(
            *TOPICS,
            bootstrap_servers=KAFKA_BROKER,
            auto_offset_reset="earliest",
            # value_deserializer=lambda m: json.loads(m.decode("utf-8")),
            value_deserializer=_safe_json_deserializer,
            key_deserializer=lambda k: k.decode("utf-8") if k is not None else None,
            enable_auto_commit=True,
            group_id="modapto-handler",
        )
        producer = KafkaProducer(
            bootstrap_servers=KAFKA_BROKER,
            value_serializer=lambda m: json.dumps(m).encode("utf-8"),
        )
        kafka_ready = True
        logger.info("Kafka connection successful")
    except Exception as e:
        kafka_ready = False
        logger.error(f"Kafka connection failed: {e}")
        raise

# ---------------------------------
# ES helpers
# ---------------------------------
def create_index_if_missing(index_name, mappings=None, settings=None):
    try:
        if not es.indices.exists(index=index_name):
            logger.info(f"Index '{index_name}' not found. Creating...")
            body = {}
            if settings:
                body["settings"] = settings
            if mappings:
                body["mappings"] = {"properties": mappings["properties"]} if "properties" in mappings else mappings
            es.indices.create(index=index_name, body=body or None)
            logger.info(f"Index '{index_name}' created.")
    except Exception as e:
        logger.error(f"Failed to create index '{index_name}': {e}")
        raise

def find_document_by_module_id(module_id, index_name=ES_INDEX):
    try:
        search_query = {"query": {"term": {"moduleId": module_id}}}
        search_response = es.search(index=index_name, body=search_query)
        hits = search_response.get("hits", {}).get("hits", [])
        if not hits:
            logger.warning(f"No doc with moduleId '{module_id}' in '{index_name}'")
            return None, None
        if len(hits) > 1:
            logger.warning(f"Multiple docs for moduleId '{module_id}'. Using first.")
        hit = hits[0]
        return hit["_id"], hit["_source"]
    except Exception as e:
        logger.error(f"Error searching moduleId '{module_id}': {e}")
        return None, None


# Generic Handlers 

def _safe_json_deserializer(m: bytes):
    if not m:  
        return None
    try:
        v = json.loads(m.decode("utf-8"))
    except JSONDecodeError:
        return None
    return v  

def _is_blank(obj) -> bool:
    # None -> blank
    if obj is None:
        return True
    # empty containers -> blank
    if isinstance(obj, (list, tuple, set, dict)) and len(obj) == 0:
        return True
    # dict
    if isinstance(obj, dict):
        for v in obj.values():
            if not _is_blank(v):
                return False
        return True
    return False


def _to_camel_key(s: str) -> str:

    if not isinstance(s, str):
        return s

    # First split on spaces and underscores
    tokens = re.split(r'[\s_]+', s.strip())

    # Then split each token on capital letters
    expanded_tokens = []
    for token in tokens:
        if token:
            # Split on capital letters
            parts = re.findall(r'[A-Z]?[a-z]+|[A-Z]+(?=[A-Z][a-z]|\b)', token)
            if parts:
                expanded_tokens.extend(parts)
            else:
                expanded_tokens.append(token)

    if not expanded_tokens:
        return s.lower()

    head = expanded_tokens[0].lower()
    tail = [t.capitalize() for t in expanded_tokens[1:]]
    return head + "".join(tail)

def _normalize_keys(obj):
   
   
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            nk = _to_camel_key(k)
            out[nk] = _normalize_keys(v)
        return out
    elif isinstance(obj, list):
        return [_normalize_keys(x) for x in obj]
    else:
        return obj


def _normalize_sa1_item(item: dict) -> dict:
   
    if not isinstance(item, dict):
        return {}

    norm = _normalize_keys(item)

    if "dataList" in norm:
        norm["data"] = norm.pop("dataList")

    if "plc" in norm and not isinstance(norm["plc"], str):
        norm["plc"] = str(norm["plc"])

    norm["timestamp"] = _iso_or_none(norm.get("timestamp"))

    return norm


def _normalize_sa2_item(item: dict) -> dict:
    if not isinstance(item, dict):
        return {}
    n = _normalize_keys(item)

    n["timestamp"] = _iso_or_none(n.get("timestamp"))

    if "value" in n and not isinstance(n["value"], str):
        n["value"] = str(n["value"])

    for k in ("lowThreshold", "highThreshold", "deviationPercentage"):
        if k in n and n[k] is not None:
            try:
                n[k] = float(n[k])
            except Exception:
                n[k] = None
    return n


def _iso_or_none(ts):

    return ts if ts else None


def _extract_robot_config(src: dict) -> dict:

    if not isinstance(src, dict):
        return {}

    rc = src.get("robotConfiguration")
    if isinstance(rc, dict) and rc:
        return rc

    cfg = src.get("config")
    if isinstance(cfg, dict):
        rc2 = cfg.get("robotConfiguration")
        if isinstance(rc2, dict) and rc2:
            return rc2

        if "robot" in cfg or "module_name" in cfg:
            return {
                "module_name": cfg.get("module_name"),
                "robot": cfg.get("robot") or cfg,
            }

    raw = src.get("rawText")
    if isinstance(raw, str) and raw.strip():
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, dict):
                if "robotConfiguration" in parsed and isinstance(parsed["robotConfiguration"], dict):
                    return parsed["robotConfiguration"]
                if "robot" in parsed or "module_name" in parsed:
                    return {
                        "module_name": parsed.get("module_name"),
                        "robot": parsed.get("robot") or parsed,
                    }
        except Exception:
            pass

    if "robot" in src or "module_name" in src:
        return {
            "module_name": src.get("module_name"),
            "robot": src.get("robot") or src,
        }

    return {}


def update_smart_services(module_id, service_data, assign=True, event=None, msg=None):
    try:
        doc_id, doc_source = find_document_by_module_id(module_id)
        if not doc_id or not doc_source:
            logger.error(f"Cannot update smart services: module '{module_id}' not found")
            return

        services = doc_source.get("smartServices") or []
        if assign:
            if not any(s.get("serviceId") == service_data["serviceId"] for s in services):
                services.append(service_data)
                logger.info(f"Assigned service '{service_data['serviceId']}' to module '{module_id}'")
            else:
                logger.warning(f"Service '{service_data['serviceId']}' already assigned")
        else:
            before = len(services)
            services = [s for s in services if s.get("serviceId") != service_data["serviceId"]]
            if len(services) < before:
                logger.info(f"Unassigned service '{service_data['serviceId']}' from '{module_id}'")
            else:
                logger.warning(f"Service '{service_data['serviceId']}' was not assigned to begin with")

        es.update(
            index=ES_INDEX,
            id=doc_id,
            body={
                "doc": {
                    "timestamp_elastic": getattr(msg, "timestamp", None),
                    "timestamp_dt": event.get("timestamp") if event else None,
                    "smartServices": services,
                }
            },
        )
    except Exception as e:
        logger.error(f"Failed to update smart services for '{module_id}': {e}")

def decode_base64_event(event):
    try:
        event_id = event.get("id")
        timestamp = event.get("timestamp")
        encoded_data = event.get("encoded")
        if not encoded_data or not event_id:
            logger.warning("Missing 'encoded' or 'id' in base64 event")
            return

        create_index_if_missing(DECODED_INDEX)
        decoded = base64.b64decode(encoded_data).decode("utf-8")
        doc = {
            "id": event_id,
            "timestamp": timestamp,
            "decoded": decoded,
            "original_encoded": encoded_data[:100] + "..." if len(encoded_data) > 100 else encoded_data,
        }
        es.index(index=DECODED_INDEX, id=event_id, document=doc)
        logger.info(f"Decoded and stored base64 event '{event_id}'")
    except Exception as e:
        logger.error(f"Failed to decode base64 event: {e}")
        logger.debug(f"Event data: {json.dumps(event, indent=2)}")

def handle_module_creation(event, msg):
    logger.info("Handling module creation...")
    results = event.get("results", {})
    module_id = results.get("id")
    if not module_id:
        logger.error("No module ID in creation event")
        return

    create_index_if_missing(ES_INDEX)

    if module_exists(ES_INDEX, module_id):
        logger.info(f"[SKIP] Module '{module_id}' already exists in '{ES_INDEX}'")
        return

    doc = {
        "name": results.get("name"),
        "moduleId": module_id,
        "endpoint": results.get("endpoint"),
        "timestamp_elastic": getattr(msg, "timestamp", None),
        "timestamp_dt": event.get("timestamp"),
        "metadata": {},
        "smartServices": [],
    }
    es.index(index=ES_INDEX, document=doc,refresh="wait_for")
    logger.info(f"Inserted module document (moduleId='{module_id}') into '{ES_INDEX}'")

    if producer:
        producer.send(TARGET_TOPIC, value=doc)
        logger.debug(f"Sent module creation to topic '{TARGET_TOPIC}'")

def handle_module_update(event, msg):
    logger.info("Handling module update...")
    results = event.get("results", {})
    module_id = event.get("module")
    if not module_id:
        logger.error("No module ID in update event")
        return

    try:
        doc_id, _ = find_document_by_module_id(module_id)
        if not doc_id:
            logger.warning(f"No doc for moduleId '{module_id}'. Creating new.")
            doc = {
                "name": results.get("name"),
                "moduleId": module_id,
                "endpoint": results.get("endpoint"),
                "timestamp_dt": event.get("timestamp"),
                "timestamp_elastic": getattr(msg, "timestamp", None),
                "metadata": {},
                "smartServices": [],
            }
            es.index(index=ES_INDEX, document=doc)
            logger.info(f"Created new module document for '{module_id}'")
            return

        update_doc = {
            "doc": {
                "name": results.get("name"),
                "endpoint": results.get("endpoint"),
                "timestamp_dt": event.get("timestamp"),
                "timestamp_elastic": getattr(msg, "timestamp", None),
            }
        }
        es.update(index=ES_INDEX, id=doc_id, body=update_doc)
        logger.info(f"Updated module document for '{module_id}'")
    except Exception as e:
        logger.error(f"Failed to update module '{module_id}': {e}")

def handle_module_deletion(event):
    logger.info("Handling module deletion...")
    module_id = event.get("module")
    if not module_id:
        logger.error("No module ID in deletion event")
        return

    try:
        search_query = {"query": {"term": {"moduleId": module_id}}}
        resp = es.search(index=ES_INDEX, body=search_query)
        hits = resp.get("hits", {}).get("hits", [])
        if not hits:
            logger.warning(f"No documents with moduleId '{module_id}' for deletion")
            return
        deleted = 0
        for hit in hits:
            es.delete(index=ES_INDEX, id=hit["_id"])
            deleted += 1
        logger.info(f"Deleted {deleted} document(s) for moduleId '{module_id}'")
    except Exception as e:
        logger.error(f"Failed to delete module '{module_id}': {e}")

def module_exists(index_name: str, module_id: str) -> bool:
    try:
        resp = es.search(
            index=index_name,
            body={
                "query": {"term": {"moduleId": module_id}},
                "size": 1,
                "_source": False
            },
        )
        hits = resp.get("hits", {}).get("hits", [])
        return len(hits) > 0
    except Exception as e:
        logger.error(f"Exists-check failed for moduleId='{module_id}': {e}")
        return False


def handle_smart_service_event(event, topic, msg):
    results = event.get("results", {})
    module_id = event.get("module")
    assign = topic == "smart-service-assigned"
    if not module_id:
        logger.error(f"No module ID in {topic} event")
        return

    service_data = {
        "name": results.get("name"),
        "catalogueId": results.get("serviceCatalogId"),
        "serviceId": results.get("id"),
        "endpoint": results.get("endpoint"),
    }
    logger.info(f"Handling smart service {'assignment' if assign else 'unassignment'} for '{module_id}'")
    update_smart_services(module_id, service_data, assign=assign, event=event, msg=msg)

def handle_grouping_predictive_maintenance(event):

    try:
        create_index_if_missing(GROUPING_INDEX, mappings=GROUPING_RESULT_MAPPINGS)

        module_id = event.get("module") or event.get("moduleId")
        smart_service_id = event.get("smartService") or event.get("smartServiceId")
        evt_ts = _iso_or_none(event.get("timestamp"))

        raw_results = event.get("results") or {}
        nres = _normalize_keys(raw_results)

        cost_savings = nres.get("costSavings")
        grouping_maint = nres.get("groupingMaintenance")
        individual_maint = nres.get("individualMaintenance")

        tw = nres.get("timeWindow") or {}
        time_window = {
            "begin": _iso_or_none(tw.get("begin")),
            "end": _iso_or_none(tw.get("end")),
        } if tw else None

        doc = {
            "moduleId":             module_id,
            "smartServiceId":       smart_service_id,
            "costSavings":          cost_savings,
            "timeWindow":           time_window,
            "groupingMaintenance":  grouping_maint,
            "individualMaintenance": individual_maint,
            "timestamp":            evt_ts,

            "sourceRaw": {
                "description": event.get("description"),
                "priority": event.get("priority"),
                "eventType": event.get("eventType"),
                "sourceComponent": event.get("sourceComponent"),
                "topic": event.get("topic"),
            }
        }

        logger.info(f"[KAFKA-INP][GROUPING] module={module_id} smartService={smart_service_id} ts={evt_ts}")
        logger.info(f"[KAFKA-INP][GROUPING] {event}")

        es.index(index=GROUPING_INDEX, document=doc, refresh="wait_for")
        logger.info(f"[ES] Indexed grouping PM result (moduleId={module_id}) into {GROUPING_INDEX}")
    except Exception as e:
        logger.error(f"Failed to index grouping PM result: {e}")
        logger.debug(f"Payload: {json.dumps(event, indent=2)}")



def handle_production_schedule_simulation(event):
    """
    Store simulation results for SEW production schedule into simulation-sew
    """
    try:
        create_index_if_missing(PROD_SIM_INDEX)

        payload = event.get("results") or event or {}

        module_id = payload.get("moduleId") or event.get("module") or event.get("moduleId")
        smart_service_id = payload.get("smartServiceId") or event.get("smartService") or event.get("smartServiceId")
        ts = payload.get("timestamp") or event.get("timestamp")
        data = payload.get("data") or {}

        doc = {
            "moduleId":       module_id,
            "smartServiceId": smart_service_id,
            "timestamp":      ts,
            "data":           data
        }

        logger.info(f"[KAFKA-INP][SEW-SIM] module={module_id} ts={ts}, doc {doc}")
        es.index(index=PROD_SIM_INDEX, document=doc, refresh="wait_for")
        logger.info(f"[ES] Indexed SEW simulation result into '{PROD_SIM_INDEX}'")
    except Exception as e:
        logger.error(f"Failed to index SEW simulation result: {e}")
        logger.debug(f"Payload: {json.dumps(event, indent=2)}")




def handle_production_schedule_optimization(event):
   
   
    try:
        create_index_if_missing(PROD_OPT_INDEX, mappings=PROD_OPT_RESULT_MAPPINGS)

        payload = event.get("results") or event or {}

        module_id = payload.get("moduleId") or event.get("module") or event.get("moduleId")
        smart_service_id = payload.get("smartServiceId") or event.get("smartService") or event.get("smartServiceId")
        ts = payload.get("timestamp") or event.get("timestamp")
        data = payload.get("data") or {}   # solutions map


        doc = {
            "moduleId":       module_id,
            "smartServiceId": smart_service_id,
            "timestamp":      ts,
            "data":           data,
            "sourceRaw": {
                "description": event.get("description"),
                "priority": event.get("priority"),
                "eventType": event.get("eventType"),
                "sourceComponent": event.get("sourceComponent"),
                "topic": "production-schedule-optimization",
            }
        }

        logger.info(f"[KAFKA-INP][SEW-OPT] module={module_id} ts={ts}")
        es.index(index=PROD_OPT_INDEX, document=doc, refresh="wait_for")
        logger.info(f"[ES] Indexed SEW optimization result into '{PROD_OPT_INDEX}'")
    except Exception as e:
        logger.error(f"Failed to index SEW optimization result: {e}")
        logger.debug(f"Payload: {json.dumps(event, indent=2)}")

def handle_threshold_predictive_maintenance(event):   
    try:
        create_index_if_missing(THRESHOLD_INDEX, mappings=THRESHOLD_RESULT_MAPPINGS)

        results = event.get("results") or {}
        module_id = results.get("moduleId") or event.get("module")
        smart_service_id = results.get("smartServiceId") or event.get("smartService")
        rec = results.get("recommendation")
        details = results.get("details")
        ts = _iso_or_none(results.get("timestamp") or event.get("timestamp"))

       
        doc = {
            "moduleId":         module_id,
            "smartServiceId":   smart_service_id,
            "recommendation":   rec,
            "details":          details,
            "timestamp":        ts,
            "sourceRaw": {
                "description": event.get("description"),
                "priority": event.get("priority"),
                "eventType": event.get("eventType"),
                "sourceComponent": event.get("sourceComponent"),
                "topic": event.get("topic"),
            }
        }

        logger.info(f"[KAFKA-INP][THRESHOLD] module={module_id} smartService={smart_service_id} ts={ts}")
        logger.info(f"[KAFKA-INP][THRESHOLD] {event}")

        es.index(index=THRESHOLD_INDEX, document=doc, refresh="wait_for")
        logger.info(f"[ES] Indexed threshold PM result (moduleId={module_id}) into {THRESHOLD_INDEX}")
    except Exception as e:
        logger.error(f"Failed to index threshold PM result: {e}")
        logger.debug(f"Payload: {json.dumps(event, indent=2)}")

def handle_crf_sa_wear_detection_event(event):

    try:
        create_index_if_missing(CRF_SA_INDEX, mappings=CRF_SA_MAPPINGS)

        results = event.get("results") or {}

        ts = results.get("timestamp") or event.get("timestamp")
        ts = _iso_or_none(ts)

        doc = {
            "moduleId":        event.get("module"),
            "eventType":       event.get("eventType"),            
            "rfidStation":     results.get("rfidStation"),
            "khType":          results.get("khType"),
            "khId":            results.get("khId"),
            "timestamp":       ts
        }

        logger.info(f"[KAFKA-INP][WEAR] module={doc.get('moduleId')} ts={ts} doc={doc}")
        logger.debug(f"[KAFKA-INP][WEAR] payload: {json.dumps(event, indent=2)}")

        es.index(index=CRF_SA_INDEX, document=doc, refresh="wait_for")
        logger.info(f"[ES] Indexed wear detection event into '{CRF_SA_INDEX}'")
    except Exception as e:
        logger.error(f"Failed to index wear detection event: {e}")
        logger.debug(f"Payload: {json.dumps(event, indent=2)}")

def handle_sa1_kpis_event(event):

    try:
        create_index_if_missing(SA1_KPIS_INDEX, mappings=SA1_KPIS_MAPPINGS)

        # Extract top-level fields
        top_level_module = event.get("module")
        top_level_smart_service = event.get("smartService")
        top_level_timestamp = event.get("timestamp")

        records = []
        if isinstance(event, dict):
            if isinstance(event.get("data"), list):
                records = event["data"]
            elif isinstance(event.get("results"), list):
                records = event["results"]
            elif isinstance(event.get("results"), dict):
                records = [event["results"]]
            else:
                records = [event]
        else:
            logger.warning("[SA1-KPIS] Unsupported event format")
            return

        indexed = 0
        for rec in records:
            nr = _normalize_sa1_item(rec)

            doc = {
                "smartServiceId": top_level_smart_service,
                "moduleId": top_level_module,
                "timestamp":top_level_timestamp,
                "stage": nr.get("stage"),
                "cell": nr.get("cell"),
                "plc": nr.get("plc"),
                "module": nr.get("module"),
                "subElement": nr.get("subElement"),
                "component": nr.get("component"),
                "variable": nr.get("variable"),
                "variableType": nr.get("variableType"),
                "startingDate": nr.get("startingDate"),
                "endingDate": nr.get("endingDate"),
                "dataSource": nr.get("dataSource"),
                "bucket": nr.get("bucket"),
                "data": nr.get("data"),
            }

            es.index(index=SA1_KPIS_INDEX, document=doc, refresh="wait_for")
            indexed += 1

        logger.info(f"[ES] Indexed {indexed} SA1 KPI record(s) '{doc}' into '{SA1_KPIS_INDEX}'")
    except Exception as e:
        logger.error(f"Failed to index SA1 KPIs: {e}")
        logger.debug(f"Payload: {json.dumps(event, indent=2)}")

def handle_sa2_monitoring_event(event):

    try:
        create_index_if_missing(SA2_MONITORING_INDEX, mappings=SA2_MONITORING_MAPPINGS)

        # Συγκέντρωση records από πιθανά wrappers
        if isinstance(event, dict):
            if isinstance(event.get("results"), list):
                records = event["results"]
            elif isinstance(event.get("data"), list):
                records = event["data"]
            else:
                records = [event]
        else:
            logger.warning("[SA2] Unsupported event format")
            return

        indexed = 0
        for rec in records:
            nr = _normalize_sa2_item(rec)

            doc = {
                "timestamp": nr.get("timestamp"),
                "moduleId": nr.get("moduleId"),
                "module": nr.get("module"),
                "component": nr.get("component"),
                "property": nr.get("property"),
                "value": nr.get("value"),
                "lowThreshold": nr.get("lowThreshold"),
                "highThreshold": nr.get("highThreshold"),
                "deviationPercentage": nr.get("deviationPercentage"),
            }

            es.index(index=SA2_MONITORING_INDEX, document=doc, refresh="wait_for")
            indexed += 1

        logger.info(f"[ES] Indexed {indexed} SA2 monitoring record(s) '{doc}' into '{SA2_MONITORING_INDEX}'")
    except Exception as e:
        logger.error(f"Failed to index SA2 monitoring results: {e}")
        logger.debug(f"Payload: {json.dumps(event, indent=2)}")


def _first_present(*vals):
    for v in vals:
        if v is not None:
            return v
    return None

def handle_crf_picking_sequence_optimization(event):
    
    try:
        create_index_if_missing(CRF_OPT_INDEX, mappings=CRF_OPT_RESULT_MAPPINGS)
        payload = event.get("results") if isinstance(event, dict) and isinstance(event.get("results"), dict) else event

        ts = _first_present(payload.get("timestamp"), event.get("timestamp"))
        module_id = _first_present(payload.get("moduleId"), event.get("moduleId"), event.get("module"))
        message = _first_present(payload.get("message"), event.get("message"))
        opt_results = _first_present(
            payload.get("optimization_results"),
            payload.get("optimizationResults"),
        )
        opt_run = _first_present(payload.get("optimization_run"), payload.get("optimizationRun"))
        solution_time = payload.get("solutionTime")
        total_time = payload.get("totalTime")

        doc = {
            "timestamp": ts,
            "message": message,
            "moduleId": module_id,
            "optimization_results": opt_results,
            "optimization_run": opt_run,
            "solutionTime": solution_time,
            "totalTime": total_time,
        }

        logger.info(f"[KAFKA-INP][CRF-OPT] module={module_id} ts={ts}")
        es.index(index=CRF_OPT_INDEX, document=doc, refresh="wait_for")
        logger.info(f"[ES] Indexed CRF optimization of '{doc} into '{CRF_OPT_INDEX}'")
    except Exception as e:
        logger.error(f"Failed to index CRF optimization: {e}")
        logger.debug(f"Payload: {json.dumps(event, indent=2)}")


def handle_crf_picking_sequence_simulation(event):
   
    try:
        create_index_if_missing(CRF_SIM_INDEX, mappings=CRF_SIM_RESULT_MAPPINGS)
        payload = event.get("results") if isinstance(event, dict) and isinstance(event.get("results"), dict) else event

        ts = _first_present(payload.get("timestamp"), event.get("timestamp"))
        module_id = _first_present(payload.get("moduleId"), event.get("moduleId"), event.get("module"))
        message = _first_present(payload.get("message"), event.get("message"))

        simulation_run = _first_present(payload.get("simulation_run"), payload.get("simulationRun"))
        solution_time = payload.get("solutionTime")
        total_time = payload.get("totalTime")

        baseline = _first_present(payload.get("baseline"))
        best_phase = _first_present(payload.get("best_phase"), payload.get("bestPhase"))

        doc = {
            "timestamp": ts,
            "message": message,
            "moduleId": module_id,
            "simulation_run": simulation_run,
            "solutionTime": solution_time,
            "totalTime": total_time,
            "baseline": baseline,
            "best_phase": best_phase,
        }

        logger.info(f"[KAFKA-INP][CRF-SIM] module={module_id} ts={ts}")
        es.index(index=CRF_SIM_INDEX, document=doc, refresh="wait_for")
        logger.info(f"[ES] Indexed CRF simulation of '{doc} into '{CRF_SIM_INDEX}'")
    except Exception as e:
        logger.error(f"Failed to index CRF simulation: {e}")
        logger.debug(f"Payload: {json.dumps(event, indent=2)}")



def _case_to_index(case: str) -> str:
    case = (case or "").lower()
    if case == "opt":
        return OPT_CONFIG_INDEX
    if case == "sim":
        return SIM_CONFIG_INDEX
    raise HTTPException(status_code=400, detail="case must be 'opt' or 'sim'")

def _ensure_config_index(index_name: str):
    create_index_if_missing(index_name, mappings=CONFIG_MAPPINGS)

def _summarize_config(parsed: dict):
    try:
        containers_obj = parsed.get("containers_opt") or parsed.get("containers_sim") or {}
        kit_holders_obj = parsed.get("kit_holders_opt") or parsed.get("kit_holders_sim") or {}
        distance_list = parsed.get("distance_matrix_opt") or parsed.get("distance_matrix_sim") or []

        containers = len(containers_obj) if isinstance(containers_obj, dict) else None
        kit_holders = len(kit_holders_obj) if isinstance(kit_holders_obj, dict) else None
        distance_edges = len(distance_list) if isinstance(distance_list, list) else None

        return {
            "containers": containers,
            "kitHolders": kit_holders,
            "distanceEdges": distance_edges,
        }
    except Exception:
        return {}


# ---------------------------------
# FastAPI models & app
# ---------------------------------


class DriftPayload(BaseModel):
    # IDs / required
    moduleId: str = Field(..., min_length=1)
    component: str = Field(..., min_length=1)

    # UI form fields (all required όπως το Angular validation σου τώρα)
    stage: str = Field(..., min_length=1)
    cell: str = Field(..., min_length=1)
    failureType: str = Field(..., min_length=1)
    failureDescription: str = Field(..., min_length=1)
    maintenanceAction: str = Field(..., min_length=1)
    componentReplacement: str = Field(..., min_length=1)
    workerName: str = Field(..., min_length=1)
    driftDone: bool = Field(...)

    # generic timestamp from UI and lifecycle all ISO
    timestamp: str  
    starttime: str 
    endtime: str    

    # optional module name
    module: Optional[str] = None

app = FastAPI(title="Process Drift API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN] if FRONTEND_ORIGIN != "*" else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/healthz")
def healthz():
    ok_es = False
    try:
        es.info()
        ok_es = True
    except Exception:
        ok_es = False
    return {
        "ok": True,
        "elastic_ok": ok_es,
        "kafka_enabled": RUN_MODE in ("kafka", "both"),
        "kafka_ready": kafka_ready,
        "mode": RUN_MODE,
        "time": datetime.utcnow().isoformat() + "Z",
    }


def _search_es(index: str, module_id: Optional[str], smart_service_id: Optional[str], from_: int, size: int):
    must = []
    if module_id:
        must.append({"term": {"moduleId": module_id}})
    if smart_service_id:
        must.append({"term": {"smartServiceId": smart_service_id}})

    query = {"bool": {"must": must}} if must else {"match_all": {}}

    resp = es.search(
        index=index,
        body={
            "query": query,
            "from": from_,
            "size": size,
            "sort": [{"timestamp": {"order": "desc", "unmapped_type": "date"}}],
        },
    )
    hits = resp.get("hits", {}).get("hits", [])
    return [{"id": h.get("_id"), **h.get("_source", {})} for h in hits]

def _case_doc_id(case: str) -> str:
    case = (case or "").lower()
    if case not in ("opt", "sim"):
        raise HTTPException(status_code=400, detail="case must be 'opt' or 'sim'")
    return f"{case}-current"


@app.post("/config/upload/{case}")
async def upload_config_file_case(
    case: str = Path(..., description="Either 'opt' or 'sim'"),
    file: UploadFile = File(...),
):
    if not file.filename.lower().endswith(".json"):
        raise HTTPException(status_code=400, detail="Only .json files are accepted")

    raw = await file.read()
    if len(raw) > MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=413, detail="File too large")

    raw_text = raw.decode("utf-8", errors="replace")

    import hashlib
    etag = hashlib.sha256(raw).hexdigest()

    try:
        parsed = json.loads(raw_text)
    except Exception:
        parsed = None  

    index_name = _case_to_index(case)
    _ensure_config_index(index_name)

    doc = {
        "filename": file.filename,
        "uploadedAt": datetime.utcnow().isoformat() + "Z",
        "rawText": raw_text,
        "config": parsed if isinstance(parsed, dict) else None,
        "case": case,
        "etag": etag,
    }

    try:
        es.index(index=index_name, id=_case_doc_id(case), document=doc, refresh="wait_for")
    except Exception as e:
        logger.error(f"Failed to index config ({case}): {e}")
        raise HTTPException(status_code=500, detail="Failed to store config")

    summary = _summarize_config(parsed or {})
    return {"ok": True, "case": case, "filename": file.filename, "summary": summary, "id": etag}




@app.post("/config/upload/fft/opt")
async def upload_config_fft_case(
    file: UploadFile = File(...),
):
    if not file.filename.lower().endswith(".json"):
        raise HTTPException(status_code=400, detail="Only .json files are accepted")

    raw = await file.read()
    if len(raw) > MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=413, detail="File too large")

    raw_text = raw.decode("utf-8", errors="replace")

    import hashlib
    etag = hashlib.sha256(raw).hexdigest()

    try:
        parsed = json.loads(raw_text)
    except Exception:
        parsed = None  

    index_name = OPT_FFT_CONFIG_INDEX
    _ensure_config_index(index_name)

    doc = {
        "filename": file.filename,
        "uploadedAt": datetime.utcnow().isoformat() + "Z",
        "rawText": raw_text,
        "config": parsed if isinstance(parsed, (dict, list)) else None,
        "case": "opt-fft",
        "etag": etag,
    }

    try:
        es.index(index=index_name, id=etag, document=doc, refresh="wait_for")
    except Exception as e:
        logger.error(f"Failed to index FFT opt config: {e}")
        raise HTTPException(status_code=500, detail="Failed to store config")

    summary = {}
    if isinstance(parsed, list):
        try:
            module_names = [x.get("module_name") for x in parsed if isinstance(x, dict)]
            summary = {
                "items": len(parsed),
                "moduleNames": [m for m in module_names if m],
            }
        except Exception:
            summary = {"items": len(parsed)}
    elif isinstance(parsed, dict):
        summary = _summarize_config(parsed or {})  # αν θέλεις reuse

    return {"ok": True, "case": "opt", "filename": file.filename, "summary": summary, "id": etag}


@app.get("/robot-config/fft")
def get_robot_config_fft(module_id: Optional[str], module_name: Optional[str] = Query(None, alias="moduleName")):
    """
    Returns robotConfiguration
    """
    try:
        must = [{"term": {"moduleId": module_id}}]
        query = {"bool": {"must": must}}

        resp = es.search(
            index=ROBOT_CONFIG_FFT_INDEX,
            body={
                # "query": query,
                "size": 1,
                "sort": [
                    {"uploadedAt": {"order": "desc", "unmapped_type": "date"}},
                    {"_score": {"order": "desc"}}
                ],
            },
        )
        hits = resp.get("hits", {}).get("hits", []) or []

        if not hits and module_name:
            resp2 = es.search(
                index=ROBOT_CONFIG_FFT_INDEX,
                body={
                    "query": {"term": {"module_name": module_name}},
                    "size": 1,
                    "sort": [
                        {"uploadedAt": {"order": "desc", "unmapped_type": "date"}},
                        {"_score": {"order": "desc"}}
                    ],
                },
            )
            hits = resp2.get("hits", {}).get("hits", []) or []

        if not hits:
            raise HTTPException(status_code=404, detail="No robot configuration found for given module")

        hit = hits[0]
        src = hit.get("_source", {})
        robot_cfg = _extract_robot_config(src)

        if not robot_cfg:
            raise HTTPException(status_code=422, detail="Document found but robotConfiguration is missing or unreadable")

        return {
            "ok": True,
            "moduleId": module_id,
            "moduleName": module_name,
            "id": hit.get("_id"),
            "robotConfiguration": robot_cfg,
            "documentMeta": {
                "uploadedAt": src.get("uploadedAt"),
                "index": ROBOT_CONFIG_FFT_INDEX,
            }
        }

    except NotFoundError:
        raise HTTPException(status_code=404, detail="Index not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch robot config for '{module_id}': {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch robot configuration")



@app.get("/config/current/{case}")
def get_current_config(case: str = Path(..., description="Either 'opt' or 'sim'")):
    index_name = _case_to_index(case)
    doc_id = _case_doc_id(case)
    try:
        res = es.get(index=index_name, id=doc_id)
        return {"ok": True, "case": case, "document": res["_source"], "id": doc_id}
    except NotFoundError:
        raise HTTPException(status_code=404, detail="No current config found")

# ---------------------------------
# Kafka consumer loop (thread)
# ---------------------------------
def kafka_loop():
    logger.info("Kafka consumer thread starting...")
    try:
        init_kafka()
    except Exception:
        logger.error("Kafka init failed; consumer thread not started.")
        return

    message_count = 0
    try:
        while not stop_event.is_set():
            msg = consumer.poll(timeout_ms=500)
            if not msg:
                continue
            for tp, records in msg.items():
                for record in records:
                    message_count += 1
                    topic = record.topic
                    event = record.value
                    kkey = getattr(record, "key", None)

                    # DROP of empty events
                    if _is_blank(event):
                        logger.warning(f"[Kafka] Dropping blank/invalid event from '{topic}' (key='{kkey}')")
                        continue

                    if not isinstance(event, dict):
                        logger.warning(f"[Kafka] Dropping non-dict event from '{topic}': {type(event)}")
                        continue

                    if topic not in TOPICS_ALLOWING_NULL_RESULTS:
                        if "results" in event and event["results"] is None:
                            logger.warning(f"[Kafka] Dropping event {event} from '{topic}' because results is null)")
                            continue


                    logger.info(f"[Kafka] #{message_count} from '{topic}' key='{kkey}'")
                    try:
                        if topic == "modapto-module-creation":
                            handle_module_creation(event, record)
                        elif topic == "modapto-module-update":
                            handle_module_update(event, record)
                        elif topic == "modapto-module-deletion":
                            handle_module_deletion(event)
                        elif topic in ["smart-service-assigned", "smart-service-unassigned"]:
                            handle_smart_service_event(event, topic, record)
                        elif topic == GROUPING_TOPIC:
                            handle_grouping_predictive_maintenance(event)
                        elif topic == THRESHOLD_TOPIC:
                            handle_threshold_predictive_maintenance(event)
                        elif topic == "base64-input-events":
                            logger.info("Handling base64 encoded input...")
                            decode_base64_event(event)
                        elif topic == PROD_OPT_TOPIC:
                            logger.info("Handling SEW optimization output...")
                            handle_production_schedule_optimization(event)
                        elif topic == PROD_SIM_TOPIC:
                            logger.info("Handling SEW simulation output...")
                            handle_production_schedule_simulation(event)
                        elif topic == CRF_SA_TOPIC:
                            logger.info("Handling CRF self-awareness wear detection...")
                            handle_crf_sa_wear_detection_event(event)
                        elif topic == SA1_KPIS_TOPIC:
                            logger.info("Handling SEW SA1 monitoring KPIs...")
                            handle_sa1_kpis_event(event)
                        elif topic == SA2_MONITORING_TOPIC:
                            logger.info("Handling SEW SA2 real-time monitoring...")
                            handle_sa2_monitoring_event(event)
                        elif topic == MQTT_TOPIC:
                            if kkey == "production-schedule-optimization":
                                logger.info("[MQTT] Routed to production-schedule-optimization")
                                handle_production_schedule_optimization(event)
                            elif kkey == "production-schedule-simulation":
                                logger.info("[MQTT] Routed to production-schedule-simulation")
                                handle_production_schedule_simulation(event)
                            elif kkey == "kh-picking-sequence-optimization":
                                logger.info("[MQTT] Routed to kh-picking-sequence-optimization")
                                handle_crf_picking_sequence_optimization(event)
                            elif kkey == "kh-picking-sequence-simulation":
                                logger.info("[MQTT] Routed to kh-picking-sequence-simulation")
                                handle_crf_picking_sequence_simulation(event)
                            else:
                                logger.warning(f"[MQTT] Unknown key '{kkey}' - ignoring")
                        else:
                            logger.warning(f"Unknown topic received: '{topic}'")
                        
                        logger.info(f"[Kafka] processed from '{topic}'")
                    except Exception as e:
                        logger.error(f"[Kafka] Error processing message from '{topic}': {e}")
                        logger.debug(f"Failed event data: {json.dumps(event, indent=2)}")
                        continue
    except Exception as e:
        logger.error(f"[Kafka] Fatal loop error: {e}")
    finally:
        logger.info("[Kafka] Closing consumer/producer...")
        try:
            if consumer:
                consumer.close()
            if producer:
                producer.close()
        except Exception as e:
            logger.error(f"Kafka Error on close: {e}")
        logger.info("[Kafka] Thread exit.")

# ---------------------------------
# Entrypoint helpers
# ---------------------------------
def run_api_blocking():
    import uvicorn
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "5000"))
    logger.info(f"Starting FastAPI on {host}:{port} (CORS origin: {FRONTEND_ORIGIN})")
    uvicorn.run(app, host=host, port=port, log_level="info")

def main_both():
    t = threading.Thread(target=kafka_loop, name="kafka-consumer", daemon=True)
    t.start()
    run_api_blocking()
    stop_event.set()
    t.join(timeout=5)

def main_kafka_only():
    kafka_loop()

def main_api_only():
    run_api_blocking()

def signal_handler(sig, frame):
    logger.info(f"Signal {sig} received; shutting down...")
    stop_event.set()
    time.sleep(0.5)
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# ----------------------------------
# Main
# ----------------------------------
if __name__ == "__main__":
    if RUN_MODE == "both":
        main_both()
    elif RUN_MODE == "kafka":
        main_kafka_only()
    elif RUN_MODE == "api":
        main_api_only()
    else:
        logger.warning(f"Unknown RUN_MODE '{RUN_MODE}', defaulting to 'both'")
        main_both()