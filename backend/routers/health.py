from fastapi import FastAPI

def register_health_routes(app: FastAPI):
    @app.get("/health")
    def health():
        return {"status": "healthy"}
