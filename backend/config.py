import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from cors import add_cors, parse_allowed_origins
import firebase_admin
from google.cloud import firestore as gcloud_firestore

from telemetry import setup_logging, init_telemetry, flush_telemetry, setup_telemetry

project_id = os.getenv("PROJECT_ID")
service_name = os.getenv("K_SERVICE") or os.getenv("SERVICE_NAME")
if not service_name:
    raise RuntimeError("Missing required service name: set K_SERVICE or SERVICE_NAME.")

# Initialize logging and OpenTelemetry
setup_logging(project_id=project_id)
init_telemetry(service_name=service_name, project_id=project_id)

if not firebase_admin._apps:
    firebase_admin.initialize_app()

database_id = os.getenv("FIRESTORE_DATABASE")
if not database_id:
    raise RuntimeError("FIRESTORE_DATABASE environment variable is required but not set.")

db = gcloud_firestore.Client(database=database_id)


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    flush_telemetry()


def setup_cors(app: FastAPI):
    add_cors(app, parse_allowed_origins(os.getenv("ALLOWED_ORIGINS")))
