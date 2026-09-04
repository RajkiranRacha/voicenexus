import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.config import config
from app.api.routes.telemetry import router as telemetry_router
from app.api.routes.agent import router as agent_router
from app.api.routes.admin import router as admin_router
from app.api.websocket_call import router as call_ws_router

app = FastAPI(
    title="VoiceNexus Conversational IVR Platform",
    description="Enterprise AI IVR Platform engineered for high-containment customer care.",
    version="1.0.0"
)

# Enable CORS for local and web clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API and WebSocket Routers
app.include_router(telemetry_router)
app.include_router(agent_router)
app.include_router(admin_router)
app.include_router(call_ws_router)


@app.get("/api/health")
def health_check():
    return {
        "status": "HEALTHY",
        "service": "VoiceNexus IVR Platform",
        "version": "1.0.0",
        "operator": config.OPERATOR_NAME,
        "voice": config.DEFAULT_VOICE,
        "language": config.LANGUAGE,
        "voice_rate": config.VOICE_RATE,
        "regulatory_disclosure_enabled": config.REGULATORY_DISCLOSURE_ENABLED
    }

# Mount built frontend static files if present
frontend_dist = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist"))
if os.path.exists(frontend_dist):
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=config.HOST, port=config.PORT, reload=True)
