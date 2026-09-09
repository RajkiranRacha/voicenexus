import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.types import Scope
from starlette.responses import Response
from app.config import config


class SPAStaticFiles(StaticFiles):
    """
    Vite's build hashes every JS/CSS filename (e.g. assets/index-CX4G6Vq3.js),
    so those can be cached forever -- but the default StaticFiles response has
    no explicit Cache-Control at all, which leaves browsers free to apply
    their own (often long) heuristic caching to index.html. Since index.html
    is what points at the current hashed bundle, a stale cached copy of it
    silently keeps serving an old JS bundle after every rebuild/deploy, with
    no visible error -- clicks land in dead code with no console output.
    Force index.html (and any HTML-mode fallback) to always revalidate,
    while hashed assets stay immutable.
    Also handles SPA client-side routes (/customer, /agent, /ops, /admin, etc.)
    by falling back to index.html instead of returning 404.
    """

    async def get_response(self, path: str, scope: Scope) -> Response:
        normalized = path.replace("\\", "/").lstrip("/")
        try:
            response = await super().get_response(path, scope)
            if response.status_code == 404 and not normalized.startswith("api/"):
                fallback_resp = await super().get_response("index.html", scope)
                fallback_resp.headers["Cache-Control"] = "no-cache"
                return fallback_resp
        except Exception:
            if not normalized.startswith("api/"):
                fallback_resp = await super().get_response("index.html", scope)
                fallback_resp.headers["Cache-Control"] = "no-cache"
                return fallback_resp
            raise

        if normalized.startswith("assets/"):
            response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
        else:
            response.headers["Cache-Control"] = "no-cache"
        return response
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
    app.mount("/", SPAStaticFiles(directory=frontend_dist, html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=config.HOST, port=config.PORT, reload=True)
