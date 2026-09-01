from fastapi import FastAPI
from config import lifespan, setup_cors, setup_telemetry
from routers.chat import register_chat_routes
from routers.health import register_health_routes

app = FastAPI(title="SRE GenAI Agent Backend", lifespan=lifespan)

setup_cors(app)

register_chat_routes(app)
register_health_routes(app)

setup_telemetry(app)
